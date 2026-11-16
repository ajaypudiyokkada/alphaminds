from __future__ import annotations

from datetime import timedelta

from django.db import models

from core.models import TimeStampedActiveModel


class ProgramTypeChoices(models.TextChoices):
    SIX_MONTH = "6_month", "6-Month Intensive"
    THREE_MONTH = "3_month", "3-Month Program"
    ONE_OFF = "one_off", "One-Off Sessions"


class ProgramStatusChoices(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class ProgramSessionStatusChoices(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No Show"


# ── Program Template ─────────────────────────────────────────────────────────

class ProgramTemplate(TimeStampedActiveModel):
    program_type = models.CharField(
        max_length=20,
        choices=ProgramTypeChoices.choices,
        unique=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_weeks = models.PositiveIntegerField(help_text="Total weeks (0 for one-off)")
    sessions_per_week = models.PositiveIntegerField(default=1)
    protocols = models.ManyToManyField(
        "kpis.KPIProtocol",
        related_name="program_templates",
        blank=True,
        help_text="KPI protocols to capture each session",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "program_template"
        ordering = ["program_type"]

    def __str__(self):
        return self.name

    @property
    def total_sessions(self):
        if self.program_type == ProgramTypeChoices.ONE_OFF:
            return self.sessions_per_week  # treat as total count
        return self.duration_weeks * self.sessions_per_week


# ── Program ───────────────────────────────────────────────────────────────────

class Program(TimeStampedActiveModel):
    athlete = models.ForeignKey(
        "athletes.Athlete",
        on_delete=models.CASCADE,
        related_name="programs",
    )
    enrollment = models.ForeignKey(
        "athletes.AthleteEnrollment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="programs",
    )
    template = models.ForeignKey(
        ProgramTemplate,
        on_delete=models.PROTECT,
        related_name="programs",
    )
    mtq_session = models.ForeignKey(
        "assessments.AssessmentSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommended_programs",
        help_text="MTQ assessment that triggered this program",
    )
    program_type = models.CharField(max_length=20, choices=ProgramTypeChoices.choices)
    status = models.CharField(
        max_length=20,
        choices=ProgramStatusChoices.choices,
        default=ProgramStatusChoices.DRAFT,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    mtq_total_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="MTQ total score that determined this program",
    )
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "program"
        ordering = ["-start_date", "-id"]
        indexes = [
            models.Index(fields=["athlete", "status"], name="program_ath_status_idx"),
        ]

    def __str__(self):
        return f"{self.athlete} — {self.get_program_type_display()} ({self.start_date})"

    def save(self, *args, **kwargs):
        if not self.end_date and self.template and self.template.duration_weeks:
            self.end_date = self.start_date + timedelta(weeks=self.template.duration_weeks)
        super().save(*args, **kwargs)

    def generate_sessions(self):
        """Auto-generate ProgramSession rows from the template blueprint."""
        total = self.template.total_sessions
        existing = self.sessions.count()
        if existing >= total:
            return 0

        protocols = list(self.template.protocols.all())
        created = 0

        if self.template.program_type == ProgramTypeChoices.ONE_OFF:
            for i in range(existing, total):
                ProgramSession.objects.create(
                    program=self,
                    session_number=i + 1,
                    scheduled_date=self.start_date,
                )
                created += 1
        else:
            spw = self.template.sessions_per_week
            for i in range(existing, total):
                week = i // spw
                day_in_week = i % spw
                day_offset = week * 7 + (day_in_week * (7 // max(spw, 1)))
                session_date = self.start_date + timedelta(days=day_offset)
                ProgramSession.objects.create(
                    program=self,
                    session_number=i + 1,
                    scheduled_date=session_date,
                )
                created += 1

        return created


# ── Program Session ───────────────────────────────────────────────────────────

class ProgramSession(TimeStampedActiveModel):
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    session_number = models.PositiveIntegerField()
    scheduled_date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=ProgramSessionStatusChoices.choices,
        default=ProgramSessionStatusChoices.SCHEDULED,
    )
    assessment_session = models.OneToOneField(
        "assessments.AssessmentSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="program_session",
        help_text="Linked assessment session with KPI data",
    )
    coach_notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "program_session"
        ordering = ["program", "session_number"]
        indexes = [
            models.Index(fields=["program", "scheduled_date"], name="progsess_prog_date_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["program", "session_number"],
                name="progsess_unique_number",
            ),
        ]

    def __str__(self):
        return f"Session {self.session_number} — {self.scheduled_date} ({self.get_status_display()})"
