from django.urls import path

from . import views

app_name = "venues"

urlpatterns = [
    path("", views.venue_map, name="venue_map"),
    path("<int:venue_id>/", views.venue_detail, name="venue_detail"),
    path("<int:venue_id>/sports/<int:sport_id>/", views.sport_detail, name="sport_detail"),
]
