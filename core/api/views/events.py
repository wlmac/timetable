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
        start = timezone.now()
        if self.request.data.get("start"):
            start = self.request.data.get("start")
        elif self.request.query_params.get("start"):
            start = self.request.query_params.get("start")

        if not self.request.user.is_anonymous:
            if self.request.data.get("end"):
                end = self.request.data.get("end")
                events = (
                    models.Event.objects.filter(
                        end_date__gte=start, start_date__lte=end
                    )
                    .filter(
                        Q(is_public=True) | Q(organization__member=self.request.user.id)
                    )
                    .distinct()
                    .order_by("start_date")
                )
            elif self.request.query_params.get("end"):
                end = self.request.query_params.get("end")
                events = (
                    models.Event.objects.filter(
                        end_date__gte=start, start_date__lte=end
                    )
                    .filter(
                        Q(is_public=True) | Q(organization__member=self.request.user.id)
                    )
                    .distinct()
                    .order_by("start_date")
                )
            else:
                events = (
                    models.Event.objects.filter(end_date__gte=start)
                    .filter(
                        Q(is_public=True) | Q(organization__member=self.request.user.id)
                    )
                    .distinct()
                    .order_by("start_date")
                )
        else:
            if self.request.data.get("end"):
                end = self.request.data.get("end")
                events = models.Event.objects.filter(
                    end_date__gte=start, start_date__lte=end, is_public=True
                ).order_by("start_date")
            elif self.request.query_params.get("end"):
                end = self.request.query_params.get("end")
                events = models.Event.objects.filter(
                    end_date__gte=start, start_date__lte=end, is_public=True
                ).order_by("start_date")
            else:
                events = models.Event.objects.filter(
                    end_date__gte=start, is_public=True
                ).order_by("start_date")

        return events
