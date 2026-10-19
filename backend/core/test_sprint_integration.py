"""Sprint 1 API regression flow across US1, US3, US7, and US9."""

import json
from datetime import time, timedelta

from accounts.test_support import force_university_login
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from parties.models import JoinRequest, Party, PartyMembership
from venues.models import Sport, Venue, VenueOpeningHour, VenueSport


class SprintOneApiFlowTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.host = users.objects.create_user(username="sprint-host")
        self.applicant = users.objects.create_user(username="sprint-applicant")
        self.host_client = Client(enforce_csrf_checks=True)
        self.applicant_client = Client(enforce_csrf_checks=True)
        force_university_login(self.host_client, self.host)
        force_university_login(self.applicant_client, self.applicant)

        self.sport = Sport.objects.create(name="Sprint badminton")
        self.venue = Venue.objects.create(name="Sprint court", location_text="Campus")
        VenueSport.objects.create(venue=self.venue, sport=self.sport)
        self.start = (timezone.localtime() + timedelta(days=2)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        VenueOpeningHour.objects.create(
            venue=self.venue,
            weekday=self.start.weekday(),
            opens_at=time(9),
            closes_at=time(18),
        )

    @staticmethod
    def write(client, method, url, payload):
        token = client.get(reverse("accounts:csrf")).json()["data"]["csrf_token"]
        return getattr(client, method)(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

    def test_verified_users_complete_create_join_edit_and_cancel_flow(self):
        sports = self.host_client.get(reverse("sport-list"))
        self.assertEqual(sports.status_code, 200)
        self.assertIn(self.sport.pk, {row["id"] for row in sports.json()["data"]})
        venues = self.host_client.get(reverse("venue-list"), {"sport_id": self.sport.pk})
        self.assertEqual(venues.status_code, 200)
        self.assertIn(self.venue.pk, {row["id"] for row in venues.json()["data"]})

        created = self.write(
            self.host_client,
            "post",
            reverse("party-create"),
            {
                "title": "Sprint practice",
                "description": "API integration flow",
                "sport_id": self.sport.pk,
                "venue_id": self.venue.pk,
                "starts_at": self.start.isoformat(),
                "ends_at": (self.start + timedelta(hours=1)).isoformat(),
                "capacity": 2,
            },
        )
        self.assertEqual(created.status_code, 201)
        party_id = created.json()["data"]["id"]
        self.assertEqual(created.json()["data"]["host"]["id"], self.host.pk)
        self.assertEqual(
            (created.json()["data"]["member_count"], created.json()["data"]["remaining_slots"]),
            (1, 1),
        )
        self.assertTrue(PartyMembership.objects.filter(party_id=party_id, user=self.host).exists())

        requested = self.write(
            self.applicant_client,
            "post",
            reverse("party-join-request-create", args=[party_id]),
            {},
        )
        self.assertEqual(requested.status_code, 201)
        self.assertEqual(requested.json()["data"]["status"], "Pending")
        self.assertTrue(
            JoinRequest.objects.filter(
                party_id=party_id, user=self.applicant, status="Pending"
            ).exists()
        )
        self.assertEqual(PartyMembership.objects.filter(party_id=party_id).count(), 1)

        detail_url = reverse("party-detail", args=[party_id])
        forbidden = self.write(self.applicant_client, "patch", detail_url, {"title": "Forged"})
        self.assertEqual(forbidden.status_code, 403)

        edited = self.write(self.host_client, "patch", detail_url, {"title": "Updated practice"})
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.json()["data"]["title"], "Updated practice")

        cancelled = self.write(
            self.host_client,
            "post",
            reverse("party-cancel", args=[party_id]),
            {},
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["data"]["state"], "Cancelled")
        self.assertIsNotNone(Party.objects.get(pk=party_id).cancelled_at)
