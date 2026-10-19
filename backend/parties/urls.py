from django.urls import path

from . import views

urlpatterns = [
    path("parties", views.create_party_api, name="party-create"),
    path("parties/<int:party_id>/cancel", views.cancel_party_api, name="party-cancel"),
    path("parties/<int:party_id>", views.party_detail, name="party-detail"),
    path(
        "parties/<int:party_id>/join-requests",
        views.create_join_request,
        name="party-join-request-create",
    ),
    path(
        "parties/<int:party_id>/join-requests/me",
        views.my_join_request,
        name="party-join-request-me",
    ),
]
