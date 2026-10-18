"""Shared Party rules. Writers must lock Party before requests/memberships."""

from datetime import datetime

from django.db import transaction
from django.utils import timezone
from venues.services import ScheduleError, validate_party_schedule

from .models import JoinRequest, Party, PartyMembership


class PartyError(Exception):
    def __init__(self, code, message, status=400, fields=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.fields = fields


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
    """Validate basic fields and persist Party and Host membership together.

    The caller must supply the authenticated user and parsed datetimes.
    Validate the full schedule with the shared US9 rules before writing.
    """
    fields = {}
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 150:
        fields["title"] = "กรุณาระบุชื่อกิจกรรมไม่เกิน 150 ตัวอักษร"
    if not isinstance(description, str) or len(description) > 2000:
        fields["description"] = "รายละเอียดต้องเป็นข้อความไม่เกิน 2,000 ตัวอักษร"
    if type(capacity) is not int or capacity < 1:
        fields["capacity"] = "จำนวนผู้เข้าร่วมต้องเป็นจำนวนเต็มตั้งแต่ 1 ขึ้นไป"
    for field, value in (("starts_at", starts_at), ("ends_at", ends_at)):
        if not isinstance(value, datetime) or timezone.is_naive(value):
            fields[field] = "กรุณาระบุวันเวลาที่มี timezone"
    if fields:
        raise PartyError("INVALID_INPUT", "ข้อมูลกิจกรรมไม่ถูกต้อง", fields=fields)

    if starts_at <= timezone.now():
        fields["starts_at"] = "เวลาเริ่มกิจกรรมต้องอยู่ในอนาคต"
    if ends_at <= starts_at:
        fields["ends_at"] = "เวลาสิ้นสุดต้องอยู่หลังเวลาเริ่ม"
    if fields:
        raise PartyError("INVALID_TIME_RANGE", "ช่วงเวลาไม่ถูกต้อง", fields=fields)

    try:
        validate_party_schedule(sport_id, venue_id, starts_at, ends_at)
    except ScheduleError as error:
        raise PartyError(error.code, error.message, error.status, error.fields) from error

    party = Party.objects.create(
        host=user,
        title=title.strip(),
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
