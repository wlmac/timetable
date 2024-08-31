import datetime
from typing import Final

import pytz

timezone_choices = [(i, i) for i in pytz.common_timezones]


def calculate_graduating_year_choices():
    """
    Calculates possible graduation years for high school students,
    taking into account the current time, considering the academic year
    starts in September and ends in June.

    Returns:
            list: A list of tuples containing possible graduation years and their string representations.
    """

    # Get the current year and month
    current_year = datetime.datetime.now().year
    current_month = datetime.datetime.now().month

    # Adjust the current year if it's after June (academic year ends in June)
    if current_month > 6:  # June is the 6th month
        current_year += 1

    graduating_year_choices = [
        (year, year) for year in range(current_year, current_year + 4)
    ]

    # Add the "Does not apply" option at the beginning
    graduating_year_choices.insert(0, (None, "Does not apply"))

    return graduating_year_choices


graduating_year_choices: Final = calculate_graduating_year_choices()

announcement_status_choices = [
    ("d", "Draft"),
    ("p", "Pending Approval"),
    ("a", "Approved"),
    ("r", "Rejected"),
]

announcement_status_initial_choices = [
    ("d", "Draft (don't send)"),
    ("p", "Send to supervisor for review"),
]
