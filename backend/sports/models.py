from django.db import models

from core.models import TimeStampedActiveModel


class Sport(TimeStampedActiveModel):
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "sport"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
