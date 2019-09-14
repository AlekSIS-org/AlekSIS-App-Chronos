from django.urls import path

from . import views


urlpatterns = [
    path('timetable', views.timetable, name='timetable'),
    path('timetable/<int:year>/<int:week>', views.timetable, name='timetable_by_week'),
    path('lessons', views.lessons_day, name='lessons_day'),
    path('lessons/<when>', views.lessons_day, name='lessons_day_by_date'),
    path('lessons/<int:id_>/<int:week>/substition', views.edit_substitution, name='edit_substitution'),
    path('lessons/<int:id_>/<int:week>/substition/delete', views.delete_substitution, name='delete_substitution')
]
