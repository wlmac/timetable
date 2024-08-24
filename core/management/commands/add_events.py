"""
This script is used to.
Code owned by Phil of metropolis backend team.
"""

import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from core.models import Event, Organization, Term

# TODO: consider adding this to metropolis/settings.py in the "Event calender Settings" section (?)
SECRET_CAL_ADDRESS = "Change me"

class Command(BaseCommand):
    help = "Imports events that that have not yet ended from Google Calendar. See https://github.com/wlmac/metropolis/issues/250"

    def handle(self, *args, **options):
        if SECRET_CAL_ADDRESS == "Change me":
            raise AssertionError("SECRET_CAL_ADDRESS is not set. Please change in metropolis/settings.py")

        response = requests.get(SECRET_CAL_ADDRESS)

        if response.status_code != 200:
            raise AssertionError(
                f"Error {response.status_code}, {response.reason}. Could not get calendar data. Are you sure the calendar link is set correctly? See the instructions in core/management/commands/add_events.py"
            )

        event_data = {}
        in_event = False

        for line in response.text.splitlines():
            line = line.strip()

            if line == "BEGIN:VEVENT":
                event_data = {
                    "name": "Unnamed Event",
                    "description": "",
                    "start_date": None,
                    "end_date": None,
                    "term": None,
                    "organization": None,
                    "schedule_format": "default",
                    "is_instructional": True,
                    "is_public": True,
                    "should_announce": False,
                }
                in_event = True

            elif line == "END:VEVENT":
                in_event = False

                # Because past events are not deleted from the .ics file, we don't
                # add any events that have already passed to prevent duplication.
                if datetime.now() > event_data["end_date"]:
                    self.stdout.write(
                        self.style.ERROR(
                            f"\nEvent '{event_data["name"]}' skipped because it has already passed."
                        )
                    )
                    continue

                self.stdout.write(
                    self.style.SUCCESS(f"\nNew event created:")
                )

                for key, value in event_data.items():
                    self.stdout.write(f"\t{key}: {value}\n")

                event_data["term"] = self._get_term()
                event_data["organization"] = self._get_organization()
                event_data["schedule_format"] = self._get_schedule_format()

                for key in ["is_instructional", "is_public", "should_announce"]:
                    event_data[key] = self._get_boolean(key, event_data[key])

                event = Event(
                    name=event_data["name"],
                    description=event_data["description"],
                    start_date=event_data["start_date"],
                    end_date=event_data["end_date"],
                    term=event_data["term"],
                    organization=event_data["organization"],
                    schedule_format=event_data["schedule_format"],
                    is_instructional=event_data["is_instructional"],
                    is_public=event_data["is_public"],
                    should_announce=event_data["should_announce"],
                )
                event.save()

                self.stdout.write(self.style.SUCCESS(f"\n\tEvent saved: {event}"))

            elif in_event:
                if line.startswith("SUMMARY:"):
                    event_data["name"] = line[len("SUMMARY:"):]
                elif line.startswith("DESCRIPTION:"):
                    event_data["description"] = line[len("DESCRIPTION:"):]
                elif line.startswith("DTSTART"):
                    if line.startswith("DTSTART;VALUE=DATE:"):
                        start_date = line[len("DTSTART;VALUE=DATE:"):]
                        event_data["start_date"] = datetime.strptime(start_date, "%Y%m%d")
                    elif line.startswith("DTSTART:"):
                        start_date = line[len("DTSTART:"):]
                        event_data["start_date"] = datetime.strptime(start_date, "%Y%m%dT%H%M%SZ")
                elif line.startswith("DTEND"):
                    if line.startswith("DTEND;VALUE=DATE:"):
                        end_date = line[len("DTEND;VALUE=DATE:"):]
                        event_data["end_date"] = datetime.strptime(end_date, "%Y%m%d")
                    elif line.startswith("DTEND:"):
                        end_date = line[len("DTEND:"):]
                        event_data["end_date"] = datetime.strptime(end_date, "%Y%m%dT%H%M%SZ")

    def _get_yesno_response(self, question):
        while True:
            self.stdout.write(f"\t{question} (y/N):", ending="")

            i = input().lower()

            if i == "y":
                return True
            elif i == "n" or i == "":
                return False
            else:
                self.stdout.write(
                    self.style.ERROR("Please enter 'y' or 'n' (leave blank for 'n')."), ending="\n\t"
                )

    def _get_term(self):
        self.stdout.write(f"\n\tPlease enter the name of the event's affiliated term (case insensitive): ", ending="\n\t")

        while True:
            term_name = input()
            try:
                term = Term.objects.get(name__iexact=term_name)

                self.stdout.write(
                    self.style.SUCCESS(f"\tTerm found: {term}")
                )
                return term

            except Term.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        "\tTerm not found. Did you make a typo? Please try again."
                    ), ending="\n\t"
                )

    def _get_organization(self):
        self.stdout.write(f"\n\tPlease enter the name of the event's affiliated organization (case insensitive): ", ending="\n\t")
        organization = None

        while True:
            organization_name = input()
            try:
                organization = Organization.objects.get(name__iexact=organization_name)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\tOrganization found: {organization}"
                    )
                )
                break

            except Organization.DoesNotExist:
                try:
                    organization = Organization.objects.get(slug__iexact=organization_name)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\tOrganization found: {organization}"
                        )
                    )
                    break

                except Organization.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            "\tOrganization not found. Did you make a typo? Please try again."
                        ), ending="\n\t"
                    )

        return organization

    def _get_schedule_format(self):
        schedule_format = "default"
        
        if self._get_yesno_response(f"\n\tChange schedule format from its default value ({schedule_format})?"):
            options = [
                "early-dismissal",
                "one-hour-lunch",
                "early-early-dismissal",
                "default",
                "half-day",
                "late-start",
                "sac-election",
            ]

            self.stdout.write("\t------------------------")
            for i, option in enumerate(options):
                self.stdout.write(f"\t{i+1}: {option}")
            self.stdout.write("\t------------------------")

            while True:
                self.stdout.write("\tSelect a new format by number: ", ending="")

                i = input()

                try:
                    if int(i) > 0 and int(i) <= len(options):
                        schedule_format = options[int(i) - 1]

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"\tNew value: {schedule_format}"
                            )
                        )
                        break

                    else:
                        raise ValueError

                except ValueError:
                    self.stdout.write(
                        self.style.ERROR(
                            "\tInvalid input. Please enter a number within the list."
                        )
                    )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\tNo change")
            )
        
        return schedule_format

    def _get_boolean(self, key, value):
        if self._get_yesno_response(f"\n\tChange {key} from its default value ({value})?"):
            self.stdout.write(
                self.style.SUCCESS(f"\tNew value: {not value}")
            )
            return not value

        else:
            self.stdout.write(
                self.style.SUCCESS(f"\tNo change")
            )
            return value
    