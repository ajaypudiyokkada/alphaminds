from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string

from core.choices import AthleteLevelChoices, EnrollmentStatusChoices, GenderChoices
from core.models import TimeStampedActiveModel


User = get_user_model()


class Athlete(TimeStampedActiveModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="athlete_profile",
    )
    external_ref = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    first_name = models.CharField(max_length=100, db_index=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True, db_index=True)
    full_name = models.CharField(max_length=255, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True, db_index=True)
    gender = models.CharField(max_length=20, choices=GenderChoices.choices, blank=True, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    dominant_hand = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "athlete"
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["first_name", "last_name"], name="athlete_name_idx"),
        ]

    def _generate_full_name(self) -> str:
        return " ".join(
            part.strip() for part in [self.first_name, self.middle_name, self.last_name] if part and part.strip()
        )

    def _candidate_usernames(self):
        parts = [p.lower() for p in [self.first_name, self.last_name] if p and p.strip()]
        base_name = ".".join(parts) if parts else f"athlete{self.pk or ''}"
        candidates = [base_name]

        if self.external_ref:
            candidates.append(str(self.external_ref).strip().lower())

        if self.email:
            email_prefix = self.email.split("@")[0].strip().lower()
            if email_prefix:
                candidates.append(email_prefix)

        if self.phone:
            phone_digits = "".join(ch for ch in str(self.phone) if ch.isdigit())
            if phone_digits:
                candidates.append(f"athlete{phone_digits[-6:]}")

        # fallback after pk exists
        if self.pk:
            candidates.append(f"{base_name}.{self.pk}")
            candidates.append(f"athlete.{self.pk}")

        seen = set()
        for candidate in candidates:
            candidate = candidate.replace(" ", "").replace("..", ".").strip(".")
            if candidate and candidate not in seen:
                seen.add(candidate)
                yield candidate

    def _generate_unique_username(self) -> str:
        for candidate in self._candidate_usernames():
            if not User.objects.filter(username=candidate).exclude(pk=getattr(self.user, "pk", None)).exists():
                return candidate

        while True:
            fallback = f"athlete.{self.pk}.{get_random_string(4).lower()}"
            if not User.objects.filter(username=fallback).exists():
                return fallback

    def _ensure_athlete_group(self):
        group, _ = Group.objects.get_or_create(name="Athlete")
        return group

    def ensure_linked_user(self):
        if self.user_id:
            updated = False

            expected_email = self.email or ""
            if self.user.email != expected_email:
                self.user.email = expected_email
                updated = True

            expected_first_name = self.first_name or ""
            if self.user.first_name != expected_first_name:
                self.user.first_name = expected_first_name
                updated = True

            expected_last_name = self.last_name or ""
            if self.user.last_name != expected_last_name:
                self.user.last_name = expected_last_name
                updated = True

            athlete_group = self._ensure_athlete_group()
            if not self.user.groups.filter(pk=athlete_group.pk).exists():
                self.user.groups.add(athlete_group)

            if updated:
                self.user.save(update_fields=["first_name", "last_name", "email"])

            meta = self.metadata or {}
            meta["login_username"] = self.user.username
            self.metadata = meta
            return

        username = self._generate_unique_username()
        temp_password = get_random_string(12)

        user = User.objects.create_user(
            username=username,
            email=self.email or "",
            password=temp_password,
            first_name=self.first_name or "",
            last_name=self.last_name or "",
        )

        athlete_group = self._ensure_athlete_group()
        user.groups.add(athlete_group)

        self.user = user

        meta = self.metadata or {}
        meta["login_username"] = user.username
        self.metadata = meta

        # Never persisted. Available only on this in-memory instance so the
        # creating view can show it once to staff.
        self.generated_password = temp_password

    def save(self, *args, **kwargs):
        generated_full_name = self._generate_full_name()
        if generated_full_name:
            self.full_name = generated_full_name

        is_new = self.pk is None
        super().save(*args, **kwargs)

        self.ensure_linked_user()

        update_fields = ["user", "metadata", "updated_at"]
        if is_new:
            Athlete.objects.filter(pk=self.pk).update(
                user=self.user,
                metadata=self.metadata,
            )
        else:
            super().save(update_fields=update_fields)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def age_group(self):
        a = self.age
        if a is None:
            return None
        if a < 8:
            return "Under 8"
        if a <= 10:
            return "8-10"
        if a <= 13:
            return "11-13"
        if a <= 16:
            return "14-16"
        if a <= 19:
            return "17-19"
        return "20+"

    def __str__(self) -> str:
        return self.full_name


class AthleteSport(TimeStampedActiveModel):
    athlete = models.ForeignKey(
        "athletes.Athlete",
        on_delete=models.CASCADE,
        related_name="athlete_sports",
    )
    sport = models.ForeignKey(
        "sports.Sport",
        on_delete=models.PROTECT,
        related_name="athlete_sports",
    )
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    level = models.CharField(
        max_length=50,
        choices=AthleteLevelChoices.choices,
        blank=True,
        db_index=True,
    )
    role_or_position = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "athlete_sport"
        ordering = ["-is_primary", "-start_date", "id"]
        indexes = [
            models.Index(fields=["athlete", "sport", "is_primary"], name="ath_sport_primary_idx"),
            models.Index(fields=["athlete", "start_date", "end_date"], name="ath_sport_dates_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["athlete", "sport", "start_date"],
                name="athlete_sport_unique_start",
            ),
        ]

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("end_date cannot be earlier than start_date.")

    def __str__(self) -> str:
        return f"{self.athlete} - {self.sport}"


class AthleteCenter(TimeStampedActiveModel):
    athlete = models.ForeignKey(
        "athletes.Athlete",
        on_delete=models.CASCADE,
        related_name="athlete_centers",
    )
    center = models.ForeignKey(
        "orgs.Center",
        on_delete=models.PROTECT,
        related_name="athlete_centers",
    )
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    is_primary = models.BooleanField(default=False, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "athlete_center"
        ordering = ["-is_primary", "-start_date", "id"]
        indexes = [
            models.Index(fields=["athlete", "center", "is_primary"], name="ath_center_primary_idx"),
            models.Index(fields=["center", "start_date", "end_date"], name="ath_center_dates_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["athlete", "center", "start_date"],
                name="athlete_center_unique_start",
            ),
        ]

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("end_date cannot be earlier than start_date.")

    def __str__(self) -> str:
        return f"{self.athlete} - {self.center}"


class AthleteEnrollment(TimeStampedActiveModel):
    athlete = models.ForeignKey(
        "athletes.Athlete",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    center = models.ForeignKey(
        "orgs.Center",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    sport = models.ForeignKey(
        "sports.Sport",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    enrollment_code = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    status = models.CharField(
        max_length=30,
        choices=EnrollmentStatusChoices.choices,
        default=EnrollmentStatusChoices.ACTIVE,
        db_index=True,
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    batch_name = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "athlete_enrollment"
        ordering = ["-start_date", "id"]
        indexes = [
            models.Index(fields=["athlete", "center", "sport", "status"], name="enroll_ctx_status_idx"),
            models.Index(fields=["center", "sport", "status"], name="enroll_center_sport_idx"),
            models.Index(fields=["athlete", "start_date", "end_date"], name="enroll_ath_dates_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["athlete", "center", "sport", "start_date"],
                name="athlete_enrollment_unique_start",
            ),
        ]

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("end_date cannot be earlier than start_date.")

    def __str__(self) -> str:
        return f"{self.athlete} @ {self.center} / {self.sport}"