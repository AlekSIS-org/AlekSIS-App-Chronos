from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Sequence, Tuple

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

        return cls(year=when.strftime('%Y'), week=when.strftime('%V'))

    def __post_init__(self) -> None:
        today = date.today()

        if not self.year:
            self.year = today.year
        if not self.week:
            self.week = today.isoweekday()

    def __str__(self) -> str:
        return '%s %d (%s %s %s)' % (_('Kalenderwoche'), self.week, self[0], _('to'), self[-1])

    def __len__(self) -> int:
        return 7

    def __getitem__(self, n: int) -> date:
        if n < -7 or n > 6:
            raise IndexError('Week day %d is out of range.' % n)

        if n < 0:
            n += 7

        return datetime.strptime('%d-%d-%d' % (self.year, self.week, n + 1), '%G-%V-%u').date()

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


def current_lesson_periods(when: Optional[datetime] = None) -> models.query.QuerySet:
    now = when or datetime.now()

    LessonPeriod = apps.get_model('chronos.LessonPeriod')
    return LessonPeriod.objects.filter(lesson__date_start__lte=now.date(),
                                       lesson__date_end__gte=now.date(),
                                       period__weekday=now.isoweekday(),
                                       period__time_start__lte=now.time(),
                                       period__time_end__gte=now.time())


def week_weekday_from_date(when: date) -> Tuple[CalendarWeek, int]:
    return (CalendarWeek.from_date(when), when.isoweekday())


def week_weekday_to_date(week: CalendarWeek, weekday: int) -> date:
    return week[weekday - 1]
