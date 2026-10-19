"""US7 HTTP integration with university session fixtures and real CSRF middleware."""

import json
from datetime import time, timedelta

from accounts.models import UniversityIdentity
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from venues.models import Sport, Venue, VenueOpeningHour, VenueSport

from .models import Party, PartyMembership


class PartyManagementApiTests(TestCase):
    def setUp(self):
        self.host = get_user_model().objects.create_user(username="management-host")
        self.other = get_user_model().objects.create_user(username="management-other")
        self.identities = {}
        for user in (self.host, self.other):
            self.identities[user.pk] = UniversityIdentity.objects.create(
                user=user,
                provider_key="tu",
                subject=str(user.pk),
                student_verified_at=timezone.now(),
                eligibility_checked_at=timezone.now(),
            )
        sport = Sport.objects.create(name="Badminton")
        venue = Venue.objects.create(name="Court", location_text="Campus")
        VenueSport.objects.create(venue=venue, sport=sport)
        start = (timezone.localtime() + timedelta(days=2)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        VenueOpeningHour.objects.create(
            venue=venue,
            weekday=start.weekday(),
            opens_at=time(9),
            closes_at=time(18),
        )
        self.payload = dict(
            title="Practice",
            sport_id=sport.pk,
            venue_id=venue.pk,
            starts_at=start.isoformat(),
            ends_at=(start + timedelta(hours=1)).isoformat(),
            capacity=3,
        )
        self.party = Party.objects.create(
            host=self.host,
            sport=sport,
            venue=venue,
            title="Existing",
            starts_at=start,
            ends_at=start + timedelta(hours=1),
            capacity=3,
        )
        PartyMembership.objects.create(party=self.party, user=self.host)
        self.create_url = reverse("party-create")
        self.edit_url = reverse("party-detail", args=[self.party.pk])
        self.cancel_url = reverse("party-cancel", args=[self.party.pk])
        self.client = Client(enforce_csrf_checks=True)

    def login(self, user=None):
        user = user or self.host
        self.client.force_login(user)
        session = self.client.session
        session["university_identity_id"] = self.identities[user.pk].pk
        session.save()

    def send(self, method, url, payload, *, csrf=True, **headers):
        if csrf:
            token = self.client.get(reverse("accounts:csrf")).json()["data"]["csrf_token"]
            headers.setdefault("HTTP_X_CSRFTOKEN", token)
        return getattr(self.client, method)(
            url, data=json.dumps(payload), content_type="application/json", **headers
        )

    def writes(self):
        return (
            ("post", self.create_url, self.payload),
            ("patch", self.edit_url, {"title": "Changed"}),
            ("post", self.cancel_url, {}),
        )

    def test_create_edit_cancel_flow_through_real_urls(self):
        self.login()
        created = self.send("post", self.create_url, self.payload)
        self.assertEqual(created.status_code, 201)
        data = created.json()["data"]
        self.assertEqual(data["host"]["id"], self.host.pk)
        self.assertEqual((data["member_count"], data["remaining_slots"]), (1, 2))
        self.assertTrue(data["is_host"] and data["is_member"])
        detail_url = reverse("party-detail", args=[data["id"]])
        self.assertEqual(self.client.get(detail_url).json()["data"], data)
        edited = self.send("patch", detail_url, {"title": "Updated", "capacity": 2})
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.json()["data"]["title"], "Updated")
        cancelled_url = reverse("party-cancel", args=[data["id"]])
        cancelled = self.send("post", cancelled_url, {})
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["data"]["state"], "Cancelled")
        self.assertEqual(self.send("post", cancelled_url, {}).json(), cancelled.json())
        self.assertEqual(self.send("patch", detail_url, {"title": "Late"}).status_code, 409)
        self.assertEqual(PartyMembership.objects.filter(party_id=data["id"]).count(), 1)
        self.login(self.other)
        join_url = reverse("party-join-request-create", args=[data["id"]])
        response = self.send("post", join_url, {})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "PARTY_CANCELLED")

    def test_all_writes_require_university_session(self):
        for method, url, payload in self.writes():
            self.assertEqual(self.send(method, url, payload).status_code, 401)
        self.client.force_login(self.host)
        for method, url, payload in self.writes():
            response = self.send(method, url, payload)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")
        self.assertEqual(Party.objects.count(), 1)
        self.party.refresh_from_db()
        self.assertEqual(self.party.title, "Existing")
        self.assertIsNone(self.party.cancelled_at)

    def test_identity_must_belong_to_session_user_and_remain_verified(self):
        self.login()
        session = self.client.session
        session["university_identity_id"] = self.identities[self.other.pk].pk
        session.save()
        for method, url, payload in self.writes():
            self.assertEqual(self.send(method, url, payload).status_code, 403)
        self.login()
        self.identities[self.host.pk].delete()
        for method, url, payload in self.writes():
            self.assertEqual(self.send(method, url, payload).status_code, 403)
        self.assertEqual(Party.objects.count(), 1)

    def test_verified_outsider_cannot_manage_another_hosts_party(self):
        self.login(self.other)
        for method, url in (("patch", self.edit_url), ("post", self.cancel_url)):
            response = self.send(method, url, {})
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")
        self.party.refresh_from_db()
        self.assertIsNone(self.party.cancelled_at)

    def test_csrf_missing_bad_token_and_untrusted_origin_reject_all_writes(self):
        self.login()
        for method, url, payload in self.writes():
            for headers in ({}, {"HTTP_X_CSRFTOKEN": "bad"}):
                response = self.send(method, url, payload, csrf=False, **headers)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["error"]["code"], "CSRF_FAILED")
            response = self.send(method, url, payload, HTTP_ORIGIN="https://untrusted.example")
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["error"]["code"], "CSRF_FAILED")
        self.assertEqual(Party.objects.count(), 1)
        self.party.refresh_from_db()
        self.assertIsNone(self.party.cancelled_at)
        self.assertEqual(self.party.title, "Existing")

    def test_logout_and_inactive_account_cannot_write(self):
        self.login()
        self.host.is_active = False
        self.host.save()
        for method, url, payload in self.writes():
            self.assertIn(self.send(method, url, payload).status_code, (401, 403))
        self.host.is_active = True
        self.host.save()
        self.login()
        self.assertEqual(self.send("post", reverse("accounts:logout"), {}).status_code, 200)
        for method, url, payload in self.writes():
            self.assertEqual(self.send(method, url, payload).status_code, 401)
        self.assertEqual(Party.objects.count(), 1)

    def test_readonly_fields_invalid_schedule_and_missing_party(self):
        self.login()
        self.assertEqual(
            self.send(
                "post", self.create_url, self.payload | {"host_id": self.other.pk}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.send("patch", self.edit_url, {"host_id": self.other.pk}).status_code, 400
        )
        self.assertEqual(
            self.send(
                "patch", self.edit_url, {"ends_at": self.party.ends_at.replace(hour=19).isoformat()}
            ).status_code,
            400,
        )
        for method, route in (("patch", "party-detail"), ("post", "party-cancel")):
            response = self.send(method, reverse(route, args=[self.party.pk + 999]), {})
            self.assertEqual(response.status_code, 404)
        self.party.refresh_from_db()
        self.assertEqual(self.party.host_id, self.host.pk)
        self.assertIsNone(self.party.cancelled_at)

    def test_wrong_methods_use_json_and_allow_header(self):
        self.login()
        for method, url, expected in (
            ("get", self.create_url, "POST"),
            ("get", self.cancel_url, "POST"),
            ("post", self.edit_url, "GET, PATCH"),
        ):
            if method == "get":
                response = self.client.get(url)
            else:
                response = self.send(method, url, {})
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], expected)
