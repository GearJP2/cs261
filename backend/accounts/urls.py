from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("auth/login", views.university_login, name="login"),
]
