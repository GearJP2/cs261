"""Shared Party rules. Writers must lock Party before requests/memberships."""

from django.db import transaction
from django.utils import timezone

from .models import JoinRequest, Party, PartyMembership


class JoinRequestError(Exception):
    def __init__(self, code, message, status=409):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def count_active_members(party):
    return party.memberships.filter(left_at__isnull=True).count()


def get_party_state(party, now=None, *, member_count=None):
    """Use one timestamp and, optionally, the count already read by the caller."""
    if now is None:
        now = timezone.now()
    if party.cancelled_at is not None:
        return "Cancelled"
    if now >= party.ends_at:
        return "Completed"
    if now >= party.starts_at:
        return "InProgress"
    if member_count is None:
        member_count = count_active_members(party)
    if member_count >= party.capacity:
        return "Full"
    return "Open"


@transaction.atomic
def create_party(
    *,
    user,
    title,
    description,
    sport_id,
    venue_id,
    starts_at,
    ends_at,
    capacity,
):
    """Persist a validated Party and its Host membership together.

    The caller must supply the authenticated user and validated data, including
    the shared US9 schedule checks, before exposing this through an API.
    """
    party = Party.objects.create(
        host=user,
        title=title,
        description=description,
        sport_id=sport_id,
        venue_id=venue_id,
        starts_at=starts_at,
        ends_at=ends_at,
        capacity=capacity,
    )
    PartyMembership.objects.create(party=party, user=user)
    return party


@transaction.atomic
def submit_join_request(*, party_id, user):
    """Create/reopen a Pending request without changing membership or capacity.

    The Party lock serializes competing requests and is also the lock that
    approval, withdrawal and cancellation services must acquire first.
    The caller must apply the shared authentication/eligibility guard and pass
    its trusted user, never a user selected from request data.
    """
    try:
        party = Party.objects.select_for_update().get(pk=party_id)
    except Party.DoesNotExist:
        raise JoinRequestError("NOT_FOUND", "ไม่พบกิจกรรมที่ต้องการ", 404) from None

    # Evaluate time after acquiring the lock: a waiting request may cross starts_at.
    now = timezone.now()
    state = get_party_state(party, now)
    if state == "Cancelled":
        raise JoinRequestError("PARTY_CANCELLED", "กิจกรรมนี้ถูกยกเลิกแล้ว")
    if state in {"InProgress", "Completed"}:
        raise JoinRequestError("PARTY_STARTED", "กิจกรรมนี้เริ่มแล้ว")
    if state == "Full":
        raise JoinRequestError("PARTY_FULL", "กิจกรรมนี้เต็มแล้ว")

    membership = party.memberships.filter(user=user).first()
    if party.host_id == user.pk or (membership is not None and membership.left_at is None):
        raise JoinRequestError("ALREADY_MEMBER", "คุณเป็นสมาชิกของกิจกรรมนี้แล้ว")

    # The existing unique(party, user) constraint remains the final DB safeguard.
    join_request, created = JoinRequest.objects.select_for_update().get_or_create(
        party=party, user=user
    )
    if created:
        return join_request
    if join_request.status == JoinRequest.Status.PENDING:
        raise JoinRequestError("REQUEST_EXISTS", "คุณส่งคำขอเข้าร่วมกิจกรรมนี้แล้ว")
    if join_request.status == JoinRequest.Status.APPROVED and (
        membership is None or membership.left_at is None
    ):
        raise JoinRequestError("REQUEST_DECIDED", "คำขอนี้ได้รับการตัดสินแล้ว")

    # Schema contract 4.1.1: reuse the latest request after rejection/withdrawal.
    join_request.status = JoinRequest.Status.PENDING
    join_request.created_at = now
    join_request.decided_at = None
    join_request.decided_by = None
    join_request.save(update_fields=["status", "created_at", "decided_at", "decided_by"])
    return join_request
