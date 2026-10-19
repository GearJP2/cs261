"""US7 HTTP integration with university session fixtures and real CSRF middleware."""

import json
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

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

    def test_us9_catalogue_drives_party_creation_and_editing(self):
        self.login()
        response = self.client.get(reverse("sport-list"))
        self.assertEqual(response.status_code, 200)
        sport = next(row for row in response.json()["data"] if row["id"] == self.party.sport_id)
        response = self.client.get(reverse("venue-list"), {"sport_id": sport["id"], "page_size": 1})
        self.assertEqual(response.status_code, 200)
        venue = response.json()["data"][0]
        response = self.client.get(reverse("venue-opening-hours", args=[venue["id"]]))
        self.assertEqual(response.status_code, 200)
        hours = response.json()["data"]
        local_timezone = ZoneInfo(hours["timezone"])
        day = self.party.starts_at.astimezone(local_timezone).date()
        interval = next(row for row in hours["intervals"] if row["weekday"] == day.weekday())
        start = datetime.combine(day, time.fromisoformat(interval["opens_at"]), local_timezone)
        end = datetime.combine(day, time.fromisoformat(interval["closes_at"]), local_timezone)
        response = self.send(
            "post",
            self.create_url,
            self.payload
            | {
                "sport_id": sport["id"],
                "venue_id": venue["id"],
                "starts_at": start.isoformat(),
                "ends_at": end.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]
        created = Party.objects.get(pk=data["id"])
        self.assertEqual((created.sport_id, created.venue_id), (sport["id"], venue["id"]))
        self.assertEqual((created.starts_at, created.ends_at), (start, end))
        self.assertEqual(created.memberships.get().user_id, self.host.pk)
        response = self.send(
            "patch",
            reverse("party-detail", args=[created.pk]),
            {
                "description": "Selected from US9 catalogue",
            },
        )
        self.assertEqual(response.status_code, 200)
        created.refresh_from_db()
        self.assertEqual(created.description, "Selected from US9 catalogue")
        self.assertEqual((created.starts_at, created.ends_at), (start, end))

    def test_venue_only_edit_checks_old_times_and_merged_schedule_can_succeed(self):
        self.login()
        start = timezone.localtime(self.party.starts_at)
        venue = Venue.objects.create(name="Afternoon Court", location_text="Campus")
        VenueSport.objects.create(venue=venue, sport=self.party.sport)
        VenueOpeningHour.objects.create(
            venue=venue,
            weekday=start.weekday(),
            opens_at=time(13),
            closes_at=time(16),
        )
        original_venue_id = self.party.venue_id
        original_updated_at = self.party.updated_at
        response = self.send("patch", self.edit_url, {"venue_id": venue.pk})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VENUE_CLOSED")
        self.party.refresh_from_db()
        self.assertEqual(self.party.venue_id, original_venue_id)
        self.assertEqual(self.party.updated_at, original_updated_at)
        new_start, new_end = start.replace(hour=13), start.replace(hour=16)
        response = self.send(
            "patch",
            self.edit_url,
            {
                "venue_id": venue.pk,
                "starts_at": new_start.isoformat(),
                "ends_at": new_end.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.party.refresh_from_db()
        self.assertEqual(self.party.venue_id, venue.pk)
        self.assertEqual((self.party.starts_at, self.party.ends_at), (new_start, new_end))
        self.assertEqual(self.party.memberships.count(), 1)

    def test_us9_overlapping_hours_error_prevents_create_and_partial_edit(self):
        self.login()
        VenueOpeningHour.objects.create(
            venue=self.party.venue,
            weekday=timezone.localtime(self.party.starts_at).weekday(),
            opens_at=time(10),
            closes_at=time(12),
        )
        updated_at = self.party.updated_at
        for method, url, payload in (
            ("post", self.create_url, self.payload),
            ("patch", self.edit_url, {"title": "Must not save"}),
        ):
            with self.subTest(method=method):
                response = self.send(method, url, payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"]["code"], "INVALID_OPENING_HOURS")
        self.assertEqual(Party.objects.count(), 1)
        self.assertEqual(PartyMembership.objects.count(), 1)
        self.party.refresh_from_db()
        self.assertEqual(self.party.title, "Existing")
        self.assertEqual(self.party.updated_at, updated_at)

    def test_us9_missing_sport_and_inactive_venue_errors_preserve_data(self):
        self.login()
        for method, url, payload in (
            ("post", self.create_url, self.payload | {"sport_id": 999999}),
            ("patch", self.edit_url, {"sport_id": 999999}),
        ):
            response = self.send(method, url, payload)
            self.assertEqual(response.status_code, 400)
            error = response.json()["error"]
            self.assertEqual(error["code"], "INVALID_INPUT")
            self.assertIn("sport_id", error["fields"])
        self.party.venue.is_active = False
        self.party.venue.save()
        response = self.client.get(reverse("venue-list"), {"sport_id": self.party.sport_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], [])
        for method, url, payload in (
            ("post", self.create_url, self.payload),
            ("patch", self.edit_url, {"title": "Must not save"}),
        ):
            response = self.send(method, url, payload)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        self.assertEqual(Party.objects.count(), 1)
        self.assertEqual(PartyMembership.objects.count(), 1)
        self.party.refresh_from_db()
        self.assertEqual(self.party.title, "Existing")
        self.assertEqual(self.party.sport_id, self.payload["sport_id"])

    def test_create_rejects_capacity_over_database_limit_without_writing(self):
        self.login()
        original_parties = list(Party.objects.values().order_by("pk"))
        original_memberships = list(PartyMembership.objects.values().order_by("pk"))
        for capacity in (2_147_483_648, 10**100):
            with self.subTest(capacity=capacity):
                response = self.send("post", self.create_url, self.payload | {"capacity": capacity})
                self.assertEqual(response.status_code, 400)
                error = response.json()["error"]
                self.assertEqual(error["code"], "INVALID_INPUT")
                self.assertIn("capacity", error["fields"])
                self.assertEqual(list(Party.objects.values().order_by("pk")), original_parties)
                self.assertEqual(
                    list(PartyMembership.objects.values().order_by("pk")),
                    original_memberships,
                )

    def test_edit_rejects_capacity_over_database_limit_without_partial_update(self):
        self.login()
        original_party = Party.objects.values().get(pk=self.party.pk)
        original_memberships = list(self.party.memberships.values().order_by("pk"))
        for capacity in (2_147_483_648, 10**100):
            with self.subTest(capacity=capacity):
                response = self.send(
                    "patch",
                    self.edit_url,
                    {
                        "title": "Must not save",
                        "capacity": capacity,
                    },
                )
                self.assertEqual(response.status_code, 400)
                error = response.json()["error"]
                self.assertEqual(error["code"], "INVALID_INPUT")
                self.assertIn("capacity", error["fields"])
                self.assertEqual(Party.objects.values().get(pk=self.party.pk), original_party)
                self.assertEqual(
                    list(self.party.memberships.values().order_by("pk")),
                    original_memberships,
                )

    def test_create_and_edit_accept_capacity_at_database_limit(self):
        self.login()
        capacity = 2_147_483_647
        response = self.send("post", self.create_url, self.payload | {"capacity": capacity})
        self.assertEqual(response.status_code, 201)
        created = Party.objects.get(pk=response.json()["data"]["id"])
        self.assertEqual(created.capacity, capacity)
        response = self.send("patch", self.edit_url, {"capacity": capacity})
        self.assertEqual(response.status_code, 200)
        self.party.refresh_from_db()
        self.assertEqual(self.party.capacity, capacity)

    def test_create_rejects_nul_in_text_without_writing(self):
        self.login()
        original_parties = list(Party.objects.values().order_by("pk"))
        original_memberships = list(PartyMembership.objects.values().order_by("pk"))
        for field in ("title", "description"):
            with self.subTest(field=field):
                response = self.send("post", self.create_url, self.payload | {field: "Bad\x00text"})
                self.assertEqual(response.status_code, 400)
                error = response.json()["error"]
                self.assertEqual(error["code"], "INVALID_INPUT")
                self.assertIn(field, error["fields"])
                self.assertEqual(list(Party.objects.values().order_by("pk")), original_parties)
                self.assertEqual(
                    list(PartyMembership.objects.values().order_by("pk")),
                    original_memberships,
                )

    def test_edit_rejects_nul_in_text_without_partial_update(self):
        self.login()
        original_party = Party.objects.values().get(pk=self.party.pk)
        original_memberships = list(self.party.memberships.values().order_by("pk"))
        for field in ("title", "description"):
            with self.subTest(field=field):
                changes = {"title": "Must not save", "capacity": 4, field: "Bad\x00text"}
                response = self.send("patch", self.edit_url, changes)
                self.assertEqual(response.status_code, 400)
                error = response.json()["error"]
                self.assertEqual(error["code"], "INVALID_INPUT")
                self.assertIn(field, error["fields"])
                self.assertEqual(Party.objects.values().get(pk=self.party.pk), original_party)
                self.assertEqual(
                    list(self.party.memberships.values().order_by("pk")),
                    original_memberships,
                )

    def test_regular_unicode_text_and_empty_description_are_preserved(self):
        self.login()
        title = "นัดตีแบด 🏸"
        description = "ชั้น ๒\nพบกันที่สนาม\tเวลาเดิม"
        response = self.send(
            "post",
            self.create_url,
            self.payload
            | {
                "title": title,
                "description": description,
            },
        )
        self.assertEqual(response.status_code, 201)
        created = Party.objects.get(pk=response.json()["data"]["id"])
        self.assertEqual((created.title, created.description), (title, description))
        response = self.send(
            "patch", reverse("party-detail", args=[created.pk]), {"description": ""}
        )
        self.assertEqual(response.status_code, 200)
        created.refresh_from_db()
        self.assertEqual(created.description, "")
