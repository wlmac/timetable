# Generated by Django 3.2.6 on 2021-08-15 05:11

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_auto_20210815_0504"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="announcement",
            name="replaces",
        ),
    ]
