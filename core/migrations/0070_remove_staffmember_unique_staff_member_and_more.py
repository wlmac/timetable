# Generated by Django 5.0 on 2024-01-04 12:02

import core.utils.fields
import core.models.user
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("core", "0069_staffmember_alter_user_options_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="staffmember",
            name="unique_staff_member",
        ),
        migrations.AlterField(
            model_name="staffmember",
            name="positions",
            field=core.utils.fields.ChoiceArrayField(
                base_field=models.CharField(
                    choices=[
                        ("Project Manager", "Project Manager"),
                        ("Frontend Developer", "Frontend Developer"),
                        ("Backend Developer", "Backend Developer"),
                        ("App Developer", "App Developer"),
                        ("Graphic Designer", "Graphic Designer"),
                        ("Content Creator", "Content Creator"),
                        ("Doodle Developer", "Doodle Developer"),
                    ]
                ),
                help_text="The positions the user had/does hold.",
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="staffmember",
            name="positions_leading",
            field=core.utils.fields.ChoiceArrayField(
                base_field=models.CharField(
                    choices=[
                        ("Frontend Developer", "Frontend Developer"),
                        ("Backend Developer", "Backend Developer"),
                        ("App Developer", "App Developer"),
                        ("Graphic Designer", "Graphic Designer"),
                        ("Content Creator", "Content Creator"),
                        ("Doodle Developer", "Doodle Developer"),
                    ]
                ),
                blank=True,
                null=True,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="staffmember",
            name="years",
            field=core.utils.fields.ChoiceArrayField(
                base_field=models.CharField(
                    choices=[
                        ("2021-2022", "2021-2022"),
                        ("2022-2023", "2022-2023"),
                        ("2023-2024", "2023-2024"),
                        ("2024-2025", "2024-2025"),
                    ]
                ),
                help_text="The years the user was a staff member. Used to determine if the user is an alumni.",
                size=None,
            ),
        ),
        migrations.AlterModelOptions(
            name="user",
            options={"verbose_name": "user", "verbose_name_plural": "users"},
        ),
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", core.models.user.CaseInsensitiveUserManager()),
            ],
        ),
    ]
