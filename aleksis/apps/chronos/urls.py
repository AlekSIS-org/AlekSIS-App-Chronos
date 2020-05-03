from django.urls import path

from . import views

urlpatterns = [
    path("", views.all_timetables, name="all_timetables"),
    path("timetable/my/", views.my_timetable, name="my_timetable"),
    path(
        "timetable/my/<int:year>/<int:month>/<int:day>/",
        views.my_timetable,
        name="my_timetable_by_date",
    ),
    path("timetable/<str:type_>/<int:pk>/", views.timetable, name="timetable"),
    path(
        "timetable/<str:type_>/<int:pk>/<int:year>/<int:week>/",
        views.timetable,
        name="timetable_by_week",
    ),
    path(
        "timetable/<str:type_>/<int:pk>/<str:regular>/", views.timetable, name="timetable_regular",
    ),
    path("lessons/", views.lessons_day, name="lessons_day"),
    path(
        "lessons/<int:year>/<int:month>/<int:day>/", views.lessons_day, name="lessons_day_by_date",
    ),
    path(
        "lessons/<int:id_>/<int:week>/substition/",
        views.edit_substitution,
        name="edit_substitution",
    ),
    path(
        "lessons/<int:id_>/<int:week>/substition/delete/",
        views.delete_substitution,
        name="delete_substitution",
    ),
    path("substitutions/", views.substitutions, name="substitutions"),
    path(
        "substitutions/print/", views.substitutions, {"is_print": True}, name="substitutions_print",
    ),
    path(
        "substitutions/<int:year>/<int:month>/<int:day>/",
        views.substitutions,
        name="substitutions_by_date",
    ),
    path(
        "substitutions/<int:year>/<int:month>/<int:day>/print/",
        views.substitutions,
        {"is_print": True},
        name="substitutions_print_by_date",
    ),
]
