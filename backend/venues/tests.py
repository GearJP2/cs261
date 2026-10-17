from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from parties.models import Party

from .models import Sport, Venue, VenueOpeningHour, VenueSport


class VenueSchemaTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Court A", location_text="Gym")
        self.sport = Sport.objects.create(name="Badminton")

    def test_venue_and_sport_must_be_unique(self):
        VenueSport.objects.create(venue=self.venue, sport=self.sport)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VenueSport.objects.create(venue=self.venue, sport=self.sport)
        other_sport = Sport.objects.create(name="Basketball")
        VenueSport.objects.create(venue=self.venue, sport=other_sport)
        self.assertEqual(VenueSport.objects.count(), 2)

    def test_weekday_outside_zero_to_six_is_rejected(self):
        for weekday in (-1, 7):
            with self.subTest(weekday=weekday):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        VenueOpeningHour.objects.create(
                            venue=self.venue,
                            weekday=weekday,
                            opens_at=time(9),
                            closes_at=time(18),
                        )
        self.assertEqual(VenueOpeningHour.objects.count(), 0)

    def test_closing_time_must_be_after_opening_time(self):
        for closes_at in (time(8), time(9)):
            with self.subTest(closes_at=closes_at):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        VenueOpeningHour.objects.create(
                            venue=self.venue,
                            weekday=0,
                            opens_at=time(9),
                            closes_at=closes_at,
                        )

    def test_valid_opening_hours_allow_weekday_boundaries(self):
        for weekday in (0, 6):
            VenueOpeningHour.objects.create(
                venue=self.venue,
                weekday=weekday,
                opens_at=time(9),
                closes_at=time(18),
            )
        self.assertEqual(VenueOpeningHour.objects.count(), 2)

    def test_sport_name_is_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Sport.objects.create(name=self.sport.name)

    def test_join_and_opening_hour_foreign_keys_reject_missing_parents(self):
        invalid_rows = (
            (VenueSport, {"venue_id": 999999999, "sport": self.sport}),
            (VenueSport, {"venue": self.venue, "sport_id": 999999999}),
            (
                VenueOpeningHour,
                {"venue_id": 999999999, "weekday": 0, "opens_at": time(9), "closes_at": time(18)},
            ),
        )
        for model, values in invalid_rows:
            with self.subTest(model=model.__name__, values=values):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    model.objects.create(**values)
                    # PostgreSQL checks these FKs at transaction end unless forced here.
                    connection.check_constraints()

    def test_multiple_intervals_and_same_start_on_other_day_or_venue_are_allowed(self):
        other_venue = Venue.objects.create(name="Court B", location_text="Outdoor")
        for venue, weekday, start, end in (
            (self.venue, 0, time(9), time(12)),
            (self.venue, 0, time(13), time(18)),
            (self.venue, 1, time(9), time(12)),
            (other_venue, 0, time(9), time(12)),
        ):
            VenueOpeningHour.objects.create(
                venue=venue, weekday=weekday, opens_at=start, closes_at=end
            )
        self.assertEqual(VenueOpeningHour.objects.count(), 4)


class VenueDeletionAndValidationTests(TestCase):
    def setUp(self):
        self.sport = Sport.objects.create(name="Badminton")
        self.venue = Venue.objects.create(name="สนามกีฬา", location_text="TU Rangsit")

    def test_deleting_venue_cascades_venue_sport(self):
        link = VenueSport.objects.create(venue=self.venue, sport=self.sport)

        self.venue.delete()

        self.assertFalse(VenueSport.objects.filter(pk=link.pk).exists())

    def test_sport_referenced_by_venue_cannot_be_deleted(self):
        VenueSport.objects.create(venue=self.venue, sport=self.sport)
        with self.assertRaises(ProtectedError):
            self.sport.delete()
        self.assertTrue(Sport.objects.filter(pk=self.sport.pk).exists())

    def test_party_protects_its_venue_and_sport_even_without_a_mapping(self):
        host = get_user_model().objects.create_user(username="venue-host")
        start = timezone.now() + timedelta(days=1)
        party = Party.objects.create(
            host=host,
            sport=self.sport,
            venue=self.venue,
            title="Venue history",
            starts_at=start,
            ends_at=start + timedelta(hours=1),
            capacity=2,
        )
        for parent in (self.venue, self.sport):
            with self.subTest(parent=type(parent).__name__):
                with self.assertRaises(ProtectedError):
                    parent.delete()
        self.assertTrue(Party.objects.filter(pk=party.pk).exists())

    def test_deleting_unreferenced_venue_cascades_opening_hours(self):
        hour = VenueOpeningHour.objects.create(
            venue=self.venue, weekday=0, opens_at=time(9), closes_at=time(18)
        )
        self.venue.delete()
        self.assertFalse(VenueOpeningHour.objects.filter(pk=hour.pk).exists())

    def test_opening_hour_start_is_unique_per_venue_and_weekday(self):
        VenueOpeningHour.objects.create(
            venue=self.venue,
            weekday=0,
            opens_at=time(9, 0),
            closes_at=time(12, 0),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            VenueOpeningHour.objects.create(
                venue=self.venue,
                weekday=0,
                opens_at=time(9, 0),
                closes_at=time(13, 0),
            )
