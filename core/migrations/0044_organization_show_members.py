# Generated by Django 3.2.6 on 2021-09-29 02:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0043_auto_20210917_0325"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="show_members",
            field=models.BooleanField(default=True),
        ),
    ]
