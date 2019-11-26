import datetime
import os
from typing import List

from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import cache_page

from dashboard.caches import SUBS_VIEW_CACHE, MY_PLAN_VIEW_CACHE, PLAN_VIEW_CACHE
from schoolapps.settings import BASE_DIR
from schoolapps.settings import SHORT_WEEK_DAYS, LONG_WEEK_DAYS
from timetable.filters import HintFilter
from timetable.forms import HintForm
from timetable.hints import get_all_hints_by_time_period, get_all_hints_by_class_and_time_period, \
    get_all_hints_for_teachers_by_time_period, get_all_hints_not_for_teachers_by_time_period
from timetable.pdf import generate_class_tex_header, generate_class_tex_body, generate_pdf
from untisconnect.api import *
from untisconnect.datetimeutils import get_calendar_week, get_calendar_weeks, get_next_weekday, find_out_what_is_today, \
    get_next_weekday_with_time
from untisconnect.events import get_all_events_by_date
from untisconnect.plan import get_plan, parse_lesson_times
from untisconnect.sub import SubRow
from untisconnect.sub import get_substitutions_by_date, generate_sub_table, get_header_information
from untisconnect.utils import get_type_and_object_of_user, overview_dict
from .models import Hint


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
    context = overview_dict()
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
    context = overview_dict()
    return render(request, 'timetable/quicklaunch.html', context)


#########
# PLANS #
#########

@login_required
@permission_required("timetable.show_plan")
@cache_page(PLAN_VIEW_CACHE.expiration_time)
def plan(request, plan_type, plan_id, regular="", year=None, calendar_week=None):
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
    if year is None or calendar_week is None:
        date = get_next_weekday_with_time(timezone.datetime.now(), timezone.datetime.now().time())
        year = date.year
        calendar_week = date.isocalendar()[1]

    # Regular or smart plan?
    if regular == "regular":
        smart = False
    else:
        smart = True

    # Get monday and friday of week
    monday = get_calendar_week(calendar_week, year)["first_day"]
    friday = monday + datetime.timedelta(days=4)

    # Init hints
    hints = None
    hints_b = None

    if plan_type == 'teacher':
        # Teacher
        _type = TYPE_TEACHER
        el = get_teacher_by_id(plan_id)

        # Get hints
        if smart:
            hints = list(get_all_hints_for_teachers_by_time_period(monday, friday))
            hints_b = list(get_all_hints_not_for_teachers_by_time_period(monday, friday))

    elif plan_type == 'class':
        # Class
        _type = TYPE_CLASS
        el = get_class_by_id(plan_id)

        # Get hints
        if smart:
            hints = list(get_all_hints_by_class_and_time_period(el, monday, friday))

    elif plan_type == 'room':
        # Room
        _type = TYPE_ROOM
        el = get_room_by_id(plan_id)
    else:
        raise Http404('Plan not found.')

    # Get plan
    plan, holidays = get_plan(_type, plan_id, smart=smart, monday_of_week=monday)

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
        "short_week_days": zip(SHORT_WEEK_DAYS, holidays) if smart else zip(SHORT_WEEK_DAYS),
        "long_week_days": zip(LONG_WEEK_DAYS, holidays) if smart else zip(LONG_WEEK_DAYS),
        "holidays": holidays,
        "hints": hints,
        "hints_b": hints_b,
        "hints_b_mode": "week",
    }

    return render(request, 'timetable/plan.html', context)


@login_required
@permission_required("timetable.show_plan")
@cache_page(MY_PLAN_VIEW_CACHE.expiration_time)
def my_plan(request, year=None, month=None, day=None):
    date, time = find_out_what_is_today(year, month, day)

    # Get next weekday if it is a weekend
    next_weekday = get_next_weekday_with_time(date, time)
    if next_weekday != date:
        return redirect("timetable_my_plan", next_weekday.year, next_weekday.month, next_weekday.day)

    # Get calendar week and monday of week
    calendar_week = date.isocalendar()[1]
    monday_of_week = get_calendar_week(calendar_week, date.year)["first_day"]

    # Get user type (student, teacher, etc.)
    _type, el = get_type_and_object_of_user(request.user)
    if _type == TYPE_TEACHER:
        # Teacher
        plan_id = el.id
        raw_type = "teacher"

        # Get hints
        hints = list(get_all_hints_for_teachers_by_time_period(date, date))
        hints_b = list(get_all_hints_not_for_teachers_by_time_period(date, date))

    elif _type == TYPE_CLASS:
        # Student
        plan_id = el.id
        raw_type = "class"

        # Get hints
        hints = list(get_all_hints_by_class_and_time_period(el, date, date))
        hints_b = None

    else:
        # No student or teacher > no my plan
        return redirect("timetable_admin_all")

    # Get plan
    plan, holidays = get_plan(_type, plan_id, smart=True, monday_of_week=monday_of_week)
    # print(parse_lesson_times())

    holiday_for_the_day = holidays[date.isoweekday() - 1]
    # print(holiday_for_the_day)

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
        "holiday": holiday_for_the_day,
        "hints": hints,
        "hints_b": hints_b,
        "hints_b_mode": "day",
    }

    return render(request, 'timetable/myplan.html', context)


#################
# SUBSTITUTIONS #
#################

# TODO: Move to own helper file later
def equal(sub_row_1: SubRow, sub_row_2: SubRow) -> bool:
    """
    Checks the equality of two sub rows

    :param sub_row_1: SubRow 1
    :param sub_row_2: SubRow 2
    :return: Equality
    """
    return sub_row_1.classes == sub_row_2.classes and sub_row_1.sub and sub_row_2.sub and \
           sub_row_1.sub.teacher_old == sub_row_2.sub.teacher_old and \
           sub_row_1.sub.teacher_new == sub_row_2.sub.teacher_new and \
           sub_row_1.sub.subject_old == sub_row_2.sub.subject_old and \
           sub_row_1.sub.subject_new == sub_row_2.sub.subject_new and \
           sub_row_1.sub.room_old == sub_row_2.sub.room_old and \
           sub_row_1.sub.room_new == sub_row_2.sub.room_new and \
           sub_row_1.sub.text == sub_row_2.sub.text


def merge_sub_rows(sub_table: List[SubRow]) -> List[SubRow]:
    """
    Merge equal sub rows with different lesson numbers to one

    :param sub_table:
    :return:
    """
    new_sub_table = []
    i = 0
    while i < len(sub_table) - 1:
        j = 1

        while equal(sub_table[i], sub_table[i + j]):
            j += 1
            if i + j > len(sub_table) - 1:
                break
        if j > 1:
            new_sub_row = sub_table[i]
            new_sub_row.lesson = sub_table[i].lesson + '-' + sub_table[i + j - 1].lesson
            new_sub_table.append(new_sub_row)
        else:
            new_sub_table.append(sub_table[i])
            # get last item
            if i == len(sub_table) - 2:
                new_sub_table.append(sub_table[i + 1])
                break
        i += j
    return new_sub_table


def sub_pdf(request, plan_date=None):
    """Show substitutions as PDF for the next weekday (specially for monitors)"""

    if plan_date:
        splitted_date = [int(i) for i in plan_date.split("-")]
        today = timezone.datetime(year=splitted_date[0], month=splitted_date[1], day=splitted_date[2])
    else:
        today = timezone.datetime.now()

    # Get the next weekday
    # today = parse_datetime(date)
    print("Today is:", today)

    first_day = get_next_weekday_with_time(today, today.time())
    second_day = get_next_weekday(first_day + datetime.timedelta(days=1))

    tex = generate_class_tex_header()
    # Get subs and generate table
    for i, date in enumerate([first_day, second_day]):
        # Get subs and generate table
        events = get_all_events_by_date(date)
        subs = get_substitutions_by_date(date)

        sub_table = generate_sub_table(subs, events)
        sub_table = merge_sub_rows(sub_table)

        # Get header information and hints
        header_info = get_header_information(subs, date, events)
        hints = list(get_all_hints_by_time_period(date, date))

        # latex = convert_markdown_2_latex(hints[0].text)
        # print(latex)
        # Generate LaTeX
        tex += generate_class_tex_body(sub_table, date, header_info, hints)

    tex += "\end{document}"
    # Generate PDF
    generate_pdf(tex, "aktuell")

    # # Merge PDFs
    # try:
    #     merger = PdfFileMerger()
    #     class0 = open(os.path.join(BASE_DIR, "latex", "aktuell0.pdf"), "rb")
    #     class1 = open(os.path.join(BASE_DIR, "latex", "aktuell1.pdf"), "rb")
    #     merger.append(fileobj=class0)
    #     merger.append(fileobj=class1)
    #
    #     # Write merged PDF to aktuell.pdf
    #     output = open(os.path.join(BASE_DIR, "latex", "aktuell.pdf"), "wb")
    #     merger.write(output)
    #     output.close()
    #
    #     # Register successful merge in debugging tool
    #     register_return_0("merge_class", "pypdf2")
    # except Exception:
    #     # Register exception in debugging tool
    #     register_traceback("merge_class", "pypdf2")

    # Read and response PDF
    file = open(os.path.join(BASE_DIR, "latex", "aktuell.pdf"), "rb")
    return FileResponse(file, content_type="application/pdf")


@login_required
@permission_required("timetable.show_plan")
@cache_page(SUBS_VIEW_CACHE.expiration_time)
def substitutions(request, year=None, month=None, day=None):
    """Show substitutions in a classic view"""

    date, time = find_out_what_is_today(year, month, day)

    # Get next weekday if it is a weekend
    next_weekday = get_next_weekday_with_time(date, time)
    if next_weekday != date:
        return redirect("timetable_substitutions_date", next_weekday.year, next_weekday.month, next_weekday.day)

    # Get subs and generate table
    events = get_all_events_by_date(date)
    subs = get_substitutions_by_date(date)

    sub_table = generate_sub_table(subs, events)

    # Merge Subs
    sub_table = merge_sub_rows(sub_table)

    # Get header information and hints
    header_info = get_header_information(subs, date, events)
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
