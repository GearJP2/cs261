from django.conf import settings
from django.db import models


class Party(models.Model):
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="hosted_parties",
    )
    sport = models.ForeignKey(
        "venues.Sport",
        on_delete=models.PROTECT,
        related_name="parties",
    )
    venue = models.ForeignKey(
        "venues.Venue",
        on_delete=models.PROTECT,
        related_name="parties",
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.IntegerField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1),
                name="party_capacity_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")),
                name="party_end_after_start",
            ),
        ]
        indexes = [
            models.Index(fields=["sport", "starts_at"]),
        ]


class PartyMembership(models.Model):
    party = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="party_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["party", "user"],
                name="unique_party_membership",
            ),
        ]


class JoinRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "รออนุมัติ"
        APPROVED = "Approved", "อนุมัติ"
        REJECTED = "Rejected", "ปฏิเสธ"

    party = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        related_name="join_requests",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="join_requests",
    )
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="decided_join_requests",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["party", "user"],
                name="unique_party_join_request",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        status="Pending",
                        decided_at__isnull=True,
                        decided_by__isnull=True,
                    )
                    | models.Q(
                        status__in=["Approved", "Rejected"],
                        decided_at__isnull=False,
                        decided_by__isnull=False,
                    )
                ),
                name="join_request_valid_decision",
            ),
        ]
        indexes = [
            models.Index(fields=["party", "status", "created_at"]),
        ]