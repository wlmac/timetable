"""
This script is used to add organizations from a Google Sheets link. It is used to add organizations that are not already in the database.
Code owned by Phil of metropolis backend team.

Usage:
    python manage.py add_clubs <google_sheets_link>
"""

from __future__ import annotations

import csv
from io import StringIO

import requests
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from core.models import Organization, User


class Command(BaseCommand):
    help = "Adds organizations from Google Sheets. Does not modify existing organizations. See https://github.com/wlmac/metropolis/issues/247"

    def error(self, *args, **kwargs):
        self.stdout.write(
            self.style.ERROR(*args, **kwargs),
        )

    def success(self, *args, **kwargs):
        self.stdout.write(
            self.style.SUCCESS(*args, **kwargs),
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "sheets_link",
            type=str,
            help="Link to Google Sheets (must be published as CSV). "
            "Follow this guide (https://support.google.com/docs/answer/183965) to publish the spreadsheet, "
            "set the dropbox to 'Comma-separated-values (.csv)' and copy the link underneath (https://web.archive.org/web/20240902165418/https://cdn.discordapp.com/attachments/1280208592712241285/1280209073949638717/publish_to_web.png?ex=66d73f1c&is=66d5ed9c&hm=616b70187f8f3a54885b050e5f80c606d275318382333e5819364e020ba421bb&)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't actually add the organizations to the database",
        )

    def handle(self, *args, **options):
        sheets_url = str(options["sheets_link"])
        if not ("output=csv" in sheets_url or sheets_url.endswith(".csv")):
            raise AssertionError(
                "Make sure to make a copy of the club spreadsheet and use the link provided when publishing as .csv file (https://support.google.com/docs/answer/183965)"
            )

        csv_reader = csv.reader(StringIO(requests.get(sheets_url).text))

        expected_header = [
            "CLUB NAME",
            "APPROVED & MAILED",
            "SAF PAID",
            "PRESIDENT(S)",
            "PRESIDENT(S) EMAIL",
            "STAFF SUPERVISOR(S)",
            "STAFF(S) EMAIL",
            "BUDGET REQUEST",
            "TIME + PLACE",
            "SOCIAL LINKS",
        ]

        assert (
            expected_header == next(csv_reader)
        ), "Google Sheets layout changed since the last time the script was updated, please consult the backend team."

        for row in csv_reader:
            organization_is_not_approved = row[1] != "TRUE"
            has_duplicate_owner = len(row[0]) == 0
            if organization_is_not_approved:
                self.error(f"Skipping {row[0]} because it is not approved\n")
                continue
            elif has_duplicate_owner:
                self.error(f"Skipping {row[0]} as it's a duplicate owner\n")
                continue

            self.success(f"New organization: {row[0]}")
            (
                organization_name,
                _,
                _,
                owner_name,
                owner_email,
                staff_name,
                staff_email,
                _,
                time_and_place,
                social_links,
            ) = row

            club_owner = self.get_user_by_email(owner_name, owner_email)
            if club_owner == "skipped":  # prevent a repeat of the same error message
                continue

            supervisor_user = self.get_user_by_email(staff_name, staff_email)

            user_statuses = ""

            if club_owner == "skipped":
                user_statuses += "owner"
            elif supervisor_user == "skipped":
                user_statuses += "supervisor"

            if user_statuses != "":
                self.error(
                    f"Skipping {organization_name} as {user_statuses} is not found\n"
                )
                continue

            try:
                # Consider updating the google sheets table so we can automatically fill out bio and slug and stuff - NOTE: (json) Planned by Crystal for the upcoming 25-26 school year.
                defaults = (
                    {
                        "owner": club_owner,
                        "name": organization_name,
                        "extra_content": time_and_place + "\n\n" + social_links,
                        "show_members": True,
                        "is_active": True,
                        "is_open": False,
                    },
                )
                if not options["dry_run"]:
                    club, created = Organization.objects.update_or_create(
                        slug="".join(
                            c.casefold() if c.isalnum() else "-"
                            for c in organization_name
                        ).lower(),
                        defaults=defaults,
                        create_defaults={
                            **defaults,
                            "bio": "A WLMAC organization",
                        },
                    )
                    club.execs.add(club_owner)
                    club.supervisors.add(supervisor_user)

                    status = "added" if created else "updated"
                else:
                    status = "(dry-run | would have added)"
                self.success(
                    f"\tSuccessfully {status} {organization_name} organization, owned by {owner_name}"
                )
            except IntegrityError as IE:
                self.error(IE.__traceback__)
            self.stdout.write()

    type Status = "skipped"  # noqa: F821

    def get_user_by_email(self, name: str, email: str) -> User | Status:
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            self.error(
                f"\t{name}'s email ({email}) not found! Are you sure they registered a metro account with this email?"
            )

            self.stdout.write(
                "\tIf you have the correct email, please enter it here (type 'skip' to skip this entry):"
            )
            while True:
                try:
                    print("\t", end="")
                    email = input().casefold()
                    return User.objects.get(email=email)
                except User.DoesNotExist:
                    if email == "skip":
                        return "skipped"
                    self.error(
                        "\tUser not found. Did you make a typo? (type 'skip' to skip this entry)"
                    )

                    self.stdout.write("\tPlease re-enter email:")
