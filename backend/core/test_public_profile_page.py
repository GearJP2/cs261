"""US8 public profile page uses the same public fields as the API contract."""

from accounts.models import UserProfile, UserSportInterest
from accounts.test_support import force_university_login
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from venues.models import Sport


class PublicProfilePageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.viewer = users.objects.create_user("profile-viewer")
        UserProfile.objects.create(user=cls.viewer, display_name="ผู้เข้าชม", credit_score=0)

        cls.target = users.objects.create_user("private-login", email="private@example.invalid")
        UserProfile.objects.create(user=cls.target, display_name="เพื่อนนักกีฬา", credit_score=75)
        cls.badminton = Sport.objects.create(name="Badminton")
        cls.basketball = Sport.objects.create(name="Basketball")
        UserSportInterest.objects.create(user=cls.target, sport=cls.basketball)
        UserSportInterest.objects.create(user=cls.target, sport=cls.badminton)

        cls.empty = users.objects.create_user("profile-empty")
        UserProfile.objects.create(user=cls.empty, display_name="ยังไม่เลือกกีฬา")
        cls.no_profile = users.objects.create_user("profile-missing")

    def setUp(self):
        force_university_login(self.client, self.viewer)

    def profile_url(self, user):
        return reverse("public-profile-page", args=[user.pk])

    def test_renders_only_requested_users_public_profile_fields(self):
        response = self.client.get(self.profile_url(self.target))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "เพื่อนนักกีฬา")
        self.assertContains(response, "75 คะแนน")
        self.assertContains(response, "Badminton")
        self.assertContains(response, "Basketball")
        self.assertNotContains(response, self.target.username)
        self.assertNotContains(response, self.target.email)
        self.assertContains(response, 'href="/"')

    def test_empty_interests_and_unknown_credit_have_explicit_empty_states(self):
        response = self.client.get(self.profile_url(self.empty))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ไม่มีคะแนน")
        self.assertContains(response, "ยังไม่ได้ระบุกีฬาที่สนใจ")
        self.assertNotContains(response, 'class="profile-tags"')

    def test_missing_profile_renders_not_found_page_without_creating_data(self):
        profiles_before = UserProfile.objects.count()
        response = self.client.get(self.profile_url(self.no_profile))

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "ไม่พบผู้ใช้", status_code=404)
        self.assertEqual(UserProfile.objects.count(), profiles_before)

    def test_anonymous_user_cannot_read_profile_page(self):
        self.client.logout()

        response = self.client.get(self.profile_url(self.target))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTH_REQUIRED")

    def test_profile_page_allows_only_get(self):
        response = self.client.post(self.profile_url(self.target))

        self.assertEqual(response.status_code, 405)
