from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from venues.models import Sport

from .models import UniversityIdentity, UserProfile, UserSportInterest
from .services import UniversityAPIError, get_or_create_university_user


class AccountPersistenceTests(TestCase):
    def test_custom_user_is_persisted_with_a_hashed_password(self):
        user = get_user_model().objects.create_user("local-tester", password="test-only-password")
        user.refresh_from_db()
        self.assertEqual(user._meta.label, "accounts.User")
        self.assertNotEqual(user.password, "test-only-password")
        self.assertTrue(user.check_password("test-only-password"))

    def test_server_session_can_be_loaded_and_revoked(self):
        session = SessionStore()
        session["setup_probe"] = "persisted"
        session.save()
        session_key = session.session_key
        self.assertEqual(SessionStore(session_key)["setup_probe"], "persisted")
        session.flush()
        self.assertNotIn("setup_probe", SessionStore(session_key))


class AccountSchemaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="student")
        self.other_user = get_user_model().objects.create_user(username="other-student")
        self.sport = Sport.objects.create(name="Badminton")

    def test_identity_provider_and_subject_must_be_unique(self):
        UniversityIdentity.objects.create(user=self.user, provider_key="tu", subject="123")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UniversityIdentity.objects.create(
                    user=self.other_user, provider_key="tu", subject="123"
                )
        UniversityIdentity.objects.create(user=self.user, provider_key="other", subject="123")
        UniversityIdentity.objects.create(user=self.user, provider_key="tu", subject="456")
        self.assertEqual(UniversityIdentity.objects.count(), 3)

    def test_user_and_sport_interest_must_be_unique(self):
        UserSportInterest.objects.create(user=self.user, sport=self.sport)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserSportInterest.objects.create(user=self.user, sport=self.sport)
        UserSportInterest.objects.create(user=self.other_user, sport=self.sport)
        self.assertEqual(UserSportInterest.objects.count(), 2)


class AccountDeletionAndValidationTests(TestCase):
    def create_user(self, username):
        return get_user_model().objects.create_user(username, password="test-only-password")

    def test_profile_rejects_empty_or_whitespace_only_display_name(self):
        user = self.create_user("profile-validation")
        with self.assertRaises(IntegrityError), transaction.atomic():
            UserProfile.objects.create(user=user, display_name="")

        with self.assertRaises(IntegrityError), transaction.atomic():
            UserProfile.objects.create(user=user, display_name="   ")

    def test_deleting_user_cascades_private_profile_identity_and_interest(self):
        user = self.create_user("cascade-user")
        sport = Sport.objects.create(name="Badminton")
        UserProfile.objects.create(user=user, display_name="Cascade User")
        UniversityIdentity.objects.create(
            user=user,
            provider_key="tu-sso",
            subject="student-456",
        )
        UserSportInterest.objects.create(user=user, sport=sport)

        user.delete()

        self.assertFalse(UserProfile.objects.exists())
        self.assertFalse(UniversityIdentity.objects.exists())
        self.assertFalse(UserSportInterest.objects.exists())


class UniversityUserCreationTests(TestCase):
    def setUp(self):
        self.data = {"subject": "student-123", "display_name": "Test Student", "type": "student"}

    def test_first_login_creates_user_and_repeated_login_reuses_it(self):
        first = get_or_create_university_user(self.data)
        second = get_or_create_university_user(self.data)
        self.assertEqual(first.pk, second.pk)
        self.assertFalse(first.has_usable_password())
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(UniversityIdentity.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_identity_conflict_reuses_winner_and_rolls_back_extra_user(self):
        winner = get_or_create_university_user(self.data)
        # Simulate the first lookup missing an identity committed by another request.
        # The insert still hits the real database unique constraint.
        real_filter = UniversityIdentity.objects.filter
        with patch.object(UniversityIdentity.objects, "filter") as lookup:
            lookup.return_value.first.return_value = None
            lookup.side_effect = [
                lookup.return_value,
                real_filter(provider_key="tu", subject=self.data["subject"]),
            ]
            user = get_or_create_university_user(self.data)
        self.assertEqual(user.pk, winner.pk)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(UniversityIdentity.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_unrelated_integrity_error_is_not_hidden(self):
        with patch.object(
            UniversityIdentity.objects, "create", side_effect=IntegrityError("other failure")
        ):
            with self.assertRaisesMessage(IntegrityError, "other failure"):
                get_or_create_university_user(self.data)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(UniversityIdentity.objects.count(), 0)
        self.assertEqual(UserProfile.objects.count(), 0)


class UniversityLoginViewTests(TestCase):
    def setUp(self):
        self.login_url = reverse("accounts:login")
        self.response_data = {
            "status": True,
            "username": "student-123",
            "displayname_th": "Test Student",
            "type": "student",
        }
        self.api_patch = patch(
            "accounts.views.call_university_api", return_value=self.response_data
        )
        self.api = self.api_patch.start()
        self.addCleanup(self.api_patch.stop)

    def post_login(self, data=None):
        return self.client.post(
            self.login_url,
            data if data is not None else {"username": "student-123", "password": "test-password"},
            content_type="application/json",
        )

    def test_success_creates_session_and_repeat_login_reuses_user(self):
        first = self.post_login()
        self.assertEqual(first.status_code, 200)
        user_id = first.json()["data"]["id"]
        self.assertEqual(self.client.session["_auth_user_id"], str(user_id))
        second = self.post_login()
        self.assertEqual(second.json()["data"]["id"], user_id)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.api.assert_called_with("student-123", "test-password")

    def test_invalid_input_does_not_call_provider(self):
        for data in ([], {}, {"username": "u", "password": 123}):
            with self.subTest(data=data):
                self.assertEqual(self.post_login(data).status_code, 400)
        response = self.client.post(self.login_url, "{", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.api.assert_not_called()

    def test_provider_rejection_does_not_create_user_or_session(self):
        self.api.return_value = {"status": False}
        self.assertEqual(self.post_login().status_code, 401)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_non_student_is_forbidden(self):
        self.api.return_value = {**self.response_data, "type": "staff"}
        self.assertEqual(self.post_login().status_code, 403)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_inactive_user_is_forbidden(self):
        user = get_or_create_university_user(
            {"subject": "student-123", "display_name": "Test Student", "type": "student"}
        )
        user.is_active = False
        user.save(update_fields=["is_active"])
        self.assertEqual(self.post_login().status_code, 403)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_provider_failure_returns_generic_error(self):
        self.api.side_effect = UniversityAPIError("private provider details")
        response = self.post_login()
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private provider details", response.content.decode())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.login_url).status_code, 405)
        self.api.assert_not_called()

    def test_login_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            self.login_url,
            {"username": "u", "password": "p"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.api.assert_not_called()
