from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Sequence, Tuple, Union

from django.apps import apps
from django.db import models
from django.utils.translation import ugettext as _


@dataclass
class CalendarWeek:
    """ A calendar week defined by year and ISO week number. """

    year: Optional[int] = None
    week: Optional[int] = None

    @classmethod
    def from_date(cls, when: date):
        """ Get the calendar week by a date object (the week this date is in). """

        week = int(when.strftime("%V"))
        year = when.year + 1 if when.month == 12 and week == 1 else when.year

        return cls(year=year, week=week)

    @classmethod
    def current_week(cls) -> int:
        """ Get the current week number. """

        return cls().week

    @classmethod
    def weeks_within(cls, start: date, end: date) -> Sequence[CalendarWeek]:
        """ Get all calendar weeks within a date range. """

        if start > end:
            raise ValueError("End date must be after start date.")

        current = start
        weeks = []
        while current < end:
            weeks.append(cls.from_date(current))
            current += timedelta(days=7)

        return weeks

    def __post_init__(self) -> None:
        today = date.today()

        if not self.year:
            self.year = today.year
        if not self.week:
            self.week = int(today.strftime("%V"))

    def __str__(self) -> str:
        return "%s %d (%s %s %s)" % (_("Calendar Week"), self.week, self[0], _("to"), self[-1],)

    def __len__(self) -> int:
        return 7

    def __getitem__(self, n: int) -> date:
        if n < -7 or n > 6:
            raise IndexError("Week day %d is out of range." % n)

        if n < 0:
            n += 7

        return datetime.strptime("%d-%d-%d" % (self.year, self.week, n + 1), "%G-%V-%u").date()

    def __contains__(self, day: date) -> bool:
        return self.__class__.form_date(day) == self

    def __eq__(self, other: CalendarWeek) -> bool:
        return self.year == other.year and self.week == other.week

    def __lt__(self, other: CalendarWeek) -> bool:
        return self[0] < other[0]

    def __gt__(self, other: CalendarWeek) -> bool:
        return self[0] > other[0]

    def __le__(self, other: CalendarWeek) -> bool:
        return self[0] <= other[0]

    def __gr__(self, other: CalendarWeek) -> bool:
        return self[0] >= other[0]

    def __add__(self, weeks: int) -> CalendarWeek:
        return self.__class__.from_date(self[0] + timedelta(days=weeks * 7))

    def __sub__(self, weeks: int) -> CalendarWeek:
        return self.__class__.from_date(self[0] - timedelta(days=weeks * 7))


def week_weekday_from_date(when: date) -> Tuple[CalendarWeek, int]:
    return (CalendarWeek.from_date(when), when.isoweekday())


def week_weekday_to_date(week: CalendarWeek, weekday: int) -> date:
    return week[weekday - 1]


def week_period_to_date(week: Union[CalendarWeek, int], period) -> date:
    return period.get_date(week)
