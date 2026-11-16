from django.contrib import admin

from .models import LeadInquiry


@admin.register(LeadInquiry)
class LeadInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "inquiry_type",
        "athlete_sport",
        "academy_name",
        "email",
        "mobile_number",
        "created_at",
        "is_active",
    )
    list_filter = ("inquiry_type", "athlete_sport", "academy_city", "is_active", "created_at")
    search_fields = (
        "full_name",
        "email",
        "mobile_number",
        "academy_name",
        "contact_person_name",
        "athlete_sport",
    )
    ordering = ("-created_at", "-id")
    readonly_fields = ("created_at", "updated_at")