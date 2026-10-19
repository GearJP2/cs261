from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("users/<int:id>/", views.profile_view, name="user-public-profile"),
    path("health/live/", views.live, name="health-live"),
    path("health/ready/", views.ready, name="health-ready"),
]
