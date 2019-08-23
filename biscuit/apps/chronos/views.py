from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _

from biscuit.core.decorators import admin_required
from biscuit.core.models import Group, Person

from .models import LessonPeriod, TimePeriod, Room
from .util import current_week


@login_required
@admin_required
def timetable(request: HttpRequest) -> HttpResponse:
    context = {}

    lesson_periods = LessonPeriod.objects.all()
    filter_descs = []

    if 'group' in request.GET:
        lesson_periods = lesson_periods.filter(
            lesson__groups__pk=int(request.GET['group']))
        filter_descs.append(_('Group: %s') % Group.objects.get(
            pk=int(request.GET['group'])))
    elif 'teacher' in request.GET:
        lesson_periods = lesson_periods.filter(
            lesson__teachers__pk=int(request.GET['teacher']))
        filter_descs.append(_('Teacher: %s') % Person.objects.get(
            pk=int(request.GET['teacher'])))
    elif 'room' in request.GET:
        lesson_periods = lesson_periods.filter(
            room__pk=int(request.GET['room']))
        filter_descs.append(_('Room: %s') % Room.objects.get(
            pk=int(request.GET['room'])))
    else:
        if request.user.person:
            if request.user.person.primary_group:
                return redirect(reverse('timetable') + '?group=%d' % request.user.person.primary_group.pk)
            elif lesson_periods.filter(lesson__teachers=request.user.person).exists():
                return redirect(reverse('timetable') + '?teacher=%d' % request.user.person.pk)

    # Regroup lesson periods per weekday
    per_day = {}
    for lesson_period in lesson_periods:
        per_day.setdefault(lesson_period.period.weekday,
                           {})[lesson_period.period.period] = lesson_period

    # Determine overall first and last day and period
    min_max = TimePeriod.objects..aggregate(
        Min('period'), Max('period'),
        Min('weekday'), Max('weekday'))

    # Fill in empty lessons
    for weekday_num in range(min_max.get('weekday__min', 0),
                             min_max.get('weekday__max', 6) + 1):
        # Fill in empty weekdays
        if weekday_num not in per_day.keys():
            per_day[weekday_num] = {}

        # Fill in empty lessons on this workday
        for period_num in range(min_max.get('period__min', 1),
                                min_max.get('period__max', 7) + 1):
            if period_num not in per_day[weekday_num].keys():
                per_day[weekday_num][period_num] = None

        # Order this weekday by periods
        per_day[weekday_num] = OrderedDict(
            sorted(per_day[weekday_num].items()))

    context['lesson_periods'] = OrderedDict(sorted(per_day.items()))
    context['filter_descs'] = ', '.join(filter_descs)
    context['periods'] = TimePeriod.get_times_dict()
    context['weekdays'] = dict(TimePeriod.WEEKDAY_CHOICES)
    context['current_week'] = current_week()

    return render(request, 'chronos/tt_week.html', context)
