from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions
from rest_framework.parsers import JSONParser

from ... import models
from .. import serializers
from ..utils.fallback import ListAPIViewWithFallback


class EventsList(ListAPIViewWithFallback):
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]
    serializer_class = serializers.EventSerializer
    pagination_class = None

    def get_queryset(self):
        start = (
            self.request.data.get("start")
            or self.request.query_params.get("start")
            or timezone.now()
        )
        end = self.request.data.get("end") or self.request.query_params.get("end")

        events = models.Event.objects.filter(end_date__gte=start)

        if end:
            events = events.filter(start_date__lte=end)

        if not self.request.user.is_anonymous:
            events = events.filter(
                Q(is_public=True)
                | Q(organization__member=self.request.user.id)
                | Q(organization__supervisors=self.request.user.id)
                | Q(organization__execs=self.request.user.id)
            ).distinct()
        else:
            events = events.filter(Q(is_public=True))

        events = events.order_by("start_date")

        return events
