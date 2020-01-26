from django import forms
from django_select2.forms import ModelSelect2MultipleWidget

from .models import LessonSubstitution


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
