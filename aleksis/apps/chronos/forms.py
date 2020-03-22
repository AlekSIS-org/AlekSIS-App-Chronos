from django import forms
from django_select2.forms import ModelSelect2MultipleWidget
from django.utils.translation import gettext_lazy as _
from material import Fieldset

from .models import LessonSubstitution
from aleksis.core.forms import AnnouncementForm


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


AnnouncementForm.add_node_to_layout(Fieldset(_("Options for timetables"), "show_in_timetables"))
