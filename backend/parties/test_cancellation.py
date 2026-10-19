from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from threading import Event
from time import monotonic
from unittest.mock import patch

from django.db import close_old_connections, connection, connections, transaction
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone

from .models import JoinRequest, Party, PartyMembership
from .services import JoinRequestError, PartyError, cancel_party, submit_join_request
from .test_join_requests import JoinRequestFixture


class CancelPartyTests(JoinRequestFixture, TestCase):
    def test_host_can_cancel_without_removing_history(self):
        pending = submit_join_request(party_id=self.party.pk, user=self.applicant)
        member = PartyMembership.objects.get(party=self.party, user=self.host)
        with patch("parties.services.timezone.now", return_value=self.now):
            result = cancel_party(party_id=self.party.pk, user=self.host)
        self.assertEqual(result.cancelled_at, self.now)
        self.party.refresh_from_db()
        pending.refresh_from_db()
        member.refresh_from_db()
        self.assertEqual(self.party.cancelled_at, self.now)
        self.assertEqual(pending.status, JoinRequest.Status.PENDING)
        self.assertIsNone(member.left_at)
        with self.assertRaises(JoinRequestError) as caught:
            submit_join_request(party_id=self.party.pk, user=self.other)
        self.assertEqual(caught.exception.code, "PARTY_CANCELLED")

    def test_repeat_after_start_keeps_original_timestamps(self):
        first = cancel_party(party_id=self.party.pk, user=self.host)
        with patch("parties.services.timezone.now", return_value=self.party.ends_at):
            repeated = cancel_party(party_id=self.party.pk, user=self.host)
        self.assertEqual(repeated.cancelled_at, first.cancelled_at)
        self.assertEqual(repeated.updated_at, first.updated_at)

    def test_outsider_and_member_cannot_cancel_even_when_already_cancelled(self):
        PartyMembership.objects.create(party=self.party, user=self.applicant)
        for cancelled in (False, True):
            if cancelled:
                cancel_party(party_id=self.party.pk, user=self.host)
            for user in (self.other, self.applicant):
                with self.subTest(cancelled=cancelled, user=user.pk):
                    with self.assertRaises(PartyError) as caught:
                        cancel_party(party_id=self.party.pk, user=user)
                    self.assertEqual(
                        (caught.exception.code, caught.exception.status), ("FORBIDDEN", 403)
                    )
        self.assertEqual(PartyMembership.objects.filter(party=self.party).count(), 2)

    def test_missing_party_returns_not_found(self):
        with self.assertRaises(PartyError) as caught:
            cancel_party(party_id=self.party.pk + 999, user=self.host)
        self.assertEqual((caught.exception.code, caught.exception.status), ("NOT_FOUND", 404))

    def test_exact_start_and_later_are_rejected_without_writing(self):
        for now in (
            self.party.starts_at,
            self.party.starts_at + timedelta(seconds=1),
            self.party.ends_at,
        ):
            with self.subTest(now=now):
                with patch("parties.services.timezone.now", return_value=now):
                    with self.assertRaises(PartyError) as caught:
                        cancel_party(party_id=self.party.pk, user=self.host)
                self.assertEqual(
                    (caught.exception.code, caught.exception.status), ("PARTY_STARTED", 409)
                )
                self.party.refresh_from_db()
                self.assertIsNone(self.party.cancelled_at)

    def test_full_party_can_be_cancelled(self):
        self.party.capacity = 1
        self.party.save()
        self.assertIsNotNone(cancel_party(party_id=self.party.pk, user=self.host).cancelled_at)


@skipUnlessDBFeature("has_select_for_update")
class CancelPartyLockTests(JoinRequestFixture, TransactionTestCase):
    def worker(self, pids):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                result = cancel_party(party_id=self.party.pk, user=self.host)
                return result.cancelled_at
            except PartyError as error:
                return error.code
        finally:
            connections.close_all()

    def wait_for_lock(self, pid):
        deadline = monotonic() + 4
        while monotonic() < deadline:
            with connection.cursor() as cursor:
                cursor.execute("SELECT cardinality(pg_blocking_pids(%s)) > 0", [pid])
                if cursor.fetchone()[0]:
                    return
            Event().wait(0.01)
        self.fail("Cancellation did not wait for the Party lock")

    def test_waiter_rechecks_start_after_lock(self):
        pids = Queue()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                party = Party.objects.select_for_update().get(pk=self.party.pk)
                future = executor.submit(self.worker, pids)
                self.wait_for_lock(pids.get(timeout=5))
                party.starts_at = timezone.now() - timedelta(seconds=1)
                party.save(update_fields=["starts_at"])
            self.assertEqual(future.result(timeout=10), "PARTY_STARTED")
        self.party.refresh_from_db()
        self.assertIsNone(self.party.cancelled_at)

    def test_concurrent_cancellation_keeps_first_timestamp_and_pending(self):
        pids = Queue()
        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                pending = submit_join_request(party_id=self.party.pk, user=self.applicant)
                first = cancel_party(party_id=self.party.pk, user=self.host)
                future = executor.submit(self.worker, pids)
                self.wait_for_lock(pids.get(timeout=5))
            self.assertEqual(future.result(timeout=10), first.cancelled_at)
        pending.refresh_from_db()
        self.assertEqual(pending.status, "Pending")
