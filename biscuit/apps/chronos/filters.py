import django_filters
from django.forms import Form
from material import Fieldset, Row

from .models import Hint


class HintForm(Form):
    layout = Row("from_date", "to_date", "classes", "teachers")


class HintFilter(django_filters.FilterSet):
    class Meta:
        model = Hint
        fields = ['from_date', "to_date", "classes", "teachers"]
        form = HintForm
