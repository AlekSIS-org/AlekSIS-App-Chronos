from django.contrib import admin

# Register your models here.
from timetable.models import Hint, DebugLog, DebugLogGroup


def refresh_cache(modeladmin, request, queryset):
    for obj in queryset.all():
        obj.save()


refresh_cache.short_description = "Cache aktualisieren"


class HintAdmin(admin.ModelAdmin):
    exclude = ("text_as_latex", "classes_formatted")
    actions = [refresh_cache]


class DebugLogAdmin(admin.ModelAdmin):
    readonly_fields = ["id", "group", "return_code", "filename", "updated_at"]


class DebugLogGroupAdmin(admin.ModelAdmin):
    readonly_fields = ["id"]


admin.site.register(Hint, HintAdmin)
admin.site.register(DebugLogGroup)
admin.site.register(DebugLog, DebugLogAdmin)
