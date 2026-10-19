from django.urls import path

from . import views

urlpatterns = [
    path("sports", views.sports, name="sport-list"),
    path("venues", views.venues, name="venue-list"),
    path("venues/<int:venue_id>/opening-hours", views.opening_hours, name="venue-opening-hours"),
]
