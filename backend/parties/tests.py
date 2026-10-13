from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from venues.models import Sport, Venue

from .models import JoinRequest, Party, PartyMembership


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
