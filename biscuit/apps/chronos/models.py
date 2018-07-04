from django import forms
import dbsettings

from untisconnect.api_helper import get_terms

choices = []
terms = get_terms()
for term in terms:
    choices.append((term.id, term.name))


class UNTISSettings(dbsettings.Group):
    term = dbsettings.IntegerValue(widget=forms.Select, choices=choices)


untis_settings = UNTISSettings()
