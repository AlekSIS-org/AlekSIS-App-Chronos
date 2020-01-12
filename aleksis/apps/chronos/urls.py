from django.urls import path

from . import views

urlpatterns = [
    path("timetable/<str:_type>/<int:pk>", views.timetable, name="timetable"),
    path("all_timetables", views.all, name="all_timetables"),
    path("timetable/<str:_type>/<int:pk>/<int:year>/<int:week>", views.timetable, name="timetable_by_week"),
    path("lessons", views.lessons_day, name="lessons_day"),
    path("lessons/<when>", views.lessons_day, name="lessons_day_by_date"),
    path(
        "lessons/<int:id_>/<int:week>/substition",
        views.edit_substitution,
        name="edit_substitution",
    ),
    path(
        "lessons/<int:id_>/<int:week>/substition/delete",
        views.delete_substitution,
        name="delete_substitution",
    ),
    path("substitutions/", views.substitutions, name="substitutions"),
    path("substitutions/<int:year>/<int:month>/<int:day>/", views.substitutions, name="substitutions_by_day"),
]
