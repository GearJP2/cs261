"""Real PostgreSQL connections and observed row-lock waits for Edit races."""

from concurrent.futures import ThreadPoolExecutor
from datetime import time, timedelta
from queue import Queue
from threading import Event
from time import monotonic
from unittest.mock import patch

from django.db import close_old_connections, connection, connections, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone
from venues.models import VenueOpeningHour, VenueSport

from .models import JoinRequest, Party, PartyMembership
from .services import (
    JoinRequestError,
    PartyError,
    cancel_party,
    edit_party,
    submit_join_request,
)
from .test_join_requests import JoinRequestFixture


@skipUnlessDBFeature("has_select_for_update")
class EditPartyConcurrencyTests(JoinRequestFixture, TransactionTestCase):
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

    def worker(self, pids, operation, changes=None):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                if operation == "edit":
                    result = edit_party(party_id=self.party.pk, user=self.host, changes=changes)
                elif operation == "cancel":
                    result = cancel_party(party_id=self.party.pk, user=self.host)
                else:
                    result = submit_join_request(party_id=self.party.pk, user=self.applicant)
                return "ok", result.pk
            except (PartyError, JoinRequestError) as error:
                return error.code, error.status
        finally:
            connections.close_all()

    def wait_for_lock(self, pid):
        deadline = monotonic() + 4
        while monotonic() < deadline:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_backend_pid() = ANY(pg_blocking_pids(%s))",
                    [pid],
                )
                if cursor.fetchone()[0]:
                    return
            Event().wait(0.01)
        self.fail("Worker did not wait for this transaction's Party lock")

    def test_cancel_committed_first_prevents_edit(self):
        pids = Queue()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                cancelled = cancel_party(party_id=self.party.pk, user=self.host)
                future = executor.submit(self.worker, pids, "edit", {"title": "Changed"})
                self.wait_for_lock(pids.get(timeout=5))
            self.assertEqual(future.result(timeout=10), ("PARTY_CANCELLED", 409))
        self.party.refresh_from_db()
        self.assertEqual(self.party.title, "After class")
        self.assertEqual(self.party.cancelled_at, cancelled.cancelled_at)

    def test_edit_committed_first_is_preserved_when_cancel_follows(self):
        pids = Queue()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                edit_party(party_id=self.party.pk, user=self.host, changes={"title": "Changed"})
                future = executor.submit(self.worker, pids, "cancel")
                self.wait_for_lock(pids.get(timeout=5))
            self.assertEqual(future.result(timeout=10)[0], "ok")
        self.party.refresh_from_db()
        self.assertEqual(self.party.title, "Changed")
        self.assertIsNotNone(self.party.cancelled_at)

    def test_edit_reads_clock_only_after_acquiring_lock(self):
        pids = Queue()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with patch("parties.services.timezone.now", return_value=self.party.starts_at) as clock:
                with transaction.atomic():
                    Party.objects.select_for_update().get(pk=self.party.pk)
                    future = executor.submit(self.worker, pids, "edit", {"title": "Too late"})
                    self.wait_for_lock(pids.get(timeout=5))
                    clock.assert_not_called()
                self.assertEqual(future.result(timeout=10), ("PARTY_STARTED", 409))
        self.party.refresh_from_db()
        self.assertEqual(self.party.title, "After class")

    def test_edit_rechecks_members_committed_while_waiting(self):
        # Simulate a membership writer following the agreed Party-first lock contract.
        pids = Queue()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                Party.objects.select_for_update().get(pk=self.party.pk)
                future = executor.submit(self.worker, pids, "edit", {"capacity": 1})
                self.wait_for_lock(pids.get(timeout=5))
                PartyMembership.objects.create(party=self.party, user=self.other)
            self.assertEqual(future.result(timeout=10), ("CAPACITY_TOO_SMALL", 409))
        self.party.refresh_from_db()
        self.assertEqual(self.party.capacity, 2)
        self.assertEqual(self.party.memberships.filter(left_at__isnull=True).count(), 2)

    def test_concurrent_partial_edits_merge_latest_committed_values(self):
        pids = Queue()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                edit_party(party_id=self.party.pk, user=self.host, changes={"capacity": 3})
                future = executor.submit(self.worker, pids, "edit", {"title": "Changed"})
                self.wait_for_lock(pids.get(timeout=5))
            self.assertEqual(future.result(timeout=10)[0], "ok")
        self.party.refresh_from_db()
        self.assertEqual(self.party.capacity, 3)
        self.assertEqual(self.party.title, "Changed")

    def test_edit_filling_capacity_blocks_waiting_join_request(self):
        pids = Queue()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                edit_party(party_id=self.party.pk, user=self.host, changes={"capacity": 1})
                future = executor.submit(self.worker, pids, "join")
                self.wait_for_lock(pids.get(timeout=5))
            self.assertEqual(future.result(timeout=10), ("PARTY_FULL", 409))
        self.party.refresh_from_db()
        self.assertEqual(self.party.capacity, 1)
        self.assertFalse(JoinRequest.objects.filter(party=self.party).exists())
        self.assertEqual(self.party.memberships.count(), 1)

    def test_join_committed_first_remains_pending_after_capacity_edit(self):
        pids = Queue()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                pending = submit_join_request(party_id=self.party.pk, user=self.applicant)
                future = executor.submit(self.worker, pids, "edit", {"capacity": 1})
                self.wait_for_lock(pids.get(timeout=5))
            self.assertEqual(future.result(timeout=10)[0], "ok")
        pending.refresh_from_db()
        self.party.refresh_from_db()
        self.assertEqual(pending.status, "Pending")
        self.assertEqual(self.party.capacity, 1)
        self.assertEqual(self.party.memberships.count(), 1)
