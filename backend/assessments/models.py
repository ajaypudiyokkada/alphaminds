import uuid

from django.core.exceptions import ValidationError
from django.db import models

from core.choices import AssessmentSessionStatusChoices, SourceTypeChoices, ValueDataTypeChoices
from core.models import TimeStampedActiveModel


class AssessmentSession(TimeStampedActiveModel):
    session_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    athlete = models.ForeignKey(
        "athletes.Athlete",
        on_delete=models.CASCADE,
        related_name="assessment_sessions",
    )
    enrollment = models.ForeignKey(
        "athletes.AthleteEnrollment",
        on_delete=models.PROTECT,
        related_name="assessment_sessions",
        null=True,
        blank=True,
    )
    center = models.ForeignKey(
        "orgs.Center",
        on_delete=models.PROTECT,
        related_name="assessment_sessions",
    )
    sport = models.ForeignKey(
        "sports.Sport",
        on_delete=models.PROTECT,
        related_name="assessment_sessions",
    )
    protocol = models.ForeignKey(
        "kpis.KPIProtocol",
        on_delete=models.PROTECT,
        related_name="assessment_sessions",
    )
    assessed_on = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=30,
        choices=AssessmentSessionStatusChoices.choices,
        default=AssessmentSessionStatusChoices.DRAFT,
        db_index=True,
    )
    source = models.CharField(
        max_length=50,
        choices=SourceTypeChoices.choices,
        blank=True,
        db_index=True,
    )
    source_reference = models.CharField(max_length=100, blank=True, db_index=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "assessment_session"
        ordering = ["-assessed_on", "-id"]
        indexes = [
            models.Index(fields=["athlete", "assessed_on"], name="assess_sess_ath_date_idx"),
            models.Index(fields=["athlete", "protocol", "assessed_on"], name="assess_sess_ath_proto_idx"),
            models.Index(fields=["center", "sport", "assessed_on"], name="assess_sess_ctx_date_idx"),
            models.Index(fields=["protocol", "assessed_on"], name="assess_sess_proto_date_idx"),
            models.Index(fields=["status", "assessed_on"], name="assess_sess_status_date_idx"),
        ]

    def clean(self):
        if self.enrollment:
            if self.enrollment.athlete_id != self.athlete_id:
                raise ValidationError("Enrollment athlete must match assessment athlete.")
            if self.enrollment.center_id != self.center_id:
                raise ValidationError("Enrollment center must match assessment center.")
            if self.enrollment.sport_id != self.sport_id:
                raise ValidationError("Enrollment sport must match assessment sport.")

    def __str__(self) -> str:
        return f"{self.athlete} / {self.protocol} / {self.assessed_on:%Y-%m-%d %H:%M}"


class AssessmentMetricValue(TimeStampedActiveModel):
    assessment_session = models.ForeignKey(
        "assessments.AssessmentSession",
        on_delete=models.CASCADE,
        related_name="metric_values",
    )
    metric_definition = models.ForeignKey(
        "kpis.MetricDefinition",
        on_delete=models.PROTECT,
        related_name="assessment_values",
    )
    numeric_value = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True, db_index=True)
    text_value = models.TextField(blank=True)
    boolean_value = models.BooleanField(null=True, blank=True, db_index=True)
    date_value = models.DateField(null=True, blank=True, db_index=True)
    json_value = models.JSONField(default=dict, blank=True)
    display_value = models.CharField(max_length=255, blank=True)
    value_data_type = models.CharField(
        max_length=30,
        choices=ValueDataTypeChoices.choices,
        db_index=True,
    )
    units = models.CharField(max_length=50, blank=True)
    sequence_no = models.PositiveIntegerField(default=1, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "assessment_metric_value"
        ordering = ["sequence_no", "id"]
        indexes = [
            models.Index(fields=["assessment_session", "metric_definition"], name="assess_val_sess_metric_idx"),
            models.Index(fields=["metric_definition", "numeric_value"], name="assess_val_metric_num_idx"),
            models.Index(fields=["metric_definition", "value_data_type"], name="assess_val_metric_dtype_idx"),
            models.Index(fields=["metric_definition", "date_value"], name="assess_val_metric_date_idx"),
            models.Index(fields=["metric_definition", "boolean_value"], name="assess_val_metric_bool_idx"),
            models.Index(fields=["sequence_no", "metric_definition"], name="assess_val_seq_metric_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment_session", "metric_definition", "sequence_no"],
                name="assessment_metric_value_unique_seq",
            ),
        ]

    def clean(self):
        populated = 0
        if self.numeric_value is not None:
            populated += 1
        if self.text_value not in ("", None):
            populated += 1
        if self.boolean_value is not None:
            populated += 1
        if self.date_value is not None:
            populated += 1
        if self.json_value not in ({}, None):
            populated += 1

        if populated == 0:
            raise ValidationError("At least one typed value field must be populated.")

        if populated > 1 and self.value_data_type != ValueDataTypeChoices.JSON:
            raise ValidationError("Only one typed value field may be populated unless value_data_type is json.")

    def save(self, *args, **kwargs):
        if not self.value_data_type and self.metric_definition_id:
            self.value_data_type = self.metric_definition.value_data_type
        if not self.units and self.metric_definition_id:
            self.units = self.metric_definition.units

        if not self.display_value:
            if self.numeric_value is not None:
                self.display_value = str(self.numeric_value)
            elif self.text_value:
                self.display_value = self.text_value
            elif self.boolean_value is not None:
                self.display_value = str(self.boolean_value)
            elif self.date_value is not None:
                self.display_value = self.date_value.isoformat()
            elif self.json_value:
                self.display_value = "JSON"

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.metric_definition} = {self.display_value}"
