from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse

from core.models import Announcement
from core.utils.mail import send_mail


def request_announcement_approval(post: Announcement):
    for teacher in post.organization.supervisors.all():
        email_template_context = {
            "teacher": teacher,
            "announcement": post,
            "review_link": settings.SITE_URL
            + reverse("admin:core_announcement_change", args=(post.pk,)),
        }

        send_mail(
            f"[ACTION REQUIRED] An announcement for {post.organization.name} needs your approval.",
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
