from django.db.models import Min, Max

from aleksis.apps.chronos.models import TimePeriod

# Determine overall first and last day and period
min_max = TimePeriod.objects.aggregate(
    Min("period"), Max("period"), Min("weekday"), Max("weekday"), Min("time_start"), Max("time_end")
)

period_min = min_max.get("period__min", 1)
period_max = min_max.get("period__max", 7)

time_min = min_max.get("time_start__min", None)
time_max = min_max.get("time_end__max", None)

weekday_min_ = min_max.get("weekday__min", 0)
weekday_max = min_max.get("weekday__max", 6)


