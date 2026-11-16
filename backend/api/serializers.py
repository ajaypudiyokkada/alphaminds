from rest_framework import serializers

from athletes.models import Athlete, AthleteEnrollment
from assessments.models import AssessmentMetricValue, AssessmentSession
from frontend.models import LeadInquiry, LeadInquiryType


# ── Athlete ───────────────────────────────────────────────────────────────────

class AthleteSerializer(serializers.ModelSerializer):
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)
    age = serializers.IntegerField(read_only=True)
    age_group = serializers.CharField(read_only=True)

    class Meta:
        model = Athlete
        fields = [
            "id",
            "full_name",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "gender_display",
            "age",
            "age_group",
            "email",
            "phone",
            "dominant_hand",
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    sport_name = serializers.CharField(source="sport.name", read_only=True)
    center_name = serializers.CharField(source="center.name", read_only=True)

    class Meta:
        model = AthleteEnrollment
        fields = [
            "id",
            "sport_name",
            "center_name",
            "start_date",
            "end_date",
            "status",
            "batch_name",
        ]


# ── Assessment ────────────────────────────────────────────────────────────────

class MetricValueSerializer(serializers.ModelSerializer):
    metric_name = serializers.CharField(source="metric_definition.name", read_only=True)
    metric_label = serializers.CharField(source="metric_definition.label", read_only=True)
    interpretation_direction = serializers.CharField(
        source="metric_definition.interpretation_direction", read_only=True
    )
    is_higher_better = serializers.BooleanField(
        source="metric_definition.is_higher_better", read_only=True
    )
    units = serializers.SerializerMethodField()

    def get_units(self, obj):
        return obj.units or getattr(obj.metric_definition, "units", "")

    class Meta:
        model = AssessmentMetricValue
        fields = [
            "id",
            "metric_name",
            "metric_label",
            "value_data_type",
            "numeric_value",
            "text_value",
            "boolean_value",
            "date_value",
            "display_value",
            "units",
            "interpretation_direction",
            "is_higher_better",
            "sequence_no",
            "notes",
        ]


class AssessmentSessionListSerializer(serializers.ModelSerializer):
    protocol_name = serializers.CharField(source="protocol.name", read_only=True)
    framework_name = serializers.CharField(source="protocol.framework.name", read_only=True)
    domain_name = serializers.CharField(source="protocol.framework.domain.name", read_only=True)

    class Meta:
        model = AssessmentSession
        fields = [
            "id",
            "session_uuid",
            "assessed_on",
            "status",
            "protocol_name",
            "framework_name",
            "domain_name",
        ]


class AssessmentSessionDetailSerializer(serializers.ModelSerializer):
    protocol_name = serializers.CharField(source="protocol.name", read_only=True)
    framework_name = serializers.CharField(source="protocol.framework.name", read_only=True)
    domain_name = serializers.CharField(source="protocol.framework.domain.name", read_only=True)
    sport_name = serializers.CharField(source="sport.name", read_only=True)
    metric_values = serializers.SerializerMethodField()

    def get_metric_values(self, obj):
        from core.choices import AssessmentSessionStatusChoices
        if obj.status != AssessmentSessionStatusChoices.PUBLISHED:
            return []
        qs = obj.metric_values.select_related("metric_definition").order_by("sequence_no", "id")
        return MetricValueSerializer(qs, many=True).data

    class Meta:
        model = AssessmentSession
        fields = [
            "id",
            "session_uuid",
            "assessed_on",
            "status",
            "protocol_name",
            "framework_name",
            "domain_name",
            "sport_name",
            "notes",
            "metric_values",
        ]


# ── Lead Inquiry ──────────────────────────────────────────────────────────────

class LeadInquirySerializer(serializers.ModelSerializer):
    inquiry_types = serializers.ListField(
        child=serializers.ChoiceField(choices=LeadInquiryType.values),
        min_length=1,
    )

    class Meta:
        model = LeadInquiry
        fields = [
            "inquiry_type",
            "inquiry_types",
            "full_name",
            "email",
            "mobile_number",
            "gender",
            "date_of_birth",
            "parent_mobile",
            "pincode",
            "city",
            "state",
            "athlete_sport",
            "academy_name",
            "contact_person_name",
            "designation",
            "academy_city",
            "athlete_count",
            "message",
        ]
        read_only_fields = ["inquiry_type"]
        extra_kwargs = {
            "gender": {"required": False, "allow_blank": True},
            "date_of_birth": {"required": False, "allow_null": True},
            "parent_mobile": {"required": False, "allow_blank": True},
            "pincode": {"required": False, "allow_blank": True},
            "city": {"required": False, "allow_blank": True},
            "state": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        from datetime import date

        types = attrs.get("inquiry_types", [])
        if not types:
            raise serializers.ValidationError({"inquiry_types": "Select at least one interest."})

        attrs["inquiry_type"] = types[0]

        dob = attrs.get("date_of_birth")
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 0 or age > 120:
                raise serializers.ValidationError({"date_of_birth": "Enter a valid date of birth."})
            if age < 18 and not attrs.get("parent_mobile", ""):
                raise serializers.ValidationError(
                    {"parent_mobile": "Parent/guardian mobile is required for athletes under 18."}
                )

        return attrs
