"""
Bootstrap runtime-safe system defaults for Docker and local development.

This command is intentionally idempotent and non-destructive:
- register missing hardcoded BusinessObjects
- sync metadata for hardcoded models
- create missing default layouts
- normalize menu configuration

It avoids force-overwriting layouts so it can run during container startup.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Bootstrap runtime-safe metadata, layouts, and menu defaults"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-layouts",
            action="store_true",
            help="Force-regenerate default layouts during bootstrap.",
        )

    def handle(self, *args, **options):
        force_layouts = bool(options.get("force_layouts"))
        steps = [
            (
                "Registering core models",
                ["register_core_models", "--sync-fields"],
            ),
            (
                "Synchronizing metadata",
                ["sync_metadata"],
            ),
            (
                "Creating missing default layouts",
                ["create_default_layouts", *(["--force"] if force_layouts else [])],
            ),
            (
                "Normalizing menu configuration",
                ["update_menu_config"],
            ),
        ]

        for description, command_args in steps:
            self.stdout.write(self.style.WARNING(f"{description}..."))
            call_command(*command_args)

        self.stdout.write(self.style.SUCCESS("Bootstrap defaults completed."))
