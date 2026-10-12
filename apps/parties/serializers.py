from rest_framework import serializers
from .models import Party
from .services import get_party_state, count_active_members

class PartyDetailSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    current_member_count = serializers.SerializerMethodField()

    class Meta:
        model = Party
        fields = [
            'id', 'title', 'description', 'sport',
            'max_members', 'current_member_count',
            'state', 'location', 'start_time', 'created_at'
        ]

    def get_state(self, obj):
        return get_party_state(obj)

    def get_current_member_count(self, obj):
        return count_active_members(obj.id)