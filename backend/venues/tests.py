from datetime import time

from django.db import IntegrityError, transaction
from django.test import TestCase

from venues.models import Sport, Venue, VenueOpeningHour, VenueSport


class VenueSchemaTests(TestCase):
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
