from django.contrib import admin

from .models import KPIDomain, KPIFramework, KPIProtocol, MetricDefinition


class KPIFrameworkInline(admin.TabularInline):
    model = KPIFramework
    extra = 0
    fields = ("name", "code", "display_order", "is_active")
    show_change_link = True


class KPIProtocolInline(admin.TabularInline):
    model = KPIProtocol
    extra = 0
    fields = ("name", "code", "display_order", "source_type", "capture_mode", "is_active")
    show_change_link = True


class MetricDefinitionInline(admin.TabularInline):
    model = MetricDefinition
    extra = 0
    fields = (
        "name",
        "code",
        "value_data_type",
        "units",
        "importance",
        "display_order",
        "is_required",
        "is_active",
    )
    show_change_link = True


@admin.register(KPIDomain)
class KPIDomainAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "display_order", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "code", "description")
    ordering = ("display_order", "name")
    readonly_fields = ("created_at", "updated_at")
    inlines = [KPIFrameworkInline]
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "name",
                    "code",
                    "display_order",
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


@admin.register(KPIFramework)
class KPIFrameworkAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "domain", "display_order", "is_active", "created_at")
    list_filter = ("domain", "is_active", "created_at")
    search_fields = ("name", "code", "description", "domain__name")
    ordering = ("domain__display_order", "display_order", "name")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("domain",)
    inlines = [KPIProtocolInline]
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "domain",
                    "name",
                    "code",
                    "display_order",
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


@admin.register(KPIProtocol)
class KPIProtocolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "framework",
        "source_type",
        "capture_mode",
        "display_order",
        "is_active",
        "created_at",
    )
    list_filter = (
        "framework__domain",
        "framework",
        "source_type",
        "capture_mode",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "code", "description", "framework__name", "framework__domain__name")
    ordering = ("framework__display_order", "display_order", "name")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("framework",)
    inlines = [MetricDefinitionInline]
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "framework",
                    "name",
                    "code",
                    "display_order",
                    "description",
                    "source_type",
                    "capture_mode",
                    "is_active",
                )
            },
        ),
        (
            "Config",
            {
                "fields": ("config",),
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


@admin.register(MetricDefinition)
class MetricDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "protocol",
        "value_data_type",
        "units",
        "importance",
        "is_required",
        "is_higher_better",
        "display_order",
        "is_active",
    )
    list_filter = (
        "protocol__framework__domain",
        "protocol__framework",
        "protocol",
        "value_data_type",
        "importance",
        "is_required",
        "is_higher_better",
        "is_active",
    )
    search_fields = (
        "name",
        "label",
        "code",
        "protocol__name",
        "protocol__framework__name",
        "protocol__framework__domain__name",
        "description",
    )
    ordering = ("protocol__display_order", "display_order", "name")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("protocol",)
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "protocol",
                    "name",
                    "label",
                    "code",
                    "description",
                    "display_order",
                    "is_active",
                )
            },
        ),
        (
            "Value Rules",
            {
                "fields": (
                    "value_data_type",
                    "units",
                    "importance",
                    "interpretation_direction",
                    "min_value",
                    "max_value",
                    "allowed_text_values",
                    "is_required",
                    "is_higher_better",
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