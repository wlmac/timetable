# Generated by Django 3.2.6 on 2021-08-14 08:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="graduating_year",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (2022, 2022),
                    (2023, 2023),
                    (2024, 2024),
                    (2025, 2025),
                    (2026, 2026),
                    (2027, 2027),
                ],
                null=True,
            ),
        ),
    ]
