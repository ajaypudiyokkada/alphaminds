# AlphaMinds ARCHITECTURE.md v0.3

## Core Principles
- Separate Session Lifecycle from Metrics Visibility
- Maintain hierarchy: Domain → Framework → Protocol → Metrics
- Center-scoped data access

---

## 1. Core Entities

Athlete  
- Linked to User  
- Multiple Enrollments  

AthleteEnrollment  
- Athlete → Center → Sport  

AssessmentSession  
- Represents an appointment/event  
- Fields: athlete, enrollment, center, sport, protocol, assessed_on, status  

AssessmentMetricValue  
- Represents captured metrics  
- Linked to AssessmentSession  

---

## 2. Session Lifecycle

Statuses:
- BOOKED
- COMPLETED
- CANCELLED
- INVALIDATED

Session ≠ Metrics visibility

---

## 3. Metrics Visibility

Current:
- Uses status = PUBLISHED

Future:
- metrics_published_at / metrics_status (recommended)

---

## 4. Staff Workflow

1. Create Athlete (auto enrollment)
2. Book Assessment → BOOKED
3. Mark Complete (time gated) → COMPLETED
4. Capture Metrics
5. Publish Metrics

---

## 5. Athlete Experience

- See ALL sessions (BOOKED, COMPLETED, etc.)
- Session always visible
- Metrics visible ONLY if published

---

## 6. KPI Mapping

Domain → Framework → Protocol → Metrics

Session → Protocol  
Metrics derive hierarchy from protocol

---

## 7. HTMX Flow

Athlete → Enrollment  
Domain → Framework → Protocol  

---

## 8. Dashboard Buckets

- Pending (BOOKED)
- Ready to Complete
- Ready to Capture
- Ready to Publish

---

## 9. Guards

- staff_profile based access
- center-scoped queries

---

## Summary

v0.3:
- Separates session vs metrics
- Fixes athlete visibility
- Defines correct staff workflow
