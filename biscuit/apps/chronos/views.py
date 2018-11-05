import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from schoolapps.settings import LESSONS
from untisconnect.parse import *

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
@permission_required("timetable.show_plan")
def all(request):
    context = get_all_context()
    return render(request, 'timetable/all.html', context)


@login_required
@permission_required("timetable.show_plan")
def quicklaunch(request):
    context = get_all_context()
    return render(request, 'timetable/quicklaunch.html', context)


@login_required
@permission_required("timetable.show_plan")
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
    print(parse_lesson_times())

    context = {
        "type": _type,
        "plan": plan,
        "el": el,
        "times": parse_lesson_times()
    }

    return render(request, 'timetable/plan.html', context)


@login_required
@permission_required("timetable.show_plan")
def substitutions(request):
    return render(request, 'timetable/substitution.html')
