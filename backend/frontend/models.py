from django.core.validators import RegexValidator
from django.db import models

from core.models import TimeStampedActiveModel


class LeadInquiryType(models.TextChoices):
    ATHLETE_MENTAL_TOUGHNESS = "athlete_mental_toughness", "Athlete - Personality & Mental Toughness Assessment"
    ATHLETE_COGNITIVE_VISION = "athlete_cognitive_vision", "Athlete - Cognitive Vision Evaluation"
    ATHLETE_EMOTIONAL_REGULATION = "athlete_emotional_regulation", "Athlete - Emotional Regulation Program"
    ACADEMY_PARTNERSHIP = "academy_partnership", "Academy - Explore Alpha Minds"


class GenderChoice(models.TextChoices):
    MALE = "M", "Male"
    FEMALE = "F", "Female"
    OTHER = "O", "Other"


india_mobile_validator = RegexValidator(
    regex=r"^(?:\+91|91)?[6-9]\d{9}$",
    message="Enter a valid India mobile number.",
)


class LeadInquiry(TimeStampedActiveModel):
    inquiry_type = models.CharField(
        max_length=50,
        choices=LeadInquiryType.choices,
        db_index=True,
    )
    # Multi-type: list of LeadInquiryType values; inquiry_type stores the first for filtering
    inquiry_types = models.JSONField(default=list, blank=True)

    # Common identity
    full_name = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(db_index=True)
    mobile_number = models.CharField(max_length=15, validators=[india_mobile_validator], db_index=True)

    # Demographics
    gender = models.CharField(max_length=1, choices=GenderChoice.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    parent_mobile = models.CharField(max_length=15, validators=[india_mobile_validator], blank=True)

    # Location
    pincode = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)

    # Athlete path
    athlete_sport = models.CharField(max_length=100, blank=True, db_index=True)

    # Academy path
    academy_name = models.CharField(max_length=255, blank=True, db_index=True)
    contact_person_name = models.CharField(max_length=255, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    academy_city = models.CharField(max_length=100, blank=True, db_index=True)
    athlete_count = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField(blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "frontend_lead_inquiry"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["inquiry_type", "created_at"], name="lead_inquiry_type_date_idx"),
            models.Index(fields=["academy_name", "academy_city"], name="lead_academy_city_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_inquiry_type_display()} - {self.full_name}"