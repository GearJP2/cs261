import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import UniversityIdentity, UserProfile


class UniversityAPIError(Exception):
    """เรียก API มหาวิทยาลัยไม่สำเร็จ"""


def call_university_api(username, password):
    application_key = settings.TU_APPLICATION_KEY

    if not application_key:
        raise UniversityAPIError("ยังไม่ได้ตั้งค่า TU_APPLICATION_KEY")

    body = json.dumps(
        {
            "UserName": username,
            "PassWord": password,
        }
    ).encode("utf-8")

    request = Request(
        url="https://restapi.tu.ac.th/api/v1/auth/Ad/verify",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Application-Key": application_key,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise UniversityAPIError(f"API ตอบ HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise UniversityAPIError("เชื่อมต่อ API มหาวิทยาลัยไม่สำเร็จ") from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise UniversityAPIError("API ตอบข้อมูล JSON ไม่ถูกต้อง") from exc

    if not isinstance(result, dict):
        raise UniversityAPIError("รูปแบบ response ไม่ถูกต้อง")

    return result


class UniversityLoginRejected(Exception):
    """API ไม่ยืนยันการเข้าสู่ระบบ"""


class UniversityEligibilityRejected(Exception):
    """บัญชีไม่มีสิทธิ์เข้าใช้งานระบบ"""


def validate_university_response(result):
    if not isinstance(result, dict):
        raise UniversityAPIError("รูปแบบ response ไม่ถูกต้อง")

    if result.get("status") is not True:
        raise UniversityLoginRejected("เข้าสู่ระบบไม่สำเร็จ")

    required_fields = (
        "username",
        "displayname_th",
        "type",
    )

    for field in required_fields:
        value = result.get(field)

        if not isinstance(value, str) or not value.strip():
            raise UniversityAPIError(f"response ไม่มีข้อมูล {field} ที่ถูกต้อง")

    return {
        "subject": result["username"],
        "display_name": result["displayname_th"],
        "type": result["type"],
    }


def validate_student_eligibility(identity_data):
    if identity_data["type"] != "student":
        raise UniversityEligibilityRejected("บัญชีนี้ไม่ใช่บัญชีนักศึกษา")


def get_or_create_university_user(identity_data):
    User = get_user_model()

    with transaction.atomic():
        identity = UniversityIdentity.objects.filter(
            provider_key="tu",
            subject=identity_data["subject"],
        ).first()

        if identity is None:
            try:
                # Roll back the new User too if another request created the identity.
                with transaction.atomic():
                    user = User(username=f"tu_{uuid.uuid4().hex}")
                    user.set_unusable_password()
                    user.save()
                    identity = UniversityIdentity.objects.create(
                        user=user,
                        provider_key="tu",
                        subject=identity_data["subject"],
                    )
            except IntegrityError:
                identity = UniversityIdentity.objects.filter(
                    provider_key="tu",
                    subject=identity_data["subject"],
                ).first()
                if identity is None:
                    raise

        user = identity.user

        if not user.is_active:
            raise UniversityEligibilityRejected("บัญชีนี้ถูกระงับการใช้งาน")

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "display_name": identity_data["display_name"],
            },
        )

        now = timezone.now()
        identity.student_verified_at = now
        identity.eligibility_checked_at = now
        identity.save(
            update_fields=[
                "student_verified_at",
                "eligibility_checked_at",
            ],
        )

        return user
