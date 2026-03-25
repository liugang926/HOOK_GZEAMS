from datetime import date, datetime
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.assets.models import Asset, AssetReturn, Supplier
from apps.common.management.commands.create_demo_data import Command
from apps.finance.models import FinanceVoucher
from apps.inventory.models import InventoryScan, InventoryTask
from apps.lifecycle.models import PurchaseRequest
from apps.projects.models import AssetProject


pytestmark = [pytest.mark.django_db, pytest.mark.demo_data]


def test_seed_datetime_returns_timezone_aware_datetime_for_date_seed():
    command = Command()

    seeded_value = command._seed_datetime(
        date(2026, 3, 21),
        day_offset=2,
        hour=14,
        minute=30,
    )

    assert timezone.is_aware(seeded_value)
    assert seeded_value.date() == date(2026, 3, 23)
    assert seeded_value.hour == 14
    assert seeded_value.minute == 30


def test_seed_datetime_uses_local_date_for_aware_datetime_seed():
    command = Command()
    base_value = timezone.make_aware(
        datetime(2026, 3, 21, 9, 15),
        timezone.get_current_timezone(),
    )

    seeded_value = command._seed_datetime(base_value, day_offset=1, hour=8, minute=0)

    assert timezone.is_aware(seeded_value)
    assert seeded_value.date() == date(2026, 3, 22)
    assert seeded_value.hour == 8
    assert seeded_value.minute == 0


def test_seed_datetime_rejects_unsupported_base_values():
    command = Command()

    with pytest.raises(TypeError, match="Unsupported seed datetime base value"):
        command._seed_datetime("2026-03-21")


def test_next_prefixed_sequence_uses_max_numeric_suffix_across_mixed_width_values(
    organization,
    second_organization,
):
    command = Command()

    Supplier.objects.create(
        organization=organization,
        code="SUPSEQ999",
        name="Legacy Sequence Supplier",
    )
    Supplier.objects.create(
        organization=second_organization,
        code="SUPSEQ1000",
        name="Cross Org Sequence Supplier",
    )

    next_sequence = command._next_prefixed_sequence(
        Supplier,
        "code",
        "SUPSEQ",
        width=4,
    )

    assert next_sequence == 1001


def test_next_prefixed_sequence_tracker_increments_within_same_run(organization):
    command = Command()
    tracker = {}

    Supplier.objects.create(
        organization=organization,
        code="SUPRUN0007",
        name="Tracker Base Supplier",
    )

    first_sequence = command._next_prefixed_sequence(
        Supplier,
        "code",
        "SUPRUN",
        width=4,
        tracker=tracker,
    )
    second_sequence = command._next_prefixed_sequence(
        Supplier,
        "code",
        "SUPRUN",
        width=4,
        tracker=tracker,
    )

    assert first_sequence == 8
    assert second_sequence == 9


def test_seed_or_top_up_records_only_creates_missing_records(organization):
    command = Command()
    stats = {}

    Supplier.objects.create(
        organization=organization,
        code="SUPTOP001",
        name="Top Up Supplier 1",
    )
    Supplier.objects.create(
        organization=organization,
        code="SUPTOP002",
        name="Top Up Supplier 2",
    )

    def create_suppliers(missing_count):
        created_records = []
        for index in range(missing_count):
            supplier = Supplier.objects.create(
                organization=organization,
                code=f"SUPTOP{index + 3:03d}",
                name=f"Top Up Supplier {index + 3}",
            )
            created_records.append(supplier)
        return created_records

    records, created = command._seed_or_top_up_records(
        queryset=Supplier.objects.filter(organization=organization, code__startswith="SUPTOP"),
        create_callback=create_suppliers,
        stats=stats,
        stats_key="suppliers",
        label="suppliers",
        skip_existing=True,
        top_up_existing=True,
        target_count=5,
    )

    assert len(records) == 5
    assert len(created) == 3
    assert stats["suppliers"] == 5


def test_create_demo_data_command_smoke_runs_successfully_for_new_organization(organization):
    stdout = StringIO()

    call_command(
        "create_demo_data",
        "--organization",
        str(organization.id),
        "--count",
        "1",
        stdout=stdout,
    )

    output = stdout.getvalue()

    assert "Demo data creation completed!" in output
    assert Supplier.objects.filter(organization=organization, is_deleted=False).count() == 10
    assert Asset.objects.filter(organization=organization, is_deleted=False).count() == 1
    assert AssetProject.objects.filter(organization=organization, is_deleted=False).count() == 20
    assert FinanceVoucher.objects.filter(organization=organization, is_deleted=False).count() == 20
    assert PurchaseRequest.objects.filter(organization=organization, is_deleted=False).count() == 1
    assert AssetReturn.objects.filter(organization=organization, is_deleted=False).count() == 20
    assert InventoryTask.objects.filter(organization=organization, is_deleted=False).count() == 20


def test_create_demo_data_command_top_up_smoke_repairs_only_top_up_enabled_models(organization):
    initial_stdout = StringIO()
    top_up_stdout = StringIO()

    call_command(
        "create_demo_data",
        "--organization",
        str(organization.id),
        "--count",
        "1",
        stdout=initial_stdout,
    )

    initial_scan_count = InventoryScan.objects.filter(
        task__organization=organization,
        is_deleted=False,
    ).count()
    initial_asset_count = Asset.objects.filter(organization=organization, is_deleted=False).count()
    initial_purchase_request_count = PurchaseRequest.objects.filter(
        organization=organization,
        is_deleted=False,
    ).count()

    call_command(
        "create_demo_data",
        "--organization",
        str(organization.id),
        "--count",
        "1",
        "--skip-existing",
        "--top-up-existing",
        stdout=top_up_stdout,
    )

    top_up_output = top_up_stdout.getvalue()

    assert "Demo data creation completed!" in top_up_output
    assert "Topped up inventory scans by" in top_up_output
    assert initial_scan_count == 1
    assert initial_asset_count == 1
    assert initial_purchase_request_count == 1
    assert InventoryScan.objects.filter(task__organization=organization, is_deleted=False).count() == 20
    assert Asset.objects.filter(organization=organization, is_deleted=False).count() == 1
    assert PurchaseRequest.objects.filter(organization=organization, is_deleted=False).count() == 1


def test_create_demo_data_command_skip_existing_smoke_reuses_data_without_top_up(organization):
    initial_stdout = StringIO()
    skip_existing_stdout = StringIO()

    call_command(
        "create_demo_data",
        "--organization",
        str(organization.id),
        "--count",
        "1",
        stdout=initial_stdout,
    )

    initial_scan_count = InventoryScan.objects.filter(
        task__organization=organization,
        is_deleted=False,
    ).count()
    initial_asset_count = Asset.objects.filter(organization=organization, is_deleted=False).count()
    initial_purchase_request_count = PurchaseRequest.objects.filter(
        organization=organization,
        is_deleted=False,
    ).count()

    call_command(
        "create_demo_data",
        "--organization",
        str(organization.id),
        "--count",
        "1",
        "--skip-existing",
        stdout=skip_existing_stdout,
    )

    skip_existing_output = skip_existing_stdout.getvalue()

    assert "Demo data creation completed!" in skip_existing_output
    assert "Using existing 1 inventory scans" in skip_existing_output
    assert "Topped up inventory scans by" not in skip_existing_output
    assert InventoryScan.objects.filter(task__organization=organization, is_deleted=False).count() == initial_scan_count == 1
    assert Asset.objects.filter(organization=organization, is_deleted=False).count() == initial_asset_count == 1
    assert PurchaseRequest.objects.filter(organization=organization, is_deleted=False).count() == initial_purchase_request_count == 1
