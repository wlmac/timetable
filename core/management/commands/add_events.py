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
    # TODO: change help text
    help = "Adds organizations from Google Sheets. Does not modify existing organizations. See https://github.com/wlmac/metropolis/issues/247"

    def handle(self, *args, **options):
        if SECRET_CAL_ADDRESS == "Change me":
            raise AssertionError("SECRET_CAL_ADDRESS is not set.")
            # TODO: raise AssertionError("SECRET_CAL_ADDRESS is not set. Please change in metropolis/settings.py")

        rq = requests.get(SECRET_CAL_ADDRESS)

        if rq.status_code != 200:
            raise AssertionError(f"Error {rq.status_code}, {rq.reason}. Could not get calendar data. Are you sure the calendar link is set correctly? See the instructions in core/management/commands/add_events.py")

        lines = rq.text.splitlines()

        event_data = {}
        is_in_event = False

        for l in lines:
            # self.stdout.write(l)
            l = l.strip()

            if l == "BEGIN:VEVENT":
                # Default values
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
                    # "tags": [],
                }
                is_in_event = True
            
            elif l == "END:VEVENT":
                is_in_event = False

                # Because past events are not deleted from the calendar, we don't
                # add any events that have already passed to prevent duplication.
                if datetime.now() > event_data["end_date"]:
                    self.stdout.write(
                        self.style.ERROR(f"Event '{event_data["name"]}' skipped because it has already passed.")
                    )
                    continue

                self.stdout.write(
                    self.style.SUCCESS(f"\nNew event created:")
                )
                # self.stdout.write(f"\tData: {event_data}\n")
                for k, v in event_data.items():
                    self.stdout.write(f"\t{k}: {v}\n")

                term = None
                self.stdout.write(
                    "\n\tPlease enter the name of the event's affiliated term (case insensitive):"
                )
                while True:
                    try:
                        print("\t", end="")
                        term_name = input()
                        term = Term.objects.get(name__iexact=term_name)

                        self.stdout.write(
                            self.style.SUCCESS(f"\tTerm found: {term}")
                        )
                        break
                    except Term.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                "\tTerm not found. Did you make a typo?"
                            )
                        )
                        self.stdout.write("\tPlease re-enter term name:")
                event_data["term"] = term

                organization = None
                self.stdout.write(
                    "\n\tPlease enter the name OR slug of the event's affiliated organization (case insensitive):"
                )
                while True:
                    try:
                        print("\t", end="")
                        org_name = input()
                        organization = Organization.objects.get(name__iexact=org_name)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"\tOrganization found: {organization}"
                            )
                        )
                        break

                    except Organization.DoesNotExist:
                        try:
                            organization = Organization.objects.get(slug__iexact=org_name)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"\tOrganization found: {organization}"
                                )
                            )
                            break

                        except Organization.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(
                                    "\tOrganization not found. Did you make a typo?"
                                )
                            )
                            self.stdout.write("\tPlease re-enter organization name:")
                event_data["organization"] = organization

                schedule_format = "default"
                while True:
                    self.stdout.write(
                        f"\n\tChange schedule format from its default value ({event_data["schedule_format"]})? (y/N):"
                    )
                    print("\t", end="")

                    i = input()

                    if i.lower() == "y":
                        options = [
                            "early-dismissal",
                            "one-hour-lunch",
                            "early-early-dismissal",
                            "default",
                            "half-day",
                            "late-start",
                            "sac-election",
                        ]

                        for i, option in enumerate(options):
                            self.stdout.write(f"\t{i+1}: {option}")
                        
                        while True:
                            self.stdout.write("\tSelect a new format by number:")

                            print("\t", end="")
                            num = input()
                            try:
                                if int(num) > 0 and int(num) <= len(options):
                                    schedule_format = options[int(num) - 1]
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"\tNew value: {event_data["schedule_format"]}"
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
                        break
                    
                    elif i.lower() == "n" or i.lower() == "":
                        self.stdout.write(
                            self.style.SUCCESS(f"\tNo change")
                        )
                        break

                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                "\tInvalid input. Please enter 'y' or 'n' (leave blank for 'n')."
                            )
                        )
                event_data["schedule_format"] = schedule_format

                for s in ["is_instructional", "is_public", "should_announce"]:
                    boolean = event_data[s]
                    while True:
                        self.stdout.write(
                            f"\n\tChange {s} from its default value ({boolean})? (y/N):"
                        )
                        print("\t", end="")

                        i = input()

                        if i.lower() == "y":
                            boolean = not boolean
                            self.stdout.write(
                                self.style.SUCCESS(f"\tNew value: {boolean}")
                            )
                            break
                        
                        elif i.lower() == "n" or len(i) == 0:
                            self.stdout.write(
                                self.style.SUCCESS(f"\tNo change")
                            )
                            break

                        else:
                            self.stdout.write(
                                self.style.ERROR(
                                    "\tInvalid input. Please enter 'y' or 'n' (leave blank for 'n')."
                                )
                            )
                
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

                self.stdout.write(self.style.SUCCESS(f"\nEvent saved: {event}"))
            
            elif is_in_event:
                if l.startswith("SUMMARY:"):
                    event_data["name"] = l[len("SUMMARY:"):]

                elif l.startswith("DESCRIPTION:"):
                    event_data["description"] = l[len("DESCRIPTION:"):]

                elif l.startswith("DTSTART"):
                    if l.startswith("DTSTART;VALUE=DATE:"):
                        dtstart = l[len("DTSTART;VALUE=DATE:"):]
                        event_data["start_date"] = datetime.strptime(dtstart, "%Y%m%d") # TODO: fix timezone

                    elif l.startswith("DTSTART:"):
                        dtstart = l[len("DTSTART:"):]
                        event_data["start_date"] = datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ") # TODO: fix timezone

                elif l.startswith("DTEND"):
                    if l.startswith("DTEND;VALUE=DATE:"):
                        dtend = l[len("DTEND;VALUE=DATE:"):]
                        event_data["end_date"] = datetime.strptime(dtend, "%Y%m%d") # TODO: fix timezone

                    elif l.startswith("DTEND:"):
                        dtend = l[len("DTEND:"):]
                        event_data["end_date"] = datetime.strptime(dtend, "%Y%m%dT%H%M%SZ") # TODO: fix timezone

