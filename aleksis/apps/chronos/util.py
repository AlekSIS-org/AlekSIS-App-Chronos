from datetime import date
from typing import Tuple, List

from calendarweek import CalendarWeek


def week_weekday_from_date(when: date) -> Tuple[CalendarWeek, int]:
    return (CalendarWeek.from_date(when), when.isoweekday())


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
