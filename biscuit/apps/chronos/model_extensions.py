from biscuit.core.models import Person

from .models import Lesson, LessonPeriod


@Person.property
def lessons_as_participant(self):
    return Lesson.objects.filter(groups__members=self)


@Person.property
def lesson_periods_as_participant(self):
    return LessonPeriod.objects.filter(lesson__groups__members=self)


@Person.property
def lesson_periods_as_teacher(self):
    return LessonPeriod.objects.filter(lesson__teachers=self)
