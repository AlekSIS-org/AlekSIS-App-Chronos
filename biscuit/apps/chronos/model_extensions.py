from biscuit.core.models import Person

from .models import Lesson


@Person.property
def lessons_as_participant(self):
    return Lesson.objects.filter(groups__members=self)
