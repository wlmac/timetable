# Generated by Django 3.2.6 on 2021-09-01 02:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0024_blogpost_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="schedule_format",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
