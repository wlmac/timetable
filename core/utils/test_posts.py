from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone

from core.admin import User
from core.models import Announcement, BlogPost, Comment, Organization, Post


def create_school_org(user: User) -> Organization:
    school_org = Organization(owner=user)
    school_org.save()
    return school_org


def create_user() -> User:
    user = User(username="bob")
    user.save()
    return user


def create_announcement(org: Organization, status: str, title: str) -> Announcement:
    ann = Announcement(
        organization=org, status=status, title=title, show_after=timezone.now()
    )
    ann.save()
    return ann


def create_blog_post(author: User, title: str) -> BlogPost:
    blog = BlogPost(
        author=author,
        is_published=True,
        title=title,
        show_after=timezone.now(),
    )
    blog.save()
    return blog


def create_comment(user: User, post: Post, body: str) -> Comment:
    com = Comment.objects.create(
        content_type=ContentType.objects.get_for_model(post),
        object_id=post.id,
        author=user,
        body=body,
        parent=None,
    )
    com.save()
    return com


class TestAnnouncement(TestCase):
    def test_get_approved(self):
        org = create_school_org(create_user())
        create_announcement(org, "p", "hello")
        create_announcement(org, "p", "goodbye")
        create_announcement(org, "a", "foo")
        create_announcement(org, "a", "abc")
        create_announcement(org, "a", "bar")
        create_announcement(org, "r", "bad")
        create_announcement(org, "r", "good")
        approved = sorted(ann.title for ann in Announcement.get_approved())
        self.assertEqual(approved, ["abc", "bar", "foo"])


class TestComments(TestCase):
    def test_get_approved(self):
        org = create_school_org(create_user())
        ann = create_announcement(org, "a", "hello")
        blog = create_blog_post(author=org.owner, title="hello")
        create_comment(org.owner, ann, "hello")
        create_comment(org.owner, ann, "goodbye")
        create_comment(org.owner, blog, "hello")
        create_comment(org.owner, blog, "goodbye")
        create_comment(org.owner, blog, "sah dude")
        self.assertTrue(ann.comments.count() == 2)
        self.assertTrue(blog.comments.count() == 3)
