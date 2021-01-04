from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional, Union

from django.contrib.sites.managers import CurrentSiteManager as _CurrentSiteManager
from django.db import models
from django.db.models import Count, F, Q, QuerySet

from calendarweek import CalendarWeek

from aleksis.apps.chronos.util.date import week_weekday_from_date
from aleksis.core.managers import DateRangeQuerySetMixin, SchoolTermRelatedQuerySet
from aleksis.core.models import Group, Person
from aleksis.core.util.core_helpers import get_site_preferences


class ValidityRangeQuerySet(QuerySet, DateRangeQuerySetMixin):
    """Custom query set for validity ranges."""


class ValidityRangeRelatedQuerySet(QuerySet):
    """Custom query set for all models related to validity ranges."""

    def within_dates(self, start: date, end: date) -> "ValidityRangeRelatedQuerySet":
        """Filter for all objects within a date range."""
        return self.filter(validity__date_start__lte=end, validity__date_end__gte=start)

    def in_week(self, wanted_week: CalendarWeek) -> "ValidityRangeRelatedQuerySet":
        """Filter for all objects within a calendar week."""
        return self.within_dates(wanted_week[0], wanted_week[6])

    def on_day(self, day: date) -> "ValidityRangeRelatedQuerySet":
        """Filter for all objects on a certain day."""
        return self.within_dates(day, day)

    def for_validity_range(self, validity_range: "ValidityRange") -> "ValidityRangeRelatedQuerySet":
        return self.filter(validity=validity_range)

    def for_current_or_all(self) -> "ValidityRangeRelatedQuerySet":
        """Get all objects related to current validity range.

        If there is no current validity range, it will return all objects.
        """
        from aleksis.apps.chronos.models import ValidityRange

        current_validity_range = ValidityRange.current
        if current_validity_range:
            return self.for_validity_range(current_validity_range)
        else:
            return self

    def for_current_or_none(self) -> Union["ValidityRangeRelatedQuerySet", None]:
        """Get all objects related to current validity range.

        If there is no current validity range, it will return `None`.
        """
        from aleksis.apps.chronos.models import ValidityRange

        current_validity_range = ValidityRange.current
        if current_validity_range:
            return self.for_validity_range(current_validity_range)
        else:
            return None


class CurrentSiteManager(_CurrentSiteManager):
    use_in_migrations = False


class TimetableType(Enum):
    """Enum for different types of timetables."""

    GROUP = "group"
    TEACHER = "teacher"
    ROOM = "room"

    @classmethod
    def from_string(cls, s: Optional[str]):
        return cls.__members__.get(s.upper())


class LessonPeriodManager(CurrentSiteManager):
    """Manager adding specific methods to lesson periods."""

    def get_queryset(self):
        """Ensure all related lesson data is loaded as well."""
        return (
            super()
            .get_queryset()
            .select_related(
                "lesson",
                "lesson__subject",
                "period",
                "room",
                "lesson__validity",
                "lesson__validity__school_term",
            )
            .prefetch_related("lesson__groups", "lesson__teachers", "substitutions")
        )


class LessonSubstitutionManager(CurrentSiteManager):
    """Manager adding specific methods to lesson substitutions."""

    def get_queryset(self):
        """Ensure all related lesson data is loaded as well."""
        return (
            super()
            .get_queryset()
            .select_related(
                "lesson_period",
                "lesson_period__lesson",
                "lesson_period__lesson__subject",
                "subject",
                "lesson_period__period",
                "room",
                "lesson_period__room",
            )
            .prefetch_related(
                "lesson_period__lesson__groups",
                "lesson_period__lesson__groups__parent_groups",
                "teachers",
                "lesson_period__lesson__teachers",
            )
        )


class SupervisionManager(CurrentSiteManager):
    """Manager adding specific methods to supervisions."""

    def get_queryset(self):
        """Ensure all related data is loaded as well."""
        return (
            super()
            .get_queryset()
            .select_related(
                "teacher",
                "area",
                "break_item",
                "break_item__after_period",
                "break_item__before_period",
            )
        )


class SupervisionSubstitutionManager(CurrentSiteManager):
    """Manager adding specific methods to supervision substitutions."""

    def get_queryset(self):
        """Ensure all related data is loaded as well."""
        return (
            super()
            .get_queryset()
            .select_related(
                "teacher",
                "supervision",
                "supervision__teacher",
                "supervision__area",
                "supervision__break_item",
                "supervision__break_item__after_period",
                "supervision__break_item__before_period",
            )
        )


class EventManager(CurrentSiteManager):
    """Manager adding specific methods to events."""

    def get_queryset(self):
        """Ensure all related data is loaded as well."""
        return (
            super()
            .get_queryset()
            .select_related("period_from", "period_to")
            .prefetch_related(
                "groups", "groups__school_term", "groups__parent_groups", "teachers", "rooms",
            )
        )


class ExtraLessonManager(CurrentSiteManager):
    """Manager adding specific methods to extra lessons."""

    def get_queryset(self):
        """Ensure all related data is loaded as well."""
        return (
            super()
            .get_queryset()
            .select_related("room", "period", "subject")
            .prefetch_related("groups", "groups__school_term", "groups__parent_groups", "teachers",)
        )


class BreakManager(CurrentSiteManager):
    """Manager adding specific methods to breaks."""

    def get_queryset(self):
        """Ensure all related data is loaded as well."""
        return super().get_queryset().select_related("before_period", "after_period")


class WeekQuerySetMixin:
    def annotate_week(self, week: Union[CalendarWeek]):
        """Annotate all lessons in the QuerySet with the number of the provided calendar week."""
        return self.annotate(
            _week=models.Value(week.week, models.IntegerField()),
            _year=models.Value(week.year, models.IntegerField()),
        )


class GroupByPeriodsMixin:
    def group_by_periods(self, is_week: bool = False) -> dict:
        """Group a QuerySet of objects with attribute period by period numbers and weekdays."""
        per_period = {}
        for obj in self:
            period = obj.period.period
            weekday = obj.period.weekday

            if period not in per_period:
                per_period[period] = [] if not is_week else {}

            if is_week and weekday not in per_period[period]:
                per_period[period][weekday] = []

            if not is_week:
                per_period[period].append(obj)
            else:
                per_period[period][weekday].append(obj)

        return per_period


class LessonDataQuerySet(models.QuerySet, WeekQuerySetMixin):
    """Overrides default QuerySet to add specific methods for lesson data."""

    # Overridden in the subclasses. Swaps the paths to the base lesson period
    # and to any substitutions depending on whether the query is run on a
    # lesson period or a substitution
    _period_path = None
    _subst_path = None

    def within_dates(self, start: date, end: date):
        """Filter for all lessons within a date range."""
        return self.filter(
            **{
                self._period_path + "lesson__validity__date_start__lte": start,
                self._period_path + "lesson__validity__date_end__gte": end,
            }
        )

    def in_week(self, wanted_week: CalendarWeek):
        """Filter for all lessons within a calendar week."""
        return self.within_dates(
            wanted_week[0] + timedelta(days=1) * (F(self._period_path + "period__weekday")),
            wanted_week[0] + timedelta(days=1) * (F(self._period_path + "period__weekday")),
        ).annotate_week(wanted_week)

    def on_day(self, day: date):
        """Filter for all lessons on a certain day."""
        week, weekday = week_weekday_from_date(day)

        return (
            self.within_dates(day, day)
            .filter(**{self._period_path + "period__weekday": weekday})
            .annotate_week(week)
        )

    def at_time(self, when: Optional[datetime] = None):
        """Filter for the lessons taking place at a certain point in time."""
        now = when or datetime.now()
        week, weekday = week_weekday_from_date(now.date())

        return self.filter(
            **{
                self._period_path + "lesson__validity__date_start__lte": now.date(),
                self._period_path + "lesson__validity__date_end__gte": now.date(),
                self._period_path + "period__weekday": now.weekday(),
                self._period_path + "period__time_start__lte": now.time(),
                self._period_path + "period__time_end__gte": now.time(),
            }
        ).annotate_week(week)

    def filter_participant(self, person: Union[Person, int]):
        """Filter for all lessons a participant (student) attends."""
        return self.filter(Q(**{self._period_path + "lesson__groups__members": person}))

    def filter_group(self, group: Union[Group, int]):
        """Filter for all lessons a group (class) regularly attends."""
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
        """Filter for all lessons given by a certain teacher."""
        qs1 = self.filter(**{self._period_path + "lesson__teachers": teacher})
        qs2 = self.filter(
            **{
                self._subst_path + "teachers": teacher,
                self._subst_path + "week": F("_week"),
                self._subst_path + "year": F("_year"),
            }
        )

        return qs1.union(qs2)

    def filter_room(self, room: Union["Room", int]):
        """Filter for all lessons taking part in a certain room."""
        qs1 = self.filter(**{self._period_path + "room": room})
        qs2 = self.filter(
            **{
                self._subst_path + "room": room,
                self._subst_path + "week": F("_week"),
                self._subst_path + "year": F("_year"),
            }
        )

        return qs1.union(qs2)

    def filter_from_type(
        self, type_: TimetableType, obj: Union[Person, Group, "Room", int]
    ) -> Optional[models.QuerySet]:
        """Filter lesson data for a group, teacher or room by provided type."""
        if type_ == TimetableType.GROUP:
            return self.filter_group(obj)
        elif type_ == TimetableType.TEACHER:
            return self.filter_teacher(obj)
        elif type_ == TimetableType.ROOM:
            return self.filter_room(obj)
        else:
            return None

    def filter_from_person(self, person: Person) -> Optional[models.QuerySet]:
        """Filter lesson data for a person."""
        type_ = person.timetable_type

        if type_ == TimetableType.TEACHER:
            # Teacher

            return self.filter_teacher(person)

        elif type_ == TimetableType.GROUP:
            # Student

            return self.filter_participant(person)

        else:
            # If no student or teacher
            return None

    def daily_lessons_for_person(
        self, person: Person, wanted_day: date
    ) -> Optional[models.QuerySet]:
        """Filter lesson data on a day by a person."""
        if person.timetable_type is None:
            return None

        lesson_periods = self.on_day(wanted_day).filter_from_person(person)

        return lesson_periods

    def next_lesson(self, reference: "LessonPeriod", offset: Optional[int] = 1) -> "LessonPeriod":
        """Get another lesson in an ordered set of lessons.

        By default, it returns the next lesson in the set. By passing the offset argument,
        the n-th next lesson can be selected. By passing a negative number, the n-th
        previous lesson can be selected.
        """
        index = list(self.values_list("id", flat=True)).index(reference.id)

        next_index = index + offset
        if next_index > self.count() - 1:
            next_index %= self.count()
            week = reference._week + 1
        elif next_index < 0:
            next_index = self.count() + next_index
            week = reference._week - 1
        else:
            week = reference._week

        week = CalendarWeek(week=week, year=reference.lesson.get_year(week))

        return self.annotate_week(week).all()[next_index]


class LessonPeriodQuerySet(LessonDataQuerySet, GroupByPeriodsMixin):
    """QuerySet with custom query methods for lesson periods."""

    _period_path = ""
    _subst_path = "substitutions__"


class LessonSubstitutionQuerySet(LessonDataQuerySet):
    """QuerySet with custom query methods for substitutions."""

    _period_path = "lesson_period__"
    _subst_path = ""

    def within_dates(self, start: date, end: date):
        """Filter for all substitutions within a date range."""
        start_week = CalendarWeek.from_date(start)
        end_week = CalendarWeek.from_date(end)
        return self.filter(
            week__gte=start_week.week,
            week__lte=end_week.week,
            year__gte=start_week.year,
            year__lte=end_week.year,
        ).filter(
            Q(
                week=start_week.week,
                year=start_week.year,
                lesson_period__period__weekday__gte=start.weekday(),
            )
            | Q(
                week=end_week.week,
                year=end_week.year,
                lesson_period__period__weekday__lte=end.weekday(),
            )
            | (
                ~Q(week=start_week.week, year=start_week.year)
                & ~Q(week=end_week.week, year=end_week.year)
            )
        )

    def in_week(self, wanted_week: CalendarWeek):
        """Filter for all lessons within a calendar week."""
        return self.filter(week=wanted_week.week, year=wanted_week.year).annotate_week(wanted_week)

    def on_day(self, day: date):
        """Filter for all lessons on a certain day."""
        week, weekday = week_weekday_from_date(day)

        return self.in_week(week).filter(lesson_period__period__weekday=weekday)

    def at_time(self, when: Optional[datetime] = None):
        """Filter for the lessons taking place at a certain point in time."""
        now = when or datetime.now()

        return self.on_day(now.date()).filter(
            lesson_period__period__time_start__lte=now.time(),
            lesson_period__period__time_end__gte=now.time(),
        )

    def affected_lessons(self):
        """Return all lessons which are affected by selected substitutions."""
        from .models import Lesson  # noaq

        return Lesson.objects.filter(lesson_periods__substitutions__in=self)

    def affected_teachers(self):
        """Get affected teachers.

        Return all teachers which are affected by
        selected substitutions (as substituted or substituting).
        """
        return (
            Person.objects.filter(
                Q(lessons_as_teacher__in=self.affected_lessons()) | Q(lesson_substitutions__in=self)
            )
            .annotate(lessons_count=Count("lessons_as_teacher"))
            .order_by("short_name")
        )

    def affected_groups(self):
        """Return all groups which are affected by selected substitutions."""
        return (
            Group.objects.filter(lessons__in=self.affected_lessons())
            .annotate(lessons_count=Count("lessons"))
            .order_by("short_name")
        )


class DateRangeQuerySetMixin:
    """QuerySet with custom query methods for models with date and period ranges.

    Filterable fields: date_start, date_end, period_from, period_to
    """

    def within_dates(self, start: date, end: date):
        """Filter for all events within a date range."""
        return self.filter(date_start__lte=end, date_end__gte=start)

    def in_week(self, wanted_week: CalendarWeek):
        """Filter for all events within a calendar week."""
        return self.within_dates(wanted_week[0], wanted_week[6])

    def on_day(self, day: date):
        """Filter for all events on a certain day."""
        return self.within_dates(day, day)

    def at_time(self, when: Optional[datetime] = None):
        """Filter for the events taking place at a certain point in time."""
        now = when or datetime.now()

        return self.on_day(now.date()).filter(
            period_from__time_start__lte=now.time(), period_to__time_end__gte=now.time()
        )


class AbsenceQuerySet(DateRangeQuerySetMixin, SchoolTermRelatedQuerySet):
    """QuerySet with custom query methods for absences."""

    def absent_teachers(self):
        return (
            Person.objects.filter(absences__in=self)
            .annotate(absences_count=Count("absences"))
            .order_by("short_name")
        )

    def absent_groups(self):
        return (
            Group.objects.filter(absences__in=self)
            .annotate(absences_count=Count("absences"))
            .order_by("short_name")
        )

    def absent_rooms(self):
        return (
            Person.objects.filter(absences__in=self)
            .annotate(absences_count=Count("absences"))
            .order_by("short_name")
        )


class HolidayQuerySet(QuerySet, DateRangeQuerySetMixin):
    """QuerySet with custom query methods for holidays."""

    pass


class SupervisionQuerySet(ValidityRangeRelatedQuerySet, WeekQuerySetMixin):
    """QuerySet with custom query methods for supervisions."""

    def filter_by_weekday(self, weekday: int):
        """Filter supervisions by weekday."""
        return self.filter(
            Q(break_item__before_period__weekday=weekday)
            | Q(break_item__after_period__weekday=weekday)
        )

    def filter_by_teacher(self, teacher: Union[Person, int]):
        """Filter for all supervisions given by a certain teacher."""
        if self.count() > 0:
            if hasattr(self[0], "_week"):
                week = CalendarWeek(week=self[0]._week, year=self[0]._year)
            else:
                week = CalendarWeek.current_week()

            dates = [week[w] for w in range(0, 7)]

            return self.filter(
                Q(substitutions__teacher=teacher, substitutions__date__in=dates)
                | Q(teacher=teacher)
            )

        return self


class TimetableQuerySet(models.QuerySet):
    """Common query set methods for objects in timetables.

    Models need following fields:
    - groups
    - teachers
    - rooms (_multiple_rooms=True)/room (_multiple_rooms=False)
    """

    _multiple_rooms = True

    def filter_participant(self, person: Union[Person, int]):
        """Filter for all objects a participant (student) attends."""
        return self.filter(Q(groups__members=person))

    def filter_group(self, group: Union[Group, int]):
        """Filter for all objects a group (class) attends."""
        if isinstance(group, int):
            group = Group.objects.get(pk=group)

        if group.parent_groups.all():
            # Prevent to show lessons multiple times
            return self.filter(groups=group)
        else:
            return self.filter(Q(groups=group) | Q(groups__parent_groups=group))

    def filter_teacher(self, teacher: Union[Person, int]):
        """Filter for all lessons given by a certain teacher."""
        return self.filter(teachers=teacher)

    def filter_room(self, room: Union["Room", int]):
        """Filter for all objects taking part in a certain room."""
        if self._multiple_rooms:
            return self.filter(rooms=room)
        else:
            return self.filter(room=room)

    def filter_from_type(
        self, type_: TimetableType, obj: Union[Group, Person, "Room", int]
    ) -> Optional[models.QuerySet]:
        """Filter data for a group, teacher or room by provided type."""
        if type_ == TimetableType.GROUP:
            return self.filter_group(obj)
        elif type_ == TimetableType.TEACHER:
            return self.filter_teacher(obj)
        elif type_ == TimetableType.ROOM:
            return self.filter_room(obj)
        else:
            return None

    def filter_from_person(self, person: Person) -> Optional[models.QuerySet]:
        """Filter data by person."""
        type_ = person.timetable_type

        if type_ == TimetableType.TEACHER:
            # Teacher

            return self.filter_teacher(person)

        elif type_ == TimetableType.GROUP:
            # Student

            return self.filter_participant(person)

        else:
            # If no student or teacher
            return None


class EventQuerySet(DateRangeQuerySetMixin, SchoolTermRelatedQuerySet, TimetableQuerySet):
    """QuerySet with custom query methods for events."""

    def annotate_day(self, day: date):
        """Annotate all events in the QuerySet with the provided date."""
        return self.annotate(_date=models.Value(day, models.DateField()))


class ExtraLessonQuerySet(TimetableQuerySet, SchoolTermRelatedQuerySet, GroupByPeriodsMixin):
    """QuerySet with custom query methods for extra lessons."""

    _multiple_rooms = False

    def within_dates(self, start: date, end: date):
        """Filter all extra lessons within a specific time range."""
        week_start = CalendarWeek.from_date(start)
        week_end = CalendarWeek.from_date(end)

        return self.filter(
            week__gte=week_start.week,
            week__lte=week_end.week,
            year__gte=week_start.year,
            year__lte=week_end.year,
            period__weekday__gte=start.weekday(),
            period__weekday__lte=end.weekday(),
        )

    def on_day(self, day: date):
        """Filter all extra lessons on a day."""
        return self.within_dates(day, day)


class GroupPropertiesMixin:
    """Mixin for common group properties.

    Needed field: `groups`
    """

    @property
    def group_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([group.short_name for group in self.groups.all()])

    @property
    def groups_to_show(self) -> models.QuerySet:
        groups = self.groups.all()
        if (
            groups.count() == 1
            and groups[0].parent_groups.all()
            and get_site_preferences()["chronos__use_parent_groups"]
        ):
            return groups[0].parent_groups.all()
        else:
            return groups

    @property
    def groups_to_show_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([group.short_name for group in self.groups_to_show])


class TeacherPropertiesMixin:
    """Mixin for common teacher properties.

    Needed field: `teacher`
    """

    @property
    def teacher_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([teacher.full_name for teacher in self.teachers.all()])
