from __future__ import annotations

from collections import OrderedDict
from datetime import date, datetime, timedelta, time
from typing import Dict, Optional, Tuple, Union

from constance import config
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Max, Min, Q
from django.db.models.aggregates import Count
from django.db.models.functions import Coalesce
from django.forms import Media
from django.http.request import QueryDict
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import classproperty
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from calendarweek.django import CalendarWeek, i18n_day_names_lazy, i18n_day_abbrs_lazy
from colorfield.fields import ColorField
from django_global_request.middleware import get_request

from aleksis.apps.chronos.util.format import format_m2m
from aleksis.core.mixins import ExtensibleModel
from aleksis.core.models import Group, Person, DashboardWidget

from aleksis.apps.chronos.util.date import week_weekday_from_date
from aleksis.core.util.core_helpers import has_person


class LessonPeriodManager(models.Manager):
    """ Manager adding specific methods to lesson periods. """

    def get_queryset(self):
        """ Ensures all related lesson data is loaded as well. """

        return (
            super()
            .get_queryset()
            .select_related("lesson", "lesson__subject", "period", "room")
            .prefetch_related("lesson__groups", "lesson__teachers", "substitutions")
        )


class LessonSubstitutionManager(models.Manager):
    """ Manager adding specific methods to lesson substitutions. """

    def get_queryset(self):
        """ Ensures all related lesson data is loaded as well. """

        return (
            super()
            .get_queryset()
            .select_related(
                "lesson_period",
                "lesson_period__lesson",
                "subject",
                "lesson_period__period",
                "room",
            )
            .prefetch_related("lesson_period__lesson__groups", "teachers")
        )


class LessonDataQuerySet(models.QuerySet):
    """ Overrides default QuerySet to add specific methods for lesson data. """

    # Overridden in the subclasses. Swaps the paths to the base lesson period
    # and to any substitutions depending on whether the query is run on a
    # lesson period or a substitution
    _period_path = None
    _subst_path = None

    def within_dates(self, start: date, end: date):
        """ Filter for all lessons within a date range. """

        return self.filter(
            **{
                self._period_path + "lesson__date_start__lte": start,
                self._period_path + "lesson__date_end__gte": end,
            }
        )

    def in_week(self, wanted_week: CalendarWeek):
        """ Filter for all lessons within a calendar week. """

        return self.within_dates(
            wanted_week[0] + timedelta(days=1) * (F(self._period_path + "period__weekday") - 1),
            wanted_week[0] + timedelta(days=1) * (F(self._period_path + "period__weekday") - 1),
        ).annotate_week(wanted_week)

    def on_day(self, day: date):
        """ Filter for all lessons on a certain day. """

        week, weekday = week_weekday_from_date(day)

        return (
            self.within_dates(day, day)
            .filter(**{self._period_path + "period__weekday": weekday})
            .annotate_week(week)
        )

    def at_time(self, when: Optional[datetime] = None):
        """ Filter for the lessons taking place at a certain point in time. """

        now = when or datetime.now()
        week, weekday = week_weekday_from_date(now.date())

        return self.filter(
            **{
                self._period_path + "lesson__date_start__lte": now.date(),
                self._period_path + "lesson__date_end__gte": now.date(),
                self._period_path + "period__weekday": now.weekday(),
                self._period_path + "period__time_start__lte": now.time(),
                self._period_path + "period__time_end__gte": now.time(),
            }
        ).annotate_week(week)

    def filter_participant(self, person: Union[Person, int]):
        """ Filter for all lessons a participant (student) attends. """

        return self.filter(
            Q(**{self._period_path + "lesson__groups__members": person})
            | Q(**{self._period_path + "lesson__groups__parent_groups__members": person})
        )

    def filter_group(self, group: Union[Group, int]):
        """ Filter for all lessons a group (class) regularly attends. """

        if isinstance(group, int):
            group = Group.objects.get(pk=group)

        if group.parent_groups.all():
            # Prevent to show lessons multiple times
            return self.filter(Q(**{self._period_path + "lesson__groups": group}))
        else:
            return self.filter(
                Q(**{self._period_path + "lesson__groups": group})
                | Q(**{self._period_path + "lesson__groups__parent_groups": group})
            )

    def filter_teacher(self, teacher: Union[Person, int]):
        """ Filter for all lessons given by a certain teacher. """

        qs1 = self.filter(**{self._period_path + "lesson__teachers": teacher})
        qs2 = self.filter(**{self._subst_path + "teachers": teacher, self._subst_path + "week": F("_week"), })

        return qs1.union(qs2)

    def filter_room(self, room: Union[Room, int]):
        """ Filter for all lessons taking part in a certain room. """

        qs1 = self.filter(**{self._period_path + "room": room})
        qs2 = self.filter(**{self._subst_path + "room": room, self._subst_path + "week": F("_week"),})

        return qs1.union(qs2)

    def annotate_week(self, week: Union[CalendarWeek, int]):
        """ Annotate all lessons in the QuerySet with the number of the provided calendar week. """

        if isinstance(week, CalendarWeek):
            week_num = week.week
        else:
            week_num = week

        return self.annotate(_week=models.Value(week_num, models.IntegerField()))


class LessonPeriodQuerySet(LessonDataQuerySet):
    _period_path = ""
    _subst_path = "substitutions__"

    def next(self, reference: LessonPeriod, offset: Optional[int] = 1) -> LessonPeriod:
        """ Get another lesson in an ordered set of lessons.

        By default, it returns the next lesson in the set. By passing the offset argument,
        the n-th next lesson can be selected. By passing a negative number, the n-th
        previous lesson can be selected.
        """

        index = list(self.values_list("id", flat=True)).index(reference.id)

        next_index = index + offset
        if next_index > self.count() - 1:
            next_index %= self.count()
            week = reference._week + 1
        else:
            week = reference._week

        return self.annotate_week(week).all()[next_index]

    def filter_from_query(self, query_data: QueryDict) -> models.QuerySet:
        """ Apply all filters from a GET or POST query.

        This method expects a QueryDict, like the GET or POST attribute of a Request
        object, that contains one or more of the keys group, teacher or room.

        All three fields are filtered, in order.
        """

        if query_data.get("group", None):
            return self.filter_group(int(query_data["group"]))
        if query_data.get("teacher", None):
            return self.filter_teacher(int(query_data["teacher"]))
        if query_data.get("room", None):
            return self.filter_room(int(query_data["room"]))

    def filter_from_type(self, type_: str, pk: int) -> Optional[models.QuerySet]:
        if type_ == "group":
            return self.filter_group(pk)
        elif type_ == "teacher":
            return self.filter_teacher(pk)
        elif type_ == "room":
            return self.filter_room(pk)
        else:
            return None

    def filter_from_person(self, person: Person) -> Optional[models.QuerySet]:
        type_ = person.timetable_type

        if type_ == "teacher":
            # Teacher

            return self.filter_teacher(person)

        elif type_ == "group":
            # Student

            return self.filter(lesson__groups__members=person)

        else:
            # If no student or teacher
            return None

    def daily_lessons_for_person(self, person: Person, wanted_day: date) -> Optional[models.QuerySet]:
        if person.timetable_type is None:
            return None

        lesson_periods = self.on_day(wanted_day).filter_from_person(person)

        return lesson_periods

    def per_period_one_day(self) -> OrderedDict:
        """ Group selected lessons per period for one day """
        per_period = {}
        for lesson_period in self:
            if lesson_period.period.period in per_period:
                per_period[lesson_period.period.period].append(lesson_period)
            else:
                per_period[lesson_period.period.period] = [lesson_period]
        return OrderedDict(sorted(per_period.items()))


class LessonSubstitutionQuerySet(LessonDataQuerySet):
    _period_path = "lesson_period__"
    _subst_path = ""

    def affected_lessons(self):
        """ Return all lessons which are affected by selected substitutions """

        return Lesson.objects.filter(lesson_periods__substitutions__in=self)

    def affected_teachers(self):
        """ Return all teachers which are affected by selected substitutions (as substituted or substituting) """

        return Person.objects.filter(
            Q(lessons_as_teacher__in=self.affected_lessons())
            | Q(lesson_substitutions__in=self)
        ).annotate(lessons_count=Count("lessons_as_teacher"))

    def affected_groups(self):
        """ Return all groups which are affected by selected substitutions """

        return Group.objects.filter(lessons__in=self.affected_lessons()).annotate(
            lessons_count=Count("lessons")
        )


class TimePeriod(ExtensibleModel):
    WEEKDAY_CHOICES = list(enumerate(i18n_day_names_lazy()))
    WEEKDAY_CHOICES_SHORT = list(enumerate(i18n_day_abbrs_lazy()))

    weekday = models.PositiveSmallIntegerField(verbose_name=_("Week day"), choices=WEEKDAY_CHOICES)
    period = models.PositiveSmallIntegerField(verbose_name=_("Number of period"))

    time_start = models.TimeField(verbose_name=_("Time the period starts"))
    time_end = models.TimeField(verbose_name=_("Time the period ends"))

    def __str__(self) -> str:
        return "{}, {}.".format(
            self.get_weekday_display(),
            self.period,
        )

    @classmethod
    def get_times_dict(cls) -> Dict[int, Tuple[datetime, datetime]]:
        periods = {}
        for period in cls.objects.all():
            periods[period.period] = (period.time_start, period.time_end)

        return periods

    def get_date(self, week: Optional[Union[CalendarWeek, int]] = None) -> date:
        if isinstance(week, CalendarWeek):
            wanted_week = week
        else:
            year = date.today().year
            week_number = week or getattr(self, "_week", None) or CalendarWeek().week

            if week_number < self.school.current_term.date_start.isocalendar()[1]:
                year += 1

            wanted_week = CalendarWeek(year=year, week=week_number)

        return wanted_week[self.weekday]

    @classmethod
    def get_next_relevant_day(cls, day: Optional[date] = None, time: Optional[time] = None, prev: bool = False) -> date:
        """ Returns next (previous) day with lessons depending on date and time """

        if day is None:
            day = timezone.now().date()

        if time is not None and not prev:
            if time > cls.time_max:
                day += timedelta(days=1)

        cw = CalendarWeek.from_date(day)

        if day.weekday() > cls.weekday_max:
            if prev:
                day = cw[cls.weekday_max]
            else:
                cw += 1
                day = cw[cls.weekday_min]
        elif day.weekday() < TimePeriod.weekday_min:
            if prev:
                cw -= 1
                day = cw[cls.weekday_max]
            else:
                day = cw[cls.weekday_min]

        return day

    @classmethod
    def get_prev_next_by_day(cls, day: date, url: str) -> Tuple[str, str]:
        """ Build URLs for previous/next day """

        day_prev = cls.get_next_relevant_day(day - timedelta(days=1), prev=True)
        day_next = cls.get_next_relevant_day(day + timedelta(days=1))

        url_prev = reverse(url, args=[day_prev.year, day_prev.month, day_prev.day])
        url_next = reverse(url, args=[day_next.year, day_next.month, day_next.day])

        return url_prev, url_next

    @classproperty
    def period_min(cls) -> int:
        return cls.objects.aggregate(period__min=Coalesce(Min("period"), 1)).get("period__min")

    @classproperty
    def period_max(cls) -> int:
        return cls.objects.aggregate(period__max=Coalesce(Max("period"), 7)).get("period__max")

    @classproperty
    def time_min(cls) -> Optional[time]:
        return cls.objects.aggregate(Min("time_start")).get("time_start__min")

    @classproperty
    def time_max(cls) -> Optional[time]:
        return cls.objects.aggregate(Max("time_end")).get("time_end__max")

    @classproperty
    def weekday_min(cls) -> int:
        return cls.objects.aggregate(weekday__min=Coalesce(Min("weekday"), 0)).get("weekday__min")

    @classproperty
    def weekday_max(cls) -> int:
        return cls.objects.aggregate(weekday__max=Coalesce(Max("weekday"), 6)).get("weekday__max")

    class Meta:
        unique_together = [["weekday", "period"]]
        ordering = ["weekday", "period"]
        indexes = [models.Index(fields=["time_start", "time_end"])]
        verbose_name = _("Time period")
        verbose_name_plural = _("Time periods")


class Subject(ExtensibleModel):
    abbrev = models.CharField(
        verbose_name=_("Abbreviation of subject in timetable"), max_length=10, unique=True,
    )
    name = models.CharField(verbose_name=_("Long name of subject"), max_length=30, unique=True)

    colour_fg = models.CharField(
        verbose_name=_("Foreground colour in timetable"),
        blank=True,
        validators=[validators.RegexValidator(r"#[0-9A-F]{6}")],
        max_length=7,
    )
    colour_bg = models.CharField(
        verbose_name=_("Background colour in timetable"),
        blank=True,
        validators=[validators.RegexValidator(r"#[0-9A-F]{6}")],
        max_length=7,
    )

    def __str__(self) -> str:
        return "{} ({})".format(self.abbrev, self.name)

    class Meta:
        ordering = ["name", "abbrev"]


class Room(ExtensibleModel):
    short_name = models.CharField(
        verbose_name=_("Short name, e.g. room number"), max_length=10, unique=True
    )
    name = models.CharField(verbose_name=_("Long name"), max_length=30)

    def __str__(self) -> str:
        return "%s (%s)" % (self.name, self.short_name)

    class Meta:
        ordering = ["name", "short_name"]


class GroupPropertiesMixin:
    @property
    def group_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([group.short_name for group in self.groups.all()])

    @property
    def groups_to_show(self) -> models.QuerySet:
        groups = self.groups.all()
        if groups.count() == 1 and groups[0].parent_groups.all() and config.CHRONOS_USE_PARENT_GROUPS:
            return groups[0].parent_groups.all()
        else:
            return groups

    @property
    def groups_to_show_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([group.short_name for group in self.groups_to_show])


class TeacherPropertiesMixin:
    @property
    def teacher_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([teacher.full_name for teacher in self.teachers.all()])


class Lesson(ExtensibleModel, GroupPropertiesMixin, TeacherPropertiesMixin):
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE, related_name="lessons")
    teachers = models.ManyToManyField("core.Person", related_name="lessons_as_teacher")
    periods = models.ManyToManyField("TimePeriod", related_name="lessons", through="LessonPeriod")
    groups = models.ManyToManyField("core.Group", related_name="lessons")

    date_start = models.DateField(verbose_name=_("Effective start date of lesson"), null=True)
    date_end = models.DateField(verbose_name=_("Effective end date of lesson"), null=True)

    def get_calendar_week(self, week: int):
        year = self.date_start.year
        if week < int(self.date_start.strftime("%V")):
            year += 1

        return CalendarWeek(year=year, week=week)

    def __str__(self):
        return "{}, {}, {}".format(
            format_m2m(self.groups),
            self.subject.abbrev,
            format_m2m(self.teachers),
        )

    class Meta:
        ordering = ["date_start", "subject"]
        indexes = [models.Index(fields=["date_start", "date_end"])]
        verbose_name = _("Lesson")
        verbose_name_plural = _("Lessons")


class LessonSubstitution(ExtensibleModel):
    objects = LessonSubstitutionManager.from_queryset(LessonSubstitutionQuerySet)()

    week = models.IntegerField(verbose_name=_("Week"), default=CalendarWeek.current_week)

    lesson_period = models.ForeignKey("LessonPeriod", models.CASCADE, "substitutions")

    subject = models.ForeignKey(
        "Subject",
        on_delete=models.CASCADE,
        related_name="lesson_substitutions",
        null=True,
        blank=True,
        verbose_name=_("Subject"),
    )
    teachers = models.ManyToManyField(
        "core.Person", related_name="lesson_substitutions", blank=True
    )
    room = models.ForeignKey("Room", models.CASCADE, null=True, blank=True, verbose_name=_("Room"))

    cancelled = models.BooleanField(default=False, verbose_name=_("Cancelled?"))
    cancelled_for_teachers = models.BooleanField(default=False, verbose_name=_("Cancelled for teachers?"))

    comment = models.TextField(verbose_name=_("Comment"), blank=True, null=True)

    def clean(self) -> None:
        if self.subject and self.cancelled:
            raise ValidationError(_("Lessons can only be either substituted or cancelled."))

    @property
    def type_(self):
        if self.cancelled:
            return "cancellation"
        elif self.cancelled_for_teachers:
            return "cancellation_for_teachers"
        else:
            return "substitution"

    @property
    def date(self):
        week = CalendarWeek(week=self.week)
        return week[self.lesson_period.period.weekday]

    def __str__(self):
        return "{}, {}".format(str(self.lesson_period), date_format(self.date))

    class Meta:
        unique_together = [["lesson_period", "week"]]
        ordering = [
            "lesson_period__lesson__date_start",
            "week",
            "lesson_period__period__weekday",
            "lesson_period__period__period",
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(cancelled=True, subject__isnull=False),
                name="either_substituted_or_cancelled",
            )
        ]
        verbose_name = _("Lesson substitution")
        verbose_name_plural = _("Lesson substitutions")


class LessonPeriod(ExtensibleModel):
    label_ = "lesson_period"

    objects = LessonPeriodManager.from_queryset(LessonPeriodQuerySet)()

    lesson = models.ForeignKey("Lesson", models.CASCADE, related_name="lesson_periods")
    period = models.ForeignKey("TimePeriod", models.CASCADE, related_name="lesson_periods")

    room = models.ForeignKey("Room", models.CASCADE, null=True, related_name="lesson_periods")

    def get_substitution(self, week: Optional[int] = None) -> LessonSubstitution:
        wanted_week = week or getattr(self, "_week", None) or CalendarWeek().week

        # We iterate over all substitutions because this can make use of
        # prefetching when this model is loaded from outside, in contrast
        # to .filter()
        for substitution in self.substitutions.all():
            if substitution.week == wanted_week:
                return substitution
        return None

    def get_subject(self) -> Optional[Subject]:
        if self.get_substitution() and self.get_substitution().subject:
            return self.get_substitution().subject
        else:
            return self.lesson.subject

    def get_teachers(self) -> models.query.QuerySet:
        if self.get_substitution():
            return self.get_substitution().teachers
        else:
            return self.lesson.teachers

    def get_room(self) -> Optional[Room]:
        if self.get_substitution() and self.get_substitution().room:
            return self.get_substitution().room
        else:
            return self.room

    def get_teacher_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([teacher.full_name for teacher in self.get_teachers().all()])

    def get_groups(self) -> models.query.QuerySet:
        return self.lesson.groups

    def __str__(self) -> str:
        return "{}, {}".format(
            str(self.period),
            str(self.lesson)
        )

    class Meta:
        ordering = ["lesson__date_start", "period__weekday", "period__period", "lesson__subject"]
        indexes = [models.Index(fields=["lesson", "period"])]
        verbose_name = _("Lesson period")
        verbose_name_plural = _("Lesson periods")


class TimetableWidget(DashboardWidget):
    template = "chronos/widget.html"

    def get_context(self):
        from aleksis.apps.chronos.util.build import build_timetable # noqa

        request = get_request()
        context = {"has_plan": True}
        wanted_day = TimePeriod.get_next_relevant_day(timezone.now().date(), datetime.now().time())

        if has_person(request.user):
            person = request.user.person
            type_ = person.timetable_type

            # Build timetable
            timetable = build_timetable("person", person, wanted_day)

            if type_ is None:
                # If no student or teacher, redirect to all timetables
                context["has_plan"] = False
            else:
                context["timetable"] = timetable
                context["holiday"] = Holiday.on_day(wanted_day)
                context["type"] = type_
                context["day"] = wanted_day
                context["periods"] = TimePeriod.get_times_dict()
                context["smart"] = True
        else:
            context["has_plan"] = False

        return context

    media = Media(css={
        "all": ("css/chronos/timetable.css",)
    })

    class Meta:
        proxy = True
        verbose_name = _("Timetable widget")


class DateRangeQuerySet(models.QuerySet):
    def within_dates(self, start: date, end: date):
        """ Filter for all events within a date range. """

        return self.filter(date_start__lte=end, date_end__gte=start)

    def in_week(self, wanted_week: CalendarWeek):
        """ Filter for all events within a calendar week. """

        return self.within_dates(wanted_week[0], wanted_week[6])

    def on_day(self, day: date):
        """ Filter for all events on a certain day. """

        return self.within_dates(day, day)

    def at_time(self, when: Optional[datetime] = None):
        """ Filter for the events taking place at a certain point in time. """

        now = when or datetime.now()

        return self.on_day(now.date()).filter(
            period_from__time_start__lte=now.time(),
            period_to__time_end__gte=now.time()
        )


class AbsenceReason(ExtensibleModel):
    short_name = models.CharField(verbose_name=_("Short name"), max_length=255)
    name = models.CharField(verbose_name=_("Name"), blank=True, null=True, max_length=255)

    def __str__(self):
        if self.name:
            return "{} ({})".format(self.short_name, self.name)
        else:
            return self.short_name

    class Meta:
        verbose_name = _("Absence reason")
        verbose_name_plural = _("Absence reasons")


class AbsenceQuerySet(DateRangeQuerySet):
    def absent_teachers(self):
        return Person.objects.filter(absences__in=self).annotate(absences_count=Count("absences"))

    def absent_groups(self):
        return Group.objects.filter(absences__in=self).annotate(absences_count=Count("absences"))

    def absent_rooms(self):
        return Person.objects.filter(absences__in=self).annotate(absences_count=Count("absences"))


class Absence(ExtensibleModel):
    objects = models.Manager.from_queryset(AbsenceQuerySet)()

    reason = models.ForeignKey("AbsenceReason", on_delete=models.CASCADE, related_name="absences")

    teacher = models.ForeignKey("core.Person", on_delete=models.CASCADE, related_name="absences", null=True, blank=True)
    group = models.ForeignKey("core.Group", on_delete=models.CASCADE, related_name="absences", null=True, blank=True)
    room = models.ForeignKey("Room", on_delete=models.CASCADE, related_name="absences", null=True, blank=True)

    date_start = models.DateField(verbose_name=_("Effective start date of absence"), null=True)
    date_end = models.DateField(verbose_name=_("Effective end date of absence"), null=True)
    period_from = models.ForeignKey("TimePeriod", on_delete=models.CASCADE, verbose_name=_("Effective start period of absence"), null=True, related_name="+")
    period_to = models.ForeignKey("TimePeriod", on_delete=models.CASCADE, verbose_name=_("Effective end period of absence"), null=True, related_name="+")
    comment = models.TextField(verbose_name=_("Comment"), blank=True, null=True)

    def __str__(self):
        if self.teacher:
            return str(self.teacher)
        elif self.group:
            return str(self.group)
        elif self.room:
            return str(self.room)
        else:
            return _("Unknown absence")

    class Meta:
        ordering = ["date_start"]
        indexes = [models.Index(fields=["date_start", "date_end"])]
        verbose_name = _("Absence")
        verbose_name_plural = _("Absences")


class Exam(ExtensibleModel):
    lesson = models.ForeignKey("Lesson", on_delete=models.CASCADE, related_name="exams")

    date = models.DateField(verbose_name=_("Date of exam"), null=True)
    period_from = models.ForeignKey("TimePeriod", on_delete=models.CASCADE, verbose_name=_("Effective start period of exam"), null=True, related_name="+")
    period_to = models.ForeignKey("TimePeriod", on_delete=models.CASCADE, verbose_name=_("Effective end period of exam"), null=True, related_name="+")

    title = models.CharField(verbose_name=_("Title"), max_length=50)
    comment = models.TextField(verbose_name=_("Comment"), blank=True, null=True)

    class Meta:
        ordering = ["date"]
        indexes = [models.Index(fields=["date"])]
        verbose_name = _("Exam")
        verbose_name_plural = _("Exams")


class HolidayQuerySet(DateRangeQuerySet):
    pass


class Holiday(ExtensibleModel):
    objects = models.Manager.from_queryset(HolidayQuerySet)()

    title = models.CharField(verbose_name=_("Title of the holidays"), max_length=50)
    date_start = models.DateField(verbose_name=_("Effective start date of holidays"), null=True)
    date_end = models.DateField(verbose_name=_("Effective end date of holidays"), null=True)
    comments = models.TextField(verbose_name=_("Comments"), null=True, blank=True)

    @classmethod
    def on_day(cls, day: date) -> Optional["Holiday"]:
        holidays = cls.objects.on_day(day)
        if holidays.exists():
            return holidays[0]
        else:
            return None

    @classmethod
    def in_week(cls, week: CalendarWeek) -> Dict[int, Optional["Holiday"]]:
        per_weekday = {}

        for weekday in range(TimePeriod.weekday_min, TimePeriod.weekday_max + 1):
            holiday_date = week[weekday]
            holidays = Holiday.objects.on_day(holiday_date)
            if holidays.exists():
                per_weekday[weekday] = holidays[0]

        return per_weekday

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["date_start"]
        indexes = [models.Index(fields=["date_start", "date_end"])]
        verbose_name = _("Holiday")
        verbose_name_plural = _("Holidays")


class SupervisionArea(ExtensibleModel):
    short_name = models.CharField(verbose_name=_("Short name"), max_length=10)
    name = models.CharField(verbose_name=_("Long name"), max_length=50)
    colour_fg = ColorField(default="#000000")
    colour_bg = ColorField()

    def __str__(self):
        return "{} ({})".format(self.name, self.short_name)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Supervision area")
        verbose_name_plural = _("Supervision areas")


class Break(ExtensibleModel):
    short_name = models.CharField(verbose_name=_("Short name"), max_length=10)
    name = models.CharField(verbose_name=_("Long name"), max_length=50)

    after_period = models.ForeignKey("TimePeriod", on_delete=models.CASCADE,
                                    verbose_name=_("Effective start of break"),
                                    related_name="break_after", blank=True, null=True)
    before_period = models.ForeignKey("TimePeriod", on_delete=models.CASCADE,
                                  verbose_name=_("Effective end of break"),
                                  related_name="break_before", blank=True, null=True)

    @property
    def weekday(self):
        return (
            self.after_period.weekday
            if self.after_period
            else self.before_period.weekday
        )

    @property
    def after_period_number(self):
        return (
            self.after_period.period
            if self.after_period
            else self.before_period.period - 1
        )

    @property
    def before_period_number(self):
        return (
            self.before_period.period
            if self.before_period
            else self.after_period.period + 1
        )

    @property
    def time_start(self):
        return self.after_period.time_end if self.after_period else None

    @property
    def time_end(self):
        return self.before_period.time_start if self.before_period else None

    @classmethod
    def get_breaks_dict(cls) -> Dict[int, Tuple[datetime, datetime]]:
        breaks = {}
        for break_ in cls.objects.all():
            breaks[break_.before_period_number] = break_

        return breaks

    def __str__(self):
        return "{} ({})".format(self.name, self.short_name)

    class Meta:
        ordering = ["after_period"]
        indexes = [models.Index(fields=["after_period", "before_period"])]
        verbose_name = _("Break")
        verbose_name_plural = _("Breaks")


class SupervisionQuerySet(models.QuerySet):
    def annotate_week(self, week: Union[CalendarWeek, int]):
        """ Annotate all lessons in the QuerySet with the number of the provided calendar week. """

        if isinstance(week, CalendarWeek):
            week_num = week.week
        else:
            week_num = week

        return self.annotate(_week=models.Value(week_num, models.IntegerField()))

    def filter_by_weekday(self, weekday: int):
        self.filter(
            Q(break_item__before_period__weekday=weekday)
            | Q(break_item__after_period__weekday=weekday)
        )

    def filter_by_teacher(self, teacher: Union[Person, int]):
        """ Filter for all supervisions given by a certain teacher. """

        if self.count() > 0:
            if hasattr(self[0], "_week"):
                week = CalendarWeek(week=self[0]._week)
            else:
                week = CalendarWeek.current_week()

            dates = [week[w] for w in range(0, 7)]

            return self.filter(Q(substitutions__teacher=teacher, substitutions__date__in=dates) | Q(teacher=teacher))

        return self


class Supervision(ExtensibleModel):
    objects = models.Manager.from_queryset(SupervisionQuerySet)()

    area = models.ForeignKey(SupervisionArea, models.CASCADE, verbose_name=_("Supervision area"), related_name="supervisions")
    break_item = models.ForeignKey(Break, models.CASCADE, verbose_name=_("Break"), related_name="supervisions")
    teacher = models.ForeignKey("core.Person", models.CASCADE, related_name="supervisions", verbose_name=_("Teacher"))

    def get_substitution(
        self, week: Optional[int] = None
    ) -> Optional[SupervisionSubstitution]:
        wanted_week = week or getattr(self, "_week", None) or CalendarWeek().week
        wanted_week = CalendarWeek(week=wanted_week)
        # We iterate over all substitutions because this can make use of
        # prefetching when this model is loaded from outside, in contrast
        # to .filter()
        for substitution in self.substitutions.all():
            for weekday in range(0, 7):
                if substitution.date == wanted_week[weekday]:
                    return substitution
        return None

    @property
    def teachers(self):
        return [self.teacher]

    def __str__(self):
        return "{}, {}, {}".format(self.break_item, self.area, self.teacher)

    class Meta:
        ordering = ["area", "break_item"]
        verbose_name= _("Supervision")
        verbose_name_plural = _("Supervisions")


class SupervisionSubstitution(ExtensibleModel):
    date = models.DateField(verbose_name=_("Date"))
    supervision = models.ForeignKey(Supervision, models.CASCADE, verbose_name=_("Supervision"), related_name="substitutions")
    teacher = models.ForeignKey("core.Person", models.CASCADE, related_name="substituted_supervisions", verbose_name=_("Teacher"))

    @property
    def teachers(self):
        return [self.teacher]

    def __str__(self):
        return "{}, {}".format(self.supervision, date_format(self.date))

    class Meta:
        ordering = ["date", "supervision"]
        verbose_name = _("Supervision substitution")
        verbose_name_plural = _("Supervision substitutions")


class TimetableQuerySet(models.QuerySet):
    """ Common filters

     Models need following fields:
     - groups
     - teachers
     - rooms (_multiple_rooms=True)/room (_multiple_rooms=False)
     """

    _multiple_rooms = True

    def filter_participant(self, person: Union[Person, int]):
        """ Filter for all objects a participant (student) attends. """

        return self.filter(Q(groups_members=person))

    def filter_group(self, group: Union[Group, int]):
        """ Filter for all objects a group (class) attends. """

        if isinstance(group, int):
            group = Group.objects.get(pk=group)

        if group.parent_groups.all():
            # Prevent to show lessons multiple times
            return self.filter(groups=group)
        else:
            return self.filter(Q(groups=group) | Q(groups__parent_groups=group))

    def filter_teacher(self, teacher: Union[Person, int]):
        """ Filter for all lessons given by a certain teacher. """

        return self.filter(teachers=teacher)

    def filter_room(self, room: Union[Room, int]):
        """ Filter for all objects taking part in a certain room. """

        if self._multiple_rooms:
            return self.filter(rooms=room)
        else:
            return self.filter(room=room)

    def filter_from_type(self, type_: str, pk: int) -> Optional[models.QuerySet]:
        if type_ == "group":
            return self.filter_group(pk)
        elif type_ == "teacher":
            return self.filter_teacher(pk)
        elif type_ == "room":
            return self.filter_room(pk)
        else:
            return None

    def filter_from_person(self, person: Person) -> Optional[models.QuerySet]:
        type_ = person.timetable_type

        if type_ == "teacher":
            # Teacher

            return self.filter_teacher(person)

        elif type_ == "group":
            # Student

            return self.filter_participant(person)

        else:
            # If no student or teacher
            return None


class EventQuerySet(DateRangeQuerySet, TimetableQuerySet):
    def annotate_day(self, day: date):
        """ Annotate all events in the QuerySet with the provided date. """

        return self.annotate(_date=models.Value(day, models.DateField()))


class Event(ExtensibleModel, GroupPropertiesMixin, TeacherPropertiesMixin):
    label_ = "event"

    objects = models.Manager.from_queryset(EventQuerySet)()

    title = models.CharField(verbose_name=_("Title"), max_length=255, blank=True, null=True)

    date_start = models.DateField(verbose_name=_("Effective start date of event"), null=True)
    date_end = models.DateField(verbose_name=_("Effective end date of event"), null=True)

    period_from = models.ForeignKey("TimePeriod", on_delete=models.CASCADE, verbose_name=_("Effective start period of event"), related_name="+")
    period_to = models.ForeignKey("TimePeriod", on_delete=models.CASCADE, verbose_name=_("Effective end period of event"), related_name="+")

    groups = models.ManyToManyField("core.Group", related_name="events", verbose_name=_("Groups"))
    rooms = models.ManyToManyField("Room", related_name="events", verbose_name=_("Rooms"))
    teachers = models.ManyToManyField("core.Person", related_name="events", verbose_name=_("Teachers"))

    def __str__(self):
        if self.title:
            return self.title
        else:
            return _("Event {}".format(self.pk))

    @property
    def period_from_on_day(self) -> int:
        day = getattr(self, "_date", timezone.now().date())
        if day != self.date_start:
            return TimePeriod.period_min
        else:
            return self.period_from.period

    @property
    def period_to_on_day(self) -> int:
        day = getattr(self, "_date", timezone.now().date())
        if day != self.date_end:
            return TimePeriod.period_max
        else:
            return self.period_to.period

    class Meta:
        ordering = ["date_start"]
        indexes = [models.Index(fields=["period_from", "period_to", "date_start", "date_end"])]
        verbose_name = _("Event")
        verbose_name_plural = _("Events")


class ExtraLessonQuerySet(TimetableQuerySet):
    _multiple_rooms = False

    def within_dates(self, start: date, end: date):
        week_start = CalendarWeek.from_date(start)
        week_end = CalendarWeek.from_date(end)

        return self.filter(
            week__gte=week_start.week,
            week__lte=week_end.week,
            period__weekday__gte=start.weekday(),
            period__weekday__lte=end.weekday(),
        )

    def on_day(self, day:date):
        return self.within_dates(day, day)


class ExtraLesson(ExtensibleModel, GroupPropertiesMixin):
    label_ = "extra_lesson"

    objects = models.Manager.from_queryset(ExtraLessonQuerySet)()

    week = models.IntegerField(verbose_name=_("Week"), default=CalendarWeek.current_week)
    period = models.ForeignKey("TimePeriod", models.CASCADE, related_name="extra_lessons")

    subject = models.ForeignKey("Subject", on_delete=models.CASCADE, related_name="extra_lessons", verbose_name=_("Subject"))
    groups = models.ManyToManyField("core.Group", related_name="extra_lessons", verbose_name=_("Groups"))
    teachers = models.ManyToManyField("core.Person", related_name="extra_lessons_as_teacher", verbose_name=_("Teachers"))
    room = models.ForeignKey("Room", models.CASCADE, null=True, related_name="extra_lessons", verbose_name=_("Room"))

    comment = models.CharField(verbose_name=_("Comment"), blank=True, null=True, max_length=255)

    def __str__(self):
        return "{}, {}, {}".format(self.week, self.period, self.subject)

    class Meta:
        verbose_name = _("Extra lesson")
        verbose_name_plural = _("Extra lessons")
