from django.urls import path

from . import views

urlpatterns = [
    path("users/<int:user_id>/profile", views.public_profile, name="user-public-profile"),
]
