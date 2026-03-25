from __future__ import annotations

from typing import Any, Iterable

from django.core.management.base import BaseCommand, CommandError

from apps.system.models import BusinessObject, PageLayout
from apps.system.services.layout_generator import LayoutGenerator


REQUIRED_LAYOUT_TYPES = ("form", "detail", "search")
SECTION_I18N_LAYOUT_TYPES = ("form", "detail")


def _normalize_sections(layout_config: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(layout_config, dict):
        return []
    sections = layout_config.get("sections")
    return sections if isinstance(sections, list) else []


def _normalize_columns(layout_config: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(layout_config, dict):
        return []
    columns = layout_config.get("columns")
    return columns if isinstance(columns, list) else []


def _has_translation_payload(title: Any) -> bool:
    if isinstance(title, dict):
        translation_key = title.get("translationKey")
        return isinstance(translation_key, str) and bool(translation_key.strip())
    if isinstance(title, list):
        return any(_has_translation_payload(item) for item in title)
    return False


def _expected_layout_code(business_object: BusinessObject, layout_type: str) -> str:
    return f"{str(business_object.code or '').lower()}_{layout_type}"


def _published_default_layouts_for(business_object: BusinessObject, layout_type: str) -> Iterable[PageLayout]:
    return PageLayout.objects.filter(
        business_object=business_object,
        layout_code=_expected_layout_code(business_object, layout_type),
        layout_type=layout_type,
        is_default=True,
        is_active=True,
        status="published",
        is_deleted=False,
    ).order_by("-published_at", "-updated_at")


class Command(BaseCommand):
    help = "Verify bootstrap-generated default layouts and section i18n payloads."

    def add_arguments(self, parser):
        parser.add_argument(
            "--object-code",
            type=str,
            help="Only verify one business object code.",
        )

    def handle(self, *args, **options):
        object_code = str(options.get("object_code") or "").strip()

        queryset = BusinessObject.objects.filter(is_deleted=False).order_by("code")
        if object_code:
            queryset = queryset.filter(code=object_code)

        business_objects = list(queryset)
        if not business_objects:
            raise CommandError(f"No BusinessObject rows found for object code: {object_code or 'ALL'}")

        failures: list[str] = []
        checked_layouts = 0

        for business_object in business_objects:
            self.stdout.write(self.style.WARNING(f"Verifying {business_object.code}..."))

            for layout_type in REQUIRED_LAYOUT_TYPES:
                layout = _published_default_layouts_for(business_object, layout_type).first()
                if not layout:
                    failures.append(
                        f"{business_object.code}: missing published default {layout_type} layout"
                    )
                    continue

                checked_layouts += 1
                layout_config = layout.layout_config if isinstance(layout.layout_config, dict) else {}

                if layout_type == "list":
                    columns = _normalize_columns(layout_config)
                    if not columns:
                        failures.append(
                            f"{business_object.code}: default list layout has no columns"
                        )
                    continue

                sections = _normalize_sections(layout_config)
                if not sections:
                    failures.append(
                        f"{business_object.code}: default {layout_type} layout has no sections"
                    )
                    continue

                if layout_type in SECTION_I18N_LAYOUT_TYPES:
                    for index, section in enumerate(sections, start=1):
                        title = section.get("title")
                        if not _has_translation_payload(title):
                            section_id = section.get("id") or section.get("name") or f"section_{index}"
                            failures.append(
                                f"{business_object.code}: {layout_type} layout section '{section_id}' is missing translationKey payload"
                            )

            generated_list_layout = LayoutGenerator.generate_list_layout(business_object)
            if not _normalize_columns(generated_list_layout):
                failures.append(
                    f"{business_object.code}: generated list layout has no columns"
                )
            else:
                checked_layouts += 1

            self.stdout.write(self.style.SUCCESS(f"Verified {business_object.code}"))

        if failures:
            message = "\n".join(f"- {failure}" for failure in failures)
            raise CommandError(f"Runtime default verification failed:\n{message}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Runtime defaults verified for {len(business_objects)} objects / {checked_layouts} layouts."
            )
        )
