from django import forms
import dbsettings
from django.db import models

from untisconnect.api_helper import get_terms

choices = []
terms = get_terms()
for term in terms:
    choices.append((term.id, term.name))


class Timetable(models.Model):
    class Meta:
        permissions = (
            ('show_plan', 'Show plan'),
        )


class UNTISSettings(dbsettings.Group):
    term = dbsettings.IntegerValue(widget=forms.Select, choices=choices)


untis_settings = UNTISSettings()
