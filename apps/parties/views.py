from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.common.guards import IsSessionAuthenticated
from .models import Party
from .serializers import PartyDetailSerializer

class PartyDetailView(APIView):
    permission_classes = [IsSessionAuthenticated]

    def get(self, request, party_id):
        party = get_object_or_404(Party, id=party_id)
        serializer = PartyDetailSerializer(party)
        return Response(serializer.data, status=status.HTTP_200_OK)