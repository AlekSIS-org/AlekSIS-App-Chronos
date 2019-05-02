from django.contrib import admin

# Register your models here.
from timetable.models import Hint


def refresh_cache(modeladmin, request, queryset):
    for obj in queryset.all():
        obj.save()


refresh_cache.short_description = "Cache aktualisieren"


class HintAdmin(admin.ModelAdmin):
    exclude = ("text_as_latex", "classes_formatted")
    actions = [refresh_cache]


admin.site.register(Hint, HintAdmin)
