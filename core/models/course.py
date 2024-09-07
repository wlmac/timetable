from __future__ import annotations

import datetime as dt

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.utils import timezone

from .. import utils


class Term(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    timetable_format = models.CharField(max_length=64)
    start_date = models.DateField()
    end_date = models.DateField()
    is_frozen = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def start_datetime(self):
        return timezone.make_aware(dt.datetime.combine(self.start_date, dt.time()))

    def end_datetime(self):
        return timezone.make_aware(
            dt.datetime.combine(self.end_date, dt.time(hour=23, minute=59, second=59))
        )

    def is_current(self, target_date=None):
        target_date = utils.get_localdate(date=target_date)
        return self.start_date <= target_date < self.end_date

    def day_is_instructional(self, target_date=None):
        target_date = utils.get_localdate(date=target_date, time=[11, 0, 0])
        return (
            target_date.weekday() < 5
            and not self.events.filter(
                is_instructional=False,
                start_date__lte=target_date,
                end_date__gte=target_date,
            ).exists()
        )

    def day_num(self, target_date=None):
        tf = settings.TIMETABLE_FORMATS[self.timetable_format]
        methods = {
            "consecutive": self.__day_num_consecutive,
            "calendar_days": self.__day_num_calendar_days,
        }
        target_date = utils.get_localdate(date=target_date, time=[23, 59, 59])
        if not self.is_current(target_date.date()) or not self.day_is_instructional(
            target_date
        ):
            return None
        return methods[tf.get("day_num_method", "consecutive")](tf, target_date)

    @staticmethod
    def __day_num_calendar_days(tf, target_date):
        """
        Gets the day number from if the calendar day is even (day 2) or odd (day 1).
        """
        if tf["cycle"]["length"] != 2:
            raise TypeError(
                "calendar_days cannot be used in formats where cycle length != 2"
            )
        even, odd = 0, 1
        return {even: 2, odd: 1}[target_date.day % 2]

    def __day_num_consecutive(self, tf, target_date):
        """
        Gets the day number by counting consecutive days.
        """
        cycle_duration = tf["cycle"]["duration"]

        cur_iter_day = self.start_datetime().replace(hour=11, minute=0, second=0)
        cycle_day_type_set = set()

        while cur_iter_day <= target_date:
            if self.day_is_instructional(cur_iter_day):
                if cycle_duration == "day":
                    cycle_day_type_set.add(cur_iter_day.timetuple().tm_yday)
                elif cycle_duration == "week":
                    cycle_day_type_set.add(cur_iter_day.isocalendar()[1])
                else:
                    raise NotImplementedError
            cur_iter_day += dt.timedelta(1)

        return (len(cycle_day_type_set) - 1) % tf["cycle"]["length"] + 1

    def day_schedule_format(self, target_date=None):
        tds = utils.get_localdate(date=target_date, time=[0, 0, 0])  # target date start
        tde = utils.get_localdate(
            date=target_date, time=[23, 59, 59]
        )  # target date end

        schedule_formats = settings.TIMETABLE_FORMATS[self.timetable_format][
            "schedules"
        ]
        schedule_format_set = set(
            self.events.filter(start_date__lte=tde, end_date__gte=tds).values_list(
                "schedule_format", flat=True
            )
        ).intersection(set(schedule_formats.keys()))
        for schedule_format in list(schedule_formats.keys())[::-1]:
            if schedule_format in schedule_format_set:
                return schedule_format

        return "default"

    def day_schedule(self, target_date=None):
        target_date = utils.get_localdate(date=target_date)

        timetable_config = settings.TIMETABLE_FORMATS[self.timetable_format]
        day_num = self.day_num(target_date=target_date)

        if day_num is None:
            return []

        result = []

        for i in timetable_config["schedules"][
            self.day_schedule_format(target_date=target_date)
        ]:
            start_time = timezone.make_aware(
                dt.datetime.combine(target_date, dt.time(*i["time"][0]))
            )
            end_time = timezone.make_aware(
                dt.datetime.combine(target_date, dt.time(*i["time"][1]))
            )

            result.append(
                {
                    "description": i["description"],
                    "time": {
                        "start": start_time,
                        "end": end_time,
                    },
                    "position": i["position"][day_num - 1],
                    "cycle": f'{timetable_config["cycle"]["duration"].title()} {day_num}',
                    "course": f'{timetable_config["cycle"]["duration"].title()} {day_num} {i["description"]["course"]}',
                }
            )

        return result

    class MisconfiguredTermError(Exception):
        pass

    def save(self, *args, **kwargs):
        if self.start_date > self.end_date:
            raise self.MisconfiguredTermError("Start date must be before end date")

        # check for overlapping terms
        for term in Term.objects.all():
            if term.id == self.id:
                continue

            if term.start_date <= self.start_date < term.end_date:
                raise self.MisconfiguredTermError(
                    "Current term's date range overlaps with existing term"
                )

            if term.start_date < self.end_date <= term.end_date:
                raise self.MisconfiguredTermError(
                    "Current term's date range overlaps with existing term"
                )

        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls, target_date=None):
        target_date = utils.get_localdate(date=target_date)

        try:
            return cls.objects.get(
                start_date__lte=target_date, end_date__gt=target_date
            )
        except cls.DoesNotExist:
            return None
        except MultipleObjectsReturned:
            raise cls.MisconfiguredTermError


class Course(models.Model):
    code = models.CharField(max_length=16)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="courses")
    description = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField()

    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.code

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["code", "term"], name="unique_course"),
        ]


class Event(models.Model):
    name = models.CharField(max_length=64)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="events")

    organization = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="events",
        related_query_name="event",
    )
    description = models.TextField(blank=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()  # todo fix this

    schedule_format = models.CharField(max_length=64, default="default")
    is_instructional = models.BooleanField(
        default=True,
        help_text="Whether this event changes the day's schedule or not. Leave checked if not direct cause. (don't change for presentations, etc.)",
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Whether if this event pertains to the general school population, not just those in the organization.",
    )
    should_announce = models.BooleanField(
        default=False,
        help_text="Whether if this event should be announced to the general school population VIA the important events feed.",
    )

    tags = models.ManyToManyField(
        "Tag", blank=True, related_name="events", related_query_name="event"
    )

    def __str__(self):
        return self.name

    def is_current(self):
        today = timezone.localtime()
        return self.start_date <= today < self.end_date

    @classmethod
    def get_events(cls, user=None):
        events = cls.objects.filter(is_public=True)
        if user is not None and user.is_authenticated:
            events = (events | events.filter(organization__member=user)).distinct()

        return events

    def save(self, *args, **kwargs):
        if not timezone.is_aware(self.end_date):
            # Convert naive datetime to aware datetime
            self.end_date = timezone.make_aware(
                self.end_date, timezone.get_current_timezone()
            )
        if not timezone.is_aware(self.start_date):
            # Convert naive datetime to aware datetime
            self.start_date = timezone.make_aware(
                self.start_date, timezone.get_current_timezone()
            )
        super().save(*args, **kwargs)
