# AlphaMinds Architecture

## 1. Purpose

This document is the single source of truth for AlphaMinds architecture, coding decisions, and build sequencing.

AlphaMinds is a mobile-first athlete intelligence platform built around:
- athlete master data
- center and sport context
- assessment protocols
- KPI definitions
- assessment sessions
- metric values
- derived athlete insights

The platform must support multiple centers, multiple sports, evolving KPI structures, and historical trend analysis without requiring schema rewrites whenever a new assessment protocol or metric is introduced.

---

## 2. Product Scope

### Core business idea
AlphaMinds tracks an athlete across centers, sports, and assessment sessions, then maps raw assessments into structured KPI frameworks and dashboard-ready insights.

### Primary design principle
**Store definitions separately from measurements.**

That means:
- KPI taxonomy lives in master tables
- raw athlete measurements live in event tables
- dashboard summaries live in derived tables

### What AlphaMinds is not
AlphaMinds is **not** a single wide athlete profile table with dozens or hundreds of KPI columns.

---

## 3. Locked Stack

These are frozen unless explicitly changed in this document.

### Backend
- Python
- Django
- PostgreSQL
- Django REST Framework for API exposure where needed

### Frontend approach
- Django templates
- HTMX
- Tailwind CSS
- Mobile-first PWA

### Architecture style
- Monolith-first
- Modular Django apps
- Metadata-driven KPI engine
- Event-sourced measurement design at the assessment layer

### Explicit non-goals for now
- No React frontend in v0.x
- No microservices
- No premature async/event-bus complexity
- No KPI-specific schema branching unless truly unavoidable

---

## 4. Non-Negotiable Coding Rules (Anti-Drift Rules)

These rules exist to prevent architecture drift in future iterations.

### Rule 1: Never replace the metadata-driven KPI model with hardcoded KPI columns
Do not create models like:
- `reaction_time_score`
- `focus_score`
- `memory_score`
- `blazepod_score`

Those belong in `MetricDefinition` and `AssessmentMetricValue`.

### Rule 2: Athlete context must remain separate from measurement facts
Do not place center-, sport-, or session-specific values directly on the `Athlete` model unless they are truly athlete master attributes.

### Rule 3: Raw data and derived data must remain separate
- Raw captured scores go into assessment value tables
- Rollups, trends, percentiles, readiness scores, or dashboards go into derived tables/services

### Rule 4: New assessments must be added primarily through metadata
When a new protocol arrives, prefer:
- new `KPIProtocol`
- new `MetricDefinition`
- maybe new validation/config JSON

Do not alter schema unless the new use case genuinely requires a new domain object.

### Rule 5: Use append-friendly measurement storage
Assessment data is historical. Avoid overwriting prior records.

### Rule 6: Any model that represents time-bound association must include dates/status
Examples:
- athlete-center association
- athlete-sport association
- enrollment
- goals
- benchmarks

### Rule 7: Every foreign key and uniqueness rule must reflect business identity
Avoid weak or arbitrary uniqueness constraints.

### Rule 8: Avoid generic JSON unless justified
Use `JSONField` only for:
- protocol configuration
- raw machine payloads
- flexible validation/configuration
- unmodeled source detail

Do not use JSON as a substitute for relational modeling.

### Rule 9: Any new model must answer these questions before creation
1. Is it master data, transactional data, or derived data?
2. What is its business identity?
3. What owns it?
4. What changes over time?
5. Does it belong as a table or metadata JSON?

### Rule 10: Backward compatibility matters
Future versions should extend v0.1 instead of rewriting it.

### Rule 11: Prefer incremental modifications over rewrites
When changing code:
- modify existing architecture
- do not introduce a parallel architecture
- do not rename core concepts casually

### Rule 12: Keep naming stable
Use these canonical terms:
- Athlete
- Center
- Sport
- Enrollment
- KPI Domain
- KPI Framework
- KPI Protocol
- Metric Definition
- Assessment Session
- Assessment Metric Value

Do not alternate these with random synonyms unless the document is updated.

---

## 5. Domain Vocabulary

### Athlete
The person being assessed.

### Center
The physical or organizational location where the athlete trains or is assessed.

### Sport
The sport context in which the athlete participates.

### Enrollment
The athlete’s contextual participation in a center and sport over a time period.

### KPI Domain
Highest grouping level of KPI taxonomy.
Example: Cognitive Performance.

### KPI Framework
Assessment family under a domain.
Example: Reaction Time.

### KPI Protocol
Specific test or protocol under a framework.
Example: BlazePod Reaction Time.

### Metric Definition
A specific measurable field under a protocol.
Example: Average Reaction Time, Accuracy, Error Count.

### Assessment Session
A recorded assessment event for an athlete under a protocol.

### Assessment Metric Value
A specific captured value inside an assessment session.

---

## 6. Versioned Build Plan

## v0.1 — Foundation Data Model
Goal: establish the stable relational backbone and metadata-driven assessment model.

Includes:
- organizational master data
- athlete master data
- enrollment model
- KPI taxonomy master data
- protocol/metric definition model
- assessment session model
- assessment metric value model
- personality lookup support
- audit fields and indexing strategy

Excludes:
- training plans
- interventions
- advanced dashboards
- percentile engines
- benchmarking engine
- role-based access refinement
- notifications
- device integrations

Deliverable:
A working Django data model and migration baseline.

## v0.2 — Admin, Seed Data, and Validation
Goal: make the model usable by operations/admin users.

Includes:
- Django admin for all master tables
- seed importers from AlphaMind Excel taxonomy
- validation rules for metric types
- protocol config rules
- slug/code conventions
- basic API serializers/read endpoints

## v0.3 — Assessment Capture Engine
Goal: support athlete assessment entry and historical storage.

Includes:
- create assessment sessions
- capture metric values by protocol
- support text/numeric/boolean/json values
- enforce metric-level validation
- session status handling
- source attribution

## v0.4 — Mobile-First Athlete Dashboard
Goal: basic UI to inspect athlete profile and metric history.

Includes:
- athlete profile view
- enrollment context
- protocol-wise assessment history
- metric trend charts
- card-based mobile UX
- HTMX-driven forms and partial updates

## v0.5 — Derived Insights Layer
Goal: compute usable dashboard summaries.

Includes:
- latest snapshot per athlete + metric
- previous vs latest delta
- domain rollups
- framework rollups
- score banding
- trend flags

## v0.6 — Goal and Intervention Layer
Goal: connect assessment data to athlete development.

Includes:
- athlete goals
- goal review cycles
- interventions / recommendations
- coach notes
- goal-to-metric relationship

## v0.7 — Benchmarking and Norms
Goal: compare athletes to contextual standards.

Includes:
- benchmark groups
- sport/age/gender norms
- percentile calculation basis
- readiness scoring support

## v0.8 — Center and Coach Operations
Goal: operationalize AlphaMinds for real centers.

Includes:
- staff/coaches
- center-scoped athlete management
- permissions by center
- session assignment workflows

## v0.9 — Integration and Device Readiness
Goal: support external systems.

Includes:
- raw payload ingestion
- device import mapping
- external athlete identifiers
- import/export pipelines

## v1.0 — Stable Production Release
Goal: production-grade AlphaMinds MVP.

Includes:
- hardened permissions
- reporting exports
- auditability
- dashboard performance optimization
- operational workflows
- stable APIs

---

# 7. v0.1 Detailed Django Model Architecture

## 7.1 App Structure

Recommended Django apps:
- `core` → abstract base classes, shared utilities, enums
- `orgs` → centers, staff, organizational structures
- `sports` → sports master tables
- `athletes` → athlete master and enrollment
- `kpis` → domains, frameworks, protocols, metric definitions, lookups
- `assessments` → sessions and measured values
- `profiles` → optional personality profiles and later derived athlete profile objects

For v0.1, models may still live in fewer apps if needed, but the architecture should conceptually follow this split.

---

## 7.2 Common Base Model

### AbstractBaseModel
All core entities should inherit these fields.

**Fields**
- `id = models.BigAutoField(primary_key=True)`
- `created_at = models.DateTimeField(auto_now_add=True, db_index=True)`
- `updated_at = models.DateTimeField(auto_now=True)`
- `is_active = models.BooleanField(default=True, db_index=True)`

### Optional audit mixin for user stamps later
Not mandatory in v0.1, but keep room for:
- `created_by`
- `updated_by`

---

## 7.3 Organizational Layer

## Model: `orgs.Center`
**Table name:** `org_center`

Represents a physical or business center.

**Fields**
- `id` BigAutoField PK
- `code = models.CharField(max_length=50, unique=True, db_index=True)`
- `name = models.CharField(max_length=255, db_index=True)`
- `short_name = models.CharField(max_length=100, blank=True)`
- `city = models.CharField(max_length=100, blank=True, db_index=True)`
- `state = models.CharField(max_length=100, blank=True, db_index=True)`
- `country = models.CharField(max_length=100, default="India", db_index=True)`
- `timezone = models.CharField(max_length=64, default="Asia/Kolkata")`
- `address_line1 = models.CharField(max_length=255, blank=True)`
- `address_line2 = models.CharField(max_length=255, blank=True)`
- `postal_code = models.CharField(max_length=20, blank=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Indexes**
- code unique
- name index
- `(country, state, city)` composite index

**JSONField justification**
`metadata` only for optional center attributes that do not justify schema columns yet.

---

## 7.4 Sports Layer

## Model: `sports.Sport`
**Table name:** `sport`

**Fields**
- `id` BigAutoField PK
- `code = models.CharField(max_length=50, unique=True, db_index=True)`
- `name = models.CharField(max_length=100, unique=True, db_index=True)`
- `description = models.TextField(blank=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Indexes**
- code unique
- name unique

---

## 7.5 Athlete Layer

## Model: `athletes.Athlete`
**Table name:** `athlete`

This is athlete master data only.

**Fields**
- `id` BigAutoField PK
- `external_ref = models.CharField(max_length=100, blank=True, null=True, db_index=True)`
- `first_name = models.CharField(max_length=100, db_index=True)`
- `middle_name = models.CharField(max_length=100, blank=True)`
- `last_name = models.CharField(max_length=100, blank=True, db_index=True)`
- `full_name = models.CharField(max_length=255, db_index=True)`
- `date_of_birth = models.DateField(null=True, blank=True, db_index=True)`
- `gender = models.CharField(max_length=20, blank=True, db_index=True)`
- `email = models.EmailField(blank=True, null=True, db_index=True)`
- `phone = models.CharField(max_length=30, blank=True, null=True, db_index=True)`
- `dominant_hand = models.CharField(max_length=20, blank=True)`
- `notes = models.TextField(blank=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Indexes**
- external_ref index
- full_name index
- date_of_birth index
- `(first_name, last_name)` composite index

**Notes**
- Keep `full_name` stored for search convenience.
- Avoid storing `age`; compute it from DOB.
- Avoid storing current center or current sport here.

---

## Model: `athletes.AthleteSport`
**Table name:** `athlete_sport`

Tracks athlete participation in sports over time.

**Fields**
- `id` BigAutoField PK
- `athlete = models.ForeignKey("athletes.Athlete", on_delete=models.CASCADE, related_name="athlete_sports")`
- `sport = models.ForeignKey("sports.Sport", on_delete=models.PROTECT, related_name="athlete_sports")`
- `start_date = models.DateField(null=True, blank=True, db_index=True)`
- `end_date = models.DateField(null=True, blank=True, db_index=True)`
- `level = models.CharField(max_length=50, blank=True, db_index=True)`
- `role_or_position = models.CharField(max_length=100, blank=True)`
- `is_primary = models.BooleanField(default=False, db_index=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Relationship type**
This is effectively the through model for Athlete ↔ Sport.

**Indexes**
- FK indexes on athlete and sport
- composite index `(athlete, sport, is_primary)`
- composite index `(athlete, start_date, end_date)`

**Constraints**
- UniqueConstraint on `(athlete, sport, start_date)`

---

## Model: `athletes.AthleteCenter`
**Table name:** `athlete_center`

Tracks athlete association with centers over time.

**Fields**
- `id` BigAutoField PK
- `athlete = models.ForeignKey("athletes.Athlete", on_delete=models.CASCADE, related_name="athlete_centers")`
- `center = models.ForeignKey("orgs.Center", on_delete=models.PROTECT, related_name="athlete_centers")`
- `start_date = models.DateField(null=True, blank=True, db_index=True)`
- `end_date = models.DateField(null=True, blank=True, db_index=True)`
- `is_primary = models.BooleanField(default=False, db_index=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Indexes**
- composite index `(athlete, center, is_primary)`
- composite index `(center, start_date, end_date)`

**Constraints**
- UniqueConstraint on `(athlete, center, start_date)`

---

## Model: `athletes.AthleteEnrollment`
**Table name:** `athlete_enrollment`

This is the central context bridge for athlete → center → sport.

**Fields**
- `id` BigAutoField PK
- `athlete = models.ForeignKey("athletes.Athlete", on_delete=models.CASCADE, related_name="enrollments")`
- `center = models.ForeignKey("orgs.Center", on_delete=models.PROTECT, related_name="enrollments")`
- `sport = models.ForeignKey("sports.Sport", on_delete=models.PROTECT, related_name="enrollments")`
- `enrollment_code = models.CharField(max_length=100, blank=True, null=True, db_index=True)`
- `status = models.CharField(max_length=30, default="active", db_index=True)`
- `start_date = models.DateField(db_index=True)`
- `end_date = models.DateField(null=True, blank=True, db_index=True)`
- `batch_name = models.CharField(max_length=100, blank=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Why this exists even though AthleteSport and AthleteCenter exist**
Because reporting and assessment context often need a precise center+sport relationship, not two separate edges.

**Indexes**
- composite index `(athlete, center, sport, status)`
- composite index `(center, sport, status)`
- composite index `(athlete, start_date, end_date)`

**Constraints**
- UniqueConstraint on `(athlete, center, sport, start_date)`

---

## 7.6 KPI Taxonomy Layer

## Model: `kpis.KPIDomain`
**Table name:** `kpi_domain`

Maps to Excel `KPICategory1`.

**Fields**
- `id` BigAutoField PK
- `code = models.SlugField(max_length=100, unique=True)`
- `name = models.CharField(max_length=255, unique=True, db_index=True)`
- `display_order = models.PositiveIntegerField(default=0, db_index=True)`
- `description = models.TextField(blank=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Examples**
- identity-purpose
- cognitive-performance
- adaptability-flexibility

---

## Model: `kpis.KPIFramework`
**Table name:** `kpi_framework`

Maps to Excel primary `KPICategory2`.

**Fields**
- `id` BigAutoField PK
- `domain = models.ForeignKey("kpis.KPIDomain", on_delete=models.PROTECT, related_name="frameworks")`
- `code = models.SlugField(max_length=120, unique=True)`
- `name = models.CharField(max_length=255, db_index=True)`
- `display_order = models.PositiveIntegerField(default=0, db_index=True)`
- `description = models.TextField(blank=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Indexes**
- composite index `(domain, display_order)`
- composite index `(domain, name)`

**Constraints**
- UniqueConstraint on `(domain, name)`

---

## Model: `kpis.KPIProtocol`
**Table name:** `kpi_protocol`

Maps to Excel secondary `KPICategory2` test/protocol layer.

**Fields**
- `id` BigAutoField PK
- `framework = models.ForeignKey("kpis.KPIFramework", on_delete=models.PROTECT, related_name="protocols")`
- `code = models.SlugField(max_length=150, unique=True)`
- `name = models.CharField(max_length=255, db_index=True)`
- `display_order = models.PositiveIntegerField(default=0, db_index=True)`
- `description = models.TextField(blank=True)`
- `source_type = models.CharField(max_length=50, blank=True, db_index=True)`
- `capture_mode = models.CharField(max_length=50, blank=True, db_index=True)`
- `config = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Examples**
- blazepod-reaction-time
- f1-reaction-time-test
- maze-test
- visualedge

**JSONField justification**
`config` may contain protocol capture rules like repetitions, timing mode, or UI hints.

**Indexes**
- composite index `(framework, display_order)`
- composite index `(framework, name)`
- index on `source_type`
- index on `capture_mode`

**Constraints**
- UniqueConstraint on `(framework, name)`

---

## Model: `kpis.MetricDefinition`
**Table name:** `metric_definition`

Maps to Excel `KPICategory3`.

This is the core reusable metric definition table.

**Fields**
- `id` BigAutoField PK
- `protocol = models.ForeignKey("kpis.KPIProtocol", on_delete=models.PROTECT, related_name="metrics")`
- `code = models.SlugField(max_length=180, unique=True)`
- `name = models.CharField(max_length=255, db_index=True)`
- `label = models.CharField(max_length=255, blank=True)`
- `description = models.TextField(blank=True)`
- `value_data_type = models.CharField(max_length=30, db_index=True)`
- `units = models.CharField(max_length=50, blank=True, db_index=True)`
- `importance = models.CharField(max_length=30, blank=True, db_index=True)`
- `interpretation_direction = models.CharField(max_length=20, blank=True, db_index=True)`
- `min_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)`
- `max_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)`
- `allowed_text_values = models.JSONField(default=list, blank=True)`
- `is_required = models.BooleanField(default=False, db_index=True)`
- `is_higher_better = models.BooleanField(null=True, blank=True, db_index=True)`
- `display_order = models.PositiveIntegerField(default=0, db_index=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Supported `value_data_type` values**
- integer
- decimal
- text
- boolean
- date
- json

**JSONField justification**
- `allowed_text_values` for controlled enums
- `metadata` for UI/validation hints

**Indexes**
- composite index `(protocol, display_order)`
- composite index `(protocol, value_data_type)`
- composite index `(protocol, name)`
- index on `units`
- index on `importance`

**Constraints**
- UniqueConstraint on `(protocol, name)`

---

## 7.7 Personality Lookup Layer

## Model: `profiles.PersonalityType`
**Table name:** `personality_type`

Backed by the Excel lookup sheet.

**Fields**
- `id` BigAutoField PK
- `code = models.CharField(max_length=20, unique=True, db_index=True)`
- `group_name = models.CharField(max_length=100, blank=True, db_index=True)`
- `title = models.CharField(max_length=255, db_index=True)`
- `description = models.TextField(blank=True)`
- `metadata = models.JSONField(default=dict, blank=True)`
- inherited audit fields

**Examples**
- INTJ
- ENFP
- etc.

---

## 7.8 Assessment Transaction Layer

## Model: `assessments.AssessmentSession`
**Table name:** `assessment_session`

Represents a single assessment event under a protocol.

**Fields**
- `id` BigAutoField PK
- `session_uuid = models.UUIDField(unique=True, editable=False, db_index=True)`
- `athlete = models.ForeignKey("athletes.Athlete", on_delete=models.CASCADE, related_name="assessment_sessions")`
- `enrollment = models.ForeignKey("athletes.AthleteEnrollment", on_delete=models.PROTECT, related_name="assessment_sessions", null=True, blank=True)`
- `center = models.ForeignKey("orgs.Center", on_delete=models.PROTECT, related_name="assessment_sessions")`
- `sport = models.ForeignKey("sports.Sport", on_delete=models.PROTECT, related_name="assessment_sessions")`
- `protocol = models.ForeignKey("kpis.KPIProtocol", on_delete=models.PROTECT, related_name="assessment_sessions")`
- `assessed_on = models.DateTimeField(db_index=True)`
- `status = models.CharField(max_length=30, default="completed", db_index=True)`
- `source = models.CharField(max_length=50, blank=True, db_index=True)`
- `source_reference = models.CharField(max_length=100, blank=True, db_index=True)`
- `raw_payload = models.JSONField(default=dict, blank=True)`
- `notes = models.TextField(blank=True)`
- inherited audit fields

**Important notes**
- Keep `center` and `sport` directly on the session even if `enrollment` exists; this avoids denormalization pain in reporting and preserves exact session context.
- `raw_payload` is acceptable here because device/app source payloads can vary.

**Indexes**
- index on `session_uuid`
- composite index `(athlete, assessed_on)`
- composite index `(athlete, protocol, assessed_on)`
- composite index `(center, sport, assessed_on)`
- composite index `(protocol, assessed_on)`
- composite index `(status, assessed_on)`

---

## Model: `assessments.AssessmentMetricValue`
**Table name:** `assessment_metric_value`

Stores the actual values captured during a session.

**Fields**
- `id` BigAutoField PK
- `assessment_session = models.ForeignKey("assessments.AssessmentSession", on_delete=models.CASCADE, related_name="metric_values")`
- `metric_definition = models.ForeignKey("kpis.MetricDefinition", on_delete=models.PROTECT, related_name="assessment_values")`
- `numeric_value = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True, db_index=True)`
- `text_value = models.TextField(blank=True)`
- `boolean_value = models.BooleanField(null=True, blank=True, db_index=True)`
- `date_value = models.DateField(null=True, blank=True, db_index=True)`
- `json_value = models.JSONField(default=dict, blank=True)`
- `display_value = models.CharField(max_length=255, blank=True)`
- `value_data_type = models.CharField(max_length=30, db_index=True)`
- `units = models.CharField(max_length=50, blank=True)`
- `sequence_no = models.PositiveIntegerField(default=1, db_index=True)`
- `notes = models.TextField(blank=True)`
- inherited audit fields

**Why multiple value columns instead of one generic text field**
- supports numeric querying and indexing
- supports filtering and rollups efficiently
- preserves correct data semantics

**Why still keep `value_data_type` and `units` here**
To preserve historical interpretation if metric definitions evolve later.

**Indexes**
- composite index `(assessment_session, metric_definition)`
- composite index `(metric_definition, numeric_value)`
- composite index `(metric_definition, value_data_type)`
- composite index `(metric_definition, date_value)`
- composite index `(metric_definition, boolean_value)`
- composite index `(sequence_no, metric_definition)`

**Constraints**
- UniqueConstraint on `(assessment_session, metric_definition, sequence_no)`

**Validation rule**
Exactly one of the typed value columns should be populated for simple metrics, unless the metric explicitly allows JSON payload storage.

---

## 7.9 Optional Profile Link Layer for Personality

## Model: `profiles.AthletePersonalityProfile`
**Table name:** `athlete_personality_profile`

Optional in v0.1, but recommended because personality type is more than a free-text metric.

**Fields**
- `id` BigAutoField PK
- `athlete = models.ForeignKey("athletes.Athlete", on_delete=models.CASCADE, related_name="personality_profiles")`
- `personality_type = models.ForeignKey("profiles.PersonalityType", on_delete=models.PROTECT, related_name="athlete_profiles")`
- `assessment_session = models.ForeignKey("assessments.AssessmentSession", on_delete=models.SET_NULL, null=True, blank=True, related_name="personality_profiles")`
- `assessed_on = models.DateField(db_index=True)`
- `source = models.CharField(max_length=50, blank=True, db_index=True)`
- `notes = models.TextField(blank=True)`
- inherited audit fields

**Indexes**
- composite index `(athlete, assessed_on)`
- composite index `(personality_type, assessed_on)`

---

## 7.10 Relationship Summary

### ForeignKey relationships
- `AthleteSport.athlete -> Athlete`
- `AthleteSport.sport -> Sport`
- `AthleteCenter.athlete -> Athlete`
- `AthleteCenter.center -> Center`
- `AthleteEnrollment.athlete -> Athlete`
- `AthleteEnrollment.center -> Center`
- `AthleteEnrollment.sport -> Sport`
- `KPIFramework.domain -> KPIDomain`
- `KPIProtocol.framework -> KPIFramework`
- `MetricDefinition.protocol -> KPIProtocol`
- `AssessmentSession.athlete -> Athlete`
- `AssessmentSession.enrollment -> AthleteEnrollment`
- `AssessmentSession.center -> Center`
- `AssessmentSession.sport -> Sport`
- `AssessmentSession.protocol -> KPIProtocol`
- `AssessmentMetricValue.assessment_session -> AssessmentSession`
- `AssessmentMetricValue.metric_definition -> MetricDefinition`
- `AthletePersonalityProfile.athlete -> Athlete`
- `AthletePersonalityProfile.personality_type -> PersonalityType`
- `AthletePersonalityProfile.assessment_session -> AssessmentSession`

### ManyToMany usage
Use explicit through models rather than direct `ManyToManyField`.

Recommended conceptual many-to-many relationships:
- Athlete ↔ Sport via `AthleteSport`
- Athlete ↔ Center via `AthleteCenter`

Do **not** use a direct `ManyToManyField` without through models, because date ranges and status matter.

---

## 7.11 Indexed Fields Strategy

### Strongly indexed because they support common filters
- all code fields
- all name fields used in search
- athlete identifiers
- assessed_on
- status
- value_data_type
- numeric_value where comparison queries are expected
- center, sport, protocol FKs on sessions
- athlete FK on sessions and enrollments

### Avoid over-indexing text blobs
Do not index long free-text description or notes unless a search engine requirement appears later.

---

## 7.12 Field Type Rules

### ForeignKey
Use `ForeignKey` when the child belongs to one parent entity.
Examples:
- session belongs to one athlete
- metric belongs to one protocol
- protocol belongs to one framework

### ManyToMany
Only via explicit through models when the relationship has time, status, or metadata.
Examples:
- athlete to sport
- athlete to center

### JSONField
Allowed in these cases only:
- `Center.metadata`
- `Sport.metadata`
- `Athlete.metadata`
- `AthleteSport.metadata`
- `AthleteCenter.metadata`
- `AthleteEnrollment.metadata`
- `KPIDomain.metadata`
- `KPIFramework.metadata`
- `KPIProtocol.config`
- `MetricDefinition.allowed_text_values`
- `MetricDefinition.metadata`
- `AssessmentSession.raw_payload`
- `AssessmentMetricValue.json_value`
- `PersonalityType.metadata`

### DecimalField
Use for measured numeric values that may require precision.
Example:
- reaction time
- completion time
- confidence score

### CharField vs TextField
- `CharField` for searchable labels, codes, short descriptors
- `TextField` for long descriptions and notes

---

## 7.13 Import Mapping From Excel

### Excel column → target entity
- `PlayerName` → `Athlete.full_name`
- `Center` → `Center.name/code`
- `SportsType` → `Sport.name/code`
- `KPICategory1` → `KPIDomain.name`
- first `KPICategory2` → `KPIFramework.name`
- second `KPICategory2` → `KPIProtocol.name`
- `KPICategory3` → `MetricDefinition.name`
- `ValueDataType` → `MetricDefinition.value_data_type`
- `DataImportance` → `MetricDefinition.importance`
- `Units` → `MetricDefinition.units`
- `Date/Month/Year` → `AssessmentSession.assessed_on`
- `Value` → `AssessmentMetricValue`

### Important note
The uploaded Excel is a **seed taxonomy and sample measurement sheet**, not a normalized production import source.

---

## 7.14 What Is Explicitly Out of v0.1

Do not include these yet unless this document is updated:
- training plans
- interventions
- benchmarks
- percentiles
- readiness scores
- role-based access models beyond basic ownership
- billing
- notifications
- device SDK integration tables
- media storage tables

---

## 7.15 Implementation Notes for Django

### Meta options to use
Each model should explicitly define:
- `db_table`
- `ordering`
- `indexes`
- `constraints`

### Example ordering guidance
- taxonomy tables: `display_order`, then `name`
- athlete-related time tables: newest first by `start_date` or `assessed_on`
- assessment values: `sequence_no`, then `id`

### Delete behavior guidance
- `CASCADE` when child is meaningless without parent
- `PROTECT` when referenced master data should not disappear after transactions exist
- `SET_NULL` only where historical transaction should remain even if the optional link disappears

Examples:
- session -> athlete = `CASCADE`
- session -> protocol = `PROTECT`
- metric value -> session = `CASCADE`
- personality profile -> assessment session = `SET_NULL`

---

## 8. Decision Log

### Decision A
AlphaMinds will use a metadata-driven KPI architecture.

### Decision B
Athlete, center, and sport will remain separate entities with enrollment context.

### Decision C
Assessment sessions are the primary fact/event layer.

### Decision D
Metric values will use typed storage columns instead of a single generic value field.

### Decision E
Many-to-many relationships with business context will use explicit through models.

---

## 9. Working Mode for Future Development

When changing AlphaMinds code, always follow this process:

1. Refer to this architecture first.
2. State which version is being modified.
3. State whether the change affects master data, transaction data, or derived data.
4. Extend existing models before proposing new ones.
5. Do not rewrite v0.1 architecture unless a clear modeling gap is proven.

### Required prompt style for future changes
Use prompts like:
- “Modify v0.1 AthleteEnrollment to support batches without changing architecture.”
- “Extend v0.3 assessment capture to validate decimal metrics.”
- “Add v0.5 derived snapshot model consistent with existing architecture.”

Avoid prompts like:
- “Give me a better model structure”
- “Let’s redesign the whole schema”

unless we are intentionally revisiting architecture.

---

## 10. Immediate Next Step

The next implementation artifact after this document should be:

**AlphaMinds v0.1 Django model code** with:
- model classes
- enum choices
- Meta indexes/constraints
- validation helpers
- comments mapped back to this document

This must follow the architecture exactly unless explicitly changed here.
