import dbsettings
from django import forms

from untisconnect.api_helper import get_terms, get_school_years

choices_school_years = []
school_years = get_school_years()
for year in school_years:
    choices_school_years.append((year.id, year.name))

choices_terms = []
terms = get_terms()
for term in terms:
    choices_terms.append((term.id, "{}, #{}: {}".format(term.school_year_id, term.id, term.name)))


class UNTISSettings(dbsettings.Group):
    school_year = dbsettings.PositiveIntegerValue("Schuljahr", widget=forms.Select, choices=choices_school_years)
    term = dbsettings.IntegerValue("Periode", widget=forms.Select, choices=choices_terms,
                                   help_text="Bitte wähle oberhalb auch das zur Periode passende Schuljahr aus.")


untis_settings = UNTISSettings("UNTIS")
