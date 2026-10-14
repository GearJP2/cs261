import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class UniversityAPIError(Exception):
    """เรียก API มหาวิทยาลัยไม่สำเร็จ"""


def call_university_api(username, password):
    application_key = settings.TU_APPLICATION_KEY

    if not application_key:
        raise UniversityAPIError("ยังไม่ได้ตั้งค่า TU_APPLICATION_KEY")

    body = json.dumps({
        "UserName": username,
        "PassWord": password,
    }).encode("utf-8")

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
        raise UniversityAPIError(
            f"API ตอบ HTTP {exc.code}"
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise UniversityAPIError(
            "เชื่อมต่อ API มหาวิทยาลัยไม่สำเร็จ"
        ) from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise UniversityAPIError(
            "API ตอบข้อมูล JSON ไม่ถูกต้อง"
        ) from exc

    if not isinstance(result, dict):
        raise UniversityAPIError("รูปแบบ response ไม่ถูกต้อง")

    return result