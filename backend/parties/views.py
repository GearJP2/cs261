from core.api import json_error, require_authenticated_api
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .models import Party
from .services import count_active_members, get_party_state


@never_cache
@require_authenticated_api
def party_detail(request, party_id):
    if request.method != "GET":
        response = json_error("METHOD_NOT_ALLOWED", "รองรับเฉพาะ GET", 405)
        response["Allow"] = "GET"
        return response

    try:
        party = Party.objects.select_related("host__profile").get(pk=party_id)
    except Party.DoesNotExist:
        return json_error("NOT_FOUND", "ไม่พบกิจกรรมที่ต้องการ", 404)

    profile = getattr(party.host, "profile", None)
    member_count = count_active_members(party)
    return JsonResponse(
        {
            "data": {
                "id": party.pk,
                "title": party.title,
                "description": party.description,
                "host": {
                    "id": party.host_id,
                    # Legacy/local accounts may not have a profile. Never expose
                    # their login identifier as a replacement display name.
                    "display_name": profile.display_name if profile else "ผู้จัดกิจกรรม",
                },
                "sport_id": party.sport_id,
                "venue_id": party.venue_id,
                "starts_at": timezone.localtime(party.starts_at).isoformat(),
                "ends_at": timezone.localtime(party.ends_at).isoformat(),
                "capacity": party.capacity,
                "member_count": member_count,
                "remaining_slots": party.capacity - member_count,
                "state": get_party_state(party, member_count=member_count),
                "is_host": request.user.pk == party.host_id,
                "is_member": party.memberships.filter(
                    user=request.user, left_at__isnull=True
                ).exists(),
            }
        }
    )
