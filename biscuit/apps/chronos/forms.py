from django.core.exceptions import ValidationError
from django.forms import ModelForm

from timetable.models import Hint


class HintForm(ModelForm):
    class Meta:
        model = Hint
        fields = ("from_date", "to_date", "text", "classes", "teachers")

    def clean(self):
        super().clean()
        print("validate")
        print(self.cleaned_data["classes"], self.cleaned_data["teachers"])
        if len(self.cleaned_data["classes"]) == 0 and self.cleaned_data["teachers"] is False:
            raise ValidationError("Bitte gib eine Zielgruppe an (Klassen oder Lehrer).")
