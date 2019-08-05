import os
from datetime import date

from django.db import models, ProgrammingError
from django.utils import timezone
from martor.models import MartorField

from schoolapps.settings import BASE_DIR
from timetable.m2l import convert_markdown_2_latex

from untisconnect.models import Terms

try:
    from untisconnect.api import get_all_classes, format_classes
    from untisconnect.models import Class

    classes = get_all_classes()
    class_choices = [(x.id, x.name) for x in classes]
except Terms.DoesNotExist:
    classes = []
    class_choices = []


class HintClass(models.Model):
    """Maps a UNTIS class to a usable format for Django models"""
    class_id = models.IntegerField(choices=class_choices)
    name = models.CharField(max_length=100, default="…")

    def __str__(self):
        return self.name


# Map all classes from UNTIS to HintClass objects
try:
    for x in classes:
        obj, _ = HintClass.objects.get_or_create(class_id=x.id)
        obj.name = x.name
        obj.save()
except ProgrammingError:
    pass


class Hint(models.Model):
    # Time
    from_date = models.DateField(default=date.today, verbose_name="Startdatum")
    to_date = models.DateField(default=date.today, verbose_name="Enddatum")

    # Text
    text = MartorField(verbose_name="Hinweistext")

    # Relations
    classes = models.ManyToManyField(HintClass, related_name="hints", verbose_name="Klassen", blank=True)
    teachers = models.BooleanField(verbose_name="Lehrer?", default=False, blank=True)

    # Caching
    text_as_latex = models.TextField(verbose_name="LaTeX (automatisch)", blank=True)
    classes_formatted = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Hinweis"
        verbose_name_plural = "Hinweise"

    def __init__(self, *args, **kwargs):
        super(Hint, self).__init__(*args, **kwargs)

    def __str__(self):
        targets = self.classes_formatted
        if self.teachers and targets != "":
            targets += ", Lehrkräfte"
        elif self.teachers:
            targets = "Lehrkräfte"

        return "[{}]: {}–{}".format(targets, self.from_date, self.to_date)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # Convert LaTeX already when saving as cache because then is no need to do it later > performance savings
        self.text_as_latex = convert_markdown_2_latex(self.text)

        super(Hint, self).save(force_insert=force_insert, force_update=force_update, using=using,
                               update_fields=update_fields)

        # Format classes already > cache, too
        self.classes_formatted = format_classes(self.classes.all())

        super(Hint, self).save(force_insert=force_insert, force_update=force_update, using=using,
                               update_fields=update_fields)


class Timetable(models.Model):
    class Meta:
        permissions = (
            ('show_plan', 'Show plan'),
        )
