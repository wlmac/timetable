# Generated by Django 3.2.6 on 2021-09-01 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_auto_20210901_1059'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='graduating_year',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(None, 'Does not apply'), (2022, 2022), (2023, 2023), (2024, 2024), (2025, 2025), (2026, 2026), (2027, 2027)], null=True),
        ),
    ]
