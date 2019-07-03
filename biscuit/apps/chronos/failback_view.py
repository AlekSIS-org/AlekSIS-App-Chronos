from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def failback(request, *args, **kwargs):
    return render(request, "timetable/failback.html")
