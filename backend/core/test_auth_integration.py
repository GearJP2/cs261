"""BASE-04/US3/US8 integration with US1; only the external TU call is mocked."""

from datetime import timedelta
from unittest.mock import patch

from accounts.models import UniversityIdentity, UserProfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from parties.models import JoinRequest, Party, PartyMembership
from venues.models import Sport, Venue


class UniversityBusinessApiTests(TestCase):
    def setUp(self):
        self.browser = Client(enforce_csrf_checks=True)
        self.provider_patch = patch(
            "accounts.views.call_university_api",
            return_value={
                "status": True,
                "username": "integration-student",
                "displayname_th": "Integration Student",
                "type": "student",
            },
        )
        self.provider = self.provider_patch.start()
        self.addCleanup(self.provider_patch.stop)
        self.login_url = reverse("accounts:login")
        self.logout_url = reverse("accounts:logout")
        response = self.browser.post(
            self.login_url,
            {"username": "integration-student", "password": "fixture-only-password"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token(self.browser),
        )
        self.assertEqual(response.status_code, 200)
        self.user = get_user_model().objects.get(pk=response.json()["data"]["id"])
        self.identity = UniversityIdentity.objects.get(
            pk=self.browser.session["university_identity_id"]
        )
        self.provider.reset_mock()
        self.host = get_user_model().objects.create_user("integration-host")
        now = timezone.now()
        self.party = Party.objects.create(
            host=self.host,
            sport=Sport.objects.create(name="Integration Badminton"),
            venue=Venue.objects.create(name="Integration Court", location_text="Campus"),
            title="Integration Party",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=1),
            capacity=2,
        )
        PartyMembership.objects.create(party=self.party, user=self.host)
        self.me_url = reverse("accounts:me")
        self.detail_url = reverse("party-detail", args=[self.party.pk])
        self.profile_url = reverse("accounts:user-public-profile", args=[self.user.pk])
        self.mine_url = reverse("party-join-request-me", args=[self.party.pk])
        self.create_url = reverse("party-join-request-create", args=[self.party.pk])
        self.read_urls = (self.me_url, self.detail_url, self.profile_url, self.mine_url)

    def csrf_token(self, browser):
        response = browser.get(reverse("accounts:csrf"))
        self.assertEqual(response.status_code, 200)
        return response.json()["data"]["csrf_token"]

    def post_join(self, browser):
        return browser.post(
            self.create_url,
            data="{}",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token(browser),
        )

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(set(response.json()), {"error"})
        self.assertEqual(set(response.json()["error"]), {"code", "message"})
        self.assertEqual(response.json()["error"]["code"], code)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertNotIn("Location", response)

    def assert_all_denied(self, browser, status, code):
        requests_before = list(JoinRequest.objects.order_by("pk").values())
        memberships_before = list(PartyMembership.objects.order_by("pk").values())
        for url in self.read_urls:
            with self.subTest(url=url):
                self.assert_error(browser.get(url), status, code)
        # Valid CSRF ensures this assertion exercises auth, not CSRF rejection.
        self.assert_error(self.post_join(browser), status, code)
        self.assertEqual(list(JoinRequest.objects.order_by("pk").values()), requests_before)
        self.assertEqual(list(PartyMembership.objects.order_by("pk").values()), memberships_before)
        self.provider.assert_not_called()

    def test_login_session_can_read_and_join_without_rechecking_provider(self):
        for url in self.read_urls:
            with self.subTest(url=url):
                response = self.browser.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(self.browser.get(self.mine_url).json(), {"data": None})
        response = self.post_join(self.browser)
        self.assertEqual(response.status_code, 201)
        request = JoinRequest.objects.get()
        self.assertEqual((request.user_id, request.party_id), (self.user.pk, self.party.pk))
        self.assertEqual(request.status, "Pending")
        self.assertEqual(self.browser.get(self.mine_url).json()["data"]["id"], request.pk)
        detail = self.browser.get(self.detail_url).json()["data"]
        self.assertEqual((detail["member_count"], detail["remaining_slots"]), (1, 1))
        self.assertFalse(detail["is_member"])
        self.assertEqual(self.browser.get(self.profile_url).json()["data"]["id"], self.user.pk)
        self.provider.assert_not_called()

    def test_anonymous_session_cannot_access_any_business_api(self):
        self.assert_all_denied(Client(enforce_csrf_checks=True), 401, "AUTH_REQUIRED")

    def test_local_and_admin_login_do_not_replace_university_session(self):
        # Even an account with verified evidence in DB needs the session marker.
        for is_superuser in (False, True):
            with self.subTest(is_superuser=is_superuser):
                self.user.is_staff = is_superuser
                self.user.is_superuser = is_superuser
                self.user.save(update_fields=["is_staff", "is_superuser"])
                local = Client(enforce_csrf_checks=True)
                local.force_login(self.user)
                self.assert_all_denied(local, 403, "FORBIDDEN")
                forged = {
                    "university_identity_id": self.identity.pk,
                    "student_verified": "true",
                    "user_id": self.user.pk,
                }
                for url in self.read_urls:
                    self.assert_error(local.get(url, forged), 403, "FORBIDDEN")
                self.assert_error(
                    local.post(
                        self.create_url,
                        forged,
                        content_type="application/json",
                        HTTP_X_CSRFTOKEN=self.csrf_token(local),
                    ),
                    403,
                    "FORBIDDEN",
                )
                self.assertFalse(JoinRequest.objects.exists())

    def test_invalid_identity_markers_are_denied(self):
        for marker in (None, True, 0, -1, "1", [], {}, self.identity.pk + 999):
            with self.subTest(marker=marker):
                session = self.browser.session
                session["university_identity_id"] = marker
                session.save()
                self.assert_all_denied(self.browser, 403, "FORBIDDEN")

    def test_identity_of_another_verified_user_is_denied(self):
        identity = UniversityIdentity.objects.create(
            user=self.host,
            provider_key="tu",
            subject="other-verified-student",
            student_verified_at=timezone.now(),
            eligibility_checked_at=timezone.now(),
        )
        session = self.browser.session
        session["university_identity_id"] = identity.pk
        session.save()
        self.assert_all_denied(self.browser, 403, "FORBIDDEN")

    def test_revoked_wrong_provider_and_deleted_identity_are_denied(self):
        for change in (
            {"student_verified_at": None},
            {"eligibility_checked_at": None},
            {"provider_key": "other-provider"},
        ):
            with self.subTest(change=change):
                UniversityIdentity.objects.filter(pk=self.identity.pk).update(
                    provider_key="tu",
                    student_verified_at=self.identity.student_verified_at,
                    eligibility_checked_at=self.identity.eligibility_checked_at,
                )
                UniversityIdentity.objects.filter(pk=self.identity.pk).update(**change)
                self.assert_all_denied(self.browser, 403, "FORBIDDEN")
        self.identity.delete()
        self.assert_all_denied(self.browser, 403, "FORBIDDEN")

    def test_disabling_account_invalidates_previously_valid_session(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        # ModelBackend resolves inactive sessions as anonymous, matching US1.
        self.assert_all_denied(self.browser, 401, "AUTH_REQUIRED")

    def test_logout_revokes_access_in_original_and_copied_browser(self):
        self.assertEqual(self.post_join(self.browser).status_code, 201)
        old_key = self.browser.cookies[settings.SESSION_COOKIE_NAME].value
        copied = Client(enforce_csrf_checks=True)
        copied.cookies[settings.SESSION_COOKIE_NAME] = old_key
        response = self.browser.post(
            self.logout_url,
            data="{}",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token(self.browser),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())
        self.assert_all_denied(self.browser, 401, "AUTH_REQUIRED")
        self.assert_all_denied(copied, 401, "AUTH_REQUIRED")
        self.assertEqual(JoinRequest.objects.get().status, "Pending")

    def test_expired_login_session_is_denied(self):
        Session.objects.filter(session_key=self.browser.session.session_key).update(
            expire_date=timezone.now() - timedelta(seconds=1)
        )
        self.assert_all_denied(self.browser, 401, "AUTH_REQUIRED")

    def test_university_session_still_requires_csrf_for_join(self):
        for headers in (
            {},
            {"HTTP_X_CSRFTOKEN": "invalid"},
            {
                "HTTP_X_CSRFTOKEN": self.csrf_token(self.browser),
                "HTTP_ORIGIN": "https://untrusted.invalid",
            },
        ):
            with self.subTest(headers=headers):
                response = self.browser.post(
                    self.create_url, data="{}", content_type="application/json", **headers
                )
                self.assert_error(response, 403, "CSRF_FAILED")
                self.assertFalse(JoinRequest.objects.exists())
        self.assertEqual(self.post_join(self.browser).status_code, 201)

    def test_guard_rejects_before_lookup_of_missing_resources(self):
        self.browser.session.flush()
        self.browser.force_login(self.user)
        for name in ("party-detail", "party-join-request-me", "accounts:user-public-profile"):
            with self.subTest(name=name):
                self.assert_error(
                    self.browser.get(reverse(name, args=[999999999])), 403, "FORBIDDEN"
                )
        self.create_url = reverse("party-join-request-create", args=[999999999])
        self.assert_error(self.post_join(self.browser), 403, "FORBIDDEN")

    def test_rejected_university_login_does_not_grant_business_access(self):
        for result, expected_status in (
            ({"status": False}, 401),
            ({**self.provider.return_value, "type": "staff"}, 403),
        ):
            with self.subTest(result=result):
                browser = Client(enforce_csrf_checks=True)
                self.provider.return_value = result
                response = browser.post(
                    self.login_url,
                    {"username": "rejected", "password": "fixture-only"},
                    content_type="application/json",
                    HTTP_X_CSRFTOKEN=self.csrf_token(browser),
                )
                self.assertEqual(response.status_code, expected_status)
                self.provider.assert_called_once()
                self.provider.reset_mock()
                self.assert_all_denied(browser, 401, "AUTH_REQUIRED")
        self.assertEqual(UserProfile.objects.count(), 1)
