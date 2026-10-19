import json
from datetime import time, timedelta

from accounts.models import UniversityIdentity
from accounts.test_support import force_university_login
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from venues.models import VenueOpeningHour, VenueSport

from .models import PartyMembership
from .services import cancel_party
from .test_join_requests import JoinRequestFixture
from .views import edit_party_api


class EditPartyHandlerTests(JoinRequestFixture, TestCase):
    """RequestFactory handler tests; full HTTP integration is tested separately."""

    def setUp(self):
        super().setUp()
        self.party.starts_at = (timezone.localtime(self.now) + timedelta(days=2)).replace(
            hour=10,
            minute=0,
            second=0,
            microsecond=0,
        )
        self.party.ends_at = self.party.starts_at + timedelta(hours=1)
        self.party.save()
        VenueSport.objects.create(venue=self.party.venue, sport=self.party.sport)
        VenueOpeningHour.objects.create(
            venue=self.party.venue,
            weekday=self.party.starts_at.weekday(),
            opens_at=time(9),
            closes_at=time(18),
        )

    def call(
        self,
        payload=None,
        *,
        body=None,
        user=None,
        method="patch",
        content_type="application/json",
        party_id=None,
    ):
        if body is None:
            body = json.dumps(payload if payload is not None else {})
        request = getattr(RequestFactory(), method)(
            f"/api/v1/parties/{self.party.pk}",
            data={} if method == "get" else body,
            content_type=content_type,
        )
        request.user = user if user is not None else self.host
        identity, _ = UniversityIdentity.objects.get_or_create(
            user=request.user,
            provider_key="tu",
            subject=str(request.user.pk),
            defaults={
                "student_verified_at": timezone.now(),
                "eligibility_checked_at": timezone.now(),
            },
        )
        request.session = {"university_identity_id": identity.pk}
        return edit_party_api(request, party_id if party_id is not None else self.party.pk)

    def test_partial_update_matches_get_and_keeps_unsupplied_fields(self):
        response = self.call({"title": " New name "})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)["data"]
        self.assertEqual(data["title"], "New name")
        self.assertEqual(data["capacity"], self.party.capacity)
        force_university_login(self.client, self.host)
        detail = self.client.get(reverse("party-detail", args=[self.party.pk]))
        self.assertEqual(data, detail.json()["data"])

    def test_datetime_strings_are_parsed_and_validated(self):
        start = self.party.starts_at + timedelta(hours=1)
        end = start + timedelta(hours=1)
        response = self.call({"starts_at": start.isoformat(), "ends_at": end.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.party.refresh_from_db()
        self.assertEqual(self.party.starts_at, start)
        self.assertEqual(self.party.ends_at, end)
        response = self.call({"ends_at": start.replace(hour=19).isoformat()})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)["error"]["code"], "VENUE_CLOSED")

    def test_invalid_payloads_do_not_change_party(self):
        for body, content_type in (
            ("{", "application/json"),
            ("[]", "application/json"),
            ("null", "application/json"),
            (b"\xff", "application/json"),
            ("{}", "text/plain"),
        ):
            with self.subTest(body=body):
                self.assertEqual(self.call(body=body, content_type=content_type).status_code, 400)
        for payload in (
            {"host_id": self.other.pk},
            {"state": "Cancelled"},
            {"capacity": True},
            {"starts_at": None},
            {"ends_at": "2030-01-01T12:00:00"},
            {"ends_at": "2030-02-31T12:00:00+07:00"},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.call(payload).status_code, 400)
        self.party.refresh_from_db()
        self.assertEqual(self.party.title, "After class")
        self.assertEqual(self.party.host_id, self.host.pk)

    def test_service_errors_have_expected_http_status(self):
        cases = (
            (self.call({"title": "x"}, user=self.other), 403, "FORBIDDEN"),
            (self.call(party_id=self.party.pk + 999), 404, "NOT_FOUND"),
        )
        for response, status, code in cases:
            self.assertEqual(response.status_code, status)
            self.assertEqual(json.loads(response.content)["error"]["code"], code)
        PartyMembership.objects.create(party=self.party, user=self.applicant)
        response = self.call({"capacity": 1})
        self.assertEqual(response.status_code, 409)
        error = json.loads(response.content)["error"]
        self.assertEqual(error["code"], "CAPACITY_TOO_SMALL")
        self.assertIn("capacity", error["fields"])
        cancel_party(party_id=self.party.pk, user=self.host)
        response = self.call({"title": "x"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(json.loads(response.content)["error"]["code"], "PARTY_CANCELLED")

    def test_started_party_is_conflict(self):
        self.party.starts_at = self.now
        self.party.save()
        response = self.call({"title": "x"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(json.loads(response.content)["error"]["code"], "PARTY_STARTED")

    def test_empty_patch_is_noop_and_other_methods_rejected(self):
        self.assertEqual(self.call({}).status_code, 200)
        self.party.refresh_from_db()
        previous_update = self.party.updated_at
        for method in ("get", "post", "delete", "put"):
            response = self.call(method=method)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response["Allow"], "PATCH")
        self.party.refresh_from_db()
        self.assertEqual(self.party.updated_at, previous_update)
