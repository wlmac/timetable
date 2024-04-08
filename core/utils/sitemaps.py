from django.contrib.flatpages.models import FlatPage
from django.contrib.sitemaps import Sitemap

from core.models import *


class BlogSitemap(Sitemap):
    priority = 0.7

    def items(self):
        return BlogPost.public()

    @staticmethod
    def lastmod(obj):
        return obj.last_modified_date


class AnnouncementsSitemap(Sitemap):
    priority = 0.5

    def items(self):
        return Announcement.get_approved()

    @staticmethod
    def lastmod(obj):
        return obj.last_modified_date


class ClubsSitemap(Sitemap):
    priority = 0.7

    def items(self):
        return Organization.active()
