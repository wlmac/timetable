# Generated by Django 3.2.6 on 2021-10-07 23:53

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0044_organization_show_members"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="organization",
            options={"verbose_name": "club", "verbose_name_plural": "clubs"},
        ),
        migrations.AlterModelOptions(
            name="organizationurl",
            options={"verbose_name": "Club URL", "verbose_name_plural": "Club URLs"},
        ),
    ]
