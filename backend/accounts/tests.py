from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.db import IntegrityError, transaction
from django.test import TestCase
from venues.models import Sport

from accounts.models import UniversityIdentity, UserProfile, UserSportInterest


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
    def create_user(self, username):
        return get_user_model().objects.create_user(username, password="test-only-password")

    def test_university_identity_is_unique_per_provider_subject(self):
        first_user = self.create_user("identity-first")
        second_user = self.create_user("identity-second")
        UniversityIdentity.objects.create(
            user=first_user,
            provider_key="tu-sso",
            subject="student-123",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            UniversityIdentity.objects.create(
                user=second_user,
                provider_key="tu-sso",
                subject="student-123",
            )

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
