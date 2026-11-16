from django.conf import settings
from django.db import models

from core.models import TimeStampedActiveModel


class Center(TimeStampedActiveModel):
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    short_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)
    state = models.CharField(max_length=100, blank=True, db_index=True)
    country = models.CharField(max_length=100, default="India", db_index=True)
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "org_center"
        ordering = ["country", "state", "city", "name"]
        indexes = [
            models.Index(fields=["country", "state", "city"], name="org_center_loc_idx"),
        ]

    def __str__(self) -> str:
        return self.short_name or self.name


class StaffProfile(TimeStampedActiveModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    center = models.ForeignKey(
        "orgs.Center",
        on_delete=models.PROTECT,
        related_name="staff_profiles",
    )
    role = models.CharField(max_length=50, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "org_staff_profile"
        ordering = ["center__name", "user__username"]
        indexes = [
            models.Index(fields=["center", "role"], name="staff_profile_center_role_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["user"], name="staff_profile_user_unique"),
        ]

    def __str__(self):
        role = f" ({self.role})" if self.role else ""
        return f"{self.user} @ {self.center}{role}"