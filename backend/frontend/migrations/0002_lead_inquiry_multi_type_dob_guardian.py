import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("frontend", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="leadinquiry",
            name="inquiry_types",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="leadinquiry",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="leadinquiry",
            name="enrolling_for",
            field=models.CharField(
                blank=True,
                choices=[
                    ("myself", "Myself"),
                    ("my_child", "My Child"),
                    ("my_children", "My Children"),
                ],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="leadinquiry",
            name="parent_mobile",
            field=models.CharField(
                blank=True,
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Enter a valid India mobile number.",
                        regex="^(?:\\+91|91)?[6-9]\\d{9}$",
                    )
                ],
            ),
        ),
    ]
