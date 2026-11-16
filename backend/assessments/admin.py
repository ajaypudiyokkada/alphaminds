from datetime import date

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse

from .forms import AssessmentMetricValueAdminForm, AssessmentSessionAdminForm
from .models import AssessmentMetricValue, AssessmentSession


class AssessmentMetricValueInline(admin.TabularInline):
    model = AssessmentMetricValue
    form = AssessmentMetricValueAdminForm
    extra = 0
    autocomplete_fields = ("metric_definition",)
    fields = (
        "sequence_no",
        "metric_definition",
        "value_data_type",
        "numeric_value",
        "text_value",
        "boolean_value",
        "date_value",
        "json_value",
        "display_value",
        "units",
    )
    readonly_fields = ()
    show_change_link = True

    class Media:
        js = ("assessments/js/assessment_metric_value_inline.js",)


@admin.register(AssessmentSession)
class AssessmentSessionAdmin(admin.ModelAdmin):
    form = AssessmentSessionAdminForm
    actions = ["create_program_from_mtq"]

    list_display = (
        "session_uuid",
        "athlete",
        "protocol",
        "center",
        "sport",
        "assessed_on",
        "status",
        "source",
        "is_active",
    )
    list_filter = (
        "status",
        "source",
        "center",
        "sport",
        "protocol__framework__domain",
        "protocol__framework",
        "protocol",
        "is_active",
        "assessed_on",
    )
    search_fields = (
        "session_uuid",
        "athlete__full_name",
        "protocol__name",
        "protocol__framework__name",
        "protocol__framework__domain__name",
        "center__name",
        "sport__name",
        "source_reference",
        "notes",
    )
    ordering = ("-assessed_on", "-id")
    readonly_fields = ("created_at", "updated_at", "session_uuid")
    autocomplete_fields = ("athlete", "enrollment", "center", "sport", "protocol")
    inlines = [AssessmentMetricValueInline]
    fieldsets = (
        (
            "Context",
            {
                "fields": (
                    "session_uuid",
                    "athlete",
                    "enrollment",
                    "center",
                    "sport",
                    "protocol",
                    "assessed_on",
                    "status",
                    "is_active",
                )
            },
        ),
        (
            "Source",
            {
                "fields": (
                    "source",
                    "source_reference",
                )
            },
        ),
        (
            "Notes & Payload",
            {
                "fields": (
                    "notes",
                    "raw_payload",
                ),
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

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)

        enrollment_id = request.GET.get("enrollment")

        if enrollment_id:
            try:
                enrollment = self.model._meta.get_field("enrollment").remote_field.model.objects.select_related(
                    "athlete",
                    "center",
                    "sport",
                ).get(pk=enrollment_id)

                initial.update(
                    {
                        "enrollment": enrollment.pk,
                        "athlete": enrollment.athlete_id,
                        "center": enrollment.center_id,
                        "sport": enrollment.sport_id,
                    }
                )

            except Exception:
                pass

        return initial

    def _create_missing_metric_values(self, session):
        if not session.protocol_id:
            return 0

        protocol_metrics = session.protocol.metrics.filter(is_active=True).order_by("display_order", "id")
        existing_metric_ids = set(
            session.metric_values.values_list("metric_definition_id", flat=True)
        )

        to_create = []
        for metric in protocol_metrics:
            if metric.id in existing_metric_ids:
                continue

            to_create.append(
                AssessmentMetricValue(
                    assessment_session=session,
                    metric_definition=metric,
                    value_data_type=metric.value_data_type,
                    units=metric.units,
                    sequence_no=1,
                    display_value="",
                )
            )

        if to_create:
            AssessmentMetricValue.objects.bulk_create(to_create)

        return len(to_create)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        created_count = self._create_missing_metric_values(form.instance)
        if created_count:
            self.message_user(
                request,
                f"{created_count} metric value row(s) auto-created from the selected protocol.",
            )

    @admin.action(description="Create program from MTQ result")
    def create_program_from_mtq(self, request, queryset):
        from programs.models import Program, ProgramTemplate
        from programs.services.mtq_engine import compute_mtq_total, get_mtq_scores, recommend_program_type

        if queryset.count() != 1:
            self.message_user(request, "Select exactly one MTQ assessment session.", level=messages.ERROR)
            return

        session = queryset.first()
        scores = get_mtq_scores(session)
        total = compute_mtq_total(scores)

        if total is None:
            self.message_user(request, "No MTQ metric values found in this session.", level=messages.ERROR)
            return

        rec_type = recommend_program_type(total)
        template = ProgramTemplate.objects.filter(program_type=rec_type).first()

        if not template:
            self.message_user(
                request,
                f"No ProgramTemplate configured for '{rec_type}'. Create one first.",
                level=messages.ERROR,
            )
            return

        program = Program.objects.create(
            athlete=session.athlete,
            enrollment=session.enrollment,
            template=template,
            mtq_session=session,
            program_type=rec_type,
            start_date=date.today(),
            mtq_total_score=total,
            status="draft",
        )
        created = program.generate_sessions()

        self.message_user(
            request,
            f"Program created: {template.name} (MTQ={total}) with {created} sessions. "
            f"Review and activate it.",
            level=messages.SUCCESS,
        )
        return redirect(reverse("admin:programs_program_change", args=[program.pk]))


class AssessmentMetricValueInline(admin.TabularInline):
    model = AssessmentMetricValue
    form = AssessmentMetricValueAdminForm
    extra = 0
    autocomplete_fields = ()
    fields = (
        "sequence_no",
        "metric_definition",
        "value_data_type",
        "numeric_value",
        "text_value",
        "boolean_value",
        "date_value",
        "json_value",
        "display_value",
        "units",
    )
    readonly_fields = ()
    show_change_link = True

    class Media:
        js = ("assessments/js/assessment_metric_value_inline.js",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "metric_definition":
            qs = formfield.queryset.select_related("protocol", "protocol__framework")
            choices = [("", "---------")]
            for metric in qs:
                label = str(metric)
                choices.append(
                    (
                        metric.pk,
                        label,
                        {
                            "data-value-data-type": metric.value_data_type or "",
                            "data-units": metric.units or "",
                        },
                    )
                )
            formfield.choices = choices
        return formfield

@admin.register(AssessmentMetricValue)
class AssessmentMetricValueAdmin(admin.ModelAdmin):
    form = AssessmentMetricValueAdminForm

    list_display = (
        "assessment_session",
        "metric_definition",
        "sequence_no",
        "value_data_type",
        "display_value",
        "units",
        "is_active",
        "created_at",
    )
    list_filter = (
        "value_data_type",
        "metric_definition__protocol__framework__domain",
        "metric_definition__protocol__framework",
        "metric_definition__protocol",
        "metric_definition",
        "is_active",
        "created_at",
    )
    search_fields = (
        "assessment_session__athlete__full_name",
        "metric_definition__name",
        "metric_definition__code",
        "display_value",
        "notes",
    )
    ordering = ("assessment_session", "sequence_no", "id")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("assessment_session", "metric_definition")
    fieldsets = (
        (
            "Core",
            {
                "fields": (
                    "assessment_session",
                    "metric_definition",
                    "sequence_no",
                    "value_data_type",
                    "units",
                    "display_value",
                    "is_active",
                )
            },
        ),
        (
            "Typed Values",
            {
                "fields": (
                    "numeric_value",
                    "text_value",
                    "boolean_value",
                    "date_value",
                    "json_value",
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

    class Media:
        js = ("assessments/js/assessment_metric_value_inline.js",)