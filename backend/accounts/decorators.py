from functools import wraps

from django.http import JsonResponse

from .models import UniversityIdentity


def require_university_user(view):
    """Require a session established by university login before calling a JSON view."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"error": {"code": "AUTH_REQUIRED", "message": "กรุณาเข้าสู่ระบบ"}},
                status=401,
            )

        if not request.user.is_active:
            return JsonResponse(
                {"error": {"code": "ACCOUNT_INACTIVE", "message": "บัญชีนี้ถูกระงับการใช้งาน"}},
                status=403,
            )

        identity_id = request.session.get("university_identity_id")
        identity = None
        if type(identity_id) is int and identity_id > 0:
            identity = UniversityIdentity.objects.filter(
                pk=identity_id,
                user=request.user,
                provider_key="tu",
                student_verified_at__isnull=False,
                eligibility_checked_at__isnull=False,
            ).first()

        if identity is None:
            return JsonResponse(
                {"error": {"code": "FORBIDDEN", "message": "กรุณายืนยันบัญชีมหาวิทยาลัย"}},
                status=403,
            )

        request.university_identity = identity
        return view(request, *args, **kwargs)

    return wrapped
