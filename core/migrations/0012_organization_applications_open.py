# Generated by Django 3.2.6 on 2021-08-27 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_auto_20210822_2029"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="applications_open",
            field=models.BooleanField(default=False),
        ),
    ]
