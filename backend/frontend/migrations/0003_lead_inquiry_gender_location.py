import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("frontend", "0002_lead_inquiry_multi_type_dob_guardian"),
    ]

    operations = [
        # Remove enrolling_for (replaced by age-based logic only)
        migrations.RemoveField(
            model_name="leadinquiry",
            name="enrolling_for",
        ),
        # Add gender
        migrations.AddField(
            model_name="leadinquiry",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
                max_length=1,
            ),
        ),
        # Add location
        migrations.AddField(
            model_name="leadinquiry",
            name="pincode",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name="leadinquiry",
            name="city",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="leadinquiry",
            name="state",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
