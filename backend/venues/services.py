"""Schedule rules shared by Party creation and editing services."""

from datetime import datetime
from zoneinfo import ZoneInfo

from django.utils import timezone

from .models import Venue, VenueSport

BANGKOK = ZoneInfo("Asia/Bangkok")


class ScheduleValidationError(Exception):
    def __init__(self, code, message, fields=None, status=400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.fields = fields
        self.status = status


def validate_party_schedule(sport_id, venue_id, starts_at, ends_at):
    """Validate aware datetimes; return None or raise ScheduleValidationError.

    Call with the full merged schedule on PATCH, before saving in the writer's
    transaction. This checks opening hours, not reservations or Party state.
    """
    for field, value in (("sport_id", sport_id), ("venue_id", venue_id)):
        if type(value) is not int or value <= 0 or value > 9223372036854775807:
            raise ScheduleValidationError(
                "INVALID_INPUT", "ID ต้องเป็นจำนวนเต็มบวก", {field: "ID ไม่ถูกต้อง"}
            )
    for field, value in (("starts_at", starts_at), ("ends_at", ends_at)):
        if not isinstance(value, datetime) or timezone.is_naive(value):
            raise ScheduleValidationError(
                "INVALID_TIME_RANGE", "วันเวลาต้องมี timezone offset", {field: "ระบุ offset"}
            )
    start = starts_at.astimezone(BANGKOK)
    end = ends_at.astimezone(BANGKOK)
    if start >= end or start.date() != end.date():
        raise ScheduleValidationError("INVALID_TIME_RANGE", "เวลาเริ่มต้องก่อนเวลาจบและอยู่ในวันเดียวกัน")
    try:
        venue = Venue.objects.get(pk=venue_id, is_active=True)
    except Venue.DoesNotExist:
        raise ScheduleValidationError("NOT_FOUND", "ไม่พบสนามที่เปิดใช้งาน", status=404) from None
    if not VenueSport.objects.filter(venue=venue, sport_id=sport_id).exists():
        raise ScheduleValidationError(
            "INVALID_INPUT", "สนามไม่รองรับกีฬาที่เลือก", {"sport_id": "กีฬาไม่ตรงกับสนาม"}
        )
    intervals = list(venue.opening_hours.filter(weekday=start.weekday()).order_by("opens_at"))
    previous_end = None
    for interval in intervals:
        if previous_end is not None and interval.opens_at < previous_end:
            raise ScheduleValidationError(
                "INVALID_OPENING_HOURS", "ตารางเวลาเปิดสนามซ้อนกัน กรุณาติดต่อผู้ดูแล"
            )
        previous_end = interval.closes_at
    if not any(
        interval.opens_at <= start.time() and end.time() <= interval.closes_at
        for interval in intervals
    ):
        raise ScheduleValidationError("VENUE_CLOSED", "ช่วงเวลาที่เลือกอยู่นอกเวลาเปิดสนาม")
