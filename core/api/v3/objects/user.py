import base64
import hashlib

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from rest_framework import permissions, serializers, status, validators

from core.api.serializers.custom import UserOrganizationField
from core.api.utils.gravatar import gravatar_url
from core.models import User, graduating_year_choices

from .base import BaseProvider


class UserSerializer(serializers.ModelSerializer):
    email_hash = serializers.SerializerMethodField(read_only=True)
    gravatar_url = serializers.SerializerMethodField(read_only=True)
    username = serializers.CharField(required=False)
    password = serializers.CharField(
        required=False, write_only=True, trim_whitespace=False
    )
    old_password = serializers.CharField(
        required=False, write_only=True, trim_whitespace=False
    )
    organizations = UserOrganizationField()
    organizations_leading = UserOrganizationField()
    organizations_supervising = UserOrganizationField()

    @staticmethod
    def get_gravatar_url(obj):
        return gravatar_url(obj.email)

    @staticmethod
    def get_email_hash(obj):
        return base64.standard_b64encode(
            hashlib.md5(obj.email.encode("utf-8")).digest()
        )

    def validate(self, data):
        if ("password" in data) != ("old_password" in data):
            raise serializers.ValidationError(
                "password and old_password must be in pairs"
            )
        return data

    def validate_old_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError("old_password is wrong")

    def save(self, **kwargs):
        set_new_password = (
            "password" in self.validated_data and "old_password" in self.validated_data
        )
        if set_new_password:
            new_password = self.validated_data.pop("password")
            old_password = self.validated_data.pop("old_password")
        obj = super().save(**kwargs)
        if set_new_password and obj.check_password(old_password):  # noqa
            obj.set_password(new_password)  # noqa
            obj.save()
        return obj

    class Meta:
        fields = [
            "id",
            "username",
            "password",
            "old_password",
            "email_hash",
            "first_name",
            "last_name",
            "bio",
            "graduating_year",
            "organizations",
            "organizations_leading",
            "organizations_supervising",
            "tags_following",
            "gravatar_url",
            "saved_blogs",
            "saved_announcements",
            "is_teacher",
            "is_superuser",
            "is_deleted",
            "deleted_at",
        ]
        model = User


class ListSerializer(serializers.ModelSerializer):
    email_hash = serializers.SerializerMethodField(read_only=True)
    gravatar_url = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    def get_gravatar_url(obj):
        return gravatar_url(obj.email)

    @staticmethod
    def get_email_hash(obj):
        return base64.standard_b64encode(
            hashlib.md5(obj.email.encode("utf-8")).digest()
        )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "graduating_year",
            "email_hash",
            "gravatar_url",
        ]


def tdsb_email(value):
    if not (
        value.endswith(settings.TEACHER_EMAIL_SUFFIX)
        or value.endswith(settings.STUDENT_EMAIL_SUFFIX)
    ):
        raise serializers.ValidationError("Must be either a teacher or student email.")


class NewSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(max_length=30, required=True)
    graduating_year = serializers.ChoiceField(
        choices=graduating_year_choices, required=True
    )
    email = serializers.EmailField(
        validators=[
            tdsb_email,
            validators.UniqueValidator(queryset=User.objects.all()),
        ],
        required=True,
    )
    username = serializers.RegexField(
        r"^[\w.@+-]+$",
        validators=[validators.UniqueValidator(queryset=User.objects.all())],
        max_length=30,
        required=True,
    )
    password = serializers.CharField(required=True, write_only=True)

    # Default `create` and `update` behavior...
    def create(self, validated_data) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        if validated_data["email"].endswith(settings.TEACHER_EMAIL_SUFFIX):
            user.is_teacher = True
        user.set_password(password)
        user.save()
        # if Group.objects.filter(name="Supervisors").exists():
        #     user.groups.add(Group.objects.get(name="Supervisors"))
        return user

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "graduating_year",
            "email",
            "username",
            "password",
            "bio",
        ]


class Identity(permissions.BasePermission):
    def has_object_permission(self, request, view, user):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user == user:
            return True
        return False


class UserProvider(BaseProvider):
    model = User
    additional_lookup_fields = ["username"]
    listing_filters = {
        "organizations": int,
        "organizations_leading": int,
        "organizations_owning": int,
        "organizations_supervising": int,
    }
    raw_serializers = {
        "new": NewSerializer,
        "list": ListSerializer,
        "_": UserSerializer,
    }

    @property
    def permission_classes(self):
        return [Identity] if self.request.mutate else [permissions.IsAuthenticated]

    @staticmethod
    def get_queryset(request):
        return User.objects.filter(is_active=True)

    @staticmethod
    def get_last_modified(view):
        return view.get_object().last_modified_date

    @staticmethod
    def get_last_modified_queryset():
        return (
            LogEntry.objects.filter(
                content_type=ContentType.objects.get(app_label="core", model="user")
            )
            .latest("action_time")
            .action_time
        )

    @staticmethod
    def delete(request, *args, **kwargs):
        """Respond with correct endpoint for deleting a user."""
        return JsonResponse(
            status=status.HTTP_304_NOT_MODIFIED,
            data={
                "detail": "Not allowed, Please read the docs for the correct endpoint."
            },
        )
