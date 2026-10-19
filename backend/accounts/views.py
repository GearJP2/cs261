import json
from datetime import timedelta

from core.api import json_error, require_authenticated_api
from django.conf import settings
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from .decorators import require_university_user
from .models import UniversityIdentity, UserProfile, UserSportInterest
from .services import (
    UniversityAPIError,
    UniversityEligibilityRejected,
    UniversityLoginRejected,
    call_university_api,
    get_or_create_university_user,
    validate_student_eligibility,
    validate_university_response,
)


def _error(code, message, status):
    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


@require_GET
@never_cache
def csrf_token(request):
    return JsonResponse({"data": {"csrf_token": get_token(request)}})


@require_POST
@never_cache
@csrf_protect
def university_logout(request):
    logout(request)
    return JsonResponse({"data": {"logged_out": True}})


@require_POST
@csrf_protect
def university_login(request):
    if request.content_type != "application/json":
        return _error("INVALID_INPUT", "กรุณาส่งข้อมูลเป็น JSON", 400)

    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return _error("INVALID_INPUT", "ข้อมูล JSON ไม่ถูกต้อง", 400)

    if not isinstance(data, dict):
        return _error("INVALID_INPUT", "ข้อมูลต้องเป็น JSON object", 400)

    username = data.get("username")
    password = data.get("password")
    if (
        not isinstance(username, str)
        or not username.strip()
        or not isinstance(password, str)
        or not password
    ):
        return _error("INVALID_INPUT", "กรุณาระบุ username และ password", 400)

    try:
        result = call_university_api(username, password)
        identity_data = validate_university_response(result)
        validate_student_eligibility(identity_data)
        user = get_or_create_university_user(identity_data)
    except UniversityLoginRejected:
        return _error("LOGIN_FAILED", "เข้าสู่ระบบไม่สำเร็จ", 401)
    except UniversityEligibilityRejected:
        return _error("FORBIDDEN", "บัญชีไม่มีสิทธิ์เข้าใช้งาน", 403)
    except UniversityAPIError:
        return _error("UNIVERSITY_API_UNAVAILABLE", "ไม่สามารถยืนยันบัญชีได้ กรุณาลองใหม่", 502)

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session.set_expiry(timezone.now() + timedelta(seconds=settings.UNIVERSITY_SESSION_AGE))
    request.session["university_identity_id"] = UniversityIdentity.objects.get(
        provider_key="tu", subject=identity_data["subject"], user=user
    ).pk
    return JsonResponse({"data": {"logged_in": True, "id": user.pk}})


@require_GET
@never_cache
@require_university_user
def current_user(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if profile is None:
        return _error("FORBIDDEN", "ไม่พบข้อมูลโปรไฟล์ กรุณาเข้าสู่ระบบใหม่", 403)

    return JsonResponse(
        {
            "data": {
                "id": request.user.pk,
                "display_name": profile.display_name,
                "student_verified": True,
            }
        }
    )


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
