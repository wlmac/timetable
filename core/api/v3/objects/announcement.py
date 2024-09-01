from __future__ import annotations

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.urls import reverse
from rest_framework import permissions, serializers
from rest_framework.exceptions import ValidationError

from core.api.serializers.custom import (
    CommentField,
    LikeField,
    OrganizationField,
    SingleUserField,
    SupervisorField,
    TagRelatedField,
)
from core.api.utils.last_modified import ModelAbilityField
from core.models import Announcement, User
from core.utils.mail import send_mail

from .base import BaseProvider


def exec_validator(value, serializer_field):
    if value not in {"d", "p"}:
        raise ValidationError("only draft or pending allowed", code="exec")


def always_fail_validator(value, serializer_field):
    raise ValidationError("always fail", code="exec")


class Serializer(serializers.ModelSerializer):
    message = serializers.CharField(read_only=True)
    comments = CommentField()
    likes = LikeField()
    tags = TagRelatedField()
    author = SingleUserField()
    organization = OrganizationField()

    def save(self, **kwargs):
        notify_supervisors = False
        obj: Announcement = super().save(**kwargs)
        user = self.context["request"].user
        if user in obj.organization.supervisors.all():
            obj.supervisor = user
            if obj.status not in {"d", "p"} and user != obj.author:
                obj.message = (
                    f"Successfully marked announcement as {obj.get_status_display()}."
                )
        else:
            if obj.status not in ("d", "p"):
                notify_supervisors = True
                if obj.status != "a":
                    obj.message = "Successfully sent announcement for review."
            obj.status = "p" if obj.status != "d" else "d"

        if notify_supervisors:
            for teacher in obj.organization.supervisors.all():
                email_template_context = {
                    "teacher": teacher,
                    "announcement": obj,
                    "review_link": settings.SITE_URL
                    + reverse("admin:core_announcement_change", args=(obj.pk,)),
                }

                send_mail(
                    f"【{obj.organization.name}】Announcement Approval Requested: {obj.title}",
                    render_to_string(
                        "core/email/verify_announcement.txt",
                        email_template_context,
                    ),
                    None,
                    [teacher.email],
                    bcc=settings.ANNOUNCEMENT_APPROVAL_BCC_LIST,
                    html_message=render_to_string(
                        "core/email/verify_announcement.html",
                        email_template_context,
                    ),
                )
        return obj

    class Meta:
        model = Announcement
        fields = [
            "id",
            "created_date",
            "last_modified_date",
            "show_after",
            "title",
            "body",
            "is_public",
            "status",
            "rejection_reason",
            "author",
            "organization",
            "supervisor",
            "tags",
            "likes",
            "comments",
            "message",
        ]


class OneSerializer(Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context["request"].user
        # these HiddenFields should never be used to set values
        self.status = serializers.HiddenField(
            default="", validators=[always_fail_validator]
        )
        self.rejection_reason = serializers.HiddenField(
            default="", validators=[always_fail_validator]
        )
        instance = self.instance
        if instance:
            if user in instance.organization.supervisors.all():
                self.supervisor = SupervisorField(
                    "edit", queryset=User.objects.filter(is_teacher=True)
                )
                self.status = ModelAbilityField(
                    "approve",
                    model_field=Announcement()._meta.get_field("status"),
                )
                self.rejection_reason = ModelAbilityField(
                    "approve",
                    model_field=Announcement()._meta.get_field("rejection_reason"),
                )
            elif user in instance.organization.execs.all():
                self.supervisor = SupervisorField(
                    "edit", queryset=User.objects.filter(is_teacher=True)
                )
                self.status = serializers.CharField(validators=[exec_validator])
                self.rejection_reason = serializers.CharField(read_only=True)


class Inner(permissions.BasePermission):
    def has_object_permission(self, request, view, ann):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.can_edit(ann):
            return True
        return False


class AnnouncementProvider(BaseProvider):
    model = Announcement
    listing_filters = {
        "tags": [(int, ""), (str, "name")],
        "organization": int,
        "author": int,
    }
    raw_serializers = {
        "single": OneSerializer,
        "retrieve": OneSerializer,
        "_": Serializer,
    }

    @property
    def permission_classes(self):
        return (
            [permissions.DjangoModelPermissions, Inner]
            if self.request.mutate
            else [permissions.AllowAny]
        )

    @staticmethod
    def get_queryset(request):
        return Announcement.get_all(request.user)

    @staticmethod
    def get_last_modified(view):
        return view.get_object().last_modified_date

    @staticmethod
    def get_last_modified_queryset():
        return (
            LogEntry.objects.filter(
                content_type=ContentType.objects.get(
                    app_label="core", model="announcement"
                )
            )
            .latest("action_time")
            .action_time
        )
