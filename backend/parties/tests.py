from datetime import timedelta

from accounts.models import UniversityIdentity, UserProfile
from accounts.test_support import force_university_login
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from venues.models import Sport, Venue

from .models import JoinRequest, Party, PartyMembership
from .services import count_active_members, get_party_state


class PartySchemaTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.host = users.objects.create_user(username="host")
        self.member = users.objects.create_user(username="member")
        self.decider = users.objects.create_user(username="decider")
        self.sport = Sport.objects.create(name="Badminton")
        self.venue = Venue.objects.create(name="Court A", location_text="Gym")
        self.starts_at = timezone.now() + timedelta(days=1)
        self.party = self.create_party()

    def create_party(self, **overrides):
        fields = {
            "host": self.host,
            "sport": self.sport,
            "venue": self.venue,
            "title": "Practice",
            "starts_at": self.starts_at,
            "ends_at": self.starts_at + timedelta(hours=1),
            "capacity": 6,
        }
        fields.update(overrides)
        return Party.objects.create(**fields)

    def test_capacity_below_one_is_rejected(self):
        for capacity in (0, -1):
            with self.subTest(capacity=capacity):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        self.create_party(capacity=capacity)
        self.create_party(capacity=1)
        self.assertEqual(Party.objects.count(), 2)

    def test_end_time_must_be_after_start_time(self):
        for ends_at in (self.starts_at, self.starts_at - timedelta(seconds=1)):
            with self.subTest(ends_at=ends_at):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        self.create_party(ends_at=ends_at)

    def test_membership_pair_must_be_unique_even_after_leaving(self):
        membership = PartyMembership.objects.create(party=self.party, user=self.member)
        for left_at in (None, timezone.now()):
            membership.left_at = left_at
            membership.save(update_fields=["left_at"])
            with self.subTest(left_at=left_at):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        PartyMembership.objects.create(party=self.party, user=self.member)
        PartyMembership.objects.create(party=self.party, user=self.host)
        self.assertEqual(PartyMembership.objects.count(), 2)

    def test_join_request_pair_must_be_unique(self):
        JoinRequest.objects.create(party=self.party, user=self.member)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                JoinRequest.objects.create(party=self.party, user=self.member)
        JoinRequest.objects.create(party=self.party, user=self.host)
        self.assertEqual(JoinRequest.objects.count(), 2)

    def test_pending_cannot_have_decision_time_or_decider(self):
        for fields in (
            {"decided_at": timezone.now()},
            {"decided_by": self.decider},
            {"decided_at": timezone.now(), "decided_by": self.decider},
        ):
            with self.subTest(fields=fields):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        JoinRequest.objects.create(
                            party=self.party,
                            user=self.member,
                            status=JoinRequest.Status.PENDING,
                            **fields,
                        )
        request = JoinRequest.objects.create(party=self.party, user=self.member)
        self.assertEqual(request.status, JoinRequest.Status.PENDING)
        self.assertIsNone(request.decided_at)
        self.assertIsNone(request.decided_by_id)

    def test_decided_requests_require_decision_time(self):
        for status in (JoinRequest.Status.APPROVED, JoinRequest.Status.REJECTED):
            for decided_by in (None, self.decider):
                with self.subTest(status=status, decided_by=decided_by):
                    with self.assertRaises(IntegrityError):
                        with transaction.atomic():
                            JoinRequest.objects.create(
                                party=self.party,
                                user=self.member,
                                status=status,
                                decided_by=decided_by,
                            )

    def test_decided_requests_can_store_both_decision_fields(self):
        for status in (JoinRequest.Status.APPROVED, JoinRequest.Status.REJECTED):
            with self.subTest(status=status):
                request = JoinRequest.objects.create(
                    party=self.party,
                    user=self.member,
                    status=status,
                    decided_at=timezone.now(),
                    decided_by=self.decider,
                )
                request.refresh_from_db()
                self.assertIsNotNone(request.decided_at)
                self.assertEqual(request.decided_by_id, self.decider.pk)
                request.delete()

    def test_decided_requests_allow_null_decider_under_current_policy(self):
        # SET_NULL requires the database to allow a missing decider.
        for status in (JoinRequest.Status.APPROVED, JoinRequest.Status.REJECTED):
            with self.subTest(status=status):
                request = JoinRequest.objects.create(
                    party=self.party,
                    user=self.member,
                    status=status,
                    decided_at=timezone.now(),
                    decided_by=None,
                )
                request.refresh_from_db()
                self.assertIsNone(request.decided_by_id)
                request.delete()

    def test_deleting_decider_preserves_decision_history(self):
        other_member = get_user_model().objects.create_user(username="other-member")
        requests = [
            JoinRequest.objects.create(
                party=self.party,
                user=user,
                status=status,
                decided_at=timezone.now(),
                decided_by=self.decider,
            )
            for user, status in (
                (self.member, JoinRequest.Status.APPROVED),
                (other_member, JoinRequest.Status.REJECTED),
            )
        ]
        original_times = [request.decided_at for request in requests]
        self.decider.delete()
        for request, decided_at in zip(requests, original_times, strict=True):
            request.refresh_from_db()
            self.assertIsNone(request.decided_by_id)
            self.assertEqual(request.decided_at, decided_at)
        self.assertEqual(JoinRequest.objects.count(), 2)


class PartyDeletionAndValidationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.host = user_model.objects.create_user("party-host", password="test-only-password")
        self.member = user_model.objects.create_user("party-member", password="test-only-password")
        self.sport = Sport.objects.create(name="Basketball")
        self.venue = Venue.objects.create(name="Gym", location_text="TU Rangsit")
        starts_at = timezone.now() + timedelta(days=1)
        self.party = Party.objects.create(
            host=self.host,
            sport=self.sport,
            venue=self.venue,
            title="Evening basketball",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            capacity=4,
        )

    def test_deleting_party_cascades_memberships_and_join_requests(self):
        membership = PartyMembership.objects.create(party=self.party, user=self.member)
        request = JoinRequest.objects.create(party=self.party, user=self.host)

        self.party.delete()

        self.assertFalse(PartyMembership.objects.filter(pk=membership.pk).exists())
        self.assertFalse(JoinRequest.objects.filter(pk=request.pk).exists())

    def test_user_with_membership_cannot_be_deleted(self):
        PartyMembership.objects.create(party=self.party, user=self.member)

        with self.assertRaises(ProtectedError):
            self.member.delete()


class PartyDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.host = users.objects.create_user("private-host-login", email="private@example.com")
        UserProfile.objects.create(user=cls.host, display_name="ชื่อสาธารณะ")
        UniversityIdentity.objects.create(
            user=cls.host, provider_key="private-provider", subject="private-subject"
        )
        cls.member = users.objects.create_user("member")
        cls.former_member = users.objects.create_user("former-member")
        cls.pending = users.objects.create_user("pending")
        cls.rejected = users.objects.create_user("rejected")
        cls.outsider = users.objects.create_user("outsider")
        cls.sport = Sport.objects.create(name="Badminton")
        cls.venue = Venue.objects.create(name="Court A", location_text="Gym")
        cls.now = timezone.now()
        cls.party = Party.objects.create(
            host=cls.host,
            sport=cls.sport,
            venue=cls.venue,
            title="เล่นแบดมินตัน",
            description="เล่นด้วยกันหลังเลิกเรียน",
            starts_at=cls.now + timedelta(days=1),
            ends_at=cls.now + timedelta(days=1, hours=2),
            capacity=4,
        )
        PartyMembership.objects.create(party=cls.party, user=cls.host)
        PartyMembership.objects.create(party=cls.party, user=cls.member)
        PartyMembership.objects.create(party=cls.party, user=cls.former_member, left_at=cls.now)
        JoinRequest.objects.create(party=cls.party, user=cls.pending)
        JoinRequest.objects.create(
            party=cls.party,
            user=cls.rejected,
            status=JoinRequest.Status.REJECTED,
            decided_at=cls.now,
            decided_by=cls.host,
        )

    def setUp(self):
        self.url = reverse("party-detail", kwargs={"party_id": self.party.pk})

    def test_anonymous_request_is_json_401_even_with_forged_user_parameters(self):
        response = self.client.get(self.url, {"user_id": self.host.pk, "host_id": self.host.pk})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"error": {"code": "AUTH_REQUIRED", "message": "กรุณาเข้าสู่ระบบ"}},
        )
        self.assertNotIn("Location", response)

    def test_detail_has_exact_public_contract_and_ignores_forged_actor(self):
        force_university_login(self.client, self.outsider)
        response = self.client.get(self.url, {"user_id": self.host.pk, "host_id": self.host.pk})
        self.assertEqual(self.url, f"/api/v1/parties/{self.party.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "id": self.party.pk,
                    "title": self.party.title,
                    "description": self.party.description,
                    "host": {"id": self.host.pk, "display_name": "ชื่อสาธารณะ"},
                    "sport_id": self.sport.pk,
                    "venue_id": self.venue.pk,
                    "starts_at": timezone.localtime(self.party.starts_at).isoformat(),
                    "ends_at": timezone.localtime(self.party.ends_at).isoformat(),
                    "capacity": 4,
                    "member_count": 2,
                    "remaining_slots": 2,
                    "state": "Open",
                    "is_host": False,
                    "is_member": False,
                }
            },
        )
        self.assertIn("no-store", response["Cache-Control"])

    def test_membership_flags_follow_the_session_and_current_membership(self):
        for user, is_host, is_member in (
            (self.host, True, True),
            (self.member, False, True),
            (self.former_member, False, False),
            (self.pending, False, False),
            (self.rejected, False, False),
        ):
            with self.subTest(user=user.username):
                force_university_login(self.client, user)
                data = self.client.get(self.url).json()["data"]
                self.assertEqual(data["is_host"], is_host)
                self.assertEqual(data["is_member"], is_member)
                self.assertEqual(data["member_count"], 2)
                self.assertEqual(data["remaining_slots"], 2)

    def test_missing_party_returns_json_404(self):
        force_university_login(self.client, self.outsider)
        response = self.client.get(reverse("party-detail", kwargs={"party_id": self.party.pk + 1}))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"error": {"code": "NOT_FOUND", "message": "ไม่พบกิจกรรมที่ต้องการ"}},
        )

    def test_missing_profile_uses_generic_label_without_exposing_login(self):
        self.host.profile.delete()
        force_university_login(self.client, self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["host"]["display_name"], "ผู้จัดกิจกรรม")
        self.assertNotContains(response, self.host.username)
        self.assertNotContains(response, self.host.email)

    def test_unsupported_methods_do_not_change_party(self):
        force_university_login(self.client, self.host)
        for method in ("post", "put", "patch", "delete", "options"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response.json()["error"]["code"], "METHOD_NOT_ALLOWED")
                self.assertEqual(response["Allow"], "GET")
        self.party.refresh_from_db()
        self.assertIsNone(self.party.cancelled_at)
        self.assertEqual(count_active_members(self.party), 2)

    def test_revoked_or_deactivated_session_cannot_read_party(self):
        force_university_login(self.client, self.outsider)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 401)
        force_university_login(self.client, self.outsider)
        self.outsider.is_active = False
        self.outsider.save(update_fields=["is_active"])
        # Django's default ModelBackend resolves an inactive session to anonymous.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "AUTH_REQUIRED")

    def test_full_party_response_has_consistent_state_and_remaining_slots(self):
        self.party.capacity = 2
        self.party.save(update_fields=["capacity"])
        force_university_login(self.client, self.outsider)
        data = self.client.get(self.url).json()["data"]
        self.assertEqual(data["state"], "Full")
        self.assertEqual(data["member_count"], 2)
        self.assertEqual(data["remaining_slots"], 0)

    def test_state_service_precedence_and_time_boundaries(self):
        self.assertEqual(count_active_members(self.party), 2)
        self.assertEqual(get_party_state(self.party, self.now), "Open")
        self.party.capacity = 2
        self.assertEqual(get_party_state(self.party, self.now), "Full")
        self.assertEqual(
            get_party_state(self.party, self.party.starts_at - timedelta(microseconds=1)), "Full"
        )
        self.assertEqual(get_party_state(self.party, self.party.starts_at), "InProgress")
        self.assertEqual(
            get_party_state(self.party, self.party.ends_at - timedelta(microseconds=1)),
            "InProgress",
        )
        self.assertEqual(get_party_state(self.party, self.party.ends_at), "Completed")
        self.party.cancelled_at = self.now
        self.assertEqual(get_party_state(self.party, self.party.ends_at), "Cancelled")
