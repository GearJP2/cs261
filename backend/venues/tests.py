from datetime import time

from django.db import IntegrityError, transaction
from django.test import TestCase

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


class VenueDeletionAndValidationTests(TestCase):
    def setUp(self):
        self.sport = Sport.objects.create(name="Badminton")
        self.venue = Venue.objects.create(name="สนามกีฬา", location_text="TU Rangsit")

    def test_venue_sport_is_unique_and_is_removed_with_venue(self):
        link = VenueSport.objects.create(venue=self.venue, sport=self.sport)

        with self.assertRaises(IntegrityError), transaction.atomic():
            VenueSport.objects.create(venue=self.venue, sport=self.sport)

        venue_id = self.venue.id
        self.venue.delete()
        self.assertFalse(VenueSport.objects.filter(pk=link.pk, venue_id=venue_id).exists())

    def test_opening_hour_rejects_invalid_weekday_and_time_range(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            VenueOpeningHour.objects.create(
                venue=self.venue,
                weekday=7,
                opens_at=time(9, 0),
                closes_at=time(10, 0),
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            VenueOpeningHour.objects.create(
                venue=self.venue,
                weekday=0,
                opens_at=time(10, 0),
                closes_at=time(10, 0),
            )

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
