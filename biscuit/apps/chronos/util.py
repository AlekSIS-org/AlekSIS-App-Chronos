from datetime import datetime
from typing import Optional

from django.apps import apps
from django.db import models


def current_week() -> int:
    return int(datetime.now().strftime('%V'))


def current_lesson_periods(when: Optional[datetime] = None) -> models.query.QuerySet:
    now = when or datetime.now()

    LessonPeriod = apps.get_model('chronos.LessonPeriod')
    return LessonPeriod.objects.filter(lesson__date_start__lte=now.date(),
                                       lesson__date_end__gte=now.date(),
                                       period__weekday=now.isoweekday(),
                                       period__time_start__lte=now.time(),
                                       period__time_end__gte=now.time())
