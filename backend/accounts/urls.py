from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("users/<int:user_id>/profile", views.public_profile, name="user-public-profile"),
    path("me", views.current_user, name="me"),
    path("auth/csrf", views.csrf_token, name="csrf"),
    path("auth/login", views.university_login, name="login"),
    path("auth/logout", views.university_logout, name="logout"),
]
