from datetime import date, timedelta, datetime
from typing import Union, Optional, OrderedDict

from aleksis.apps.chronos.util.date import week_weekday_from_date
from calendarweek import CalendarWeek
from django.db import models
from django.db.models import F, Q, Count
from django.http import QueryDict

from aleksis.core.models import Person, Group


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

    def filter_room(self, room: Union["Room", int]):
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

    def group_by_periods(self, is_person: bool = False) -> dict:
        per_period = {}
        for obj in self:
            period = obj.period.period
            weekday = obj.period.weekday

            if period not in per_period:
                per_period[period] = [] if is_person else {}

            if not is_person and weekday not in per_period[period]:
                per_period[period][weekday] = []

            if is_person:
                per_period[period].append(obj)
            else:
                per_period[period][weekday].append(obj)

        return per_period


class LessonPeriodQuerySet(LessonDataQuerySet):
    _period_path = ""
    _subst_path = "substitutions__"

    def next(self, reference: "LessonPeriod", offset: Optional[int] = 1) -> "LessonPeriod":
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

    def filter_from_type(self, type_: TimetableType, pk: int) -> Optional[models.QuerySet]:
        if type_ == TimetableType.GROUP:
            return self.filter_group(pk)
        elif type_ == TimetableType.TEACHER:
            return self.filter_teacher(pk)
        elif type_ == TimetableType.ROOM:
            return self.filter_room(pk)
        else:
            return None

    def filter_from_person(self, person: Person) -> Optional[models.QuerySet]:
        type_ = person.timetable_type

        if type_ == TimetableType.TEACHER:
            # Teacher

            return self.filter_teacher(person)

        elif type_ == TimetableType.GROUP:
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
        from .models import Lesson # noaq

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


class AbsenceQuerySet(DateRangeQuerySet):
    def absent_teachers(self):
        return Person.objects.filter(absences__in=self).annotate(absences_count=Count("absences"))

    def absent_groups(self):
        return Group.objects.filter(absences__in=self).annotate(absences_count=Count("absences"))

    def absent_rooms(self):
        return Person.objects.filter(absences__in=self).annotate(absences_count=Count("absences"))


class HolidayQuerySet(DateRangeQuerySet):
    pass

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

    def filter_from_type(self, type_: TimetableType, pk: int) -> Optional[models.QuerySet]:
        if type_ == TimetableType.GROUP:
            return self.filter_group(pk)
        elif type_ == TimetableType.TEACHER:
            return self.filter_teacher(pk)
        elif type_ == TimetableType.ROOM:
            return self.filter_room(pk)
        else:
            return None

    def filter_from_person(self, person: Person) -> Optional[models.QuerySet]:
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


class EventQuerySet(DateRangeQuerySet, TimetableQuerySet):
    def annotate_day(self, day: date):
        """ Annotate all events in the QuerySet with the provided date. """

        return self.annotate(_date=models.Value(day, models.DateField()))


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


class GroupPropertiesMixin:
    @property
    def group_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([group.short_name for group in self.groups.all()])

    @property
    def groups_to_show(self) -> models.QuerySet:
        groups = self.groups.all()
        if groups.count() == 1 and groups[0].parent_groups.all() and get_site_preferences()["chronos__use_parent_groups"]:
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
