from collections import OrderedDict
from datetime import date, timedelta

from typing import Optional
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django_tables2 import RequestConfig

from biscuit.core.decorators import admin_required
from biscuit.core.models import Group, Person

from .forms import SelectForm
from .models import LessonPeriod, TimePeriod, Room
from .util import current_week, week_weekday_from_date
from .tables import LessonsTable


@login_required
def timetable(request: HttpRequest) -> HttpResponse:
    context = {}

    lesson_periods = LessonPeriod.objects.all()

    if request.GET.get('group', None) or request.GET.get('teacher', None) or request.GET.get('room', None):
        # Incrementally filter lesson periods by GET parameters
        if 'group' in request.GET and request.GET['group']:
            lesson_periods = lesson_periods.filter(
                lesson__groups__pk=int(request.GET['group']))
        if 'teacher' in request.GET and request.GET['teacher']:
            lesson_periods = lesson_periods.filter(
                lesson__teachers__pk=int(request.GET['teacher']))
        if 'room' in request.GET and request.GET['room']:
            lesson_periods = lesson_periods.filter(
                room__pk=int(request.GET['room']))
    else:
        # Redirect to a selected view if no filter provided
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
    min_max = TimePeriod.objects.aggregate(
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

    # Add a form to filter the view
    select_form = SelectForm(request.GET or None)

    context['lesson_periods'] = OrderedDict(sorted(per_day.items()))
    context['periods'] = TimePeriod.get_times_dict()
    context['weekdays'] = dict(TimePeriod.WEEKDAY_CHOICES)
    context['current_week'] = current_week()
    context['select_form'] = select_form

    return render(request, 'chronos/tt_week.html', context)


@login_required
def lessons_day(request: HttpRequest, when: Optional[str] = None) -> HttpResponse:
    context = {}

    if when:
        day = datetime.strptime(when, '%Y-%m-%d').date()
    else:
        day = date.today()

    week, weekday = week_weekday_from_date(day)

    # Get lessons
    lesson_periods = LessonPeriod.objects.filter(
        lesson__date_start__lte=day, lesson__date_end__gte=day,
        period__weekday=weekday
    ).all()

    # Build table
    lessons_table = LessonsTable(lesson_periods)
    RequestConfig(request).configure(lessons_table)

    context['lessons_table'] = lessons_table
    context['day'] = day
    context['day_prev'] = day + timedelta(days=-1)
    context['day_next'] = day + timedelta(days=1)
    context['week'] = week
    context['lesson_periods'] = lesson_periods

    return render(request, 'chronos/lessons_day.html', context)
