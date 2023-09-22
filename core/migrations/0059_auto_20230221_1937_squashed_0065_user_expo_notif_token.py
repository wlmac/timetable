# Generated by Django 4.0.10 on 2023-04-01 23:02

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0058_fix_blogpost_featured_image_description"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="saved_announcements",
            field=models.ManyToManyField(blank=True, to="core.announcement"),
        ),
        migrations.AddField(
            model_name="user",
            name="saved_blogs",
            field=models.ManyToManyField(blank=True, to="core.blogpost"),
        ),
        migrations.CreateModel(
            name="Like",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "object_id",
                    models.PositiveIntegerField(
                        help_text="The id of the object this comment is on"
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=models.SET(None), to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        help_text="The type of object this comment is on (core | blog post or core | announcement)",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "object_id",
                    models.PositiveIntegerField(
                        help_text="The id of the object this comment is on"
                    ),
                ),
                ("body", models.TextField(max_length=512)),
                (
                    "live",
                    models.BooleanField(default=False, help_text="Shown publicly?"),
                ),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=models.SET(None), to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        help_text="The type of object this comment is on (core | blog post or core | announcement)",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "likes",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The users who liked this comment",
                        to="core.like",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="core.comment",
                    ),
                ),
            ],
            options={
                "ordering": ["created"],
                "permissions": (("view_nodelay", "View without delay"),),
            },
        ),
        migrations.AddField(
            model_name="announcement",
            name="likes",
            field=models.ManyToManyField(blank=True, to="core.like"),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="likes",
            field=models.ManyToManyField(blank=True, to="core.like"),
        ),
        migrations.AddIndex(
            model_name="comment",
            index=models.Index(
                fields=["content_type", "object_id"],
                name="core_commen_content_37d5bd_idx",
            ),
        ),
        migrations.AlterModelOptions(
            name="comment",
            options={
                "ordering": ["created_at"],
                "permissions": (("view_flagged", "View flagged comments"),),
            },
        ),
        migrations.RenameField(
            model_name="comment",
            old_name="created",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="like",
            old_name="created",
            new_name="created_at",
        ),
        migrations.AddField(
            model_name="comment",
            name="last_modified",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="comment",
            name="author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET("[deleted]"),
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="like",
            name="author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET("[deleted]"),
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)ss_authored",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="%(class)ss",
                related_query_name="%(class)s",
                to="core.tag",
            ),
        ),
        migrations.AlterField(
            model_name="blogpost",
            name="author",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)ss_authored",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="blogpost",
            name="last_modified_date",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="blogpost",
            name="tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="%(class)ss",
                related_query_name="%(class)s",
                to="core.tag",
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="body",
            field=models.TextField(max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name="comment",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name="like",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.CreateModel(
            name="CommentHistory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("body", models.TextField(max_length=512, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                (
                    "Comment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.comment"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="comment",
            name="history",
            field=models.ManyToManyField(blank=True, to="core.commenthistory"),
        ),
        migrations.RemoveField(
            model_name="announcement",
            name="likes",
        ),
        migrations.RemoveField(
            model_name="blogpost",
            name="likes",
        ),
        migrations.RemoveField(
            model_name="comment",
            name="likes",
        ),
        migrations.AddField(
            model_name="user",
            name="expo_notif_token",
            field=models.TextField(
                blank=True, null=True, verbose_name="Expo Notifications Token"
            ),
        ),
        migrations.RemoveField(
            model_name="user",
            name="expo_notif_token",
        ),
    ]
