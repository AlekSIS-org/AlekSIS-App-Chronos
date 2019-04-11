from datetime import date

from django.db import models
from django.db.models import ManyToManyField
from martor.models import MartorField

from untisconnect.api import get_class_by_id, get_all_classes
from untisconnect.models import Class

classes = get_all_classes()
class_choices = [(x.id, x.name) for x in classes]


class HintClass(models.Model):
    class_id = models.IntegerField(choices=class_choices)

    def __str__(self):
        try:
            _class = get_class_by_id(self.class_id)
            return _class.name
        except Exception:
            return "Unbekannte Klasse"


for x in classes:
    HintClass.objects.get_or_create(class_id=x.id)


class Hint(models.Model):
    # Time
    from_date = models.DateField(default=date.today, verbose_name="Startdatum")
    to_date = models.DateField(default=date.today, verbose_name="Enddatum")

    # Text
    text = MartorField(verbose_name="Hinweistext")

    # Relations
    classes = models.ManyToManyField(HintClass, related_name="hints", verbose_name="Klassen")
    teachers = models.BooleanField(verbose_name="Lehrer?", default=False)

    class Meta:
        verbose_name = "Hinweis"
        verbose_name_plural = "Hinweise"


class Timetable(models.Model):
    class Meta:
        permissions = (
            ('show_plan', 'Show plan'),
        )
