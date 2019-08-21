from datetime import datetime

from .models import LessonPeriod


def current_week():
    return int(datetime.now().strftime('%V'))


def current_lesson_periods(when=None):
    now = when or datetime.now()

    return LessonPeriod.objects.filter(lesson__date_start__lte=now.date(),
                                       lesson__date_end__gte=now.date(),
                                       period__weekday=now.isoweekday(),
                                       period__time_start__lte=now.time(),
                                       period__time_end__gte=now.time())
