from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.db import IntegrityError, transaction
from django.test import TestCase
from venues.models import Sport

from .models import UniversityIdentity, UserProfile, UserSportInterest
from .services import get_or_create_university_user


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
        sport = self.sport
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
