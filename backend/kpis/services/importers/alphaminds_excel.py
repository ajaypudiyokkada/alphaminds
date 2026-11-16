from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any

from django.db import transaction
from openpyxl import load_workbook

from assessments.models import AssessmentMetricValue, AssessmentSession
from athletes.models import Athlete, AthleteCenter, AthleteEnrollment, AthleteSport
from kpis.models import KPIDomain, KPIFramework, KPIProtocol, MetricDefinition
from orgs.models import Center
from profiles.models import PersonalityType
from sports.models import Sport


@dataclass
class ImportCounters:
    domains_created: int = 0
    frameworks_created: int = 0
    protocols_created: int = 0
    metrics_created: int = 0
    personality_types_created: int = 0
    athletes_created: int = 0
    centers_created: int = 0
    sports_created: int = 0
    enrollments_created: int = 0
    sessions_created: int = 0
    values_created: int = 0


class AlphaMindsExcelImporter:
    """
    Corrected importer for AlphaMindDashboard.xlsx.

    Important workbook mapping used here:
    - KPICategory1 -> KPI Domain
    - first KPICategory2 -> KPI Framework
    - second KPICategory2 -> KPI Protocol
    - KPICategory3 -> Metric Definition

    The workbook contains duplicated header names, so this importer resolves
    taxonomy columns by position rather than by naive dict lookups.
    """

    def __init__(
        self,
        *,
        file_path: Path,
        stdout,
        style,
        dry_run: bool = False,
        main_sheet_name: str | None = None,
        personality_sheet_name: str | None = None,
    ) -> None:
        self.file_path = Path(file_path)
        self.stdout = stdout
        self.style = style
        self.dry_run = dry_run
        self.main_sheet_name = main_sheet_name
        self.personality_sheet_name = personality_sheet_name
        self.counters = ImportCounters()

    # -------------------------
    # public API
    # -------------------------
    def run(self, *, import_taxonomy: bool, import_sample_data: bool) -> dict[str, Any]:
        wb = load_workbook(self.file_path, data_only=True)

        main_sheet = self._get_main_sheet(wb)
        personality_sheet = self._get_personality_sheet(wb)

        with transaction.atomic():
            if import_taxonomy:
                self._import_taxonomy_from_main_sheet(main_sheet)
                if personality_sheet is not None:
                    self._import_personality_types(personality_sheet)

            if import_sample_data:
                self._import_sample_data_from_main_sheet(main_sheet)

            if self.dry_run:
                transaction.set_rollback(True)

        return {
            "domains_created": self.counters.domains_created,
            "frameworks_created": self.counters.frameworks_created,
            "protocols_created": self.counters.protocols_created,
            "metrics_created": self.counters.metrics_created,
            "personality_types_created": self.counters.personality_types_created,
            "athletes_created": self.counters.athletes_created,
            "centers_created": self.counters.centers_created,
            "sports_created": self.counters.sports_created,
            "enrollments_created": self.counters.enrollments_created,
            "sessions_created": self.counters.sessions_created,
            "values_created": self.counters.values_created,
        }

    # -------------------------
    # sheet helpers
    # -------------------------
    def _get_main_sheet(self, wb):
        if self.main_sheet_name:
            return wb[self.main_sheet_name]

        if "AlphaMindDataSet" in wb.sheetnames:
            return wb["AlphaMindDataSet"]

        raise ValueError("Main data sheet not found. Expected 'AlphaMindDataSet' or --sheet override.")

    def _get_personality_sheet(self, wb):
        if self.personality_sheet_name:
            return wb[self.personality_sheet_name]

        for sheet_name in wb.sheetnames:
            normalized = self._norm(sheet_name)
            if "personality" in normalized and "type" in normalized:
                return wb[sheet_name]

        return None

    # -------------------------
    # row extraction
    # -------------------------
    def _header_positions(self, ws) -> dict[str, list[int]]:
        positions: dict[str, list[int]] = {}
        for col_idx in range(1, ws.max_column + 1):
            header = ws.cell(1, col_idx).value
            if header is None:
                continue
            key = self._norm(header)
            positions.setdefault(key, []).append(col_idx)
        return positions

    def _iter_rows_as_maps(self, ws):
        positions = self._header_positions(ws)

        for row_idx in range(2, ws.max_row + 1):
            row = {
                "_row_idx": row_idx,
                "player_first_name": self._cell(ws, row_idx, positions, "playerfirstname"),
                "player_middle_name": self._cell(ws, row_idx, positions, "playermiddlename"),
                "player_last_name": self._cell(ws, row_idx, positions, "playerlastname"),
                "player_name": self._cell(ws, row_idx, positions, "playername"),
                "dob": self._cell(ws, row_idx, positions, "dob"),
                "gender": self._cell(ws, row_idx, positions, "gender"),
                "email": self._cell(ws, row_idx, positions, "email"),
                "sport_name": self._cell(ws, row_idx, positions, "sportstype"),
                "center_name": self._cell(ws, row_idx, positions, "center"),
                "domain_name": self._cell(ws, row_idx, positions, "kpicategory1"),
                "framework_name": self._cell_n(ws, row_idx, positions, "kpicategory2", 0),
                "protocol_name": self._cell_n(ws, row_idx, positions, "kpicategory2", 1),
                "metric_name": self._cell(ws, row_idx, positions, "kpicategory3"),
                "legacy_kpi_name": self._cell(ws, row_idx, positions, "kpi"),
                "description": self._cell(ws, row_idx, positions, "description"),
                "assessed_date": self._cell(ws, row_idx, positions, "date"),
                "month": self._cell(ws, row_idx, positions, "month"),
                "year": self._cell(ws, row_idx, positions, "year"),
                "value": self._cell(ws, row_idx, positions, "value"),
                "value_data_type": self._cell(ws, row_idx, positions, "valuedatatype"),
                "importance": self._cell(ws, row_idx, positions, "dataimportance")
                or self._cell(ws, row_idx, positions, "dataimportance")
                or self._cell(ws, row_idx, positions, "dataimportance")
                or self._cell(ws, row_idx, positions, "dataimportance")
                or self._cell(ws, row_idx, positions, "dataimportance")
                or self._cell(ws, row_idx, positions, "dataimportance")
                or self._cell(ws, row_idx, positions, "dataimportance")
                or self._cell(ws, row_idx, positions, "dataimportance"),
                "units": self._cell(ws, row_idx, positions, "units"),
                "training": self._cell(ws, row_idx, positions, "training"),
            }

            # handle weird workbook header: "DataIMportance"
            if not row["importance"]:
                row["importance"] = self._cell(ws, row_idx, positions, "dataimportance") or self._cell(
                    ws, row_idx, positions, "dataimportance"
                )
            if not row["importance"]:
                row["importance"] = self._cell(ws, row_idx, positions, "dataimportance")
            if not row["importance"]:
                row["importance"] = self._cell(ws, row_idx, positions, "dataimportance")
            if not row["importance"]:
                row["importance"] = self._cell(ws, row_idx, positions, "dataimportance")
            if not row["importance"]:
                row["importance"] = self._cell(ws, row_idx, positions, "dataimportance")
            if not row["importance"] and "dataimportance" not in positions:
                weird_key = self._norm("DataIMportance")
                row["importance"] = self._cell(ws, row_idx, positions, weird_key)

            # user-confirmed correction:
            # KPICategory1 = Domain
            # KPICategory2 = Framework
            # KPICategory3 = Protocol
            # KPICategory4 = Metric Definitions
            #
            # Actual workbook shape:
            #   KPICategory1, KPICategory2, KPICategory2, KPICategory3, KPI
            # therefore:
            #   first KPICategory2  -> Framework
            #   second KPICategory2 -> Protocol
            #   KPICategory3        -> Metric Definition
            #   KPI                 -> legacy/optional metric label
            #
            # If protocol is blank but KPI exists, do NOT shift everything forward.
            # The source workbook's protocol column can be blank on sparse rows.
            if not any(
                [
                    row["domain_name"],
                    row["framework_name"],
                    row["protocol_name"],
                    row["metric_name"],
                    row["player_name"],
                ]
            ):
                continue

            yield row

    def _cell(self, ws, row_idx: int, positions: dict[str, list[int]], key: str):
        idxs = positions.get(key) or []
        if not idxs:
            return None
        return ws.cell(row_idx, idxs[0]).value

    def _cell_n(self, ws, row_idx: int, positions: dict[str, list[int]], key: str, n: int):
        idxs = positions.get(key) or []
        if len(idxs) <= n:
            return None
        return ws.cell(row_idx, idxs[n]).value

    # -------------------------
    # taxonomy import
    # -------------------------
    def _import_taxonomy_from_main_sheet(self, ws) -> None:
        for row in self._iter_rows_as_maps(ws):
            domain_name = self._clean_text(row["domain_name"])
            framework_name = self._clean_text(row["framework_name"])
            protocol_name = self._clean_text(row["protocol_name"])
            metric_name = self._clean_text(row["metric_name"])

            if not all([domain_name, framework_name, protocol_name, metric_name]):
                continue

            domain, created = KPIDomain.objects.get_or_create(
                code=self._slug(domain_name),
                defaults={
                    "name": domain_name,
                },
            )
            if created:
                self.counters.domains_created += 1

            framework, created = KPIFramework.objects.get_or_create(
                domain=domain,
                name=framework_name,
                defaults={
                    "code": self._slug(f"{domain_name}-{framework_name}"),
                },
            )
            if created:
                self.counters.frameworks_created += 1

            protocol, created = KPIProtocol.objects.get_or_create(
                framework=framework,
                name=protocol_name,
                defaults={
                    "code": self._slug(f"{domain_name}-{framework_name}-{protocol_name}"),
                },
            )
            if created:
                self.counters.protocols_created += 1

            defaults = {
                "code": self._slug(f"{domain_name}-{framework_name}-{protocol_name}-{metric_name}"),
                "label": metric_name,
                "description": self._clean_text(row["description"]) or "",
                "value_data_type": self._normalize_value_data_type(row["value_data_type"]),
                "units": self._clean_text(row["units"]) or "",
                "importance": self._clean_text(row["importance"]) or "",
                "interpretation_direction": self._interpretation_direction(row["importance"]),
                "is_higher_better": self._is_higher_better(row["importance"]),
            }

            metric, created = MetricDefinition.objects.get_or_create(
                protocol=protocol,
                name=metric_name,
                defaults=defaults,
            )
            if created:
                self.counters.metrics_created += 1
            else:
                updated = False
                for field, value in defaults.items():
                    current = getattr(metric, field)
                    if current in (None, "", {}) and value not in (None, "", {}):
                        setattr(metric, field, value)
                        updated = True
                if updated:
                    metric.save()

    def _import_personality_types(self, ws) -> None:
        header_positions = self._header_positions(ws)

        for row_idx in range(2, ws.max_row + 1):
            code = self._clean_text(self._cell(ws, row_idx, header_positions, "personalitytype"))
            if not code:
                continue

            title = code
            group_name = self._clean_text(self._cell(ws, row_idx, header_positions, "personalitygroup")) or ""
            description = self._clean_text(self._cell(ws, row_idx, header_positions, "description")) or self._clean_text(
                self._cell(ws, row_idx, header_positions, "description")
            ) or ""

            _, created = PersonalityType.objects.get_or_create(
                code=code,
                defaults={
                    "title": title,
                    "group_name": group_name,
                    "description": description,
                },
            )
            if created:
                self.counters.personality_types_created += 1

    # -------------------------
    # sample data import
    # -------------------------
    def _import_sample_data_from_main_sheet(self, ws) -> None:
        for row in self._iter_rows_as_maps(ws):
            domain_name = self._clean_text(row["domain_name"])
            framework_name = self._clean_text(row["framework_name"])
            protocol_name = self._clean_text(row["protocol_name"])
            metric_name = self._clean_text(row["metric_name"])
            player_name = self._clean_text(row["player_name"])
            center_name = self._clean_text(row["center_name"])
            sport_name = self._clean_text(row["sport_name"])

            if not all([domain_name, framework_name, protocol_name, metric_name, player_name, center_name, sport_name]):
                continue

            athlete = self._get_or_create_athlete(row)
            center = self._get_or_create_center(center_name)
            sport = self._get_or_create_sport(sport_name)
            enrollment = self._get_or_create_enrollment(athlete, center, sport, row)

            protocol = KPIProtocol.objects.filter(
                framework__domain__name=domain_name,
                framework__name=framework_name,
                name=protocol_name,
            ).first()
            if not protocol:
                continue

            metric_definition = MetricDefinition.objects.filter(
                protocol=protocol,
                name=metric_name,
            ).first()
            if not metric_definition:
                continue

            assessed_on = self._normalize_assessed_on(row)
            session, created = AssessmentSession.objects.get_or_create(
                athlete=athlete,
                protocol=protocol,
                center=center,
                sport=sport,
                assessed_on=assessed_on,
                defaults={
                    "enrollment": enrollment,
                    "status": "completed",
                },
            )
            if created:
                self.counters.sessions_created += 1

            value_kwargs = self._typed_value_kwargs(row["value"], metric_definition.value_data_type)
            display_value = self._stringify_display_value(row["value"])

            value, created = AssessmentMetricValue.objects.get_or_create(
                assessment_session=session,
                metric_definition=metric_definition,
                sequence_no=1,
                defaults={
                    "value_data_type": metric_definition.value_data_type,
                    "units": metric_definition.units,
                    "display_value": display_value,
                    **value_kwargs,
                },
            )
            if created:
                self.counters.values_created += 1
            else:
                # populate if blank
                changed = False
                if not value.display_value and display_value:
                    value.display_value = display_value
                    changed = True
                if not value.units and metric_definition.units:
                    value.units = metric_definition.units
                    changed = True
                for field, v in value_kwargs.items():
                    if getattr(value, field) in (None, "", {}) and v not in (None, "", {}):
                        setattr(value, field, v)
                        changed = True
                if changed:
                    value.save()

    def _get_or_create_athlete(self, row):
        full_name = self._clean_text(row["player_name"]) or "Unknown Athlete"
        first_name = self._clean_text(row["player_first_name"]) or full_name.split()[0]
        middle_name = self._clean_text(row["player_middle_name"]) or ""
        last_name = self._clean_text(row["player_last_name"]) or " ".join(full_name.split()[1:])

        athlete, created = Athlete.objects.get_or_create(
            full_name=full_name,
            defaults={
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "date_of_birth": self._normalize_date_only(row["dob"]),
                "gender": self._clean_text(row["gender"]) or "",
                "email": self._clean_text(row["email"]) or None,
            },
        )
        if created:
            self.counters.athletes_created += 1
        return athlete

    def _get_or_create_center(self, center_name: str):
        center, created = Center.objects.get_or_create(
            code=self._slug(center_name)[:50],
            defaults={
                "name": center_name,
            },
        )
        if created:
            self.counters.centers_created += 1
        return center

    def _get_or_create_sport(self, sport_name: str):
        sport, created = Sport.objects.get_or_create(
            code=self._slug(sport_name)[:50],
            defaults={
                "name": sport_name,
            },
        )
        if created:
            self.counters.sports_created += 1
        return sport

    def _get_or_create_enrollment(self, athlete, center, sport, row):
        start_date = self._normalize_date_only(row["assessed_date"]) or date.today()

        enrollment, created = AthleteEnrollment.objects.get_or_create(
            athlete=athlete,
            center=center,
            sport=sport,
            start_date=start_date,
            defaults={
                "status": "active",
            },
        )
        if created:
            self.counters.enrollments_created += 1

        AthleteCenter.objects.get_or_create(
            athlete=athlete,
            center=center,
            start_date=start_date,
            defaults={"is_primary": True},
        )
        AthleteSport.objects.get_or_create(
            athlete=athlete,
            sport=sport,
            start_date=start_date,
            defaults={"is_primary": True},
        )

        return enrollment

    # -------------------------
    # normalization helpers
    # -------------------------
    def _normalize_value_data_type(self, value) -> str:
        raw = self._norm(value)
        if raw in {"integer", "int", "count"}:
            return "integer"
        if raw in {"decimal", "float", "number", "numeric"}:
            return "decimal"
        if raw in {"boolean", "bool"}:
            return "boolean"
        if raw in {"date", "datetime"}:
            return "date"
        if raw in {"json", "dict", "object"}:
            return "json"
        return "text"

    def _interpretation_direction(self, importance) -> str:
        raw = self._norm(importance)
        if "higher" in raw and "better" in raw:
            return "higher_better"
        if "lower" in raw and "better" in raw:
            return "lower_better"
        if "subjective" in raw:
            return "subjective"
        return ""

    def _is_higher_better(self, importance):
        raw = self._norm(importance)
        if "higher" in raw and "better" in raw:
            return True
        if "lower" in raw and "better" in raw:
            return False
        return None

    def _typed_value_kwargs(self, raw_value, value_data_type: str) -> dict[str, Any]:
        dtype = self._normalize_value_data_type(value_data_type)

        if raw_value in (None, ""):
            return {}

        if dtype in {"integer", "decimal"}:
            try:
                return {"numeric_value": raw_value}
            except Exception:
                return {"text_value": str(raw_value)}
        if dtype == "boolean":
            if isinstance(raw_value, bool):
                return {"boolean_value": raw_value}
            normalized = self._norm(raw_value)
            return {"boolean_value": normalized in {"true", "yes", "1"}}
        if dtype == "date":
            return {"date_value": self._normalize_date_only(raw_value)}
        if dtype == "json":
            return {"json_value": raw_value if isinstance(raw_value, dict) else {"value": raw_value}}
        return {"text_value": str(raw_value)}

    def _normalize_assessed_on(self, row) -> datetime:
        raw_date = row["assessed_date"]
        if isinstance(raw_date, datetime):
            return raw_date
        if isinstance(raw_date, date):
            return datetime.combine(raw_date, datetime.min.time())

        year = row.get("year")
        month = row.get("month")
        if year and month:
            return datetime(int(year), int(month), 1)

        return datetime.now()

    def _normalize_date_only(self, value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return None

    def _stringify_display_value(self, value) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)

    def _clean_text(self, value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _norm(self, value) -> str:
        if value is None:
            return ""
        return "".join(ch.lower() for ch in str(value).strip() if ch.isalnum())

    def _slug(self, value: str) -> str:
        cleaned = self._clean_text(value) or ""
        slug = []
        prev_dash = False
        for ch in cleaned.lower():
            if ch.isalnum():
                slug.append(ch)
                prev_dash = False
            else:
                if not prev_dash:
                    slug.append("-")
                    prev_dash = True
        result = "".join(slug).strip("-")
        return result[:180] or "unnamed"
