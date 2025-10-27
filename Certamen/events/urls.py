from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.home, name="home"),
    path("<int:event_id>/", views.event_detail, name="event_detail"),
    path("<int:event_id>/join/", views.join_event_view, name="join_event"),
    path("<int:event_id>/leave/", views.leave_event_view, name="leave_event"),
]