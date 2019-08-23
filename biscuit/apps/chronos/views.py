from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _

from biscuit.core.decorators import admin_required
from biscuit.core.models import Group, Person

from .forms import SelectForm
from .models import LessonPeriod, TimePeriod, Room
from .util import current_week


@login_required
@admin_required
def timetable(request: HttpRequest) -> HttpResponse:
    context = {}

    if request.GET:
        lesson_periods = LessonPeriod.objects.all()

        # Incrementally filter lesson periods by GET parameters
        if 'group' in request.GET:
            lesson_periods = lesson_periods.filter(
                lesson__groups__pk=int(request.GET['group']))
        if 'teacher' in request.GET:
            lesson_periods = lesson_periods.filter(
                lesson__teachers__pk=int(request.GET['teacher']))
        if 'room' in request.GET:
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

    # Add a form to filter the view
    select_form = SelectForm(request.GET or None)

    context['lesson_periods'] = OrderedDict(sorted(per_day.items()))
    context['periods'] = TimePeriod.get_times_dict()
    context['weekdays'] = dict(TimePeriod.WEEKDAY_CHOICES)
    context['current_week'] = current_week()
    context['select_form'] = select_form

    return render(request, 'chronos/tt_week.html', context)
