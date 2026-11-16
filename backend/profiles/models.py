from django.db import models

from core.choices import SourceTypeChoices
from core.models import TimeStampedActiveModel


class PersonalityType(TimeStampedActiveModel):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    group_name = models.CharField(max_length=100, blank=True, db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "personality_type"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class AthletePersonalityProfile(TimeStampedActiveModel):
    athlete = models.ForeignKey(
        "athletes.Athlete",
        on_delete=models.CASCADE,
        related_name="personality_profiles",
    )
    personality_type = models.ForeignKey(
        "profiles.PersonalityType",
        on_delete=models.PROTECT,
        related_name="athlete_profiles",
    )
    assessment_session = models.ForeignKey(
        "assessments.AssessmentSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="personality_profiles",
    )
    assessed_on = models.DateField(db_index=True)
    source = models.CharField(
        max_length=50,
        choices=SourceTypeChoices.choices,
        blank=True,
        db_index=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "athlete_personality_profile"
        ordering = ["-assessed_on", "-id"]
        indexes = [
            models.Index(fields=["athlete", "assessed_on"], name="ath_pers_ath_date_idx"),
            models.Index(fields=["personality_type", "assessed_on"], name="ath_pers_type_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.athlete} - {self.personality_type} ({self.assessed_on})"
