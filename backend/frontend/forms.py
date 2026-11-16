import json

from django import forms
from django.core.exceptions import ValidationError

from assessments.models import AssessmentMetricValue, AssessmentSession
from core.choices import ValueDataTypeChoices
from kpis.models import MetricDefinition
from athletes.models import Athlete, AthleteCenter, AthleteEnrollment, AthleteSport
from django.db import transaction
from django.utils import timezone

from .models import LeadInquiry, LeadInquiryType
from sports.models import Sport


class TailwindFormMixin:
    def apply_tailwind_classes(self):
        base_class = (
            "w-full rounded-xl border border-am-border bg-am-alt "
            "px-4 py-3 text-[#e0e1ec] placeholder-am-dim focus:outline-none focus:ring-2 focus:ring-am-cyan"
        )
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {base_class}".strip()


class AssessmentSessionCreateForm(TailwindFormMixin, forms.ModelForm):
    domain = forms.ModelChoiceField(queryset=None, required=False)
    framework = forms.ModelChoiceField(queryset=None, required=False)

    class Meta:
        model = AssessmentSession
        fields = [
            "athlete",
            "enrollment",
            "center",
            "sport",
            "domain",
            "framework",
            "protocol",
            "assessed_on",
            "notes",
        ]
        widgets = {
            "assessed_on": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(
        self,
        *args,
        center=None,
        athlete_queryset=None,
        enrollment_queryset=None,
        domain_queryset=None,
        framework_queryset=None,
        protocol_queryset=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.center = center

        if athlete_queryset is not None:
            self.fields["athlete"].queryset = athlete_queryset

        if enrollment_queryset is not None:
            self.fields["enrollment"].queryset = enrollment_queryset.select_related(
                "athlete",
                "center",
                "sport",
            )

        self.fields["domain"].queryset = (
            domain_queryset.order_by("display_order", "name")
            if domain_queryset is not None
            else self.fields["domain"].queryset.none()
        )

        self.fields["framework"].queryset = (
            framework_queryset.order_by("display_order", "name")
            if framework_queryset is not None
            else self.fields["framework"].queryset.none()
        )

        self.fields["protocol"].queryset = (
            protocol_queryset.order_by("display_order", "name")
            if protocol_queryset is not None
            else self.fields["protocol"].queryset.none()
        )

        athlete_id = (
            self.data.get("athlete")
            or self.initial.get("athlete")
            or getattr(getattr(self.instance, "athlete", None), "id", None)
        )
        if athlete_id:
            self.fields["enrollment"].queryset = self.fields["enrollment"].queryset.filter(
                athlete_id=athlete_id
            )
        else:
            self.fields["enrollment"].queryset = self.fields["enrollment"].queryset.none()

        domain_id = self.data.get("domain") or self.initial.get("domain")
        framework_id = self.data.get("framework") or self.initial.get("framework")

        if domain_id:
            self.fields["framework"].queryset = self.fields["framework"].queryset.filter(
                domain_id=domain_id
            ).order_by("display_order", "name")
        else:
            self.fields["framework"].queryset = self.fields["framework"].queryset.none()

        if framework_id:
            self.fields["protocol"].queryset = self.fields["protocol"].queryset.filter(
                framework_id=framework_id
            ).order_by("display_order", "name")
        else:
            self.fields["protocol"].queryset = self.fields["protocol"].queryset.none()

        self.fields["center"].required = False
        self.fields["sport"].required = False

        self.apply_tailwind_classes()

    def clean(self):
        cleaned_data = super().clean()
        athlete = cleaned_data.get("athlete")
        enrollment = cleaned_data.get("enrollment")
        center = cleaned_data.get("center")
        sport = cleaned_data.get("sport")
        domain = cleaned_data.get("domain")
        framework = cleaned_data.get("framework")
        protocol = cleaned_data.get("protocol")

        if enrollment:
            if athlete and enrollment.athlete_id != athlete.id:
                raise ValidationError("Selected enrollment does not belong to the selected athlete.")
            if center and enrollment.center_id != center.id:
                raise ValidationError("Selected enrollment does not match selected center.")
            if sport and enrollment.sport_id != sport.id:
                raise ValidationError("Selected enrollment does not match selected sport.")

            cleaned_data["athlete"] = enrollment.athlete
            cleaned_data["center"] = enrollment.center
            cleaned_data["sport"] = enrollment.sport

        if framework and domain and framework.domain_id != domain.id:
            raise ValidationError("Selected framework does not belong to the selected domain.")

        if protocol and framework and protocol.framework_id != framework.id:
            raise ValidationError("Selected protocol does not belong to the selected framework.")

        if protocol and domain and protocol.framework.domain_id != domain.id:
            raise ValidationError("Selected protocol does not belong to the selected domain.")

        return cleaned_data


class DynamicMetricValueForm(TailwindFormMixin, forms.Form):
    def __init__(self, *args, metric_definitions=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.metric_definitions = list(metric_definitions or [])

        for metric in self.metric_definitions:
            field_name = self._field_name(metric)

            if metric.value_data_type in {
                ValueDataTypeChoices.INTEGER,
                ValueDataTypeChoices.DECIMAL,
            }:
                self.fields[field_name] = forms.DecimalField(
                    required=metric.is_required,
                    label=metric.label or metric.name,
                    min_value=metric.min_value,
                    max_value=metric.max_value,
                    decimal_places=4,
                    max_digits=14,
                )

            elif metric.value_data_type == ValueDataTypeChoices.BOOLEAN:
                self.fields[field_name] = forms.TypedChoiceField(
                    required=metric.is_required,
                    label=metric.label or metric.name,
                    choices=(("true", "Yes"), ("false", "No")),
                    coerce=lambda x: x == "true",
                    empty_value=None,
                )

            elif metric.value_data_type == ValueDataTypeChoices.DATE:
                self.fields[field_name] = forms.DateField(
                    required=metric.is_required,
                    label=metric.label or metric.name,
                    widget=forms.DateInput(attrs={"type": "date"}),
                )

            elif metric.value_data_type == ValueDataTypeChoices.JSON:
                self.fields[field_name] = forms.CharField(
                    required=metric.is_required,
                    label=metric.label or metric.name,
                    widget=forms.Textarea(attrs={"rows": 3}),
                    help_text="Enter JSON text.",
                )

            else:
                self.fields[field_name] = forms.CharField(
                    required=metric.is_required,
                    label=metric.label or metric.name,
                )

        self.apply_tailwind_classes()

    @staticmethod
    def _field_name(metric: MetricDefinition) -> str:
        return f"metric_{metric.id}"

    def build_metric_value_instances(self, assessment_session):
        instances = []

        for idx, metric in enumerate(self.metric_definitions, start=1):
            field_name = self._field_name(metric)
            value = self.cleaned_data.get(field_name)

            if value in (None, "", {}):
                continue

            payload = {
                "assessment_session": assessment_session,
                "metric_definition": metric,
                "value_data_type": metric.value_data_type,
                "units": metric.units,
                "sequence_no": idx,
                "display_value": str(value),
                "numeric_value": None,
                "text_value": "",
                "boolean_value": None,
                "date_value": None,
                "json_value": {},
            }

            if metric.value_data_type in {
                ValueDataTypeChoices.INTEGER,
                ValueDataTypeChoices.DECIMAL,
            }:
                payload["numeric_value"] = value
            elif metric.value_data_type == ValueDataTypeChoices.BOOLEAN:
                payload["boolean_value"] = value
            elif metric.value_data_type == ValueDataTypeChoices.DATE:
                payload["date_value"] = value
            elif metric.value_data_type == ValueDataTypeChoices.JSON:
                if isinstance(value, str):
                    try:
                        payload["json_value"] = json.loads(value)
                        payload["display_value"] = "JSON"
                    except json.JSONDecodeError:
                        raise ValidationError(f"Invalid JSON for {metric.name}.")
                else:
                    payload["json_value"] = {"raw": value}
                    payload["display_value"] = "JSON"
            else:
                payload["text_value"] = value

            instances.append(AssessmentMetricValue(**payload))

        return instances
    
class AthleteLeadInquiryForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = LeadInquiry
        fields = [
            "full_name",
            "athlete_sport",
            "email",
            "mobile_number",
            "message",
        ]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, inquiry_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.inquiry_type = inquiry_type
        self.apply_tailwind_classes()
        self.fields["full_name"].label = "Athlete Name"
        self.fields["athlete_sport"].label = "Athlete Sport"
        self.fields["email"].label = "Email ID"
        self.fields["mobile_number"].label = "India Mobile Phone Number"
        self.fields["message"].label = "Tell us about your goal"
        self.fields["message"].required = False

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.inquiry_type = self.inquiry_type
        if commit:
            obj.save()
        return obj


class AcademyLeadInquiryForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = LeadInquiry
        fields = [
            "academy_name",
            "contact_person_name",
            "designation",
            "academy_city",
            "email",
            "mobile_number",
            "athlete_count",
            "message",
        ]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, inquiry_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.inquiry_type = inquiry_type
        self.apply_tailwind_classes()
        self.fields["academy_name"].label = "Academy Name"
        self.fields["contact_person_name"].label = "Contact Person Name"
        self.fields["designation"].label = "Designation"
        self.fields["academy_city"].label = "City"
        self.fields["email"].label = "Official Email ID"
        self.fields["mobile_number"].label = "India Mobile Phone Number"
        self.fields["athlete_count"].label = "Approximate Number of Athletes"
        self.fields["message"].label = "What would you like to explore?"
        self.fields["message"].required = False

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.inquiry_type = self.inquiry_type
        obj.full_name = obj.contact_person_name
        if commit:
            obj.save()
        return obj
    
class StaffAthleteCreateForm(TailwindFormMixin, forms.ModelForm):
    sport = forms.ModelChoiceField(queryset=Sport.objects.none())
    start_date = forms.DateField(initial=timezone.now().date())

    class Meta:
        model = Athlete
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "dominant_hand",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, center=None, sport_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.center = center
        self.fields["sport"].queryset = sport_queryset or Sport.objects.all()
        self.apply_tailwind_classes()

    def save(self, commit=True):
        with transaction.atomic():
            athlete = super().save(commit=True)

            sport = self.cleaned_data["sport"]
            start_date = self.cleaned_data["start_date"]

            AthleteSport.objects.get_or_create(
                athlete=athlete,
                sport=sport,
                start_date=start_date,
                defaults={"is_primary": True},
            )

            AthleteCenter.objects.get_or_create(
                athlete=athlete,
                center=self.center,
                start_date=start_date,
                defaults={"is_primary": True},
            )

            AthleteEnrollment.objects.get_or_create(
                athlete=athlete,
                center=self.center,
                sport=sport,
                start_date=start_date,
                defaults={"status": "active"},
            )

            return athlete