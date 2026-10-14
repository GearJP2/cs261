from django.urls import path

from . import views

urlpatterns = [
    path("parties/<int:party_id>", views.party_detail, name="party-detail"),
]
