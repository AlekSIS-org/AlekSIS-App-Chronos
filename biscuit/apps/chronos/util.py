from datetime import date, datetime, timedelta
from typing import Optional, Sequence

from django.apps import apps
from django.db import models


def current_week() -> int:
    return int(datetime.now().strftime('%V'))


def week_days(week: Optional[int]) -> Sequence[date]:
    # FIXME Make this aware of the school term concept
    # cf. BiscuIT-ng#40

    year = date.today().year
    wanted_week = week or current_week()

    first_day = datetime.strptime('%d-%d-1' % (year, wanted_week), '%G-%V-%u')

    return [(first_day + timedelta(days=offset)).date() for offset in range(0, 7)]


def current_lesson_periods(when: Optional[datetime] = None) -> models.query.QuerySet:
    now = when or datetime.now()

    LessonPeriod = apps.get_model('chronos.LessonPeriod')
    return LessonPeriod.objects.filter(lesson__date_start__lte=now.date(),
                                       lesson__date_end__gte=now.date(),
                                       period__weekday=now.isoweekday(),
                                       period__time_start__lte=now.time(),
                                       period__time_end__gte=now.time())


def week_weekday_from_date(when: date) -> Sequence[int, int]:
    return (int(when.strftime('%V')), int(when.strftime('%u')))
