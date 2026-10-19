from datetime import time
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from venues.models import Sport, Venue, VenueOpeningHour, VenueSport
from venues.venue_catalog import VENUES, location_label


@override_settings(DEBUG=True)
class SeedVenuesTests(TestCase):
    def seed(self):
        output = StringIO()
        call_command("seed_venues", stdout=output)
        return output.getvalue()

    def test_published_hours_are_seeded_for_badminton_and_swimming(self):
        self.seed()
        for name, days, start in (
            ("สนามแบดมินตัน ยิมเนเซียม 4", set(range(7)), time(17)),
            ("สนามแบดมินตัน ยิมอินเตอร์โซน", {0, 1, 2, 3, 4, 6}, time(16)),
            ("สระว่ายน้ำ ศูนย์กีฬาทางน้ำ", set(range(7)), time(7)),
        ):
            with self.subTest(venue=name):
                venue = Venue.objects.get(name=name)
                self.assertIn("เวลา: REAL", venue.location_text)
                self.assertEqual(
                    set(venue.opening_hours.values_list("weekday", "opens_at", "closes_at")),
                    {(day, start, time(21)) for day in days},
                )

    def test_mock_hours_are_labeled_in_database_catalog_and_output(self):
        output = self.seed()
        tennis = Venue.objects.get(name="สนามเทนนิส")
        self.assertIn("สถานที่: REAL", tennis.location_text)
        self.assertIn("เวลา: MOCK (เวลาสมมติ)", tennis.location_text)
        self.assertIn("hours=MOCK", output)
        self.assertIn("hours=REAL", output)
        self.assertEqual(
            set(tennis.opening_hours.values_list("weekday", "opens_at", "closes_at")),
            {(day, time(16), time(21)) for day in range(6)},
        )
        self.assertFalse(tennis.opening_hours.filter(weekday=6).exists())
        self.assertEqual(Venue.objects.filter(location_text__contains="เวลา: MOCK").count(), 7)
        for record in VENUES:
            self.assertEqual(record["venue_kind"], "REAL")
            self.assertTrue(record["venue_source"].startswith("https://psm.tu.ac.th/"))
            self.assertLessEqual(len(location_label(record)), 255)
            if record["hours_kind"] == "MOCK":
                self.assertIsNone(record["hours_source"])
            else:
                self.assertTrue(record["hours_source"])

    def test_rerun_restores_catalog_without_duplicate_parent_ids(self):
        self.seed()
        sport_ids = list(Sport.objects.order_by("pk").values_list("pk", flat=True))
        venue_ids = list(Venue.objects.order_by("pk").values_list("pk", flat=True))
        venue = Venue.objects.get(name="สนามเทนนิส")
        venue.is_active = False
        venue.save()
        venue.opening_hours.all().delete()
        venue.venue_sports.all().delete()
        self.seed()
        self.assertEqual(list(Sport.objects.order_by("pk").values_list("pk", flat=True)), sport_ids)
        self.assertEqual(list(Venue.objects.order_by("pk").values_list("pk", flat=True)), venue_ids)
        venue.refresh_from_db()
        self.assertTrue(venue.is_active)
        self.assertEqual(Sport.objects.count(), 9)
        self.assertEqual(Venue.objects.count(), 10)
        self.assertEqual(VenueSport.objects.count(), 10)
        self.assertEqual(VenueOpeningHour.objects.count(), 62)

    def test_unrelated_and_base03_configuration_is_untouched(self):
        sport = Sport.objects.create(name="[BASE-03] Badminton")
        venue = Venue.objects.create(name="[BASE-03] Open venue", location_text="Other fixture")
        link = VenueSport.objects.create(venue=venue, sport=sport)
        hour = VenueOpeningHour.objects.create(
            venue=venue, weekday=6, opens_at=time(8), closes_at=time(17)
        )
        self.seed()
        self.seed()
        self.assertTrue(VenueSport.objects.filter(pk=link.pk).exists())
        self.assertTrue(VenueOpeningHour.objects.filter(pk=hour.pk).exists())
        venue.refresh_from_db()
        self.assertEqual(venue.location_text, "Other fixture")

    def test_name_collision_rolls_back_all_seed_changes(self):
        Venue.objects.create(name="สนามเทนนิส", location_text="User-owned data")
        with self.assertRaisesMessage(CommandError, "collision"):
            self.seed()
        self.assertEqual(Venue.objects.count(), 1)
        self.assertEqual(Sport.objects.count(), 0)
        self.assertEqual(VenueSport.objects.count(), 0)
        self.assertEqual(VenueOpeningHour.objects.count(), 0)

    def test_duplicate_reserved_venue_names_are_rejected(self):
        record = VENUES[0]
        for _ in range(2):
            Venue.objects.create(name=record["name"], location_text=location_label(record))
        with self.assertRaisesMessage(CommandError, "collision"):
            self.seed()
        self.assertEqual(Venue.objects.count(), 2)
        self.assertEqual(Sport.objects.count(), 0)

    @override_settings(DEBUG=False)
    def test_disabled_outside_development(self):
        with self.assertRaisesMessage(CommandError, "DEBUG=true"):
            self.seed()
        self.assertEqual(Sport.objects.count(), 0)
        self.assertEqual(Venue.objects.count(), 0)
