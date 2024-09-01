from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from rest_framework import permissions, serializers

from core.api.serializers.course import CourseSerializer, TermSerializer
from core.models import Timetable

from .base import BaseProvider


class ViewSerializer(serializers.ModelSerializer):
    term = TermSerializer()
    courses = CourseSerializer(many=True)

    class Meta:
        model = Timetable
        ordering = ["-term__start_date"]
        fields = ["term", "courses"]


class MutateSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        if self.Meta.model.objects.filter(
            owner=validated_data["owner"], term=validated_data["term"]
        ).exists():
            raise serializers.ValidationError(
                "You already have a timetable for this term"
            )
        return super().create(validated_data)

    class Meta:
        model = Timetable
        ordering = ["-term__start_date"]
        fields = ["term", "courses"]


class Identity(permissions.BasePermission):
    def has_object_permission(self, request, view, timetable):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if request.user == timetable.owner:
            return True
        return False


class TimetableProvider(BaseProvider):
    permission_classes = [
        Identity
    ]  # redundant but in case we make a mistake with the queryset
    model = Timetable
    listing_filters = {
        # "owner": int, since we're using the user's own timetables, we don't need this
        "term": int,
        "courses": int,
    }
    raw_serializers = {
        "new": MutateSerializer,
        "single": MutateSerializer,
        "_": ViewSerializer,
    }

    @staticmethod
    def get_queryset(request):
        if (
            request.user.is_anonymous
        ):  # it's up to the client to check if the user is logged in
            return Timetable.objects.none()
        # elif request.user.is_superuser:
        #     return Timetable.objects.all()
        else:  # it's up to the client to check if the user is logged in
            return Timetable.objects.filter(owner=request.user)

    def get_last_modified(self, view):
        return (
            LogEntry.objects.filter(
                content_type=ContentType.objects.get(
                    app_label="core", model="timetable"
                )
            )
            .filter(object_id=str(view.get_object().pk))
            .latest("action_time")
            .action_time
        )

    def get_last_modified_queryset(self):
        return (
            LogEntry.objects.filter(
                content_type=ContentType.objects.get(
                    app_label="core", model="timetable"
                )
            )
            .latest("action_time")
            .action_time
        )
