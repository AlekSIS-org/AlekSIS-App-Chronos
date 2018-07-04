from django import forms
from django.db import models
import dbsettings
from untisconnect.api import get_terms

# Create your models here.

# class Teacher(models.Model):
#     shortcode = models.CharField(max_length=10)
#     first_name = models.CharField(max_length=100)
#     name = models.CharField(max_length=100)
#
#
# class Room(models.Model):
#     shortcode = models.CharField(max_length=10)
#     name = models.CharField(max_length=100)
#
#
# class Class(models.Model):
#     name = models.CharField(max_length=10)
#     text1 = models.CharField(max_length=200)
#     text2 = models.CharField(max_length=200)
#     room = models.ForeignKey(Room, on_delete=models.CASCADE)

choices = []
terms = get_terms()
for term in terms:
    choices.append((term.id, term.name))


class UNTISSettings(dbsettings.Group):
    term = dbsettings.IntegerValue(widget=forms.Select, choices=choices)


untis_settings = UNTISSettings()
