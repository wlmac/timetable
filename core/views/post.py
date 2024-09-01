from typing import Optional

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.syndication.views import Feed
from django.core.paginator import EmptyPage, Paginator
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from rest_framework.exceptions import ValidationError

from core.templatetags.markdown_tags import markdown

from .. import models
from ..models import Exhibit
from . import mixins


def custom_feed(request, pk: int, limit: Optional[int] = None):
    assert models.Organization.objects.filter(
        pk=pk
    ).exists(), "pk for feed doesn't exist"
    custom_feed_organization = models.Organization.objects.get(pk=pk)
    feed = custom_feed_organization.get_feed(user=request.user)
    return (
        custom_feed_organization,
        feed if limit is None else feed[:limit],
    )


class AnnouncementCards(TemplateView):
    template_name = "core/announcement/cards.html"

    def dispatch(self, request, *args, **kwargs):
        self.page = request.GET.get("page", None)
        if not isinstance(self.page, str):
            return HttpResponseBadRequest("invalid page")
        if not self.page.isnumeric():
            return HttpResponseBadRequest("invalid page (non-numeric)")
        self.feed = request.GET.get("feed", None)
        if self.feed == "my":
            if not self.request.user.is_authenticated:
                return HttpResponseForbidden("not authenticated")
        elif self.feed == "all":
            pass
        else:
            if not isinstance(self.feed, str):
                return HttpResponseBadRequest("invalid feed")
            if not self.feed.isnumeric():
                return HttpResponseBadRequest("invalid feed (non-numeric)")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.feed == "my":
            feed = self.request.user.get_feed()
        elif self.feed == "all":
            feed = models.Announcement.get_all(user=self.request.user)
        else:
            feed = custom_feed(self.request, int(self.feed))[1]
        paginator = Paginator(feed, settings.LAZY_LOADING["per_page"])
        try:
            self.posts = paginator.page(self.page)
        except EmptyPage:
            self.posts = paginator.page(paginator.num_pages)
        context["feed"] = self.posts
        context["has_next"] = self.posts.has_next()
        return context


class AnnouncementList(TemplateView, mixins.TitleMixin):
    template_name = "core/announcement/list.html"
    title = "Announcements"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if settings.LAZY_LOADING:
            context["lazy_loading"] = True
            context["initial_limit"] = settings.LAZY_LOADING["initial_limit"]
            context["per_page"] = settings.LAZY_LOADING["per_page"]

        context["feed_all"] = models.Announcement.get_all(user=self.request.user)
        if settings.LAZY_LOADING:
            context["feed_all"] = context["feed_all"][
                : settings.LAZY_LOADING["initial_limit"]
            ]

        if self.request.user.is_authenticated:
            context["feed_my"] = self.request.user.get_feed()
            if settings.LAZY_LOADING:
                context["feed_my"] = context["feed_my"][
                    : settings.LAZY_LOADING["initial_limit"]
                ]

        context["feeds_custom"] = [
            custom_feed(
                self.request,
                pk,
                limit=(
                    settings.LAZY_LOADING["initial_limit"]
                    if settings.LAZY_LOADING
                    else None
                ),
            )
            for pk in settings.ANNOUNCEMENTS_CUSTOM_FEEDS
        ]

        """ to-do: search bar, DNR
        query = self.request.GET.get('q' ,'')
        feed_type = self.request.GET.get('ft','')
        print(feed_type)
        if query != '':
            if feed_type == 'get':
                context['search'] = context['feed_all'].filter(pk=query)
            else:
                context['search'] = context['feed_all'].filter(Q(body__icontains=query) | Q(title__icontains=query))
        """
        return context


class AnnouncementFeed(Feed):
    title = "Metropolis Announcements"
    link = reverse_lazy("announcement_list")

    def items(self):
        return models.Announcement.get_all()

    def item_description(self, item):
        return markdown(item.body)

    def item_title(self, item):
        return item.title

    def item_pubdate(self, item):
        return item.show_after

    def item_updateddate(self, item):
        return item.last_modified_date

    def item_category(self, item):
        return [item.organization.name] + item.tags.values_list("name", flat=True)


class AnnouncementTagList(TemplateView, mixins.TitleMixin):
    template_name = "core/announcement/tag_list.html"

    def get_title(self):
        return (
            "Announcements:" + get_object_or_404(models.Tag, id=self.kwargs["tag"]).name
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feed_tag"] = models.Announcement.get_all(
            user=self.request.user
        ).filter(tags=context["tag"])
        context["tag"] = get_object_or_404(models.Tag, id=context["tag"])
        return context


class AnnouncementDetail(UserPassesTestMixin, DetailView, mixins.TitleMixin):
    model = models.Announcement
    context_object_name = "announcement"
    template_name = "core/announcement/detail.html"

    def get_title(self):
        return self.get_object().title

    def test_func(self):
        announcement = self.get_object()
        if announcement.status == "a":
            if self.request.user in announcement.organization.members.all():
                return True
            if announcement.is_public:
                return True
        if self.request.user.is_superuser:
            return True
        if self.request.user == announcement.organization.owner:
            return True
        if self.request.user in announcement.organization.supervisors.all():
            return True
        if self.request.user in announcement.organization.execs.all():
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["feeds_custom"] = []
        for custom_feed_organization_pk in settings.ANNOUNCEMENTS_CUSTOM_FEEDS:
            custom_feed_organization = models.Organization.objects.get(
                pk=custom_feed_organization_pk
            )
            context["feeds_custom"].append(custom_feed_organization)

        return context


class BlogPostCards(TemplateView):
    template_name = "core/blogpost/cards.html"

    def dispatch(self, request, *args, **kwargs):
        self.page = request.GET.get("page", None)
        if not isinstance(self.page, str):
            return HttpResponseBadRequest("invalid page")
        if not self.page.isnumeric():
            return HttpResponseBadRequest("invalid page (non-numeric)")
        self.feed = request.GET.get("feed", None)
        if self.feed == "my":
            if not self.request.user.is_authenticated:
                return HttpResponseForbidden("not authenticated")
        elif self.feed == "all":
            pass
        else:
            if not isinstance(self.feed, str):
                return HttpResponseBadRequest("invalid feed")
            if not self.feed.isnumeric():
                return HttpResponseBadRequest("invalid feed (non-numeric)")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.feed == "all":
            feed = models.BlogPost.public()
        else:
            raise ValidationError("feed must be all")
        paginator = Paginator(feed, settings.LAZY_LOADING["per_page"])
        try:
            self.posts = paginator.page(self.page)
        except EmptyPage:
            self.posts = paginator.page(paginator.num_pages)
        context["feed"] = self.posts
        context["has_next"] = self.posts.has_next()
        return context


class BlogPostList(TemplateView, mixins.TitleMixin):
    template_name = "core/blogpost/list.html"
    title = "Blog Posts"

    def get_ordering(self):
        return "-last_modified_date"

    def get_queryset(self):
        return models.BlogPost.public()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if settings.LAZY_LOADING:
            context["lazy_loading"] = True
            context["initial_limit"] = settings.LAZY_LOADING["initial_limit"]
            context["per_page"] = settings.LAZY_LOADING["per_page"]

        context["feed_all"] = models.BlogPost.public()
        if settings.LAZY_LOADING:
            context["feed_all"] = context["feed_all"][
                : settings.LAZY_LOADING["initial_limit"]
            ]
        return context


class BlogPostDetail(UserPassesTestMixin, DetailView):
    model = models.BlogPost
    context_object_name = "blogpost"
    template_name = "core/blogpost/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blogpost"].increment_views()
        context["title"] = self.get_title()
        return context

    def get_title(self):
        return self.get_object().title

    def test_func(self):
        return self.get_object().is_published


class BlogPostTagList(TemplateView, mixins.TitleMixin):
    template_name = "core/blogpost/tag_list.html"

    def get_title(self):
        model = get_object_or_404(models.Tag, id=self.kwargs["tag"])
        return "Blogposts: " + model.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feed_tag"] = models.BlogPost.public().filter(tags=context["tag"])
        context["tag"] = get_object_or_404(models.Tag, id=context["tag"])
        return context


class ExhibitList(TemplateView, mixins.TitleMixin):
    template_name = "core/exhibit/list.html"
    title = "Gallery"

    def get_ordering(self):
        return "-last_modified_date"

    def get_queryset(self):
        return Exhibit.objects.filter(is_published=True, show_after__lte=timezone.now())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if settings.LAZY_LOADING:
            context["lazy_loading"] = True
            context["initial_limit"] = settings.LAZY_LOADING["initial_limit"]
            context["per_page"] = settings.LAZY_LOADING["per_page"]

        context["feed_all"] = models.Exhibit.objects.filter(is_published=True)
        if settings.LAZY_LOADING:
            context["feed_all"] = context["feed_all"][
                : settings.LAZY_LOADING["initial_limit"]
            ]
        return context
