from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
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

    def test_csrf_endpoint_sets_cookie_and_disables_caching(self):
        response = self.client.get(reverse("accounts:csrf"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["csrf_token"])
        self.assertIn("csrftoken", response.cookies)
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.api.assert_not_called()

    def test_login_accepts_matching_csrf_token_and_rejects_wrong_token(self):
        client = Client(enforce_csrf_checks=True)
        token_response = client.get(reverse("accounts:csrf"))
        token = token_response.json()["data"]["csrf_token"]
        data = {"username": "student-123", "password": "test-password"}
        rejected = client.post(
            self.login_url, data, content_type="application/json", HTTP_X_CSRFTOKEN="x" * 64
        )
        self.assertEqual(rejected.status_code, 403)
        self.api.assert_not_called()
        response = client.post(
            self.login_url, data, content_type="application/json", HTTP_X_CSRFTOKEN=token
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("_auth_user_id", client.session)
        self.assertNotEqual(
            client.cookies["csrftoken"].value, token_response.cookies["csrftoken"].value
        )

    def test_csrf_endpoint_does_not_accept_post(self):
        self.assertEqual(self.client.post(reverse("accounts:csrf")).status_code, 405)
        self.api.assert_not_called()

    def test_me_requires_login(self):
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, 401)
        self.api.assert_not_called()

    def test_me_returns_only_current_user_public_fields(self):
        login_response = self.post_login()
        self.api.reset_mock()
        response = self.client.get(reverse("accounts:me"), {"user_id": "999"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "id": login_response.json()["data"]["id"],
                    "display_name": "Test Student",
                    "student_verified": True,
                }
            },
        )
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.api.assert_not_called()

    def test_me_rejects_local_session_without_university_login(self):
        user = get_user_model().objects.create_user(username="local-user")
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 403)

    def test_me_rejects_deleted_or_unverified_identity(self):
        self.post_login()
        identity = UniversityIdentity.objects.get(subject="student-123")
        identity.student_verified_at = None
        identity.save(update_fields=["student_verified_at"])
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 403)
        identity.delete()
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 403)

    def test_me_rejects_identity_from_another_user(self):
        self.post_login()
        other_user = get_user_model().objects.create_user(username="other-local-user")
        identity = UniversityIdentity.objects.create(
            user=other_user, provider_key="tu", subject="other-subject"
        )
        session = self.client.session
        session["university_identity_id"] = identity.pk
        session.save()
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 403)

    def test_me_rejects_session_after_account_is_disabled(self):
        self.post_login()
        user = UniversityIdentity.objects.get(subject="student-123").user
        user.is_active = False
        user.save(update_fields=["is_active"])
        # ModelBackend stops resolving disabled users as authenticated.
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 401)

    def test_me_does_not_accept_post(self):
        self.assertEqual(self.client.post(reverse("accounts:me")).status_code, 405)

    def test_logout_revokes_session_and_replayed_cookie(self):
        self.post_login()
        session_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        other_tab = Client()
        other_tab.cookies[settings.SESSION_COOKIE_NAME] = session_key
        self.assertEqual(other_tab.get(reverse("accounts:me")).status_code, 200)
        self.api.reset_mock()

        response = self.client.post(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": {"logged_out": True}})
        self.assertEqual(response.cookies[settings.SESSION_COOKIE_NAME]["max-age"], 0)
        self.assertNotIn("_auth_user_id", SessionStore(session_key))
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 401)
        self.assertEqual(other_tab.get(reverse("accounts:me")).status_code, 401)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(UniversityIdentity.objects.count(), 1)
        self.api.assert_not_called()

    def test_logout_can_be_repeated_without_session(self):
        for _ in range(2):
            response = self.client.post(reverse("accounts:logout"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"data": {"logged_out": True}})
        self.api.assert_not_called()

    def test_logout_get_does_not_end_session(self):
        self.post_login()
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 200)

    def test_logout_requires_csrf_even_without_session(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("accounts:logout")).status_code, 403)
        self.api.assert_not_called()

    def test_csrf_protected_logout_preserves_session_until_valid_request(self):
        client = Client(enforce_csrf_checks=True)
        token = client.get(reverse("accounts:csrf")).json()["data"]["csrf_token"]
        response = client.post(
            self.login_url,
            {"username": "student-123", "password": "test-password"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.post(reverse("accounts:logout")).status_code, 403)
        self.assertEqual(client.get(reverse("accounts:me")).status_code, 200)
        token = client.get(reverse("accounts:csrf")).json()["data"]["csrf_token"]
        response = client.post(reverse("accounts:logout"), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get(reverse("accounts:me")).status_code, 401)

    def test_expired_session_cannot_read_me_or_be_replayed(self):
        self.post_login()
        session_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 200)
        Session.objects.filter(session_key=session_key).update(
            expire_date=timezone.now() - timedelta(seconds=1)
        )
        self.api.reset_mock()
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTH_REQUIRED")
        replay = Client()
        replay.cookies[settings.SESSION_COOKIE_NAME] = session_key
        self.assertEqual(replay.get(reverse("accounts:me")).status_code, 401)
        self.api.assert_not_called()

    def test_login_rotates_preexisting_anonymous_session(self):
        session = self.client.session
        session["before_login"] = True
        session.save()
        old_key = session.session_key
        self.assertEqual(self.post_login().status_code, 200)
        new_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertNotEqual(new_key, old_key)
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_university_session_expires_24_hours_after_login_without_extension(self):
        before = timezone.now()
        response = self.post_login()
        after = timezone.now()
        self.assertEqual(response.status_code, 200)
        session_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        session = Session.objects.get(session_key=session_key)
        self.assertGreaterEqual(session.expire_date, before + timedelta(hours=24))
        self.assertLessEqual(session.expire_date, after + timedelta(hours=24))
        expiry = session.expire_date
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code, 200)
        session.refresh_from_db()
        self.assertEqual(session.expire_date, expiry)
