from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("users/<int:user_id>/", views.public_profile_page, name="public-profile-page"),
    path("health/live/", views.live, name="health-live"),
    path("health/ready/", views.ready, name="health-ready"),
]
