# Generated by Django 4.0.10 on 2023-04-01 23:03

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "core",
            "0058_fix_blogpost_featured_image_description",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="should_announce",
            field=models.BooleanField(
                default=False,
                help_text="Whether if this event should be announced to the general school population VIA the important events feed.",
            ),
        ),
        migrations.CreateModel(
            name="RecurrenceRule",
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
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                            ("yearly", "Yearly"),
                            ("custom", "Custom"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "starts",
                    models.DateTimeField(
                        help_text="the date and time the repetition starts."
                    ),
                ),
                (
                    "repeats_every",
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text="the gap between repetitions. (e.g. 2 would mean every other day if type=DAILY)",
                    ),
                ),
                ("repeat_on", models.PositiveSmallIntegerField()),
                (
                    "repeat_type",
                    models.IntegerField(
                        choices=[(0, "First"), (1, "Last"), (2, "Day")]
                    ),
                ),
                ("ends", models.DateTimeField()),
                ("ends_after", models.PositiveSmallIntegerField()),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reoccurrences",
                        to="core.event",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="recurrencerule",
            constraint=models.CheckConstraint(
                check=models.Q(("ends__gt", django.db.models.expressions.F("starts"))),
                name="ends_after_greater_than_starts",
            ),
        ),
        migrations.AddConstraint(
            model_name="recurrencerule",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("ends__isnull", True),
                    ("ends_after__isnull", True),
                    _connector="OR",
                ),
                name="ends_or_ends_after",
            ),
        ),
        migrations.AddConstraint(
            model_name="recurrencerule",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("type", "weekly"), ("repeat_on__isnull", True), _connector="OR"
                ),
                name="repeat_on_only_with_weekly_type",
            ),
        ),
        migrations.AddConstraint(
            model_name="recurrencerule",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("type", "monthly"), ("repeat_type__isnull", True), _connector="OR"
                ),
                name="repeat_type_only_with_monthly_type",
            ),
        ),
    ]
