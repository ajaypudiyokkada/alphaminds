from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Program, ProgramSession, ProgramTemplate, ProgramTypeChoices


# ── Program Template ──────────────────────────────────────────────────────────

@admin.register(ProgramTemplate)
class ProgramTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "program_type", "duration_weeks", "sessions_per_week", "total_sessions", "is_active")
    list_filter = ("program_type", "is_active")
    search_fields = ("name",)
    filter_horizontal = ("protocols",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Core", {"fields": ("program_type", "name", "description", "is_active")}),
        ("Schedule", {"fields": ("duration_weeks", "sessions_per_week")}),
        ("KPI Protocols", {"fields": ("protocols",), "description": "Protocols captured each session"}),
        ("Metadata", {"fields": ("metadata",), "classes": ("collapse",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def total_sessions(self, obj):
        return obj.total_sessions
    total_sessions.short_description = "Total Sessions"


# ── Program Session Inline ────────────────────────────────────────────────────

class ProgramSessionInline(admin.TabularInline):
    model = ProgramSession
    extra = 0
    fields = ("session_number", "scheduled_date", "status", "assessment_link", "coach_notes")
    readonly_fields = ("session_number", "assessment_link")
    ordering = ("session_number",)

    def assessment_link(self, obj):
        if obj.assessment_session_id:
            url = reverse("admin:assessments_assessmentsession_change", args=[obj.assessment_session_id])
            return format_html('<a href="{}">View KPI Data</a>', url)
        if not obj.pk:
            return "—"
        # Link to create a new assessment pre-filled for this session
        program = obj.program
        params = []
        if program.enrollment_id:
            params.append(f"enrollment={program.enrollment_id}")
        else:
            params.append(f"athlete={program.athlete_id}")
            enrollment = program.athlete.enrollments.filter(is_active=True, status="active").first()
            if enrollment:
                params.append(f"center={enrollment.center_id}")
                params.append(f"sport={enrollment.sport_id}")
        url = reverse("admin:assessments_assessmentsession_add")
        if params:
            url += "?" + "&".join(params)
        return format_html('<a href="{}">+ Capture KPIs</a>', url)
    assessment_link.short_description = "KPI Data"


# ── Program ───────────────────────────────────────────────────────────────────

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        "athlete", "program_type", "status", "start_date", "end_date",
        "mtq_total_score", "session_progress", "is_active",
    )
    list_filter = ("program_type", "status", "is_active")
    search_fields = ("athlete__full_name", "notes")
    autocomplete_fields = ("athlete", "enrollment", "mtq_session")
    readonly_fields = ("created_at", "updated_at", "mtq_total_score", "program_type", "end_date")
    inlines = [ProgramSessionInline]
    fieldsets = (
        ("Context", {"fields": (
            "athlete", "enrollment", "template", "program_type",
            "status", "is_active",
        )}),
        ("Schedule", {"fields": ("start_date", "end_date")}),
        ("MTQ Result", {"fields": ("mtq_session", "mtq_total_score")}),
        ("Notes", {"fields": ("notes",)}),
        ("Metadata", {"fields": ("metadata",), "classes": ("collapse",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def session_progress(self, obj):
        total = obj.sessions.count()
        done = obj.sessions.filter(status="completed").count()
        if not total:
            return "—"
        return f"{done}/{total}"
    session_progress.short_description = "Sessions"

    def save_model(self, request, obj, form, change):
        # Auto-set program_type from template
        if obj.template_id:
            obj.program_type = obj.template.program_type
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        obj = form.instance
        created = obj.generate_sessions()
        if created:
            self.message_user(
                request,
                f"{created} session(s) auto-generated from the program template.",
            )


# ── Program Session (standalone) ──────────────────────────────────────────────

@admin.register(ProgramSession)
class ProgramSessionAdmin(admin.ModelAdmin):
    list_display = (
        "program", "session_number", "scheduled_date", "status",
        "assessment_session", "is_active",
    )
    list_filter = ("status", "is_active", "scheduled_date")
    search_fields = ("program__athlete__full_name",)
    autocomplete_fields = ("program", "assessment_session")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Core", {"fields": ("program", "session_number", "scheduled_date", "status", "is_active")}),
        ("Assessment", {"fields": ("assessment_session",)}),
        ("Notes", {"fields": ("coach_notes",)}),
        ("Metadata", {"fields": ("metadata",), "classes": ("collapse",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
