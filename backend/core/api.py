"""Shared JSON responses and session access for Django views.

This guard checks local accounts only. University eligibility belongs to US1;
its shared policy must be integrated before claiming student-only access.
"""

from functools import wraps

from django.http import JsonResponse


def json_error(code, message, status, fields=None):
    error = {"code": code, "message": message}
    if fields is not None:
        error["fields"] = fields
    return JsonResponse({"error": error}, status=status)


def require_authenticated_api(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return json_error("AUTH_REQUIRED", "กรุณาเข้าสู่ระบบก่อนใช้งาน", 401)
        if not request.user.is_active:
            return json_error("ACCOUNT_INACTIVE", "บัญชีนี้ไม่สามารถใช้งานได้", 403)
        return view(request, *args, **kwargs)

    return wrapped
