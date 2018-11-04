import datetime
import os

from django.contrib.auth.decorators import login_required
from django.http import Http404, FileResponse
from django.shortcuts import render

from timetable.pdf import generate_class_tex, generate_pdf
from untisconnect.parse import *
from untisconnect.sub import get_substitutions_by_date, date_to_untis_date, untis_date_to_date, generate_sub_table
from django.utils import timezone

try:
    from schoolapps.untisconnect.api import *
except Exception:
    pass


def get_all_context():
    teachers = get_all_teachers()
    classes = get_all_classes()
    rooms = get_all_rooms()
    subjects = get_all_subjects()
    context = {
        'teachers': teachers,
        'classes': classes,
        'rooms': rooms,
        'subjects': subjects
    }
    return context


@login_required
def all(request):
    context = get_all_context()
    return render(request, 'timetable/all.html', context)


@login_required
def quicklaunch(request):
    context = get_all_context()
    return render(request, 'timetable/quicklaunch.html', context)


@login_required
def plan(request, plan_type, plan_id):
    if plan_type == 'teacher':
        _type = TYPE_TEACHER
        el = get_teacher_by_id(plan_id)
    elif plan_type == 'class':
        _type = TYPE_CLASS
        el = get_class_by_id(plan_id)
    elif plan_type == 'room':
        _type = TYPE_ROOM
        el = get_room_by_id(plan_id)
    else:
        raise Http404('Page not found.')

    plan = get_plan(_type, plan_id)

    context = {
        "type": _type,
        "plan": plan,
        "el": el
    }

    return render(request, 'timetable/plan.html', context)


def get_next_weekday(date):
    """Get the next weekday by a datetime object"""

    if date.isoweekday() in {6, 7}:
        if date.isoweekday() == 6:
            plus = 2
        else:
            plus = 1
        date += datetime.timedelta(days=plus)
    return date


@login_required
def sub_pdf(request):
    """Show substitutions as PDF for the next weekday (specially for monitors)"""

    # Get the next weekday
    today = timezone.datetime.now()
    first_day = get_next_weekday(today)

    # Get subs and generate table
    subs = get_substitutions_by_date(first_day)
    sub_table = generate_sub_table(subs)

    # Generate LaTeX
    tex = generate_class_tex(sub_table, first_day)

    # Generate PDF
    generate_pdf(tex, "class")

    # Read and response PDF
    file = open(os.path.join("latex", "class.pdf"), "rb")
    return FileResponse(file, content_type="application/pdf")


@login_required
def substitutions(request, year=None, day=None, month=None):
    """Show substitutions in a classic view"""

    date = timezone.datetime.now()
    if year is not None and day is not None and month is not None:
        date = timezone.datetime(year=year, month=month, day=day)

    # Get subs and generate table
    subs = get_substitutions_by_date(date)
    sub_table = generate_sub_table(subs)

    context = {
        "subs": subs,
        "sub_table": sub_table,
        "date": date,
        "date_js": int(date.timestamp()) * 1000
    }

    return render(request, 'timetable/substitution.html', context)
