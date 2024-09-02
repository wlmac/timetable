from oauth2_provider.contrib.rest_framework import TokenHasScope
from rest_framework import permissions

from ... import models
from .. import serializers
from ..utils.fallback import ListAPIViewWithFallback


class AnnouncementListAll(ListAPIViewWithFallback):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.AnnouncementSerializer

    def get_queryset(self):
        return models.Announcement.get_all(user=self.request.user)


class AnnouncementListMyFeed(ListAPIViewWithFallback):
    permission_classes = [permissions.IsAuthenticated | TokenHasScope]
    required_scopes = ["me_ann"]
    serializer_class = serializers.AnnouncementSerializer

    def get_queryset(self):
        return self.request.user.get_feed()
