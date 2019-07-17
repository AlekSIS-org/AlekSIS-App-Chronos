from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from biscuit.core.decorators import admin_required

@login_required
@admin_required
def timetable(request):
    context = {}

    return render(request, 'chronos/tt_week.html')
