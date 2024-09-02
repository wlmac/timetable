from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ... import models
from ...models import User
from ..utils.gravatar import gravatar_url
from .tag import TagSerializer


class UserSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=models.Tag.objects.all())
    organizations = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=models.Organization.objects.all(),
    )
    tags_following = TagSerializer(many=True)
    gravatar_url = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    @extend_schema_field(OpenApiTypes.URI)
    def get_gravatar_url(obj):
        return gravatar_url(obj.email)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "bio",
            "graduating_year",
            "organizations",
            "tags_following",
            "gravatar_url",
            "saved_blogs",
            "saved_announcements",
        ]


class UserSerializerInternal(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=models.Tag.objects.all())
    gravatar_url = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    @extend_schema_field(OpenApiTypes.URI)
    def get_gravatar_url(obj):
        return gravatar_url(obj.email)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
            "is_superuser",
            "date_joined",
            "bio",
            "graduating_year",
            "is_teacher",
            "organizations",
            "tags_following",
            "qltrs",
            "gravatar_url",
        ]


class UserSerializer3(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=models.Tag.objects.all())
    gravatar_url = serializers.SerializerMethodField(read_only=True)

    @staticmethod
    @extend_schema_field(OpenApiTypes.URI)
    def get_gravatar_url(obj):
        return gravatar_url(obj.email)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "is_staff",
            "bio",
            "graduating_year",
            "organizations",
            "tags_following",
            "gravatar_url",
        ]
