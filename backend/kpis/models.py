from django.db import models

from core.choices import (
    CaptureModeChoices,
    ImportanceChoices,
    InterpretationDirectionChoices,
    SourceTypeChoices,
    ValueDataTypeChoices,
)
from core.models import TimeStampedActiveModel


class KPIDomain(TimeStampedActiveModel):
    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "kpi_domain"
        ordering = ["display_order", "name"]

    def __str__(self) -> str:
        return self.name


class KPIFramework(TimeStampedActiveModel):
    domain = models.ForeignKey(
        "kpis.KPIDomain",
        on_delete=models.PROTECT,
        related_name="frameworks",
    )
    code = models.SlugField(max_length=120, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "kpi_framework"
        ordering = ["domain__display_order", "display_order", "name"]
        indexes = [
            models.Index(fields=["domain", "display_order"], name="kpi_fw_domain_order_idx"),
            models.Index(fields=["domain", "name"], name="kpi_fw_domain_name_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["domain", "name"], name="kpi_framework_domain_name_uq"),
        ]

    def __str__(self) -> str:
        return f"{self.domain} / {self.name}"


class KPIProtocol(TimeStampedActiveModel):
    framework = models.ForeignKey(
        "kpis.KPIFramework",
        on_delete=models.PROTECT,
        related_name="protocols",
    )
    code = models.SlugField(max_length=150, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    description = models.TextField(blank=True)
    source_type = models.CharField(
        max_length=50,
        choices=SourceTypeChoices.choices,
        blank=True,
        db_index=True,
    )
    capture_mode = models.CharField(
        max_length=50,
        choices=CaptureModeChoices.choices,
        blank=True,
        db_index=True,
    )
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "kpi_protocol"
        ordering = ["framework__display_order", "display_order", "name"]
        indexes = [
            models.Index(fields=["framework", "display_order"], name="kpi_protocol_fw_order_idx"),
            models.Index(fields=["framework", "name"], name="kpi_protocol_fw_name_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["framework", "name"], name="kpi_protocol_fw_name_uq"),
        ]

    def __str__(self) -> str:
        return f"{self.framework} / {self.name}"


class MetricDefinition(TimeStampedActiveModel):
    protocol = models.ForeignKey(
        "kpis.KPIProtocol",
        on_delete=models.PROTECT,
        related_name="metrics",
    )
    code = models.SlugField(max_length=180, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    label = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    value_data_type = models.CharField(
        max_length=30,
        choices=ValueDataTypeChoices.choices,
        db_index=True,
    )
    units = models.CharField(max_length=50, blank=True, db_index=True)
    importance = models.CharField(
        max_length=30,
        choices=ImportanceChoices.choices,
        blank=True,
        db_index=True,
    )
    interpretation_direction = models.CharField(
        max_length=20,
        choices=InterpretationDirectionChoices.choices,
        blank=True,
        db_index=True,
    )
    min_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    max_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    allowed_text_values = models.JSONField(default=list, blank=True)
    is_required = models.BooleanField(default=False, db_index=True)
    is_higher_better = models.BooleanField(null=True, blank=True, db_index=True)
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "metric_definition"
        ordering = ["protocol__display_order", "display_order", "name"]
        indexes = [
            models.Index(fields=["protocol", "display_order"], name="metric_def_protocol_order_idx"),
            models.Index(fields=["protocol", "value_data_type"], name="metric_def_protocol_dtype_idx"),
            models.Index(fields=["protocol", "name"], name="metric_def_protocol_name_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["protocol", "name"], name="metric_definition_protocol_name_uq"),
        ]

    def __str__(self) -> str:
        return f"{self.protocol} / {self.name}"
