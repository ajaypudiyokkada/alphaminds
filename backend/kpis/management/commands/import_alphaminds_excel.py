from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from kpis.services.importers.alphaminds_excel import AlphaMindsExcelImporter


class Command(BaseCommand):
    help = "Import AlphaMinds taxonomy and optional sample data from AlphaMindDashboard.xlsx"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            required=True,
            help="Absolute or relative path to AlphaMindDashboard.xlsx",
        )
        parser.add_argument(
            "--taxonomy-only",
            action="store_true",
            help="Import only taxonomy/master data",
        )
        parser.add_argument(
            "--include-sample-data",
            action="store_true",
            help="Also import sample athlete/enrollment/session/value data",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report actions without committing data",
        )
        parser.add_argument(
            "--sheet",
            default=None,
            help="Optional main data sheet name override",
        )
        parser.add_argument(
            "--personality-sheet",
            default=None,
            help="Optional personality lookup sheet name override",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"]).expanduser().resolve()

        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        taxonomy_only = options["taxonomy_only"]
        include_sample_data = options["include_sample_data"]
        dry_run = options["dry_run"]

        if not taxonomy_only and not include_sample_data:
            # default behavior: taxonomy only
            taxonomy_only = True

        importer = AlphaMindsExcelImporter(
            file_path=file_path,
            stdout=self.stdout,
            style=self.style,
            dry_run=dry_run,
            main_sheet_name=options["sheet"],
            personality_sheet_name=options["personality_sheet"],
        )

        result = importer.run(
            import_taxonomy=True,
            import_sample_data=include_sample_data and not taxonomy_only,
        )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Import completed."))
        self.stdout.write(f"Workbook: {file_path}")
        self.stdout.write(f"Dry run: {dry_run}")
        self.stdout.write("")

        for key, value in result.items():
            self.stdout.write(f"{key}: {value}")