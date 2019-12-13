from django import forms
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

from django_select2.forms import ModelSelect2MultipleWidget, Select2Widget

from biscuit.core.models import Group, Person

from .models import LessonPeriod, LessonSubstitution, Room, Subject


class SelectForm(forms.Form):
    group = forms.ModelChoiceField(
        queryset=Group.objects.annotate(lessons_count=Count("lessons")).filter(lessons_count__gt=0),
        label=_("Group"),
        required=False,
        widget=Select2Widget,
    )
    teacher = forms.ModelChoiceField(
        queryset=Person.objects.annotate(lessons_count=Count("lessons_as_teacher")).filter(
            lessons_count__gt=0
        ),
        label=_("Teacher"),
        required=False,
        widget=Select2Widget,
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.annotate(lessons_count=Count("lesson_periods")).filter(
            lessons_count__gt=0
        ),
        label=_("Room"),
        required=False,
        widget=Select2Widget,
    )


class LessonSubstitutionForm(forms.ModelForm):
    class Meta:
        model = LessonSubstitution
        fields = ["week", "lesson_period", "subject", "teachers", "room", "cancelled"]
        widgets = {
            "teachers": ModelSelect2MultipleWidget(
                search_fields=[
                    "first_name__icontains",
                    "last_name__icontains",
                    "short_name__icontains",
                ]
            )
        }
