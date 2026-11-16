from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Athlete, AthleteCenter, AthleteEnrollment, AthleteSport


class AthleteSportInline(admin.TabularInline):
    model = AthleteSport
    extra = 0
    autocomplete_fields = ("sport",)
    fields = (
        "sport",
        "start_date",
        "end_date",
        "level",
        "role_or_position",
        "is_primary",
        "is_active",
    )


class AthleteCenterInline(admin.TabularInline):
    model = AthleteCenter
    extra = 0
    autocomplete_fields = ("center",)
    fields = (
        "center",
        "start_date",
        "end_date",
        "is_primary",
        "is_active",
    )


class AthleteEnrollmentInline(admin.TabularInline):
    model = AthleteEnrollment
    extra = 0
    autocomplete_fields = ("center", "sport")
    fields = (
        "center",
        "sport",
        "enrollment_code",
        "status",
        "start_date",
        "end_date",
        "batch_name",
        "is_active",
    )


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "external_ref",
        "gender",
        "date_of_birth",
        "age_display",
        "age_group_display",
        "email",
        "phone",
        "program_links",
        "is_active",
        "created_at",
    )
    list_filter = ("gender", "is_active", "created_at")
    search_fields = (
        "full_name",
        "first_name",
        "middle_name",
        "last_name",
        "external_ref",
        "email",
        "phone",
    )
    ordering = ("full_name",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [AthleteSportInline, AthleteCenterInline, AthleteEnrollmentInline]

    def age_display(self, obj):
        return obj.age
    age_display.short_description = "Age"

    def age_group_display(self, obj):
        return obj.age_group or "—"
    age_group_display.short_description = "Age Group"

    def program_links(self, obj):
        links = []
        # Link to schedule an MTQ assessment
        enrollment = obj.enrollments.filter(is_active=True, status="active").first()
        if enrollment:
            url = reverse("admin:assessments_assessmentsession_add")
            url += f"?enrollment={enrollment.pk}"
            links.append(format_html('<a href="{}">+ MTQ</a>', url))
        # Link to view programs
        program_count = obj.programs.filter(is_active=True).count()
        if program_count:
            url = reverse("admin:programs_program_changelist")
            url += f"?athlete__id__exact={obj.pk}"
            links.append(format_html('<a href="{}">{} prog</a>', url, program_count))
        return format_html(" | ".join(links)) if links else "—"
    program_links.short_description = "Actions"

    fieldsets = (
        (
            "Identity",
            {
                "fields": (
                    "external_ref",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "full_name",
                    "is_active",
                )
            },
        ),
        (
            "Profile",
            {
                "fields": (
                    "date_of_birth",
                    "gender",
                    "dominant_hand",
                    "email",
                    "phone",
                )
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(AthleteSport)
class AthleteSportAdmin(admin.ModelAdmin):
    list_display = (
        "athlete",
        "sport",
        "level",
        "is_primary",
        "start_date",
        "end_date",
        "is_active",
    )
    list_filter = ("sport", "level", "is_primary", "is_active", "start_date", "end_date")
    search_fields = ("athlete__full_name", "sport__name", "role_or_position")
    ordering = ("-is_primary", "-start_date", "id")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("athlete", "sport")
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "athlete",
                    "sport",
                    "level",
                    "role_or_position",
                    "is_primary",
                    "is_active",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(AthleteCenter)
class AthleteCenterAdmin(admin.ModelAdmin):
    list_display = (
        "athlete",
        "center",
        "is_primary",
        "start_date",
        "end_date",
        "is_active",
    )
    list_filter = ("center", "is_primary", "is_active", "start_date", "end_date")
    search_fields = ("athlete__full_name", "center__name", "center__code")
    ordering = ("-is_primary", "-start_date", "id")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("athlete", "center")
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "athlete",
                    "center",
                    "is_primary",
                    "is_active",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(AthleteEnrollment)
class AthleteEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "athlete",
        "center",
        "sport",
        "status",
        "start_date",
        "end_date",
        "batch_name",
        "is_active",
    )
    list_filter = (
        "center",
        "sport",
        "status",
        "is_active",
        "start_date",
        "end_date",
    )
    search_fields = (
        "athlete__full_name",
        "center__name",
        "sport__name",
        "enrollment_code",
        "batch_name",
    )
    ordering = ("-start_date", "id")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("athlete", "center", "sport")
    fieldsets = (
        (
            "Context",
            {
                "fields": (
                    "athlete",
                    "center",
                    "sport",
                    "enrollment_code",
                    "status",
                    "batch_name",
                    "is_active",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )