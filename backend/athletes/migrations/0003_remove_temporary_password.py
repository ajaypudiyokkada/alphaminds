from django.db import migrations


def remove_temporary_password(apps, schema_editor):
    Athlete = apps.get_model("athletes", "Athlete")
    for athlete in Athlete.objects.all().only("id", "metadata"):
        meta = athlete.metadata or {}
        if "temporary_password" in meta or "credentials_shared" in meta:
            meta.pop("temporary_password", None)
            meta.pop("credentials_shared", None)
            Athlete.objects.filter(pk=athlete.pk).update(metadata=meta)


class Migration(migrations.Migration):

    dependencies = [
        ("athletes", "0002_athlete_user"),
    ]

    operations = [
        migrations.RunPython(remove_temporary_password, migrations.RunPython.noop),
    ]
