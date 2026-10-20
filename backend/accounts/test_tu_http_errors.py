"""Exercise the real login view/service, mocking only the TU HTTP boundary."""

import io
import json
from unittest.mock import patch
from urllib.error import HTTPError

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import UniversityIdentity, UserProfile


@override_settings(TU_APPLICATION_KEY="synthetic-test-key")
class TuHttpErrorTests(TestCase):
    def check_failure(self, provider_status, body, expected_status, expected_code):
        client = Client(enforce_csrf_checks=True)
        csrf = client.get(reverse("accounts:csrf")).json()["data"]["csrf_token"]
        stream = io.BytesIO(body)
        error = HTTPError("https://example.invalid", provider_status, "TU error", {}, stream)
        with patch("accounts.services.urlopen", side_effect=error):
            response = client.post(
                reverse("accounts:login"),
                json.dumps({"username": "synthetic-user", "password": "synthetic-password"}),
                content_type="application/json",
                HTTP_X_CSRFTOKEN=csrf,
            )
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response.json()["error"]["code"], expected_code)
        self.assertNotContains(response, "synthetic", status_code=expected_status)
        self.assertTrue(stream.closed)
        for model in (get_user_model(), UniversityIdentity, UserProfile, Session):
            self.assertFalse(model.objects.exists())
        self.assertNotIn(settings.SESSION_COOKIE_NAME, client.cookies)
        self.assertEqual(client.get(reverse("accounts:me")).status_code, 401)

    def test_documented_invalid_credentials_return_login_failed(self):
        self.check_failure(
            400,
            b'{"status": false, "message": "User or Password Invalid!"}',
            401,
            "LOGIN_FAILED",
        )

    def test_other_bad_request_bodies_remain_provider_errors(self):
        bodies = [
            b'{"status": false, "message": "Could not read the request body!"}',
            b'{"status": false, "message": "The request body has error! (UserName or PassWord Invalid!)"}',
            b'{"status": true, "message": "User or Password Invalid!"}',
            b'{"status": "false", "message": "User or Password Invalid!"}',
            b'{"message": "User or Password Invalid!"}',
            b'{"status": false, "message": "unknown failure"}',
            b"[]",
            b"null",
            b"<html>Error</html>",
            b"{",
            b"\xff",
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.check_failure(400, body, 502, "UNIVERSITY_API_UNAVAILABLE")

    def test_key_rate_limit_and_server_errors_are_not_credential_failures(self):
        for status in (401, 403, 429, 500, 503):
            with self.subTest(status=status):
                self.check_failure(
                    status,
                    b'{"status": false, "message": "User or Password Invalid!"}',
                    502,
                    "UNIVERSITY_API_UNAVAILABLE",
                )
