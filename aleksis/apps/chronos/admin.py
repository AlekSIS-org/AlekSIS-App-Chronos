# noqa

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Absence,
    AbsenceReason,
    Break,
    Event,
    ExtraLesson,
    Holiday,
    Lesson,
    LessonPeriod,
    LessonSubstitution,
    Room,
    Subject,
    Supervision,
    SupervisionArea,
    SupervisionSubstitution,
    TimePeriod,
    TimetableWidget,
    ValidityRange,
)
from .util.format import format_date_period, format_m2m


def colour_badge(fg: str, bg: str, val: str):
    html = """
    <div style="
        color: {};
        background-color: {};
        padding-top: 3px;
        padding-bottom: 4px;
        text-align: center;
        border-radius: 3px;
    ">{}</span>
    """
    return format_html(html, fg, bg, val)


class AbsenceReasonAdmin(admin.ModelAdmin):
    list_display = ("short_name", "name")
    list_display_links = ("short_name", "name")


admin.site.register(AbsenceReason, AbsenceReasonAdmin)


class AbsenceAdmin(admin.ModelAdmin):
    def start(self, obj):
        return format_date_period(obj.date_start, obj.period_from)

    def end(self, obj):
        return format_date_period(obj.date_end, obj.period_to)

    list_display = ("__str__", "reason", "start", "end")


admin.site.register(Absence, AbsenceAdmin)


class SupervisionInline(admin.TabularInline):
    model = Supervision


class BreakAdmin(admin.ModelAdmin):
    list_display = ("__str__", "after_period", "before_period")
    inlines = [SupervisionInline]


admin.site.register(Break, BreakAdmin)


class EventAdmin(admin.ModelAdmin):
    def start(self, obj):
        return format_date_period(obj.date_start, obj.period_from)

    def end(self, obj):
        return format_date_period(obj.date_end, obj.period_to)

    def _groups(self, obj):
        return format_m2m(obj.groups)

    def _teachers(self, obj):
        return format_m2m(obj.teachers)

    def _rooms(self, obj):
        return format_m2m(obj.rooms)

    filter_horizontal = ("groups", "teachers", "rooms")
    list_display = ("__str__", "_groups", "_teachers", "_rooms", "start", "end")


admin.site.register(Event, EventAdmin)


class ExtraLessonAdmin(admin.ModelAdmin):
    def _groups(self, obj):
        return format_m2m(obj.groups)

    def _teachers(self, obj):
        return format_m2m(obj.teachers)

    list_display = ("week", "period", "subject", "_groups", "_teachers", "room")


admin.site.register(ExtraLesson, ExtraLessonAdmin)


class HolidayAdmin(admin.ModelAdmin):
    list_display = ("title", "date_start", "date_end")


admin.site.register(Holiday, HolidayAdmin)


class LessonPeriodInline(admin.TabularInline):
    model = LessonPeriod


class LessonSubstitutionAdmin(admin.ModelAdmin):
    list_display = ("lesson_period", "week", "date")
    list_display_links = ("lesson_period", "week", "date")
    filter_horizontal = ("teachers",)


admin.site.register(LessonSubstitution, LessonSubstitutionAdmin)


class LessonAdmin(admin.ModelAdmin):
    def _groups(self, obj):
        return format_m2m(obj.groups)

    def _teachers(self, obj):
        return format_m2m(obj.teachers)

    filter_horizontal = ["teachers", "groups"]
    inlines = [LessonPeriodInline]
    list_filter = ("subject", "groups", "groups__parent_groups", "teachers")
    list_display = ("_groups", "subject", "_teachers")


admin.site.register(Lesson, LessonAdmin)


class RoomAdmin(admin.ModelAdmin):
    list_display = ("short_name", "name")
    list_display_links = ("short_name", "name")


admin.site.register(Room, RoomAdmin)


class SubjectAdmin(admin.ModelAdmin):
    def _colour(self, obj):
        return colour_badge(obj.colour_fg, obj.colour_bg, obj.short_name,)

    list_display = ("short_name", "name", "_colour")
    list_display_links = ("short_name", "name")


admin.site.register(Subject, SubjectAdmin)


class SupervisionAreaAdmin(admin.ModelAdmin):
    def _colour(self, obj):
        return colour_badge(obj.colour_fg, obj.colour_bg, obj.short_name,)

    list_display = ("short_name", "name", "_colour")
    list_display_links = ("short_name", "name")
    inlines = [SupervisionInline]


admin.site.register(SupervisionArea, SupervisionAreaAdmin)


class SupervisionSubstitutionAdmin(admin.ModelAdmin):
    list_display = ("supervision", "date")


admin.site.register(SupervisionSubstitution, SupervisionSubstitutionAdmin)


class SupervisionAdmin(admin.ModelAdmin):
    list_display = ("break_item", "area", "teacher")


admin.site.register(Supervision, SupervisionAdmin)


class TimePeriodAdmin(admin.ModelAdmin):
    list_display = ("weekday", "period", "time_start", "time_end")
    list_display_links = ("weekday", "period")


admin.site.register(TimePeriod, TimePeriodAdmin)


class TimetableWidgetAdmin(admin.ModelAdmin):
    list_display = ("title", "active")


admin.site.register(TimetableWidget, TimetableWidgetAdmin)


class ValidityRangeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "date_start", "date_end")
    list_display_links = ("__str__", "date_start", "date_end")


admin.site.register(ValidityRange, ValidityRangeAdmin)
