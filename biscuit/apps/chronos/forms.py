from django import forms
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

from biscuit.core.models import Person, Group

from .models import Room


class SelectForm(forms.Form):
    group = forms.ModelChoiceField(
        queryset=Group.objects.annotate(lessons_count=Count('lessons')).filter(lessons_count__gt=0),
        label=_('Group'))
    teacher = forms.ModelChoiceField(
        queryset=Person.objects.annotate(lessons_count=Count('lessons')).filter(lessons_count__gt=0),
        label=_('Teacher'))
    room = forms.ModelChoiceField(
        queryset=Room.objects.annotate(lessons_count=Count('lesson_periods')).filter(lessons_count__gt=0),
        label=_('Room'))
