from datetime import date
from typing import Tuple, List, Union

from calendarweek import CalendarWeek
from calendarweek.django import i18n_day_names
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def week_weekday_from_date(when: date) -> Tuple[CalendarWeek, int]:
    return (CalendarWeek.from_date(when), when.weekday())


def week_weekday_to_date(week: CalendarWeek, weekday: int) -> date:
    return week[weekday - 1]


def week_period_to_date(week: Union[CalendarWeek, int], period) -> date:
    return period.get_date(week)


def get_weeks_for_year(year: int) -> List[CalendarWeek]:
    """ Generates all weeks for one year """
    weeks = []

    # Go for all weeks in year and create week list
    current_week = CalendarWeek(year=year, week=1)

    while current_week.year == year:
        weeks.append(current_week)
        current_week += 1

    return weeks
