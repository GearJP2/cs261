"""Shared JSON responses and session access for Django views.

Business APIs delegate session and university identity checks to US1.
"""

from accounts.decorators import require_university_user
from django.http import JsonResponse
from django.views.csrf import csrf_failure as django_csrf_failure
from django.views.decorators.cache import never_cache


def json_error(code, message, status, fields=None):
    error = {"code": code, "message": message}
    if fields is not None:
        error["fields"] = fields
    return JsonResponse({"error": error}, status=status)


def require_authenticated_api(view):
    """Keep the BASE-04 entry point while applying US1's shared access policy."""
    return require_university_user(view)


@never_cache
def csrf_failure(request, reason=""):
    """Keep Django's CSRF protection; give JSON APIs the shared error envelope."""
    if request.path_info.startswith("/api/v1/"):
        return json_error("CSRF_FAILED", "ตรวจสอบ CSRF ไม่ผ่าน กรุณาโหลดหน้าใหม่", 403)
    return django_csrf_failure(request, reason=reason)
