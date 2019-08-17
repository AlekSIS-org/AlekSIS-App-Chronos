from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from biscuit.core.decorators import admin_required
from biscuit.core.models import Group, Person

from .models import LessonPeriod, TimePeriod, Room


@login_required
@admin_required
def timetable(request):
    context = {}

    lesson_periods = LessonPeriod.objects.all()
    filter_descs = []

    if 'group' in request.GET:
        lesson_periods = lesson_periods.filter(
            lesson__groups__pk__contains=int(request.GET['group']))
        filter_descs.append(_('Group: %s') % Group.objects.get(
            pk=int(request.GET['group'])).name)
    if 'teacher' in request.GET:
        lesson_periods = lesson_periods.filter(
            lesson__teachers__pk__contains=int(request.GET['teacher']))
        filter_descs.append(_('Teacher: %s') % Person.objects.get(
            pk=int(request.GET['teacher'])).name)
    if 'room' in request.GET:
        lesson_periods = lesson_periods.filter(
            room__pk=int(request.GET['room']))
        filter_descs.append(_('Room: %s') % Room.objects.get(
            pk=int(request.GET['room'])).name)

    per_day = {}
    period_min, period_max = None, None
    for lesson_period in lesson_periods:
        per_day.setdefault(lesson_period.period.weekday,
                           {})[lesson_period.period.period] = lesson_period

        # Expand min and max lesson to later fill in empty lessons
        if period_min is None or period_min > lesson_period.period.period:
            period_min = lesson_period.period.period
        if period_max is None or period_max < lesson_period.period.period:
            period_max = lesson_period.period.period

    # Fill in empty lessons
    for weekday_num in range(min(per_day.keys()), max(per_day.keys()) + 1):
        # Fill in empty weekdays
        if weekday_num not in per_day.keys():
            per_day[weekday_num] = {}

        # Fill in empty lessons on this workday
        for period_num in range(period_min, period_max + 1):
            if period_num not in per_day[weekday_num].keys():
                per_day[weekday_num][period_num] = None

        # Order this weekday by periods
        per_day[weekday_num] = OrderedDict(
            sorted(per_day[weekday_num].items()))

    context['lesson_periods'] = OrderedDict(sorted(per_day.items()))
    context['filter_descs'] = ', '.join(filter_descs)
    context['periods'] = TimePeriod.get_times_dict()
    context['weekdays'] = dict(TimePeriod.WEEKDAY_CHOICES)

    return render(request, 'chronos/tt_week.html', context)
