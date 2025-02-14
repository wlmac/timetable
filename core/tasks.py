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

from google import genai
from json import dumps, loads

from core.models import (
    Announcement,
    BlogPost,
    Comment,
    Event,
    Term,
    User,
    Organization,
    DailyAnnouncement,
    Tag,
)
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

    sender.add_periodic_task(
        crontab(hour=8, minute=0, day_of_week="mon-fri"), fetch_announcements
    )

    sender.add_periodic_task(
        crontab(hour=4, minute=0, day_of_week="mon-fri"), fetch_calendar_events
    )


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
        except Exception:
            return (None, "Failed to load credentials", True)

        if not creds.valid and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                return (None, "Failed to refresh credentials", True)

            with open(AUTHORIZED_PATH, "w") as f:
                f.write(creds.to_json())

        try:
            client = gspread.authorize(creds)
        except Exception:
            return (None, "Failed to authorize credentials", True)

        return (client, None, True)

    else:
        return (None, "No file to load client from", True)


@app.task
def fetch_announcements():
    if settings.GOOGLE_SHEET_KEY == "" or settings.GOOGLE_SHEET_KEY is None:
        logger.warning("Fetch Announcements: GOOGLE_SHEET_KEY is empty")
        return

    client, error_msg, client_path_exists = load_client()

    if client is None:
        if client_path_exists:
            logger.warning(f"Fetch Announcements: {error_msg} - Run auth_google to fix")
        else:
            logger.warning(f"Fetch Announcements: {error_msg}")

        return

    worksheet = None

    try:
        worksheet = client.open_by_key(settings.GOOGLE_SHEET_KEY).sheet1
    except Exception:
        logger.warning("Fetch Announcements: Failed to open google sheet")
        return

    row_counter = 1
    while True:
        data = []

        try:
            data = [value.strip() for value in worksheet.row_values(row_counter)]
        except Exception:
            logger.warning(f"Fetch Announcements: Failed to read row {row_counter}")
            break

        if row_counter == 1:
            if data != [
                "Timestamp",
                "Email Address",
                "Today's Date",
                "Student Name (First and Last Name), if applicable.",
                "Staff Advisor",
                "Club",
                "Start Date announcement is to be read (max. 3 consecutive school days).",
                "End Date announcement is to be read",
                "Announcement to be read (max 75 words)",
            ]:
                logger.warning("Fetch Announcements: Header row does not match")
                break
        else:
            if data == []:
                break
            else:
                try:
                    parsed_data = {
                        "organization": data[5],
                        "start_date": dt.datetime.strptime(data[6], "%m/%d/%Y"),
                        "end_date": dt.datetime.strptime(data[7], "%m/%d/%Y"),
                        "content": data[8],
                    }

                    DailyAnnouncement.objects.get_or_create(**parsed_data)
                except Exception:
                    logger.warning(
                        f"Fetch Announcements: Failed to parse or create object for row {row_counter}"
                    )

        row_counter += 1


def gemini_set_time(events):
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model = "models/gemini-1.5-flash"
    data_for_llm = []

    for event in events:
        data_for_llm.append(
            {"event": event.name, "description": event.description, "id": event.gcal_id}
        )

    prompt = f"You are a meticulous and organized secretary at a Toronto high school. Your job is to accurately set the start and ending time for events based on the information in the title or description of the event. Accuracy and consistency are paramount. You will be provided an array of events below. Each element in the array will contain the data for one event. The element will be in the format of a json object containing the name, description of the event as well as a id to identify the event. All day will be referring to the entire school day (9:00 to 15:15). Holidays, P.A days, late starts and similar events will last all day. Period 1 (P1) lasts from 9:00 to 10:20. Period 2 (P2) lasts from 10:25 to 11:40. Period 3 (P3) lasts from 12:40 to 13:55. Period 4 (P4) lasts from 14:00 to 15:15. The latest that any event finish at is 18:00 unless directly specified in the event. When outputting, output a single json object. The keys of the json object will match an id of an event that needs to have their time set and the value will be an array with two values, the starting and ending time. Use 24h hour format for time. If the event title and description does not provide enough information to determine the starting or ending time, set both to be null. Do not output anything besides the tags. \nEvents: {dumps(data_for_llm)}"

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        response = response.text.replace("```json", "").replace("```", "")

        response = loads(response)

        for event in events:
            start_time = response[event.gcal_id][0]
            end_time = response[event.gcal_id][1]

            if start_time is not None:
                start_time = dt.datetime.strptime(start_time, "%H:%M")
                event.start_date = event.start_date.replace(
                    hour=start_time.hour, minute=start_time.minute
                )
            if end_time is not None:
                end_time = dt.datetime.strptime(end_time, "%H:%M")
                event.end_date = event.end_date.replace(
                    hour=end_time.hour, minute=end_time.minute
                )

            event.save()

    except Exception:
        return "Failed to set time for events"


def gemini_tag(events):
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    model = "models/gemini-1.5-flash"

    past_events = Event.objects.filter(end_date__lte=timezone.now())[:100]

    data_for_llm = {
        "past_events": [],
        "available_tags": [tag.name for tag in Tag.objects.all()],
        "new_events": [],
    }

    for past_event in past_events:
        tags = [tag.name for tag in past_event.tags.all()]
        name = past_event.name
        description = past_event.description

        data_for_llm["past_events"].append(
            {
                "event": name,
                "description": description,
                "tags": tags,
            }
        )

    for event in events:
        data_for_llm["new_events"].append(
            {"event": event.name, "description": event.description, "id": event.gcal_id}
        )

    prompt = f"You are a meticulous and organized secretary at a Toronto high school. Your job is to accurately categorize digital calendar events by placing tags on them.  Accuracy and consistency are paramount. You will be provided an array of events below to be tagged. Each element in the array will contain the data for one event. The element will be in the format of a json object containing the name, description of the event as well as a id to identify the event. The available tags for tagging the events will be provided below to you in the format of an array (E.g ['tag 1', 'tag 2', 'tag 3', ... ]). You are only allowed to use the provided tags to tag the events. {"" if data_for_llm["past_events"] == [] else "To help with your job, you will be provided below with an array of past events that have already be properly tagged. Each element of the array will be in the format of a json object, containing the name, description and tags for the event. You can reference past events to help guide your decision process in tagging the new events. "}When outputting, output a single json object. The keys of the json object will match an id of an event that needed tagging and the value will be an array of all the tags relevant. Do not output anything besides the tags.\n\nAvailable Tags: {data_for_llm["available_tags"]}\n{"" if data_for_llm["past_events"] == [] else "Past events: " + dumps(data_for_llm["past_events"])}\nEvents to be tagged: {dumps(data_for_llm["new_events"])}"

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        response = response.text.replace("```json", "").replace("```", "")
        response = loads(response)

        tags = {}

        for event in events:
            for tag in response[event.gcal_id]:
                if tag not in tags:
                    tags[tag] = Tag.objects.get(name=tag)

                event.tags.add(tags[tag])

            event.save()

    except Exception:
        return "Failed to tag events"


@app.task
def fetch_calendar_events():
    try:
        url = f"https://www.googleapis.com/calendar/v3/calendars/{"wlmacci@gmail.com"}/events"
        url += "?fields=items(id,status,summary,description,start,end)"
        params = {
            "key": settings.GCAL_API_KEY,
            "orderBy": "startTime",
            "timeMin": dt.datetime.now(dt.UTC).isoformat(),
            "timeMax": (dt.datetime.now(dt.UTC) + dt.timedelta(days=150)).isoformat(),
            "eventTypes": "default",
            "singleEvents": "True",
            "showDeleted": "True",
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            raise Exception(
                f"{str(response.status_code)} - Failed to fetch calendar events"
            )

        gcal_eventlist = response.json().get("items", [])

    except Exception:
        logger.warning(
            "core.tasks.fetch_calendar_events: Failed to fetch Google Calendar event data"
        )
        return

    for gcal_event in gcal_eventlist:
        if gcal_event.get("summary").strip().lower() in ["day 1", "day 2"]:
            continue

        try:
            event = Event.objects.filter(gcal_id=gcal_event.get("id")).first()
            status = gcal_event.get("status")

            if event is not None and (status is None or status == "cancelled"):
                event.delete()

            elif status == "confirmed":
                summary = gcal_event.get("summary").strip().lower()

                if summary == "p.a. day":
                    schedule_format = "pa-day"
                elif "late start" in summary:
                    schedule_format = "late-start"
                elif "holiday" in summary:
                    schedule_format = "holiday"
                else:
                    schedule_format = "default"

                start_date = timezone.make_aware(
                    dt.datetime.combine(
                        dt.date.fromisoformat(gcal_event.get("start").get("date")),
                        dt.time(10),
                    )
                )
                end_date = timezone.make_aware(
                    dt.datetime.combine(
                        dt.date.fromisoformat(gcal_event.get("end").get("date"))
                        + dt.timedelta(days=-1),
                        dt.time(10, 1),
                    )
                )

                event_data = {
                    "name": gcal_event.get("summary"),
                    "organization": Organization.objects.get(slug="wlmac"),
                    "term": Term.get_current(start_date),
                    "description": gcal_event.get("description") or "",
                    "start_date": start_date,
                    "end_date": end_date,
                    "schedule_format": schedule_format,
                    "is_public": True,
                }

                Event.objects.get_or_create(
                    gcal_id=gcal_event.get("id"),
                    defaults=event_data,
                )

        except Exception:
            logger.warning(
                f"core.tasks.fetch_calendar_events: Failed to parse Google Calendar event data for event {gcal_event.get("summary")}"
            )
