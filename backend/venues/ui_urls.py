from django.urls import path

from . import ui_views

app_name = "venues"

urlpatterns = [
    path("", ui_views.venue_map, name="venue_map"),
    path("<int:venue_id>/", ui_views.venue_detail, name="venue_detail"),
    path("<int:venue_id>/sports/<int:sport_id>/", ui_views.sport_detail, name="sport_detail"),
]
