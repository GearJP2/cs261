from datetime import datetime, time, timedelta
from datetime import timezone as dt_timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from venues.models import Sport, Venue, VenueOpeningHour, VenueSport
from venues.services import ScheduleValidationError, validate_party_schedule

from .models import Party, PartyMembership
from .services import PartyError, create_party


class PartyCreationTests(TestCase):
    def setUp(self):
        self.host = get_user_model().objects.create_user(username="creation-host")
        self.sport = Sport.objects.create(name="Badminton")
        self.venue = Venue.objects.create(name="Court A", location_text="Gym")
        VenueSport.objects.create(venue=self.venue, sport=self.sport)
        self.start = datetime(2030, 1, 7, 9, tzinfo=ZoneInfo("Asia/Bangkok"))
        for opens, closes in ((9, 12), (13, 18)):
            VenueOpeningHour.objects.create(
                venue=self.venue,
                weekday=self.start.weekday(),
                opens_at=time(opens),
                closes_at=time(closes),
            )
        self.data = dict(
            user=self.host,
            title=" Practice ",
            description="",
            sport_id=self.sport.pk,
            venue_id=self.venue.pk,
            starts_at=self.start,
            ends_at=self.start + timedelta(hours=3),
            capacity=1,
        )

    def test_creation_counts_host_and_allows_exact_opening_boundaries(self):
        party = create_party(**self.data)
        self.assertEqual(party.title, "Practice")
        membership = party.memberships.get()
        self.assertEqual(membership.user, self.host)
        self.assertIsNone(membership.left_at)
        self.assertEqual(party.capacity - party.memberships.count(), 0)

    def test_membership_failure_rolls_back_party(self):
        with patch("parties.services.PartyMembership.objects.create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                create_party(**self.data)
        self.assertFalse(Party.objects.exists())
        self.assertFalse(PartyMembership.objects.exists())

    def test_invalid_basic_fields_do_not_write(self):
        for changes in (
            {"title": " "},
            {"title": "x" * 151},
            {"description": None},
            {"description": "x" * 2001},
            {"capacity": True},
            {"capacity": 0},
            {"capacity": "2"},
            {"starts_at": self.start.replace(tzinfo=None)},
            {"ends_at": "2030-01-07"},
            {"ends_at": self.start},
            {"starts_at": timezone.now() - timedelta(days=1)},
        ):
            with self.subTest(changes=changes), self.assertRaises(PartyError):
                create_party(**(self.data | changes))
        self.assertFalse(Party.objects.exists())

    def test_invalid_schedules_do_not_write(self):
        for changes in (
            {"starts_at": self.start - timedelta(minutes=1)},
            {"ends_at": self.start.replace(hour=18, minute=1)},
            {"ends_at": self.start.replace(hour=14)},  # crosses lunch break
            {"ends_at": self.start + timedelta(days=1)},
            {
                "starts_at": self.start + timedelta(days=1),
                "ends_at": self.start + timedelta(days=1, hours=1),
            },  # closed day
            {"venue_id": True},
            {"sport_id": "1"},
            {"venue_id": self.venue.pk + 1000},
            {"sport_id": self.sport.pk + 1000},
        ):
            with self.subTest(changes=changes), self.assertRaises(PartyError):
                create_party(**(self.data | changes))
        self.assertFalse(Party.objects.exists())

    def test_inactive_and_unsupported_venues_are_rejected(self):
        self.venue.is_active = False
        self.venue.save()
        with self.assertRaises(PartyError):
            create_party(**self.data)
        self.venue.is_active = True
        self.venue.save()
        VenueSport.objects.all().delete()
        with self.assertRaises(PartyError):
            create_party(**self.data)
        self.assertFalse(Party.objects.exists())

    def test_schedule_uses_bangkok_day_even_for_utc_input_and_timezone_override(self):
        with timezone.override("America/New_York"):
            validate_party_schedule(
                self.sport.pk,
                self.venue.pk,
                self.start.astimezone(dt_timezone.utc),
                (self.start + timedelta(hours=3)).astimezone(dt_timezone.utc),
            )

    def test_standalone_schedule_rejects_naive_time(self):
        with self.assertRaises(ScheduleValidationError) as caught:
            validate_party_schedule(
                self.sport.pk,
                self.venue.pk,
                self.start.replace(tzinfo=None),
                self.start,
            )
        self.assertEqual(caught.exception.code, "INVALID_TIME_RANGE")
