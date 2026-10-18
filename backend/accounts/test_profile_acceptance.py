"""US8-T-01 regression acceptance tests, independent of BASE-03 seeds."""

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from venues.models import Sport

from .models import UniversityIdentity, UserProfile, UserSportInterest
from .views import public_profile


class PublicProfileAcceptanceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.viewer = get_user_model().objects.create_user("acceptance-viewer")
        cls.other_viewer = get_user_model().objects.create_user("other-viewer")
        cls.target = get_user_model().objects.create_user(
            "internal-student-id",
            email="private-acceptance@example.invalid",
            password="not-a-real-student-password",
        )
        cls.second = get_user_model().objects.create_user("second-target")
        cls.target_profile = UserProfile.objects.create(
            user=cls.target, display_name="นักกีฬา ก", credit_score=0
        )
        UserProfile.objects.create(user=cls.second, display_name="นักกีฬา ข", credit_score=None)
        cls.badminton = Sport.objects.create(name="แบดมินตัน")
        cls.football = Sport.objects.create(name="ฟุตบอล")
        UserSportInterest.objects.create(user=cls.target, sport=cls.badminton)
        UniversityIdentity.objects.create(
            user=cls.target,
            provider_key="private-provider-sentinel",
            subject="private-subject-sentinel",
        )

    def setUp(self):
        self.client.force_login(self.viewer)
        self.url = reverse("user-public-profile", args=[self.target.pk])

    def assert_private_response(self, response):
        self.assertEqual(response["Content-Type"], "application/json")
        cache = response["Cache-Control"]
        self.assertIn("no-store", cache)
        self.assertIn("private", cache)
        self.assertIn("Expires", response)

    def test_repeated_reads_across_targets_and_viewers_do_not_mix_profile_data(self):
        # The same display name deliberately cannot be used as the identity key.
        UserProfile.objects.filter(user=self.second).update(display_name="นักกีฬา ก")
        second_client = Client()
        second_client.force_login(self.other_viewer)
        for client in (self.client, second_client):
            for target, credit, sports in (
                (self.target, 0, [{"id": self.badminton.pk, "name": "แบดมินตัน"}]),
                (self.second, None, []),
                (self.target, 0, [{"id": self.badminton.pk, "name": "แบดมินตัน"}]),
            ):
                with self.subTest(viewer=client.session.session_key, target=target.pk):
                    response = client.get(reverse("user-public-profile", args=[target.pk]))
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(
                        response.json(),
                        {
                            "data": {
                                "id": target.pk,
                                "display_name": "นักกีฬา ก",
                                "sports": sports,
                                "credit_score": credit,
                            }
                        },
                    )
                    self.assert_private_response(response)

    def test_read_after_profile_and_interests_change_returns_fresh_values(self):
        self.assertEqual(self.client.get(self.url).json()["data"]["credit_score"], 0)
        UserProfile.objects.filter(user=self.target).update(display_name="ชื่อใหม่", credit_score=12)
        UserSportInterest.objects.filter(user=self.target).delete()
        UserSportInterest.objects.create(user=self.target, sport=self.football)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"],
            {
                "id": self.target.pk,
                "display_name": "ชื่อใหม่",
                "credit_score": 12,
                "sports": [{"id": self.football.pk, "name": "ฟุตบอล"}],
            },
        )

    def test_private_identity_and_session_values_are_not_in_success_payload(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        for private_value in (
            self.target.username,
            self.target.email,
            self.target.password,
            "private-provider-sentinel",
            "private-subject-sentinel",
            self.client.session.session_key,
        ):
            with self.subTest(value_type=type(private_value).__name__):
                self.assertNotIn(private_value, body)

    def test_expired_session_cannot_read_previously_accessible_profile(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        Session.objects.filter(session_key=self.client.session.session_key).update(
            expire_date=timezone.now() - timedelta(seconds=1)
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTH_REQUIRED")
        self.assert_private_response(response)

    def test_server_revoked_session_cannot_read_with_old_browser_cookie(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        Session.objects.filter(session_key=self.client.session.session_key).delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTH_REQUIRED")
        self.assert_private_response(response)

    def test_authenticated_inactive_guard_rejects_before_database_lookup(self):
        # Unit seam: ModelBackend rejects inactive sessions as anonymous (401).
        # Supply an authenticated inactive user to exercise the guard's 403 branch.
        request = RequestFactory().get(self.url)
        request.user = self.viewer
        request.user.is_active = False
        with self.assertNumQueries(0):
            response = public_profile(request, user_id=self.target.pk)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.content)["error"]["code"], "ACCOUNT_INACTIVE")
        self.assert_private_response(response)

    def test_csrf_enforcement_allows_get_but_rejects_unsafe_write_without_token(self):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.viewer)
        self.assertEqual(browser.get(self.url).status_code, 200)
        response = browser.patch(
            self.url, data={"credit_score": 999}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "CSRF_FAILED")
        self.target_profile.refresh_from_db()
        self.assertEqual(self.target_profile.credit_score, 0)

    def test_error_responses_are_private_and_do_not_echo_untrusted_query(self):
        missing_url = reverse("user-public-profile", args=[999999999])
        sentinel = "untrusted-query-sentinel@example.invalid"
        for authenticated in (True, False):
            if not authenticated:
                self.client.logout()
            response = self.client.get(missing_url, {"email": sentinel})
            self.assertEqual(response.status_code, 404 if authenticated else 401)
            self.assertEqual(set(response.json()), {"error"})
            self.assertEqual(set(response.json()["error"]), {"code", "message"})
            self.assertNotIn(sentinel, response.content.decode())
            self.assert_private_response(response)
