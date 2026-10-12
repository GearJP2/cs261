from django.urls import path
from .views import PartyDetailView

urlpatterns = [
    path('parties/<uuid:party_id>/', PartyDetailView.as_view(), name='party-detail'),
]