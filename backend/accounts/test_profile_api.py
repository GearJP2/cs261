"""API-10 public field and session tests; no university provider is simulated."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from venues.models import Sport

from .models import UniversityIdentity, UserProfile, UserSportInterest


class PublicProfileApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.viewer = users.objects.create_user("viewer")
        cls.target = users.objects.create_user(
            "private-login",
            email="private@example.com",
            password="private-test-password",
            first_name="Private",
            last_name="Name",
        )
        cls.empty_user = users.objects.create_user("empty-profile")
        cls.no_profile = users.objects.create_user("no-profile")
        # Deliberately make UserProfile.pk differ from User.pk to test the URL identity.
        cls.target_profile = UserProfile.objects.create(
            user=cls.target, display_name="เพื่อนนักกีฬา", credit_score=75
        )
        UserProfile.objects.create(user=cls.viewer, display_name="ผู้เข้าชม", credit_score=0)
        UserProfile.objects.create(user=cls.empty_user, display_name="ยังไม่เลือกกีฬา")
        UniversityIdentity.objects.create(
            user=cls.target, provider_key="private-provider", subject="private-subject"
        )
        cls.badminton = Sport.objects.create(name="Badminton")
        cls.basketball = Sport.objects.create(name="Basketball")
        cls.football = Sport.objects.create(name="Football")
        # Insert in reverse order; the API consistently orders by sport ID.
        UserSportInterest.objects.create(user=cls.target, sport=cls.basketball)
        UserSportInterest.objects.create(user=cls.target, sport=cls.badminton)
        UserSportInterest.objects.create(user=cls.viewer, sport=cls.football)

    def setUp(self):
        self.client.force_login(self.viewer)
        self.url = reverse("accounts:user-public-profile", args=[self.target.pk])

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status)
        self.assertEqual(set(response.json()), {"error"})
        self.assertEqual(set(response.json()["error"]), {"code", "message"})
        self.assertEqual(response.json()["error"]["code"], code)

    def test_profile_has_exact_public_fields_and_sports_for_requested_user(self):
        self.assertNotEqual(self.target_profile.pk, self.target.pk)
        self.assertEqual(self.url, f"/api/v1/users/{self.target.pk}/profile")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "id": self.target.pk,
                    "display_name": "เพื่อนนักกีฬา",
                    "sports": [
                        {"id": self.badminton.pk, "name": "Badminton"},
                        {"id": self.basketball.pk, "name": "Basketball"},
                    ],
                    "credit_score": 75,
                }
            },
        )
        self.assertIn("no-store", response["Cache-Control"])

    def test_own_profile_keeps_zero_credit_and_uses_user_id_not_profile_id(self):
        response = self.client.get(reverse("accounts:user-public-profile", args=[self.viewer.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "id": self.viewer.pk,
                    "display_name": "ผู้เข้าชม",
                    "sports": [{"id": self.football.pk, "name": "Football"}],
                    "credit_score": 0,
                }
            },
        )

    def test_empty_interests_and_unknown_credit_are_empty_list_and_null(self):
        response = self.client.get(
            reverse("accounts:user-public-profile", args=[self.empty_user.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "id": self.empty_user.pk,
                    "display_name": "ยังไม่เลือกกีฬา",
                    "sports": [],
                    "credit_score": None,
                }
            },
        )

    def test_missing_user_or_missing_profile_is_same_json_404_without_creating_profile(self):
        count = UserProfile.objects.count()
        for user_id in (self.no_profile.pk, self.no_profile.pk + 100):
            with self.subTest(user_id=user_id):
                response = self.client.get(reverse("accounts:user-public-profile", args=[user_id]))
                self.assertEqual(
                    response.json(),
                    {"error": {"code": "NOT_FOUND", "message": "ไม่พบโปรไฟล์ที่ต้องการ"}},
                )
                self.assertEqual(response.status_code, 404)
        self.assertEqual(UserProfile.objects.count(), count)
        self.assertFalse(UserProfile.objects.filter(user=self.no_profile).exists())

    def test_query_parameters_cannot_replace_url_target_or_change_credit(self):
        response = self.client.get(
            self.url, {"user_id": self.viewer.pk, "credit_score": 999, "display_name": "changed"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["id"], self.target.pk)
        self.target_profile.refresh_from_db()
        self.assertEqual(self.target_profile.credit_score, 75)
        self.assertEqual(self.target_profile.display_name, "เพื่อนนักกีฬา")

    def test_anonymous_user_is_denied_before_profile_lookup(self):
        self.client.logout()
        for user_id in (self.target.pk, self.no_profile.pk + 100):
            with self.subTest(user_id=user_id):
                response = self.client.get(reverse("accounts:user-public-profile", args=[user_id]))
                self.assert_error(response, 401, "AUTH_REQUIRED")
                self.assertNotIn("Location", response)

    def test_deactivated_viewer_session_cannot_access_profile(self):
        self.viewer.is_active = False
        self.viewer.save(update_fields=["is_active"])
        # Default ModelBackend resolves an inactive local account to anonymous.
        self.assert_error(self.client.get(self.url), 401, "AUTH_REQUIRED")

    def test_session_revoked_after_successful_read_cannot_access_again(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.client.logout()
        self.assert_error(self.client.get(self.url), 401, "AUTH_REQUIRED")

    def test_unsupported_methods_cannot_edit_or_delete_profile(self):
        for method in ("post", "put", "patch", "delete", "options"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    self.url, data='{"credit_score":999}', content_type="application/json"
                )
                self.assert_error(response, 405, "METHOD_NOT_ALLOWED")
                self.assertEqual(response["Allow"], "GET")
        self.target_profile.refresh_from_db()
        self.assertEqual(self.target_profile.credit_score, 75)
        self.assertEqual(self.target_profile.display_name, "เพื่อนนักกีฬา")
