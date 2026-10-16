import json

from core.api import json_error, require_authenticated_api
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import JoinRequest, Party
from .services import (
    JoinRequestError,
    count_active_members,
    get_party_state,
    submit_join_request,
)


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


@never_cache
@require_authenticated_api
def create_join_request(request, party_id):
    if request.method != "POST":
        response = json_error("METHOD_NOT_ALLOWED", "รองรับเฉพาะ POST", 405)
        response["Allow"] = "POST"
        return response

    # API-06 accepts only {} (or an empty body), never client-selected actors/status.
    if request.body:
        if request.content_type != "application/json":
            return json_error("INVALID_INPUT", "กรุณาส่ง JSON object ว่าง", 400)
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return json_error("INVALID_INPUT", "รูปแบบ JSON ไม่ถูกต้อง", 400)
        if not isinstance(payload, dict) or payload:
            return json_error("INVALID_INPUT", "รับเฉพาะ JSON object ว่าง", 400)

    try:
        join_request = submit_join_request(party_id=party_id, user=request.user)
    except JoinRequestError as error:
        return json_error(error.code, error.message, error.status)
    return JsonResponse(
        {
            "data": {
                "id": join_request.pk,
                "party_id": join_request.party_id,
                "status": join_request.status,
                "created_at": timezone.localtime(join_request.created_at).isoformat(),
            }
        },
        status=201,
    )


@never_cache
@require_authenticated_api
@ensure_csrf_cookie
def my_join_request(request, party_id):
    if request.method != "GET":
        response = json_error("METHOD_NOT_ALLOWED", "รองรับเฉพาะ GET", 405)
        response["Allow"] = "GET"
        return response
    if not Party.objects.filter(pk=party_id).exists():
        return json_error("NOT_FOUND", "ไม่พบกิจกรรมที่ต้องการ", 404)
    join_request = JoinRequest.objects.filter(party_id=party_id, user=request.user).first()
    data = None
    if join_request is not None:
        data = {
            "id": join_request.pk,
            "status": join_request.status,
            "created_at": timezone.localtime(join_request.created_at).isoformat(),
        }
    return JsonResponse({"data": data})
