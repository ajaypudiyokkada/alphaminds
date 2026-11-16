# AlphaMinds – Project Summary

## What it is
AlphaMinds is a mobile-first athlete intelligence platform built as a Django monolith. It tracks athletes across centers, sports and assessment sessions. Raw assessments are mapped into a metadata-driven KPI framework that feeds dashboards and insights. New assessment protocols are added as metadata rows, not schema changes.

`ARCHITECTURE.md` is the source of truth for design rules and the versioned roadmap (v0.1 to v1.0).

## Stack
- Python 3.12, Django, Django REST Framework
- Auth for the API: JWT (`rest_framework_simplejwt`), with `corsheaders` for CORS
- Web UI: Django templates, with HTMX-style partials (see the `*_partial` views)
- Database: **PostgreSQL** (configured via `backend/.env`, run through Docker Compose). MySQL remains supported as a fallback by setting `DB_ENGINE=django.db.backends.mysql`.
- Entry points: `manage.py`, `alphaminds/` (settings, urls, wsgi, asgi)

## Apps
| App | Role |
|---|---|
| `core` | `TimeStampedActiveModel` abstract base (created_at, updated_at, is_active), shared choices |
| `orgs` | `Center`, `StaffProfile` |
| `sports` | `Sport` |
| `athletes` | `Athlete`, `AthleteSport`, `AthleteCenter`, `AthleteEnrollment` (linked to a Django `User`) |
| `kpis` | `KPIDomain` → `KPIFramework` → `KPIProtocol` → `MetricDefinition`; Excel importer |
| `assessments` | `AssessmentSession`, `AssessmentMetricValue` (typed value columns), with admin inline JS |
| `profiles` | `PersonalityType`, `AthletePersonalityProfile` |
| `programs` | `ProgramTemplate`, `Program`, `ProgramSession` (past the v0.1 scope in ARCHITECTURE.md) |
| `frontend` | Server-rendered site, `LeadInquiry` model (contact form), templates and forms |
| `api` | REST endpoints for the mobile client |

## Data model
```
Domain → Framework → Protocol → MetricDefinition      (master / taxonomy)
Athlete ─ Enrollment (athlete + center + sport + dates)
AssessmentSession (athlete, center, sport, protocol) → AssessmentMetricValue → MetricDefinition
```
Key principles:
- Definitions are stored separately from measurements.
- Measurements are append-only history.
- Time-bound links use explicit through models (no bare M2M).
- JSONField is used only for metadata, config and raw payloads.

## Web routes (`frontend/urls.py`)
- Public: home, contact modal (form, submit, close).
- `dashboard/` is a role router that sends users to the athlete or staff home.
- Athlete: `athlete/home/` and `athlete/session/<id>/`.
- Staff:
  - Athlete CRUD under `staff/athletes/`.
  - Assessment flow: create → capture → publish → mark-complete.
  - HTMX partials for protocol metrics, athlete enrollments and domain/framework/protocol dropdowns.

## REST API (`api/urls.py`)
- Auth: `auth/login/`, `auth/refresh/`, `auth/logout/`, `auth/forgot-password/`
- Athlete: `athlete/me/`, `athlete/dashboard/`, `athlete/sessions/`, `athlete/sessions/<id>/`
- Public: `leads/` (create a lead inquiry)

## Data import
`python manage.py import_alphaminds_excel` loads the taxonomy and sample data from `AlphaMindDashboard.xlsx`, using `kpis/services/importers/alphaminds_excel.py`.

## Running
```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
This assumes the database in `backend/.env` is reachable (see the root README for the Docker setup).

## Observations and housekeeping
- **Docs vs. settings:** both now use PostgreSQL (MySQL is kept only as a fallback).
- **Secrets:** the DB password is hardcoded in `settings.py`, with `DEBUG = True` and LAN IPs in `ALLOWED_HOSTS`. Move these to environment variables before any deployment.
- **Scope creep:** the `programs` app goes beyond the v0.1 scope in ARCHITECTURE.md, so the doc is partly out of date.
- **Leftover files:** `views_bkp.py`, `*_bkp.html`, `home.html.bkp`, `~$AlphaMindDashboard.xlsx` (Excel lock file) and committed `__pycache__` directories should be cleaned up or git-ignored.
- **README:** it is a one-liner and could point to this file.
