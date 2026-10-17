from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("auth/csrf", views.csrf_token, name="csrf"),
    path("auth/login", views.university_login, name="login"),
]
