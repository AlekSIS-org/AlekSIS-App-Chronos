from django.urls import path

from . import views


urlpatterns = [
    path('timetable', views.timetable, name='timetable'),
    path('lessons', views.timetable, {'template': 'lessons_list'}, name='lessons_list'),
]
