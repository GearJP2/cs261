import json

from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

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
    return JsonResponse({"data": {"logged_in": True, "id": user.pk}})
