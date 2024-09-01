from __future__ import annotations

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from core.api.serializers.custom import (
    CommentField,
    ContentTypeField,
    LikeField,
    SingleUserField,
)
from core.models import Comment, Like, User

from .base import BaseProvider

typedir: dict[str, str] = {
    "blogpost": "core | blogpost",
    "announcement": "core | announcements",
}


class IsOwnerOrSuperuser(BasePermission):
    """
    Allows access only to staff or the owner of the object.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_superuser
            or request.user == view.get_object().author
        )


class CommentSerializer(serializers.ModelSerializer):
    likes = LikeField()
    author = SingleUserField()
    edited = serializers.SerializerMethodField(read_only=True)
    children = CommentField()
    content_type = ContentTypeField()

    def validate(self, attrs):
        """
        https://www.django-rest-framework.org/api-guide/serializers/#object-level-validation
        """
        if self.context["request"].user.is_anonymous:
            raise serializers.ValidationError("You must be logged in to comment.")
        if parent := attrs.get("parent", None):
            if parent.id == attrs.get("id", None):
                raise ValidationError("A Comment cannot be a parent of itself.")

        return super().validate(attrs)

    @staticmethod
    def get_edited(obj: Comment):
        return obj.last_modified != obj.created_at

    def update(self, instance: Comment, validated_data) -> Comment:
        if instance.deleted:
            raise ValidationError("This comment has been deleted.")
        if instance.body != validated_data.get(
            "body", instance.body
        ):  # if change is  to body.
            instance.last_modified = timezone.now()
            # contains_profanity: bool = bool(
            #    profanity_check.predict([validated_data["body"]])
            # )
            if self.context[
                "request"
            ].user.is_superuser:  # bypass content moderation if user is an SU.
                validated_data["live"] = True
            else:
                validated_data["live"] = False  # not contains_profanity
        super().update(instance, validated_data)
        return instance

    @staticmethod
    def delete(instance: Comment):
        instance.delete(force=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    class Meta:
        model = Comment
        permissions = [IsOwnerOrSuperuser]
        fields = [
            "id",
            "author",
            "content_type",
            "object_id",
            "body",
            "created_at",
            "likes",
            "edited",
            "children",
        ]


class CommentNewSerializer(CommentSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def create(self, validated_data) -> Comment:
        # contains_profanity: bool = bool(
        #      profanity_check.predict([validated_data["body"]])
        # )
        com = Comment(**validated_data)
        if self.context[
            "request"
        ].user.is_superuser:  # bypass content moderation if user is an SU.
            com.live = True
        else:
            com.live = False  # not contains_profanity
        com.save()
        return com

    class Meta:
        model = Comment
        permission_classes = [IsAuthenticated]
        fields = [
            "content_type",
            "object_id",  # obj id of the blogpost or announcement.
            "body",
            "parent",
            "author",
        ]


class CommentProvider(BaseProvider):
    model = Comment
    allow_list = False
    allow_new = settings.ALLOW_COMMENTS
    raw_serializers = {"new": CommentNewSerializer, "_": CommentSerializer}

    @property
    def permission_classes(self):
        return [permissions.IsAuthenticated]

    @staticmethod
    def get_queryset(request):
        if (
            request.user.has_perm("core.comment.view_flagged")
            or request.user.is_superuser
        ):
            return Comment.objects.all()
        return Comment.objects.filter(live=True)

    @staticmethod
    def get_last_modified(view):
        return view.get_object().last_modified_date

    @staticmethod
    def get_last_modified_queryset():
        return (
            LogEntry.objects.filter(
                content_type=ContentType.objects.get(app_label="core", model="comment")
            )
            .latest("action_time")
            .action_time
        )


# ====================================================================================================
# -------------------------------------------  LIKES  -------------------------------------------
# ====================================================================================================


class LikeSerializer(serializers.ModelSerializer):
    content_type = ContentTypeField()

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "You cannot update a like, if you wish to delete. do so."
        )

    def destroy(self, instance: Like, validated_data):
        if instance.author != self.context["request"].user:
            raise ValidationError("You cannot unlike another user's like.")
        instance.delete(force=True)

    def create(self, validated_data) -> Like:
        obj_name = validated_data["content_type"].name.lower().replace(" ", "")
        if (
            self.context["request"].user != validated_data["author"]
        ) and not self.context["request"].user.is_superuser:
            raise ValidationError("You cannot like as another user.")

        if obj_name not in settings.POST_CONTENT_TYPES:  # is the object type valid?
            raise ValidationError(
                f"Invalid object type: {obj_name}, valid types are: {settings.POST_CONTENT_TYPES}"
            )
        if (
            not validated_data["content_type"]
            .model_class()  # the model of the content type ( e.g. core.models.Announcement or core.models.Comment )
            .objects.filter(id=validated_data["object_id"])
            .exists()
        ):  # does the object exist?
            raise ValidationError(f"The specified {obj_name} does not exist.")

        if Like.objects.filter(  # has the user already liked this object?
            content_type=validated_data["content_type"],
            object_id=validated_data["object_id"],
            author=validated_data["author"],  # author is current user?
        ).exists():
            raise ValidationError(f"User has already liked this {obj_name}")
        else:
            like = Like(**validated_data)
            like.save()
            return like

    class Meta:
        model = Like
        permission_classes = [IsAuthenticated]
        fields = [
            "content_type",
            "object_id",  # obj id of the blogpost or announcement.
            "author",
        ]


class LikeProvider(BaseProvider):
    model = Like
    allow_list = False
    raw_serializers = {"_": LikeSerializer}

    @property
    def permission_classes(self):
        return [permissions.IsAuthenticated]

    def get_queryset(self, request):
        return Like.objects.all()

    def get_last_modified(self, view):
        return (
            LogEntry.objects.filter(
                content_type=ContentType.objects.get(app_label="core", model="like")
            )
            .filter(object_id=str(view.get_object().pk))
            .latest("action_time")
            .action_time
        )

    def get_last_modified_queryset(self):
        return (
            LogEntry.objects.filter(
                content_type=ContentType.objects.get(app_label="core", model="like")
            )
            .latest("action_time")
            .action_time
        )
