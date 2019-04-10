from django.forms import ModelForm
from material import Layout, Fieldset, Row

from timetable.models import Hint


class HintForm(ModelForm):
    layout = Layout(Fieldset('Zeitraum',
                             Row('from_date', 'to_date'),
                             ),
                    Fieldset('Hinweistext',
                             "text",
                             ),
                    Fieldset('Klassen',
                             'classes'),
                    )

    class Meta:
        model = Hint
        fields = ("from_date", "to_date", "text", "classes")
