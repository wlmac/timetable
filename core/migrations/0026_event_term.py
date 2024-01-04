# Generated by Django 3.2.6 on 2021-09-01 02:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0025_event_schedule_format"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="term",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to="core.term",
            ),
            preserve_default=False,
        ),
    ]
