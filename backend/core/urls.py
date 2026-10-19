from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("preview/profile/", views.profile_preview, name="profile-preview"),
    path("health/live/", views.live, name="health-live"),
    path("health/ready/", views.ready, name="health-ready"),
]
