from django import forms
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

from biscuit.core.models import Person, Group

from .models import Room, LessonSubstitution, Subject, LessonPeriod


class SelectForm(forms.Form):
    group = forms.ModelChoiceField(
        queryset=Group.objects.annotate(lessons_count=Count('lessons')).filter(lessons_count__gt=0),
        label=_('Group'), required=False)
    teacher = forms.ModelChoiceField(
        queryset=Person.objects.annotate(lessons_count=Count('lessons')).filter(lessons_count__gt=0),
        label=_('Teacher'), required=False)
    room = forms.ModelChoiceField(
        queryset=Room.objects.annotate(lessons_count=Count('lesson_periods')).filter(lessons_count__gt=0),
        label=_('Room'), required=False)

class LessonSubstitutionForm(forms.ModelForm):
    class Meta:
        model = LessonSubstitution
        fields = ['week', 'lesson_period', 'subject', 'teachers', 'room']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lesson_period'].queryset = LessonPeriod.objects.all()
        self.fields['subject'].queryset = Subject.objects.all()
        self.fields['teachers'].queryset = Person.objects.all()
        self.fields['room'].queryset = Room.objects.all()
