from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from untisconnect.api import get_all_teachers

# Create your views here.
@login_required
def admin_teachers(request):
    teachers = get_all_teachers()
    context = {
        "teachers": teachers
    }
    return render(request, "timetable/admin/teachers.html", context)
