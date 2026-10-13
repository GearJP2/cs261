from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from venues.models import Sport, Venue

from parties.models import JoinRequest, Party, PartyMembership


class PartySchemaTests(TestCase):
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

    def test_party_rejects_invalid_capacity_and_time_range(self):
        starts_at = timezone.now() + timedelta(days=2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Party.objects.create(
                host=self.host,
                sport=self.sport,
                venue=self.venue,
                title="No capacity",
                starts_at=starts_at,
                ends_at=starts_at + timedelta(hours=1),
                capacity=0,
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Party.objects.create(
                host=self.host,
                sport=self.sport,
                venue=self.venue,
                title="Invalid time",
                starts_at=starts_at,
                ends_at=starts_at,
                capacity=1,
            )

    def test_membership_and_join_request_are_unique_per_party_and_user(self):
        PartyMembership.objects.create(party=self.party, user=self.member)
        JoinRequest.objects.create(party=self.party, user=self.host)

        with self.assertRaises(IntegrityError), transaction.atomic():
            PartyMembership.objects.create(party=self.party, user=self.member)

        with self.assertRaises(IntegrityError), transaction.atomic():
            JoinRequest.objects.create(party=self.party, user=self.host)

    def test_join_request_decision_constraint_and_party_cascade(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            JoinRequest.objects.create(
                party=self.party,
                user=self.member,
                status=JoinRequest.Status.APPROVED,
            )

        membership = PartyMembership.objects.create(party=self.party, user=self.member)
        request = JoinRequest.objects.create(party=self.party, user=self.host)
        self.party.delete()

        self.assertFalse(PartyMembership.objects.filter(pk=membership.pk).exists())
        self.assertFalse(JoinRequest.objects.filter(pk=request.pk).exists())

    def test_user_with_membership_cannot_be_deleted(self):
        PartyMembership.objects.create(party=self.party, user=self.member)

        with self.assertRaises(ProtectedError):
            self.member.delete()
