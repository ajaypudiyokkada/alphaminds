from django.db import models


class GenderChoices(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"


class EnrollmentStatusChoices(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    COMPLETED = "completed", "Completed"
    SUSPENDED = "suspended", "Suspended"
    DROPPED = "dropped", "Dropped"


class ValueDataTypeChoices(models.TextChoices):
    INTEGER = "integer", "Integer"
    DECIMAL = "decimal", "Decimal"
    TEXT = "text", "Text"
    BOOLEAN = "boolean", "Boolean"
    DATE = "date", "Date"
    JSON = "json", "JSON"


class ImportanceChoices(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class InterpretationDirectionChoices(models.TextChoices):
    HIGHER_BETTER = "higher_better", "Higher is better"
    LOWER_BETTER = "lower_better", "Lower is better"
    NEUTRAL = "neutral", "Neutral"
    SUBJECTIVE = "subjective", "Subjective"


class AssessmentSessionStatusChoices(models.TextChoices):
    DRAFT = "draft", "Draft"
    BOOKED = "booked", "Booked"
    COMPLETED = "completed", "Completed"
    PUBLISHED = "published", "Published"
    CANCELLED = "cancelled", "Cancelled"
    INVALIDATED = "invalidated", "Invalidated"


class SourceTypeChoices(models.TextChoices):
    MANUAL = "manual", "Manual"
    IMPORT = "import", "Import"
    DEVICE = "device", "Device"
    API = "api", "API"
    SYSTEM = "system", "System"


class CaptureModeChoices(models.TextChoices):
    MANUAL = "manual", "Manual"
    SEMI_AUTOMATED = "semi_automated", "Semi Automated"
    AUTOMATED = "automated", "Automated"


class AthleteLevelChoices(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"
    ELITE = "elite", "Elite"
