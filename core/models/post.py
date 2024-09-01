from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone

# from ..api.utils.profanity import predict
from ..utils.file_upload import file_upload_path_generator
from .choices import announcement_status_choices

# Create your models here.

if TYPE_CHECKING:
    from .user import User


class PostInteraction(models.Model):
    """
    how to fetch a PostInteraction object:


    content_type = ContentType.objects.get_for_model(self)
        return PostInteraction.objects.filter(
            content_type=content_type, object_id=self.id
        )

    """

    author: "User" | str = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET(None),
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    # --- Generic Foreign Key --- #
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The type of object this comment is on (core | blog post or core | announcement)",
    )
    object_id = models.PositiveIntegerField(
        help_text="The id of the object this comment is on"
    )
    content_object = GenericForeignKey("content_type", "object_id")

    # --- Generic Foreign Key --- #

    @property
    def deleted(self):
        return self.created_at is None

    def get_object(
        self, obj: "PostInteraction", **kwargs
    ):  # get ken to check this in accordance with get
        content_type = ContentType.objects.get_for_model(obj)
        return self.__class__.objects.filter(
            content_type=content_type, object_id=obj.id, **kwargs
        )

    class Meta:
        abstract = True


class Like(PostInteraction):
    def delete(self, using=None, keep_parents=False, **kwargs):
        """
        Don't actually delete the object, just set the user to None and save it. This way, we can still keep track of the likes, saves and comments.
        if force is set to True, then it will actually delete the object (used for when you want to delete a comment or unlike/save something)
        """
        if kwargs.get("force", False):
            return super().delete(using=using, keep_parents=keep_parents)
        self.user = None
        self.save()


class CommentHistory(models.Model):  # todo add to admin panel
    Comment = models.ForeignKey("Comment", on_delete=models.CASCADE)
    body = models.TextField(max_length=512, null=True, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)


class Comment(PostInteraction):
    history = models.ManyToManyField(CommentHistory, blank=True)
    last_modified = models.DateTimeField(auto_now_add=True)
    body = models.TextField(max_length=512, null=True, blank=False, default="Hello!")
    parent = models.ForeignKey(
        "Comment",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    live = models.BooleanField(
        default=False,
        help_text="Shown publicly?",
    )

    def clean(self):
        if self.id == self.parent.id:
            raise ValidationError("A Comment cannot be a parent of itself.")
        return super().clean()

    def get_children(self, su: Optional = False, all: Optional = False) -> QuerySet:
        comments = Comment.objects.filter(parent=self)
        if su:
            filtered = [
                c.pk for c in comments if not c.deleted
            ]  # todo(low priority) filter using QuerySet instead of list comprehension
        else:
            filtered = [c.pk for c in comments if all([c.live, not c.deleted])]

        last = Comment.objects.filter(pk__in=filtered)
        if all:
            for comment in last:
                last = last | comment.get_children(all=True)
        return last

    def delete(self: Comment, using=None, keep_parents=False, **kwargs):
        """
        Don't actually delete the object, just set the user to None and save it, that way you can still have sub comments.
        if force is set to True, then it will actually delete the object (used for when you want to delete a comment or unlike/save something)
        """
        if kwargs.get("force", True):
            if self.bottom_lvl:  # no sub comments
                super().delete(using=using, keep_parents=keep_parents)
            else:
                self.created_at = None
                self.body = None
                self.author = None
                Like.objects.filter(
                    content_type=self.content_type, object_id=self.object_id
                ).delete()
                self.save()

        else:
            self.user = None  # in the case that the user was deleted.
            self.save()
        if self.parent and self.parent.can_be_deleted:
            self.parent.delete(force=True)

    @property
    def can_be_deleted(self):
        return self.bottom_lvl and self.deleted

    @property
    def top_lvl(self) -> bool:
        """Returns True if the comment is a top level comment, False if it is a child comment."""
        return self.parent is None

    @property
    def bottom_lvl(self) -> bool:
        """Returns True if the comment is a bottom level comment, False if it is a parent comment."""
        return not self.get_children().exists()

    @property
    def like_count(self) -> int:
        c_type = ContentType.objects.get_for_model(self.__class__)
        return Like.objects.filter(object_id=self.id, content_type=c_type).count()

    def flagged(self) -> bool:
        return self.__class__.objects.filter(live=False)

    def __str__(self) -> str:
        return str(self.body)

    def save(self, **kwargs):
        if self.pk is not None:  # Object is being updated
            old_obj = Comment.objects.get(pk=self.pk)
            if old_obj.body != self.body:
                CommentHistory.objects.create(Comment=old_obj)
                self.last_modified = timezone.now()

        if not self.deleted and self.author.is_superuser:
            return super().save(**kwargs)
        # if bool(predict(self.body)[0]):  # 0.2ms per check, .5 for 10 and 3.5 for 100
        #    self.live = True todo reimpl profanity check
        self.live = True

        return super().save(**kwargs)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]
        permissions = (("view_flagged", "View flagged comments"),)


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="%(class)ss_authored",
    )
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now=True)
    show_after = models.DateTimeField(
        verbose_name="Automatically post on",
        help_text="Show this announcement after this time.",
    )

    title = models.CharField(max_length=64)
    body = models.TextField()
    tags = models.ManyToManyField(
        "Tag",
        blank=True,
        related_name="%(class)ss",
        related_query_name="%(class)s",
    )

    @property
    def comments(self):
        content_type = ContentType.objects.get_for_model(self)
        return Comment.objects.filter(
            content_type=content_type,
            object_id=self.id,
            parent=None,
        )

    def __str__(self):
        return self.title

    class Meta:
        abstract = True
        ordering = ["-show_after"]


class Announcement(Post):
    organization = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="announcements",
        related_query_name="announcement",
    )

    is_public = models.BooleanField(
        default=True,
        help_text="Whether if this announcement pertains to the general school population, not just those in the organization.",
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="announcements_approved",
    )
    status = models.CharField(
        max_length=1, choices=announcement_status_choices, default="p"
    )
    rejection_reason = models.CharField(
        max_length=140,
        blank=True,
        verbose_name="reason for rejection",
        help_text="Only fill this field in if you are rejecting this announcement.",
    )

    def get_absolute_url(self):
        return reverse("announcement_detail", args=[self.pk])

    @classmethod
    def get_approved(cls) -> QuerySet:
        return cls.objects.filter(status="a").filter(show_after__lte=timezone.now())

    @classmethod
    def get_all(cls, user=None) -> QuerySet:
        approved_announcements = cls.get_approved()

        if user is not None and user.is_superuser:
            return approved_announcements  # return all announcements if user is superuser (admin).

        feed_all = approved_announcements.filter(is_public=True)
        if user is not None and user.is_authenticated:
            feed_all = (
                feed_all
                | approved_announcements.filter(organization__member=user)
                | cls.objects.filter(organization__execs__in=[user])
            ).distinct()
        feed = feed_all
        return feed

    def editable(self, user=None):
        if user.is_superuser:
            return True
        if user is None:
            return False
        return user in (org := self.organization).supervisors.all() | org.execs.all()

    def approvable(self, user=None):
        if user is None:
            return False
        return self.organization.supervisors.filter(user=user).exists()


def featured_image_file_path_generator(instance, file_name):
    return file_upload_path_generator("featured_image")(instance, file_name)


class BlogPost(Post):
    slug = models.SlugField(unique=True)
    featured_image = models.ImageField(
        upload_to=featured_image_file_path_generator,
        default="featured_image/default.png",
    )
    last_modified_date = models.DateTimeField(auto_now_add=True)
    featured_image_description = models.CharField(
        help_text="Alt text for the featured image e.g. what screen readers tell users",
        max_length=140,
        default="",
        blank=True,
    )
    is_published = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    is_archived = models.BooleanField(
        default=False,
        help_text="Archived posts are not shown on the blog page.",
    )

    @classmethod
    def public(cls):
        return cls.objects.filter(
            is_published=True, is_archived=False, show_after__lte=timezone.now()
        )

    def get_absolute_url(self):
        return reverse("blogpost_detail", args=[self.slug])

    def increment_views(self) -> str:
        self.views += 1
        self.save()

    class Meta:
        ordering = ["-created_date"]
        indexes = [
            models.Index(fields=["is_archived"]),
            models.Index(fields=["is_published"]),
            models.Index(fields=["created_date"], name="idx_created_date"),
        ]


class Exhibit(Post):
    slug = models.SlugField(unique=True)
    content = models.ImageField(
        upload_to=featured_image_file_path_generator,
        default="featured_image/default.png",
    )
    content_description = models.CharField(
        help_text="Alt text for the featured image e.g. what screen readers tell users",
        max_length=140,
    )
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_date"]
