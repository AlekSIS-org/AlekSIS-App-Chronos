from django.contrib.auth.decorators import login_required

from biscuit.core.decorators import admin_required


@login_required
@admin_required
def timetable(request):
    pass
