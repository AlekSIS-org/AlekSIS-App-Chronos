from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from untisconnect.api import *
from .parse import *

try:
    from schoolapps.untisconnect.api import *
except Exception:
    pass


# Create your views here.
@login_required
def admin_all(request):
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
    return render(request, 'timetable/all.html', context)


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
