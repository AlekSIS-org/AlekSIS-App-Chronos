import datetime
import os

from PyPDF2 import PdfFileMerger
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from schoolapps.settings import SHORT_WEEK_DAYS, LONG_WEEK_DAYS
from timetable.filters import HintFilter
from timetable.forms import HintForm
from timetable.hints import get_all_hints_by_time_period, get_all_hints_by_class_and_time_period, \
    get_all_hints_for_teachers_by_time_period, get_all_hints_not_for_teachers_by_time_period
from timetable.pdf import generate_class_tex, generate_pdf

from untisconnect.plan import get_plan, TYPE_TEACHER, TYPE_CLASS, TYPE_ROOM, parse_lesson_times
from untisconnect.sub import get_substitutions_by_date, generate_sub_table, get_header_information
from untisconnect.api import *
from userinformation import UserInformation

from schoolapps.settings import BASE_DIR

from .models import Hint


####################
# HELPER FUNCTIONS #
####################

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


def get_calendar_weeks(year=timezone.datetime.now().year):
    weeks = []

    # Get first day of year > first calendar week
    first_day_of_year = timezone.datetime(year=year, month=1, day=1)
    if first_day_of_year.isoweekday() != 1:
        days_to_next_monday = 1 - first_day_of_year.isoweekday()
        first_day_of_year += datetime.timedelta(days=days_to_next_monday)

    # Go for all weeks in year and create week dict
    first_day_of_week = first_day_of_year
    for i in range(52):
        calendar_week = i + 1
        last_day_of_week = first_day_of_week + datetime.timedelta(days=4)
        weeks.append({
            "calendar_week": calendar_week,
            "first_day": first_day_of_week,
            "last_day": last_day_of_week
        })
        first_day_of_week += datetime.timedelta(weeks=1)

    return weeks


def get_calendar_week(calendar_week, year=timezone.datetime.now().year):
    weeks = get_calendar_weeks(year=year)
    for week in weeks:
        if week["calendar_week"] == calendar_week:
            return week
    return None


def get_next_weekday(date):
    """Get the next weekday by a datetime object"""

    if date.isoweekday() in {6, 7}:
        if date.isoweekday() == 6:
            plus = 2
        else:
            plus = 1
        date += datetime.timedelta(days=plus)
    return date


#############
# OVERVIEWS #
#############

@login_required
@permission_required("timetable.show_plan")
def all(request):
    """
    [DJANGO VIEW]
    Show all plans as collection
    :param request: Django request
    :return: rendered template
    """
    context = get_all_context()
    return render(request, 'timetable/all.html', context)


@login_required
@permission_required("timetable.show_plan")
def quicklaunch(request):
    """
    [DJANGO VIEW]
    Show all plans as buttons
    :param request: Django request
    :return: rendered template
    """
    context = get_all_context()
    return render(request, 'timetable/quicklaunch.html', context)


#########
# PLANS #
#########

@login_required
@permission_required("timetable.show_plan")
def plan(request, plan_type, plan_id, regular="", year=timezone.datetime.now().year,
         calendar_week=timezone.datetime.now().isocalendar()[1]):
    """
    [DJANGO VIEW]
    Show a timetable (class, teacher, room, smart/regular)
    :param request: Django requests
    :param plan_type: "teacher", "class" or "room"
    :param plan_id: UNTIS-ID of corresponding object
    :param regular: regular plan = True, smart plan = False
    :param year: year of plan (only for smart plan)
    :param calendar_week: calendar week in year (only for smart plan)
    :return:
    """

    # Regular or smart plan?
    if regular == "regular":
        smart = False
    else:
        smart = True

    # Get monday and friday of week
    monday_of_week = get_calendar_week(calendar_week, year)["first_day"]
    friday = monday_of_week + datetime.timedelta(days=4)

    # Init hints
    hints = None
    hints_b = None

    if plan_type == 'teacher':
        # Teacher
        _type = TYPE_TEACHER
        el = get_teacher_by_id(plan_id)

        # Get hints
        if smart:
            hints = list(get_all_hints_for_teachers_by_time_period(monday_of_week, friday))
            hints_b = list(get_all_hints_not_for_teachers_by_time_period(monday_of_week, friday))

    elif plan_type == 'class':
        # Class
        _type = TYPE_CLASS
        el = get_class_by_id(plan_id)

        # Get hints
        if smart:
            hints = list(get_all_hints_by_class_and_time_period(el, monday_of_week, friday))

    elif plan_type == 'room':
        # Room
        _type = TYPE_ROOM
        el = get_room_by_id(plan_id)
    else:
        raise Http404('Plan not found.')

    # Get plan
    plan = get_plan(_type, plan_id, smart=smart, monday_of_week=monday_of_week)

    context = {
        "smart": smart,
        "type": _type,
        "raw_type": plan_type,
        "id": plan_id,
        "plan": plan,
        "el": el,
        "times": parse_lesson_times(),
        "weeks": get_calendar_weeks(year=year),
        "selected_week": calendar_week,
        "selected_year": year,
        "short_week_days": SHORT_WEEK_DAYS,
        "long_week_days": LONG_WEEK_DAYS,
        "hints": hints,
        "hints_b": hints_b,
        "hints_b_mode": "week",
    }

    return render(request, 'timetable/plan.html', context)


@login_required
@permission_required("timetable.show_plan")
def my_plan(request, year=None, month=None, day=None):
    date = timezone.datetime.now()
    if year is not None and day is not None and month is not None:
        date = timezone.datetime(year=year, month=month, day=day)

    # Get next weekday if it is a weekend
    next_weekday = get_next_weekday(date)
    if next_weekday != date:
        return redirect("timetable_my_plan", next_weekday.year, next_weekday.month, next_weekday.day)

    # Get calendar week and monday of week
    calendar_week = date.isocalendar()[1]
    monday_of_week = get_calendar_week(calendar_week, date.year)["first_day"]

    # Get user type (student, teacher, etc.)
    _type = UserInformation.user_type(request.user)

    if _type == UserInformation.TEACHER:
        # Teacher
        _type = TYPE_TEACHER
        shortcode = request.user.username
        el = get_teacher_by_shortcode(shortcode)
        plan_id = el.id
        raw_type = "teacher"

        # Get hints
        hints = list(get_all_hints_for_teachers_by_time_period(date, date))
        hints_b = list(get_all_hints_not_for_teachers_by_time_period(date, date))

    elif _type == UserInformation.STUDENT:
        # Student
        _type = TYPE_CLASS
        _name = UserInformation.user_classes(request.user)[0]
        el = get_class_by_name(_name)
        plan_id = el.id
        raw_type = "class"

        # Get hints
        hints = list(get_all_hints_by_class_and_time_period(el, date, date))
        hints_b = None

    else:
        # No student or teacher > no my plan
        return redirect("timetable_admin_all")

    # Get plan
    plan = get_plan(_type, plan_id, smart=True, monday_of_week=monday_of_week)

    context = {
        "type": _type,
        "raw_type": raw_type,
        "id": plan_id,
        "plan": plan,
        "el": el,
        "times": parse_lesson_times(),
        "week_day": date.isoweekday() - 1,
        "date": date,
        "date_js": int(date.timestamp()) * 1000,
        "display_date_only": True,
        "hints": hints,
        "hints_b": hints_b,
        "hints_b_mode": "day",
    }

    return render(request, 'timetable/myplan.html', context)


#################
# SUBSTITUTIONS #
#################

def sub_pdf(request):
    """Show substitutions as PDF for the next weekday (specially for monitors)"""

    # Get the next weekday
    today = timezone.datetime.now()

    first_day = get_next_weekday(today)
    second_day = get_next_weekday(first_day + datetime.timedelta(days=1))

    # Get subs and generate table
    for i, date in enumerate([first_day, second_day]):
        # Get subs and generate table
        subs = get_substitutions_by_date(date)
        sub_table = generate_sub_table(subs)
        header_info = get_header_information(subs, date)
        hints = list(get_all_hints_by_time_period(date, date))

        # latex = convert_markdown_2_latex(hints[0].text)
        # print(latex)
        # Generate LaTeX
        tex = generate_class_tex(sub_table, date, header_info, hints)

        # Generate PDF
        generate_pdf(tex, "class{}".format(i))

    # Merge PDFs
    merger = PdfFileMerger()
    class0 = open(os.path.join(BASE_DIR, "latex", "class0.pdf"), "rb")
    class1 = open(os.path.join(BASE_DIR, "latex", "class1.pdf"), "rb")
    merger.append(fileobj=class0)
    merger.append(fileobj=class1)

    # Write merged PDF to class.pdf
    output = open(os.path.join(BASE_DIR, "latex", "class.pdf"), "wb")
    merger.write(output)
    output.close()

    # Read and response PDF
    file = open(os.path.join(BASE_DIR, "latex", "class.pdf"), "rb")
    return FileResponse(file, content_type="application/pdf")


@login_required
@permission_required("timetable.show_plan")
def substitutions(request, year=None, month=None, day=None):
    """Show substitutions in a classic view"""

    date = timezone.datetime.now()
    if year is not None and day is not None and month is not None:
        date = timezone.datetime(year=year, month=month, day=day)

    # Get next weekday if it is a weekend
    next_weekday = get_next_weekday(date)
    if next_weekday != date:
        return redirect("timetable_substitutions_date", next_weekday.year, next_weekday.month, next_weekday.day)

    # Get subs and generate table
    subs = get_substitutions_by_date(date)
    sub_table = generate_sub_table(subs)

    # Get header information and hints
    header_info = get_header_information(subs, date)
    hints = list(get_all_hints_by_time_period(date, date))

    context = {
        "subs": subs,
        "sub_table": sub_table,
        "date": date,
        "date_js": int(date.timestamp()) * 1000,
        "header_info": header_info,
        "hints": hints,
    }

    return render(request, 'timetable/substitution.html', context)


###################
# HINT MANAGEMENT #
###################

@login_required
@permission_required("timetable.can_view_hint")
def hints(request):
    f = HintFilter(request.GET, queryset=Hint.objects.all())
    msg = None
    if request.session.get("msg", False):
        msg = request.session["msg"]
        request.session["msg"] = None
    return render(request, "timetable/hints.html", {"f": f, "msg": msg})


@login_required
@permission_required('timetable.can_add_hint')
def add_hint(request):
    msg = None
    if request.method == 'POST':
        form = HintForm(request.POST)

        if form.is_valid():
            i = form.save()
            i.save()
            # return redirect('timetable_add_hint')
            form = HintForm()
            msg = "success"
    else:
        form = HintForm()

    return render(request, 'timetable/hintform.html', {'form': form, "martor": True, "msg": msg, "mode": "new"})


@login_required
@permission_required("timetable.can_edit_hint")
def edit_hint(request, id):
    hint = get_object_or_404(Hint, pk=id)
    if request.method == 'POST':
        form = HintForm(request.POST, instance=hint)

        if form.is_valid():
            i = form.save()
            i.save()
            request.session["msg"] = "success_edit"
            return redirect('timetable_hints')
    else:
        form = HintForm(instance=hint)

    return render(request, 'timetable/hintform.html', {'form': form, "martor": True, "mode": "edit"})


@login_required
@permission_required("timetable.can_delete_hint")
def delete_hint(request, id):
    hint = get_object_or_404(Hint, pk=id)
    hint.delete()
    request.session["msg"] = "success_delete"
    return redirect('timetable_hints')
