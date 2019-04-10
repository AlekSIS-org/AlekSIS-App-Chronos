from django.contrib import admin

# Register your models here.
from timetable.models import Hint, HintClass

admin.site.register(Hint)
admin.site.register(HintClass)
