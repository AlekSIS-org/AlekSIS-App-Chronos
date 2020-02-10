from datetime import datetime
from collections import OrderedDict

from django.forms.widgets import Media
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_global_request.middleware import get_request

from aleksis.apps.chronos.models import TimePeriod
from aleksis.apps.chronos.util.date import get_name_for_day_from_today
from aleksis.apps.chronos.util.prev_next import get_next_relevant_day
from aleksis.core.models import DashboardWidget
from aleksis.core.util.core_helpers import has_person


class TimetableWidget(DashboardWidget):
    template = "chronos/widget.html"

    def get_context(self):
        request = get_request()
        context = {"has_plan": True}
        wanted_day = get_next_relevant_day(timezone.now().date(), datetime.now().time())

        if has_person(request.user):
            person = request.user.person

            if person.is_teacher:
                # Teacher

                type_ = "teacher"
                lesson_periods_person = person.lesson_periods_as_teacher

            elif person.primary_group:
                # Student

                type_ = "group"
                lesson_periods_person = person.lesson_periods_as_participant

            else:
                # If no student or teacher, redirect to all timetables
                context["has_plan"] = False

        lesson_periods = lesson_periods_person.on_day(wanted_day)

        # Build dictionary with lessons
        per_period = {}
        for lesson_period in lesson_periods:
            if lesson_period.period.period in per_period:
                per_period[lesson_period.period.period].append(lesson_period)
            else:
                per_period[lesson_period.period.period] = [lesson_period]

        context["lesson_periods"] = OrderedDict(sorted(per_period.items()))
        context["type"] = type_
        context["day"] = wanted_day
        context["day_label"] = get_name_for_day_from_today(wanted_day)
        context["periods"] = TimePeriod.get_times_dict()
        context["smart"] = True
        return context

    media = Media(css={
        "all": ("css/chronos/timetable.css",)
    })

    class Meta:
        proxy = True
        verbose_name = _("Timetable widget")
