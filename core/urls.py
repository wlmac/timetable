from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from .utils.sitemaps import AnnouncementsSitemap, BlogSitemap, ClubsSitemap
from .views.index import (
    AboutView,
    CalendarFeed,
    CalendarView,
    Index,
    Json,
    Justinian,
    MapView,
    Teapot,
)
from .views.organization import OrganizationDetail, OrganizationList, OrganizationShort
from .views.post import (
    AnnouncementCards,
    AnnouncementDetail,
    AnnouncementFeed,
    AnnouncementList,
    AnnouncementTagList,
    BlogPostCards,
    BlogPostDetail,
    BlogPostList,
    BlogPostTagList,
    ExhibitList,
)
from .views.raffle import RaffleRedirect
from .views.timetable import (
    CourseCreate,
    TimetableCreate,
    TimetableList,
    TimetableUpdate,
)
from .views.tv import TVClubView, TVView
from .views.user import Profile, ProfileRedirect, ProfileUpdate

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path(
        "sitemap.xml",
        sitemap,
        {
            "sitemaps": {
                "blog": BlogSitemap,
                "announcements": AnnouncementsSitemap,
                "clubs": ClubsSitemap,
                # "flatpages": FlatPageSitemap
            }
        },
        name="django.contrib.sitemaps.sitemaps",
    ),
    path("api/", include("core.api.urls")),
    path("timetable", TimetableList.as_view(), name="timetable_list"),
    path(
        "timetable/add/term/<int:pk>",
        TimetableCreate.as_view(),
        name="timetable_create",
    ),
    path(
        "timetable/edit/<int:pk>",
        TimetableUpdate.as_view(),
        name="timetable_update",
    ),
    path(
        "course/add/term/<int:pk>",
        CourseCreate.as_view(),
        name="course_create",
    ),
    path("accounts/profile", ProfileRedirect.as_view(), name="profile_redirect"),
    path(
        "accounts/profile/update",
        ProfileUpdate.as_view(),
        name="profile_update",
    ),
    path("user/<str:slug>", Profile.as_view(), name="profile_detail"),
    path("clubs", OrganizationList.as_view(), name="organization_list"),
    path(
        "club/<str:slug>",
        OrganizationDetail.as_view(),
        name="organization_detail",
    ),
    path("announcements", AnnouncementList.as_view(), name="announcement_list"),
    path(
        "announcement/<int:pk>",
        AnnouncementDetail.as_view(),
        name="announcement_detail",
    ),
    path(
        "announcements/tag/<int:tag>",
        AnnouncementTagList.as_view(),
        name="announcement_tag_list",
    ),
    path("announcements/feed", AnnouncementFeed(), name="announcement_feed"),
    path("gallery", ExhibitList.as_view(), name="exhibit_list"),
    path("blog", BlogPostList.as_view(), name="blogpost_list"),
    path("blog/<str:slug>", BlogPostDetail.as_view(), name="blogpost_detail"),
    path(
        "blog/tag/<int:tag>",
        BlogPostTagList.as_view(),
        name="blogpost_tag_list",
    ),
    path("calendar", CalendarView.as_view(), name="calendar"),
    path("calendar.ics", CalendarFeed(), name="calendar_ical"),
    path("map", MapView.as_view(), name="map"),
    path("about", AboutView.as_view(), name="about"),
    path("teapot", Teapot.as_view(), name="teapot"),
    path("justinian", Justinian.as_view(), name="justinian"),
    path("json", Json.as_view(), name="json"),
    path("tv", TVView.as_view(), name="tv"),
    path("tv/clubs", TVClubView.as_view(), name="tvclub"),
    path("c/<int:pk>", OrganizationShort.as_view(), name="organization_short"),
    path("raffle", RaffleRedirect.as_view(), name="raffle"),
    path("hijack/", include("hijack.urls")),
]

if settings.LAZY_LOADING:
    urlpatterns += [
        path(
            "announcements/cards",
            AnnouncementCards.as_view(),
            name="api_announcements_card",
        ),
        path(
            "blogs/cards",
            BlogPostCards.as_view(),
            name="api_blog_card",
        ),
    ]
