from django import forms

from core.choices import ValueDataTypeChoices
from .models import AssessmentMetricValue, AssessmentSession


class AssessmentSessionAdminForm(forms.ModelForm):
    class Meta:
        model = AssessmentSession
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        enrollment = cleaned_data.get("enrollment")

        if enrollment:
            cleaned_data["athlete"] = enrollment.athlete
            cleaned_data["center"] = enrollment.center
            cleaned_data["sport"] = enrollment.sport

        return cleaned_data


class AssessmentMetricValueAdminForm(forms.ModelForm):
    class Meta:
        model = AssessmentMetricValue
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        metric_definition = cleaned_data.get("metric_definition")
        value_data_type = cleaned_data.get("value_data_type")
        units = cleaned_data.get("units")

        if metric_definition:
            if not value_data_type:
                value_data_type = metric_definition.value_data_type
                cleaned_data["value_data_type"] = value_data_type
            if not units:
                cleaned_data["units"] = metric_definition.units

        typed_fields = {
            ValueDataTypeChoices.INTEGER: "numeric_value",
            ValueDataTypeChoices.DECIMAL: "numeric_value",
            ValueDataTypeChoices.TEXT: "text_value",
            ValueDataTypeChoices.BOOLEAN: "boolean_value",
            ValueDataTypeChoices.DATE: "date_value",
            ValueDataTypeChoices.JSON: "json_value",
        }

        keep_field = typed_fields.get(value_data_type)

        if keep_field != "numeric_value":
            cleaned_data["numeric_value"] = None
        if keep_field != "text_value":
            cleaned_data["text_value"] = ""
        if keep_field != "boolean_value":
            cleaned_data["boolean_value"] = None
        if keep_field != "date_value":
            cleaned_data["date_value"] = None
        if keep_field != "json_value":
            cleaned_data["json_value"] = {}

        return cleaned_data