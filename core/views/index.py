from typing import Dict, List, Union

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django_ical.views import ICalFeed

from core.utils import generate_slam as gs
from core.utils import get_week_schedule_info

from .. import models
from ..api.views.staff import StaffSerializer
from ..models import StaffMember
from . import mixins


class Index(TemplateView, mixins.TitleMixin):
    template_name = "core/index.html"
    title = "Home"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["announcements"] = models.Announcement.get_all(user=self.request.user)[
            :3
        ]

        datetime_now = timezone.localtime()

        def events1():
            return (
                models.Event.get_events(user=self.request.user)
                .filter(end_date__gte=datetime_now)
                .order_by("start_date")
            )

        events = list(
            events1().filter(
                ~Q(schedule_format="default"),
            )[:1]
        )
        events += events1().filter(
            Q(schedule_format="default"),
        )[: 3 - len(events)]
        context["events"] = events

        context["blogpost"] = models.BlogPost.public().first()

        context["banner_data"] = get_week_schedule_info(self.request.user)
        return context


class CalendarView(TemplateView, mixins.TitleMixin):
    template_name = "core/calendar/view.html"
    title = "Calendar"


class CalendarFeed(ICalFeed, View):
    product_id = "-//maclyonsden.com//calendar//EN"
    timezone = "UTC"
    file_name = "metropolis_school-wide.ics"

    def items(self):
        now = timezone.now()
        padding = settings.ICAL_PADDING
        return (
            models.Event.get_events(user=None)
            .filter(
                end_date__gte=now - padding,
                # todo add ?start= and ?end= to url via self.request.query_params
                start_date__lte=now + padding,
            )
            .order_by("-start_date")
        )

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return item.description

    def _is_hms(self, dt, hour, minute, second):
        return dt.hour == hour and dt.minute == minute and dt.second == second

    def item_rrule(self, item: models.Event):
        if hasattr(item, "reoccurrences") and item.reoccurrences.rule:
            return item.reoccurrences.rule
        return None

    def item_start_datetime(self, item):
        return (
            item.start_date
            if self._is_hms(item.start_date, 0, 0, 0)
            else item.start_date.date()
        )

    def item_end_datetime(self, item):
        return (
            item.end_date
            if self._is_hms(item.end_date, 23, 59, 0)
            else item.end_date.date()
        )

    def item_link(self, item):
        return reverse("calendar") + f"?pk={item.pk}"  # NOTE: workaround for UID

    def item_categories(self, item):
        return (
            [tag.name for tag in item.tags.all()]
            + (["public"] if item.is_public else [])
            + (["instructional"] if item.is_instructional else [])
        )

    def item_author_name(self, item):
        return item.organization.name


class MapView(TemplateView, mixins.TitleMixin):
    template_name = "core/map/map.html"
    title = "Map"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapbox_apikey"] = {"apikey": settings.MAPBOX_APIKEY}
        return context


UserType = Dict[str, Union[int, str, bool, List[str]]]
PositionType = Dict[str, Union[UserType, str, List[str], bool]]  # str being None

TeamData = Dict[
    str,  # Team role (e.g., "Project Manager", "Frontend Developer", etc.)
    List[PositionType],  # List of positions and associated details
]


class AboutView(TemplateView, mixins.TitleMixin):
    template_name = "core/about/about.html"
    title = "About"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        members_data = StaffSerializer(
            StaffMember.objects.filter(is_active=True), many=True
        ).data

        # Group members based on positions and alumni status
        grouped_members = {
            position: [] for _, position in settings.METROPOLIS_POSITIONS
        }
        grouped_members["Alumni"] = []

        # Sort positions to ensure that lead positions come first

        for member in members_data:
            positions = member.get("positions", None)
            if member["is_alumni"] or positions is None:
                grouped_members["Alumni"].append(member)
                continue

            for position in positions:
                if (pol := member.get("positions_leading", None)) is not None:
                    if pol.__contains__(position):
                        grouped_members[position].insert(0, member)
                        continue
                grouped_members[position].append(member)

        context["members"] = grouped_members
        context["member_count"] = len(members_data)
        return context


class Teapot(View):
    def get(self, request):
        return HttpResponse("orz teapot", status=418)


class Justinian(View):
    def get(self, request):
        return HttpResponse(
            "orz our exalted leader justinian luxtel, waba skyflarus, as payment for his services<br>"
            + gs.justinian_slam(),
            status=402,
        )


class Json(View):
    @staticmethod
    def get(request):
        response = dict(message="hi")
        if request.user.is_authenticated:
            response["name"] = request.user.username
            response["message"] += " Json's last name is NOT DERULO"
        # check if the user "Jason Cameron" exists
        if (
            json := models.User.objects.filter(
                is_superuser=True, first_name="Jason", last_name="Cameron"
            )
        ).exists():
            response["bio"] = json.first().bio
        return JsonResponse(response, status=418)
