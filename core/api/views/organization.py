from django.db.models import Count
from rest_framework import generics

from ... import models
from .. import serializers
from ..utils.fallback import ListAPIViewWithFallback


class ApiOrganizationList(ListAPIViewWithFallback):
    queryset = (
        models.Organization.objects.filter(is_active=True)
        .annotate(num_members=Count("member"))
        .order_by("-num_members")
    )
    serializer_class = serializers.OrganizationSerializer


class OrganizationDetail(generics.RetrieveAPIView):
    queryset = models.Organization.objects.filter(is_active=True)
    serializer_class = serializers.OrganizationSerializer
