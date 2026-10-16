from datetime import datetime, timedelta, timezone
from io import StringIO
from unittest.mock import patch

from accounts.models import UniversityIdentity, UserProfile, UserSportInterest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from parties.models import JoinRequest, Party, PartyMembership
from venues.models import Sport, Venue, VenueOpeningHour, VenueSport

from .management.commands.seed_demo import PREFIX


@override_settings(DEBUG=True)
class SeedDemoTests(TestCase):
    now = datetime(2026, 10, 16, 8, tzinfo=timezone.utc)

    def seed(self, now=None):
        with patch("core.management.commands.seed_demo.timezone.now", return_value=now or self.now):
            call_command("seed_demo", stdout=StringIO())

    def party(self, name):
        return Party.objects.get(title=f"{PREFIX} {name}")

    def test_seed_has_required_scenarios_and_consistent_membership_counts(self):
        self.seed()
        self.assertEqual(get_user_model().objects.count(), 6)
        self.assertEqual(Party.objects.count(), 6)
        self.assertEqual(UserProfile.objects.count(), 6)
        self.assertEqual(UniversityIdentity.objects.count(), 0)
        self.assertEqual(UserSportInterest.objects.count(), 4)
        for user in get_user_model().objects.all():
            self.assertFalse(user.has_usable_password())
            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)
        self.assertFalse(get_user_model().objects.get(username="base03_inactive").is_active)
        self.assertFalse(PartyMembership.objects.filter(user__username="base03_x").exists())
        for party in Party.objects.all():
            self.assertEqual(party.memberships.filter(left_at__isnull=True).count(), 2)
            self.assertTrue(
                party.memberships.filter(user=party.host, left_at__isnull=True).exists()
            )
            self.assertLess(party.starts_at, party.ends_at)
        last = self.party("Last slot")
        self.assertEqual(last.capacity - last.memberships.count(), 1)
        self.assertEqual(last.join_requests.filter(status="Pending").count(), 2)
        self.assertFalse(
            last.memberships.filter(user__username__in=["base03_a", "base03_b"]).exists()
        )
        self.assertEqual(self.party("Full").capacity, 2)
        self.assertGreater(self.party("Open").starts_at, self.now)
        self.assertLessEqual(self.party("InProgress").starts_at, self.now)
        self.assertGreater(self.party("InProgress").ends_at, self.now)
        self.assertLess(self.party("Completed").ends_at, self.now)
        self.assertIsNotNone(self.party("Cancelled").cancelled_at)
        self.assertEqual(
            set(JoinRequest.objects.values_list("status", flat=True)),
            {"Pending", "Approved", "Rejected"},
        )
        for request in JoinRequest.objects.exclude(status="Pending"):
            self.assertLessEqual(request.created_at, request.decided_at)
            self.assertLessEqual(request.decided_at, self.now)
        self.assertEqual(Venue.objects.get(name=f"{PREFIX} Open venue").opening_hours.count(), 7)
        self.assertFalse(Venue.objects.get(name=f"{PREFIX} Closed venue").opening_hours.exists())
        self.assertFalse(Venue.objects.get(name=f"{PREFIX} Inactive venue").is_active)

    def test_rerun_preserves_primary_ids_resets_interactions_and_refreshes_dates(self):
        self.seed()
        ids = dict(Party.objects.values_list("title", "pk"))
        user_ids = list(get_user_model().objects.values_list("pk", flat=True))
        counts = [
            model.objects.count()
            for model in (Party, PartyMembership, JoinRequest, Venue, VenueOpeningHour, VenueSport)
        ]
        party = self.party("Last slot")
        party.memberships.filter(user__username="base03_m").update(left_at=self.now)
        party.join_requests.filter(user__username="base03_a").update(
            status="Rejected", decided_at=self.now, decided_by=party.host
        )
        self.seed(self.now + timedelta(days=7))
        self.assertEqual(dict(Party.objects.values_list("title", "pk")), ids)
        self.assertEqual(list(get_user_model().objects.values_list("pk", flat=True)), user_ids)
        self.assertEqual(
            [
                model.objects.count()
                for model in (
                    Party,
                    PartyMembership,
                    JoinRequest,
                    Venue,
                    VenueOpeningHour,
                    VenueSport,
                )
            ],
            counts,
        )
        party.refresh_from_db()
        self.assertGreater(party.starts_at, self.now + timedelta(days=7))
        self.assertEqual(party.memberships.filter(left_at__isnull=True).count(), 2)
        self.assertEqual(party.join_requests.filter(status="Pending").count(), 2)

    def test_non_demo_data_is_preserved(self):
        user = get_user_model().objects.create_user(username="real_local_test")
        sport = Sport.objects.create(name="Existing sport")
        venue = Venue.objects.create(name="Existing venue", location_text="Existing location")
        party = Party.objects.create(
            host=user,
            sport=sport,
            venue=venue,
            title="Existing party",
            starts_at=self.now,
            ends_at=self.now + timedelta(hours=1),
            capacity=1,
        )
        member = PartyMembership.objects.create(party=party, user=user)
        self.seed()
        self.seed()
        self.assertTrue(PartyMembership.objects.filter(pk=member.pk).exists())
        self.assertEqual(Party.objects.get(pk=party.pk).title, "Existing party")
        user.refresh_from_db()
        self.assertEqual(user.email, "")

    def test_seeded_parties_can_be_read_through_existing_detail_api(self):
        self.seed()
        self.client.force_login(get_user_model().objects.get(username="base03_x"))
        for name, state in (
            ("Open", "Open"),
            ("Last slot", "Open"),
            ("Full", "Full"),
            ("InProgress", "InProgress"),
            ("Completed", "Completed"),
            ("Cancelled", "Cancelled"),
        ):
            with (
                self.subTest(name=name),
                patch("parties.services.timezone.now", return_value=self.now),
            ):
                response = self.client.get(f"/api/v1/parties/{self.party(name).pk}")
                self.assertEqual(response.status_code, 200)
                data = response.json()["data"]
                self.assertEqual(data["state"], state)
                self.assertEqual(data["member_count"], 2)
                self.assertFalse(data["is_member"])
                self.assertFalse(data["is_host"])

    @override_settings(DEBUG=False)
    def test_refuses_non_development_settings(self):
        with self.assertRaisesMessage(CommandError, "DEBUG=true"):
            self.seed()
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_reserved_username_collision_rolls_back_entire_seed(self):
        get_user_model().objects.create_user(username="base03_m", email="someone@example.invalid")
        with self.assertRaisesMessage(CommandError, "collision"):
            self.seed()
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 0)
        self.assertEqual(Party.objects.count(), 0)
