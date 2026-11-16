from django.contrib import admin

from .models import Center, StaffProfile


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "city",
        "state",
        "country",
        "timezone",
        "is_active",
        "created_at",
    )
    list_filter = ("country", "state", "city", "is_active", "created_at")
    search_fields = ("name", "short_name", "code", "city", "state", "country")
    ordering = ("country", "state", "city", "name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "code",
                    "name",
                    "short_name",
                    "is_active",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "city",
                    "state",
                    "country",
                    "timezone",
                    "address_line1",
                    "address_line2",
                    "postal_code",
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
    
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "center", "role", "is_active", "created_at")
    list_filter = ("center", "role", "is_active")
    search_fields = ("user__username", "user__first_name", "user__last_name", "center__name")
    autocomplete_fields = ("user", "center")
    readonly_fields = ("created_at", "updated_at")