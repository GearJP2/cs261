"""Shared read rules for Party details and subsequent Party features."""

from django.utils import timezone


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
