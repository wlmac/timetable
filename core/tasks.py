import os 
import datetime as dt
import functools
from pathlib import Path

import pytz
import requests
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import F, JSONField, Q, Value
from django.db.models.functions.text import Concat
from django.utils import timezone
from django.utils.translation import gettext_lazy as _l
from django.utils.translation import ngettext
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushTicketError,
)
from oauth2_provider.models import clear_expired
from requests.exceptions import ConnectionError, HTTPError

import gspread 
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from core.models import Announcement, BlogPost, Comment, Event, User, DailyAnnouncement
from core.utils.tasks import get_random_username
from metropolis.celery import app

logger = get_task_logger(__name__)
session = requests.Session()
session.headers.update(
    {
        # "Authorization": f"Bearer {os.getenv('EXPO_TOKEN')}", # TODO: expo push notifications authn?
        "accept": "application/json",
        "accept-encoding": "gzip, deflate",
        "content-type": "application/json",
    }
)
for m in ("get", "options", "head", "post", "put", "patch", "delete"):
    setattr(
        session,
        m,
        functools.partial(
            getattr(session, m), timeout=settings.NOTIF_EXPO_TIMEOUT_SECS
        ),
    )


def users_with_token():
    return User.objects.exclude(Q(expo_notif_tokens=Value({}, JSONField())))


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=0, minute=0), delete_expired_users)
    sender.add_periodic_task(crontab(hour=18, minute=0), notif_events_singleday)
    sender.add_periodic_task(crontab(day_of_month=1), run_group_migrations)
    sender.add_periodic_task(
        crontab(hour=1, minute=0), clear_expired
    )  # Delete expired oauth2 tokens from db everyday at 1am

    sender.add_periodic_task(crontab(hour=8, minute=0, day_of_week="mon-fri"), fetch_announcements)


@app.task
def delete_expired_users():
    """Scrub user data from inactive accounts that have not logged in for 14 days. (marked deleted)"""
    queryset = User.objects.filter(
        is_deleted=True,
        last_login__lt=dt.datetime.now() - dt.timedelta(days=14),
    )
    comments = Comment.objects.filter(author__in=queryset)
    comments.update(
        body=None, last_modified=timezone.now()
    )  # if body is None "deleted on %last_modified% would be shown
    queryset.update(  # We need to object to not break posts or comments
        first_name="Deleted",
        last_name="User",
        username=get_random_username(),
        bio="",
        timezone="",
        graduating_year=None,
        is_teacher=False,
        organizations=[],
        tags_following=[],
        qltrs=None,
        saved_blogs=[],
        saved_announcements=[],
        expo_notif_tokens={},
    )
    queryset.update(email=Concat(F("random_username"), Value("@maclyonsden.com")))


@app.task
def run_group_migrations():
    from scripts.migrations import migrate_groups

    print(migrate_groups())


@app.task
def notif_broker_announcement(obj_id):
    if not settings.NOTIFICATIONS_ENABLED:
        return
    logger.info(f"notif_broker_announcement for {obj_id}")
    try:
        ann = Announcement.objects.get(id=obj_id)
    except Announcement.DoesNotExist:
        logger.warning(
            f"notif_broker_announcement: announcement {obj_id} does not exist"
        )
        return
    affected = users_with_token()
    if ann.organization.id in settings.ANNOUNCEMENTS_NOTIFY_FEEDS:
        category = "ann.public"
    else:
        affected = affected.filter(
            Q(tags_following__in=ann.tags.all())
            | Q(organizations__in=[ann.organization])
        )
        category = "ann.personal"
    for u in affected.all():
        notif_single.delay(
            u.id,
            dict(
                title=_l("New Announcement: %(title)s") % dict(title=ann.title),
                body=ann.body,
                category=category,
            ),
        )


@app.task
def notif_broker_blogpost(obj_id):
    logger.info(f"notif_broker_blogpost for {obj_id}")
    try:
        post = BlogPost.objects.get(id=obj_id)
    except BlogPost.DoesNotExist:
        logger.warning(f"notif_broker_blogpost: blogpost {obj_id} does not exist")
        return
    if settings.NOTIFICATIONS_ENABLED:
        affected = users_with_token()
        for u in affected.all():
            notif_single.delay(
                u.id,
                dict(
                    title=_l("New Blog Post: %(title)s") % dict(title=post.title),
                    body=post.body,
                    category="blog",
                ),
            )


@app.task
def notif_events_singleday(date: dt.date = None):
    if not settings.NOTIFICATIONS_ENABLED:
        return
    tz = pytz.timezone(settings.TIME_ZONE)
    if date is None:
        date = dt.date.today() + dt.timedelta(days=1)
    elif isinstance(date, str):  # ken things
        date = dt.datetime.fromisoformat(date)
        raise RuntimeError(f"date {type(date)} {date}")
    eligible = users_with_token()
    for u in eligible.all():
        # assume we don't have 10 million events overlapping a single day (we can't fit it in a single notif aniway)
        date_mintime = tz.localize(dt.datetime.combine(date, dt.datetime.min.time()))
        date_maxtime = tz.localize(dt.datetime.combine(date, dt.datetime.max.time()))
        covering = list(
            Event.get_events(u)
            .filter(
                start_date__lte=date_maxtime,
                end_date__gte=date_mintime,
            )
            .all()
        )
        if len(covering) == 0:
            continue
        covering.sort(key=lambda e: int(e.schedule_format == "default"))
        covering.sort(key=lambda e: e.start_date - date_mintime)
        body = ngettext(
            "%(count)d Event:\n",
            "%(count)d Events:\n",
            len(covering),
        ) % dict(count=len(covering))
        for i, e in enumerate(covering):
            body += _l("%(i)d. %(title)s\n") % dict(i=i + 1, title=e.name)
        headline = covering[0]
        notif_single.delay(
            u.id,
            dict(
                title=_l("%(date)s: %(headline)s")
                % dict(date=date.strftime("%a %b %d"), headline=headline.name),
                body=body,
                category="event.singleday",
            ),
        )


@app.task(bind=True)
def notif_single(self, recipient_id: int, msg_kwargs):
    if not settings.NOTIFICATIONS_ENABLED:
        return
    recipient = User.objects.get(id=recipient_id)
    logger.info(
        f"notif_single to {recipient} ({recipient.expo_notif_tokens}): {msg_kwargs}"
        + ("(dry run)" if settings.NOTIF_DRY_RUN else "")
    )
    if settings.NOTIF_DRY_RUN:
        return
    notreg_tokens = set()
    for token, options in recipient.expo_notif_tokens.items():
        if options is not None:
            allowlist = options.get("allow")
            if (
                isinstance(allowlist, dict)
                and msg_kwargs["category"] not in allowlist.keys()
            ):
                logger.info(
                    f"notif_single (category {msg_kwargs['category']}) not allowed to {recipient} (allowlist {allowlist}) ({recipient.expo_notif_tokens}): {msg_kwargs}"
                    + ("(dry run)" if settings.NOTIF_DRY_RUN else "")
                )
                continue
        try:
            resp = PushClient(session=session).publish(
                PushMessage(to=f"ExponentPushToken[{token}]", **msg_kwargs)
            )
        except (ConnectionError, HTTPError) as exc:
            raise self.retry(exc=exc)
        try:
            resp.validate_response()
        except DeviceNotRegisteredError:
            notreg_tokens.add(token)
        except PushTicketError as exc:
            raise self.retry(exc=exc)
    if notreg_tokens:
        u = User.objects.filter(id=recipient_id).first()
        for token in notreg_tokens:
            del u.expo_notif_tokens[token]
        u.save()


def load_client() -> tuple[gspread.Client | None, str | None, bool]:
    """
    Returns a client from authorized_user.json file 

    :returns: Tuple with the client, error message and 
    whether the client secret file exists 
    """
    CLIENT_PATH = settings.SECRETS_PATH + "/client_secret.json"
    AUTHORIZED_PATH = settings.SECRETS_PATH + "/authorized_user.json"

    if not Path(settings.SECRETS_PATH).is_dir():
        return (None, f"{settings.SECRETS_PATH} directory does not exist", False)
    
    if not Path(CLIENT_PATH).is_file():
        return (None, f"{CLIENT_PATH} does not exist", False)
    
    client = None 
    scopes = gspread.auth.READONLY_SCOPES

    if Path(AUTHORIZED_PATH).is_file():
        creds = None 

        try:
            creds = Credentials.from_authorized_user_file(AUTHORIZED_PATH, scopes)
        except Exception as e:
            return (None, "Failed to load credentials", True) 

        if not creds.valid and creds.expired and creds.refresh_token:

            try:
                creds.refresh(Request())
            except Exception as e:
                return (None, "Failed to refresh credentials", True)

            with open(AUTHORIZED_PATH, "w") as f:
                f.write(creds.to_json())

        try:
            client = gspread.authorize(creds)
        except Exception as e:
            return (None, "Failed to authorize credentials", True)

        return (client, None, True) 

    else:
        return (None, "No file to load client from", True) 

@app.task
def fetch_announcements():
    if settings.GOOGLE_SHEET_KEY == "" or settings.GOOGLE_SHEET_KEY == None:
        logger.warning(f"Fetch Announcements: GOOGLE_SHEET_KEY is empty")
        return 

    client, error_msg, client_path_exists = load_client()

    if client == None:
        if client_path_exists:
            logger.warning(f"Fetch Announcements: {error_msg} - Run auth_google to fix")
        else:
            logger.warning(f"Fetch Announcements: {error_msg}")
        
        return 
    
    worksheet = None 

    try:
        worksheet = client.open_by_key(settings.GOOGLE_SHEET_KEY).sheet1    
    except Exception as e:
        logger.warning("Fetch Announcements: Failed to open google sheet")
        return

    row_counter = 1 
    while True:

        data = [] 

        try:
            data = [value.strip() for value in worksheet.row_values(row_counter)]
        except:
            logger.warning(f"Fetch Announcements: Failed to read row {row_counter}")
            break 

        if row_counter == 1:
            if data != data != ['Timestamp', 'Email Address', "Today's Date", 'Student Name (First and Last Name), if applicable.', 'Staff Advisor', 'Club', 'Start Date announcement is to be read (max. 3 consecutive school days).', 'End Date announcement is to be read', 'Announcement to be read (max 75 words)']:
                logger.warning("Fetch Announcements: Header row does not match")
                break
        else:
            if data == []:
                break
            else:
                try:
                    parsed_data = {
                            "organization": data[5],
                            "start_date": dt.datetime.strptime(data[6],'%m/%d/%Y'),
                            "end_date": dt.datetime.strptime(data[7],'%m/%d/%Y'),
                            "content": data[8] 
                        }

                    DailyAnnouncement.objects.get_or_create(**parsed_data)
                except:
                    logger.warning(f"Fetch Announcements: Failed to parse or create object for row {row_counter}") 

        row_counter += 1 