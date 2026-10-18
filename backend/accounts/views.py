from core.api import json_error, require_authenticated_api
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

from .models import UserProfile, UserSportInterest


@never_cache
@require_authenticated_api
def public_profile(request, user_id):
    if request.method != "GET":
        response = json_error("METHOD_NOT_ALLOWED", "รองรับเฉพาะ GET", 405)
        response["Allow"] = "GET"
        return response

    try:
        profile = UserProfile.objects.get(user_id=user_id)
    except UserProfile.DoesNotExist:
        return json_error("NOT_FOUND", "ไม่พบโปรไฟล์ที่ต้องการ", 404)

    interests = (
        UserSportInterest.objects.filter(user_id=user_id)
        .select_related("sport")
        .order_by("sport_id")
    )
    return JsonResponse(
        {
            "data": {
                "id": profile.user_id,
                "display_name": profile.display_name,
                "sports": [
                    {"id": interest.sport_id, "name": interest.sport.name} for interest in interests
                ],
                "credit_score": profile.credit_score,
            }
        }
    )
