"""
This script is used to add events from Google Calendar to the maclyonsden database.

If you are getting an error related to the SECRET_GCAL_ADDRESS not being set correctly,
first obtain the correct link by following the instructions below:
https://web.archive.org/web/20240902165230/https://cdn.discordapp.com/attachments/1280208592712241285/1280208610848407714/instructions.png?ex=66d73ead&is=66d5ed2d&hm=8f1e5943cad6f4869d7d83737d5d171d8512b5a67b2b3818271a0e84e9e02125&

After you have copied the link, go to metropolis/local_settings.py
and add the link to the SECRET_GCAL_ADDRESS variable.

Code owned by Phil of metropolis backend team.
"""

import datetime
from zoneinfo import ZoneInfo

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Event, Organization, Term


class Command(BaseCommand):
    help = "Imports events that that have not yet ended from Google Calendar. See https://github.com/wlmac/metropolis/issues/250"

    def add_arguments(self, parser):
        parser.add_argument(
            "--term",
            "-t",
            type=str,
            help="The name of the term globally assigned for all future events from the google calendar.",
        )

        parser.add_argument(
            "--log-past-events",
            "-P",
            action="store_true",
            help="Logs the names of past events that got skipped",
        )

        parser.add_argument(
            "--log-duplicate-events",
            "-D",
            action="store_true",
            help="Logs the names of duplicate events that got skipped",
        )

    def handle(self, *args, **options):
        TERM_OVERRIDE = self._get_term_from_args(options)
        TZID = "America/Toronto"

        SECRET_GCAL_ADDRESS = settings.SECRET_GCAL_ADDRESS

        if SECRET_GCAL_ADDRESS == "Change me":
            raise AssertionError(
                "SECRET_GCAL_ADDRESS is not set. Please change in metropolis/local_settings.py"
            )

        response = requests.get(SECRET_GCAL_ADDRESS)

        if response.status_code != 200:
            raise AssertionError(
                f"Error {response.status_code}, {response.reason}. Could not get calendar data. Are you sure the calendar link is set correctly? See the instructions in core/management/commands/add_events.py"
            )

        event_data = {}
        in_event = False
        vevent_paragraph = ""
        contains_rrule = False

        for line in response.text.splitlines():
            if line.startswith("BEGIN:VEVENT"):
                event_data = {
                    "name": "Unnamed Event",
                    "description": "",
                    "start_date": None,
                    "end_date": None,
                    "term": options["term"] if options["term"] else None,
                    "organization": None,
                    "schedule_format": "default",
                    "is_public": True,
                    "should_announce": False,
                }
                in_event = True
                vevent_paragraph = ""

            elif line.startswith("END:VEVENT"):
                in_event = False

                if event_data["start_date"] is None:
                    self.stdout.write(
                        self.style.ERROR(
                            f"\nEvent '{event_data['name']}' will be skipped because start date does not exist or is not parsed correctly."
                        )
                    )

                    self.stdout.write(f"Event raw data: \n{vevent_paragraph}")

                    self.stdout.write(
                        "Press 'Enter' to acknowledge that you will have to create the event manually"
                    )

                    input()

                    continue

                # Events that do not have a DTEND
                if event_data["end_date"] is None:
                    event_data["end_date"] = event_data[
                        "start_date"
                    ] + datetime.timedelta(minutes=1)

                # Uses cli argument if possible, otherwise use date from event
                event_data["term"] = (
                    TERM_OVERRIDE
                    if TERM_OVERRIDE is not None
                    else self._get_term_from_date(
                        event_data["start_date"], event_data["end_date"]
                    )
                )

                # Because past events are not deleted from the .ics file, we don't
                # add any events that have already passed to prevent duplication.
                if timezone.now() > event_data["end_date"]:
                    if options["log_past_events"]:
                        self.stdout.write(
                            self.style.WARNING(
                                f"\nEvent '{event_data["name"]}' skipped because it has already passed."
                            )
                        )
                    continue

                # Skip creating a duplicate event of one that already exists
                if Event.objects.filter(
                    name__iexact=event_data["name"],
                    start_date=event_data["start_date"],
                    end_date=event_data["end_date"],
                ).exists():
                    if options["log_duplicate_events"]:
                        self.stdout.write(
                            self.style.WARNING(
                                f"\nEvent '{event_data["name"]}' skipped because it already exists."
                            )
                        )
                    continue

                if contains_rrule:
                    self.stdout.write(
                        self.style.WARNING(
                            "Automatically recurring event (RRULE) detected in event. Reccurence rules are not supported by the script; you must create any future instances of this event manually."
                        )
                    )

                    contains_rrule = False

                self.stdout.write(self.style.SUCCESS("\nNew event created:"))

                # Print known attributes of the event
                for key, value in event_data.items():
                    self.stdout.write(f"\t{key}: {value}\n")

                if Term.get_current(event_data["start_date"]) != event_data["term"]:
                    self.stdout.write(
                        self.style.WARNING(
                            f"\nEvent '{event_data['name']}' has a term that does not match the current term's date range."
                        )
                    )

                if event_data["term"] is None:
                    self.stdout.write(
                        "\n\tPlease enter the name of the event's affiliated term (case insensitive, type 'skip' to skip the creation this event): ",
                        ending="\n\t",
                    )

                    event_data["term"] = self._get_term_from_name(options)

                event_data["organization"] = self._get_organization()
                event_data["schedule_format"] = self._get_schedule_format(
                    event_data["term"]
                )

                for key in ["is_public", "should_announce"]:
                    event_data[key] = self._get_boolean(key, event_data[key])

                event = Event(**event_data)
                event.save()

                self.stdout.write(self.style.SUCCESS(f"\n\tEvent saved: {event}"))

            elif in_event:
                vevent_paragraph += line.strip() + "\n"

                try:
                    if line.startswith("SUMMARY"):
                        event_data["name"] = line[line.index(":") + 1 :]

                    elif line.startswith("DESCRIPTION"):
                        event_data["description"] = (
                            line[line.index(":") + 1 :]
                            .replace("\\r", "\r")
                            .replace("\\n", "\n")
                        )

                    elif line.startswith("DTSTART"):
                        start_date = line[line.index(":") + 1 :]
                        if "VALUE=DATE" in line:
                            # gcalendar's all-day events aren't supported on the mld calendar so we hack it here and hope the people that are looking are in america/toronto
                            event_data["start_date"] = timezone.make_aware(
                                datetime.datetime.strptime(start_date, "%Y%m%d"),
                                timezone=ZoneInfo(TZID),
                            )
                        elif "TZID" in line:
                            TEMP_TZID = line[line.index("TZID=") + 5 : line.index(":")]
                            event_data["start_date"] = timezone.make_aware(
                                datetime.datetime.strptime(start_date, "%Y%m%dT%H%M%S"),
                                timezone=ZoneInfo(TEMP_TZID),
                            )
                        else:
                            event_data["start_date"] = timezone.make_aware(
                                datetime.datetime.strptime(
                                    start_date, "%Y%m%dT%H%M%SZ"
                                ),
                                datetime.timezone.utc,
                            )

                    elif line.startswith("DTEND"):
                        end_date = line[line.index(":") + 1 :]
                        if "VALUE=DATE:" in line:
                            # gcalendar's all-day events aren't supported on the mld calendar so we hack it here and hope the people that are looking are in america/toronto
                            event_data["end_date"] = timezone.make_aware(
                                datetime.datetime.strptime(end_date, "%Y%m%d"),
                                timezone.get_current_timezone(),
                            )
                        elif "TZID" in line:
                            TEMP_TZID = line[line.index("TZID=") + 5 : line.index(":")]
                            event_data["end_date"] = timezone.make_aware(
                                datetime.datetime.strptime(end_date, "%Y%m%dT%H%M%S"),
                                timezone=ZoneInfo(TEMP_TZID),
                            )
                        else:
                            event_data["end_date"] = timezone.make_aware(
                                datetime.datetime.strptime(end_date, "%Y%m%dT%H%M%SZ"),
                                datetime.timezone.utc,
                            )

                    elif line.startswith(
                        " "
                    ):  # to whoever decided to turn DESCRIPTION into a multiline field, i hope your coffee machine malfunctions often
                        event_data["description"] += (
                            line[1:].replace("\\r", "\r").replace("\\n", "\n")
                        )

                    elif line.startswith("RRULE"):
                        # TODO: might implement this in the future but this thing gave me a headache for way too long
                        contains_rrule = True
                        pass

                except ValueError:
                    pass

            elif line.startswith("TZID"):
                pass
                # tzid = line[line.index(":") + 1 :] # todo: do something with this?

        self.stdout.write(self.style.SUCCESS("\nDone."))
        self.stdout.write(
            self.style.WARNING(
                "\nPlease double check that all the events from google calendar were added correctly.\n"
            )
        )

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
                    self.style.ERROR("Please enter 'y' or 'n' (leave blank for 'n')."),
                    ending="\n\t",
                )

    def _get_term_from_date(self, start_date, end_date):
        try:
            return Term.get_current(start_date)
        except Term.DoesNotExist:
            try:
                return Term.get_current(end_date)
            except Term.DoesNotExist:
                return None

    def _get_term_from_args(self, options):
        if options["term"] is None:
            return None

        try:
            term = Term.objects.get(name__iexact=options["term"])
            self.stdout.write(
                self.style.SUCCESS(f"Using term '{term}' for all upcoming events...")
            )

            return term

        except Term.DoesNotExist:
            raise AssertionError(
                f"Term '{options["term"]}' does not exist. Did you make a typo?"
            )

        except Term.MultipleObjectsReturned:
            self.stdout.write(
                self.style.WARNING(
                    "Multiple terms found. Please provide the term's id:"
                ),
            )

            return self._get_term_from_id(options["term"])

    def _get_term_from_name(self, options):
        while True:
            term_name = input()

            if term_name == "skip":
                return None

            try:
                term = Term.objects.get(name__iexact=term_name)

                self.stdout.write(self.style.SUCCESS(f"\tTerm found: {term}"))
                return term

            except Term.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        "\tTerm not found. Did you make a typo? Please try again."
                    ),
                    ending="\n\t",
                )

            except Term.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.WARNING(
                        "Multiple terms found. Please provide the term's id:"
                    ),
                )

                return self._get_term_from_id(term_name)

    def _get_term_from_id(self, term_name):
        for term in Term.objects.filter(name__iexact=term_name):
            self.stdout.write(f"\t{term.name} (id = {term.id}): ")
            for field in {"description", "start_date", "end_date", "timetable_format"}:
                self.stdout.write(f"\t\t{field}: {getattr(term, field)}")

        while True:
            self.stdout.write("\n\tEnter the term's id: ", ending="")

            term_id = input()
            try:
                term = Term.objects.get(id=term_id)

                self.stdout.write(
                    self.style.SUCCESS(f"Using term '{term}' with id '{term.id}'.")
                )

                return term

            except (Term.DoesNotExist, ValueError):
                self.stdout.write(
                    self.style.ERROR(
                        f"\tTerm '{term_id}' does not exist. Please try again: "
                    ),
                    ending="\n\t",
                )

    def _get_organization(self):
        self.stdout.write(
            "\n\tPlease enter the name of the event's affiliated organization (case insensitive): ",
            ending="\n\t",
        )
        organization = None

        while True:
            organization_name = input()
            try:
                organization = Organization.objects.get(name__iexact=organization_name)

                self.stdout.write(
                    self.style.SUCCESS(f"\tOrganization found: {organization}")
                )
                break

            except Organization.DoesNotExist:
                try:
                    organization = Organization.objects.get(
                        slug__iexact=organization_name
                    )

                    self.stdout.write(
                        self.style.SUCCESS(f"\tOrganization found: {organization}")
                    )
                    break

                except Organization.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            "\tOrganization not found. Did you make a typo? Please try again."
                        ),
                        ending="\n\t",
                    )

        return organization

    def _get_schedule_format(self, term):
        schedule_format = "default"

        if self._get_yesno_response(
            "\n\tChange schedule format from its default value ('default')?"
        ):
            options = list(
                settings.TIMETABLE_FORMATS[term.timetable_format]["schedules"].keys()
            )

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
                            self.style.SUCCESS(f"\tNew value: {schedule_format}")
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
            self.stdout.write(self.style.SUCCESS("\tNo change"))

        return schedule_format

    def _get_boolean(self, key, value):
        if self._get_yesno_response(
            f"\n\tChange {key} from its default value ({value})?"
        ):
            self.stdout.write(self.style.SUCCESS(f"\tNew value: {not value}"))
            return not value

        else:
            self.stdout.write(self.style.SUCCESS("\tNo change"))
            return value
