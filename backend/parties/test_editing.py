from datetime import time, timedelta
from unittest.mock import patch

from django.test import TestCase
from venues.models import Venue, VenueOpeningHour, VenueSport

from .models import PartyMembership
from .services import PartyError, cancel_party, edit_party, submit_join_request
from .test_join_requests import JoinRequestFixture


class EditPartyTests(JoinRequestFixture, TestCase):
    def setUp(self):
        super().setUp()
        # Fix the schedule within one opening interval regardless of current time.
        self.party.starts_at = (self.now + timedelta(days=2)).replace(
            hour=10,
            minute=0,
            second=0,
            microsecond=0,
        )
        self.party.ends_at = self.party.starts_at + timedelta(hours=1)
        self.party.save()
        VenueSport.objects.create(venue=self.party.venue, sport=self.party.sport)
        VenueOpeningHour.objects.create(
            venue=self.party.venue,
            weekday=self.party.starts_at.weekday(),
            opens_at=time(0),
            closes_at=time(23, 59),
        )

    def edit(self, changes, user=None):
        return edit_party(party_id=self.party.pk, user=user or self.host, changes=changes)

    def test_partial_edit_preserves_memberships_and_pending(self):
        pending = submit_join_request(party_id=self.party.pk, user=self.applicant)
        updated = self.edit({"title": " New name ", "capacity": 3})
        self.assertEqual(updated.title, "New name")
        self.assertEqual(updated.starts_at, self.party.starts_at)
        self.assertEqual(updated.capacity, 3)
        pending.refresh_from_db()
        self.assertEqual(pending.status, "Pending")
        self.assertEqual(updated.memberships.count(), 1)
        self.assertEqual(updated.host_id, self.host.pk)

    def test_capacity_uses_active_members_only_and_full_party_is_editable(self):
        PartyMembership.objects.create(party=self.party, user=self.applicant)
        self.assertEqual(self.edit({"capacity": 2}).capacity, 2)
        with self.assertRaises(PartyError) as caught:
            self.edit({"capacity": 1})
        self.assertEqual(caught.exception.code, "CAPACITY_TOO_SMALL")
        self.party.refresh_from_db()
        self.assertEqual(self.party.capacity, 2)
        self.party.memberships.filter(user=self.applicant).update(left_at=self.now)
        self.assertEqual(self.edit({"capacity": 1}).capacity, 1)

    def test_non_host_and_readonly_fields_are_rejected(self):
        for user in (self.applicant, self.other):
            with self.assertRaises(PartyError) as caught:
                self.edit({"title": "Forged"}, user)
            self.assertEqual((caught.exception.code, caught.exception.status), ("FORBIDDEN", 403))
        for changes in (
            {"host_id": self.other.pk},
            {"cancelled_at": self.now},
            {"state": "Open"},
            [],
        ):
            with self.subTest(changes=changes), self.assertRaises(PartyError):
                self.edit(changes)
        self.party.refresh_from_db()
        self.assertEqual(self.party.title, "After class")

    def test_old_state_cannot_be_bypassed_by_moving_start(self):
        for now in (self.party.starts_at, self.party.ends_at):
            with patch("parties.services.timezone.now", return_value=now):
                with self.assertRaises(PartyError) as caught:
                    self.edit({"starts_at": now + timedelta(days=1)})
            self.assertEqual(caught.exception.code, "PARTY_STARTED")
        cancel_party(party_id=self.party.pk, user=self.host)
        with self.assertRaises(PartyError) as caught:
            self.edit({"title": "Changed"})
        self.assertEqual(caught.exception.code, "PARTY_CANCELLED")

    def test_venue_only_edit_checks_existing_sport_and_schedule(self):
        venue = Venue.objects.create(name="Other", location_text="Campus")
        with self.assertRaises(PartyError):
            self.edit({"venue_id": venue.pk})
        VenueSport.objects.create(venue=venue, sport=self.party.sport)
        with self.assertRaises(PartyError) as caught:
            self.edit({"venue_id": venue.pk})
        self.assertEqual(caught.exception.code, "VENUE_CLOSED")
        self.party.refresh_from_db()
        self.assertNotEqual(self.party.venue_id, venue.pk)

    def test_invalid_candidate_does_not_partially_save(self):
        for changes in (
            {"title": " "},
            {"capacity": True},
            {"description": None},
            {"ends_at": self.party.starts_at},
            {"starts_at": self.now - timedelta(seconds=1)},
        ):
            with self.subTest(changes=changes), self.assertRaises(PartyError):
                self.edit(changes)
        self.party.refresh_from_db()
        self.assertEqual(self.party.title, "After class")
        self.assertEqual(self.party.capacity, 2)

    def test_missing_party_and_empty_patch(self):
        with self.assertRaises(PartyError) as caught:
            edit_party(party_id=self.party.pk + 999, user=self.host, changes={})
        self.assertEqual(caught.exception.status, 404)
        self.assertEqual(self.edit({}).updated_at, self.party.updated_at)
