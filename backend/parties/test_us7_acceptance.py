"""US7-T backend acceptance across Create, Pending, Edit and Cancel.

Uses real URLs, CSRF middleware and isolated university-session fixtures;
does not exercise a browser or call the university provider.
"""

import json
from datetime import time, timedelta

from accounts.models import UserProfile
from accounts.test_support import force_university_login
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from venues.models import Sport, Venue, VenueOpeningHour, VenueSport

from .models import JoinRequest, Party, PartyMembership


class PartyLifecycleAcceptanceTests(TestCase):
    def setUp(self):
        self.host = get_user_model().objects.create_user("us7-acceptance-host")
        self.applicant = get_user_model().objects.create_user("us7-acceptance-applicant")
        UserProfile.objects.create(user=self.host, display_name="US7 Host")
        self.host_client = Client(enforce_csrf_checks=True)
        self.applicant_client = Client(enforce_csrf_checks=True)
        force_university_login(self.host_client, self.host)
        force_university_login(self.applicant_client, self.applicant)
        sport = Sport.objects.create(name="US7 Badminton")
        venue = Venue.objects.create(name="US7 Court")
        VenueSport.objects.create(venue=venue, sport=sport)
        start = (timezone.localtime() + timedelta(days=2)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        VenueOpeningHour.objects.create(
            venue=venue, weekday=start.weekday(), opens_at=time(9), closes_at=time(18)
        )
        self.payload = {
            "title": "US7 acceptance",
            "sport_id": sport.pk,
            "venue_id": venue.pk,
            "starts_at": start.isoformat(),
            "ends_at": (start + timedelta(hours=1)).isoformat(),
            "capacity": 2,
        }

    def send(self, client, method, url, payload):
        token = client.get(reverse("accounts:csrf")).json()["data"]["csrf_token"]
        return getattr(client, method)(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

    def create(self, capacity=2):
        response = self.send(
            self.host_client,
            "post",
            reverse("party-create"),
            self.payload | {"capacity": capacity},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["data"]

    def test_created_party_pending_survives_edit_and_cancel_without_consuming_a_slot(self):
        created = self.create()
        party_id = created["id"]
        detail_url = reverse("party-detail", args=[party_id])
        join_url = reverse("party-join-request-create", args=[party_id])
        response = self.send(self.applicant_client, "post", join_url, {})
        self.assertEqual(response.status_code, 201)
        pending = JoinRequest.objects.get(party_id=party_id, user=self.applicant)
        self.assertEqual(response.json()["data"]["id"], pending.pk)
        request_before = JoinRequest.objects.values().get(pk=pending.pk)
        members_before = list(PartyMembership.objects.filter(party_id=party_id).values())
        self.assertEqual(len(members_before), 1)
        self.assertEqual(members_before[0]["user_id"], self.host.pk)
        self.assertIsNone(members_before[0]["left_at"])

        # Pending is a request, not an active membership or a reserved slot.
        detail = self.applicant_client.get(detail_url).json()["data"]
        self.assertEqual(
            (detail["state"], detail["member_count"], detail["remaining_slots"]), ("Open", 1, 1)
        )
        response = self.send(
            self.host_client, "patch", detail_url, {"title": "Updated after request", "capacity": 1}
        )
        self.assertEqual(response.status_code, 200)
        edited = response.json()["data"]
        self.assertEqual(
            (edited["state"], edited["member_count"], edited["remaining_slots"]), ("Full", 1, 0)
        )
        self.assertEqual(JoinRequest.objects.values().get(pk=pending.pk), request_before)

        # Even a full party can be cancelled; history and the first timestamp stay intact.
        cancel_url = reverse("party-cancel", args=[party_id])
        cancelled = self.send(self.host_client, "post", cancel_url, {})
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["data"]["state"], "Cancelled")
        self.assertEqual(
            self.send(self.host_client, "post", cancel_url, {}).json(), cancelled.json()
        )
        party_before = Party.objects.values().get(pk=party_id)
        response = self.send(self.host_client, "patch", detail_url, {"title": "Must not save"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "PARTY_CANCELLED")
        response = self.send(self.applicant_client, "post", join_url, {})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "PARTY_CANCELLED")
        self.assertEqual(Party.objects.values().get(pk=party_id), party_before)
        self.assertEqual(JoinRequest.objects.values().get(pk=pending.pk), request_before)
        self.assertEqual(request_before["status"], JoinRequest.Status.PENDING)
        self.assertEqual(
            list(PartyMembership.objects.filter(party_id=party_id).values()), members_before
        )
        response = self.applicant_client.get(reverse("party-join-request-me", args=[party_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "Pending")

    def test_capacity_one_is_full_immediately_and_join_cannot_leave_partial_data(self):
        created = self.create(capacity=1)
        self.assertEqual(
            (created["state"], created["member_count"], created["remaining_slots"]), ("Full", 1, 0)
        )
        party = Party.objects.get(pk=created["id"])
        self.assertEqual(party.host_id, self.host.pk)
        response = self.send(
            self.applicant_client,
            "post",
            reverse("party-join-request-create", args=[party.pk]),
            {},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "PARTY_FULL")
        self.assertFalse(JoinRequest.objects.filter(party=party).exists())
        membership = PartyMembership.objects.get(party=party)
        self.assertEqual(membership.user_id, self.host.pk)
        self.assertIsNone(membership.left_at)
        self.assertEqual(
            self.host_client.get(reverse("party-detail", args=[party.pk])).json()["data"], created
        )
