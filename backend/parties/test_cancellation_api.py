import json

from django.test import RequestFactory, TestCase
from django.utils import timezone

from .test_join_requests import JoinRequestFixture
from .views import cancel_party_api


class CancelPartyHandlerTests(JoinRequestFixture, TestCase):
    """Handler only; route/auth/CSRF integration waits for US1."""

    def call(
        self, *, user=None, body="{}", content_type="application/json", method="post", party_id=None
    ):
        request = getattr(RequestFactory(), method)(
            f"/api/v1/parties/{self.party.pk}/cancel",
            data=body,
            content_type=content_type,
        )
        request.user = user if user is not None else self.host
        return cancel_party_api(request, self.party.pk if party_id is None else party_id)

    def test_success_and_repeat_return_same_public_data(self):
        response = self.call()
        self.assertEqual(response.status_code, 200)
        self.party.refresh_from_db()
        self.assertEqual(
            json.loads(response.content),
            {
                "data": {
                    "id": self.party.pk,
                    "state": "Cancelled",
                    "cancelled_at": timezone.localtime(self.party.cancelled_at).isoformat(),
                }
            },
        )
        self.assertEqual(json.loads(self.call().content), json.loads(response.content))

    def test_invalid_body_does_not_cancel(self):
        for body, content_type in (
            ("", "application/json"),
            ("{", "application/json"),
            ("[]", "application/json"),
            ("null", "application/json"),
            ('{"host_id":1}', "application/json"),
            ('{"cancelled_at":null}', "application/json"),
            ("{}", "text/plain"),
            (b"\xff", "application/json"),
        ):
            with self.subTest(body=body, content_type=content_type):
                response = self.call(body=body, content_type=content_type)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(json.loads(response.content)["error"]["code"], "INVALID_INPUT")
        self.party.refresh_from_db()
        self.assertIsNone(self.party.cancelled_at)

    def test_service_errors_are_mapped_to_json(self):
        response = self.call(user=self.other)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content)["error"]["code"], "FORBIDDEN")
        response = self.call(party_id=self.party.pk + 999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content)["error"]["code"], "NOT_FOUND")
        self.party.starts_at = self.now
        self.party.save()
        response = self.call()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(json.loads(response.content)["error"]["code"], "PARTY_STARTED")
        self.party.refresh_from_db()
        self.assertIsNone(self.party.cancelled_at)

    def test_wrong_method_returns_allow_header(self):
        for method in ("get", "patch", "delete"):
            with self.subTest(method=method):
                response = self.call(method=method, body={} if method == "get" else "{}")
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response["Allow"], "POST")
                self.assertEqual(
                    json.loads(response.content)["error"]["code"], "METHOD_NOT_ALLOWED"
                )
        self.party.refresh_from_db()
        self.assertIsNone(self.party.cancelled_at)
