from django.contrib import admin

from .models import AthletePersonalityProfile, PersonalityType


class AthletePersonalityProfileInline(admin.TabularInline):
    model = AthletePersonalityProfile
    extra = 0
    autocomplete_fields = ("athlete", "assessment_session")
    fields = (
        "athlete",
        "assessment_session",
        "assessed_on",
        "source",
        "is_active",
    )
    show_change_link = True


@admin.register(PersonalityType)
class PersonalityTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "group_name", "is_active", "created_at")
    list_filter = ("group_name", "is_active", "created_at")
    search_fields = ("code", "title", "group_name", "description")
    ordering = ("code",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [AthletePersonalityProfileInline]
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "code",
                    "title",
                    "group_name",
                    "description",
                    "is_active",
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


@admin.register(AthletePersonalityProfile)
class AthletePersonalityProfileAdmin(admin.ModelAdmin):
    list_display = (
        "athlete",
        "personality_type",
        "assessed_on",
        "source",
        "is_active",
        "created_at",
    )
    list_filter = ("personality_type", "source", "is_active", "assessed_on")
    search_fields = (
        "athlete__full_name",
        "personality_type__code",
        "personality_type__title",
        "notes",
    )
    ordering = ("-assessed_on", "-id")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("athlete", "personality_type", "assessment_session")
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "athlete",
                    "personality_type",
                    "assessment_session",
                    "assessed_on",
                    "source",
                    "is_active",
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
            "Audit",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )