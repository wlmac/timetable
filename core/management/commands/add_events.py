"""
This script is used to.
Code owned by Phil of metropolis backend team.
"""

import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from core.models import Event

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
            raise AssertionError("Could not get calendar data. Are you sure the calendar link is set correctly? See the instructions in core/management/commands/add_events.py")

        lines = rq.text.splitlines()

        event_data = {}
        is_in_event = False

        for l in lines:
            # self.stdout.write(l)
            l = l.strip()

            if l == "BEGIN:VEVENT":
                is_in_event = True
            
            elif l == "END:VEVENT":
                is_in_event = False

                # TODO: because past events are not deleted from the calendar,
                #       we have to somehow make sure we don't add the same event twice
                #       => maybe discard any events that have end before the script was run?
                self.stdout.write(f"New event discovered:\n")
                self.stdout.write(f"\tData: {event_data}\n")
                for k, v in event_data.items():
                    self.stdout.write(f"\t{k}: {v}\n")
                
                event_data = {}
            
            elif is_in_event:
                if l.startswith("SUMMARY:"):
                    event_data["name"] = l[len("SUMMARY:"):]

                elif l.startswith("DESCRIPTION:"):
                    event_data["description"] = l[len("DESCRIPTION:"):]

                elif l.startswith("DTSTART:"):
                    dtstart = l[len("DTSTART:"):]
                    event_data["start"] = datetime.strptime(dtstart, "%Y%m%dT%H%M%SZ") # TODO: check if timezone is correct
                    # TODO: all-day events are stored as DTSTART;VALUE=DATE:%Y%m%d for some weird reason

                elif l.startswith("DTEND:"):
                    dtend = l[len("DTEND:"):]
                    event_data["end"] = datetime.strptime(dtend, "%Y%m%dT%H%M%SZ") # TODO: check if timezone is correct
                    # TODO: all-day events are stored as DTSTART;VALUE=DATE:%Y%m%d for some weird reason
