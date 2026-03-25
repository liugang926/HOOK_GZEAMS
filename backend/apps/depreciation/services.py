"""
Depreciation management service layer.

Provides business logic for depreciation configuration, monthly
depreciation runs, and individual asset depreciation calculations.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.common.services.base_crud import BaseCRUDService
from .models import DepreciationConfig, DepreciationRecord, DepreciationRun


class DepreciationConfigService(BaseCRUDService):
    """Service layer for depreciation configuration management."""

    def __init__(self):
        super().__init__(DepreciationConfig)

    def get_config_for_category(self, category_id, organization_id=None, user=None):
        """Get valid depreciation config for a given asset category."""
        configs = self.query(
            filters={'category_id': category_id, 'is_active': True},
            organization_id=organization_id,
            user=user,
        )
        return configs.first()


class DepreciationRecordService(BaseCRUDService):
    """Service layer for depreciation record queries."""

    def __init__(self):
        super().__init__(DepreciationRecord)

    def get_asset_history(self, asset_id, organization_id=None, user=None):
        """Get full depreciation history for an asset ordered by period."""
        return self.query(
            filters={'asset_id': asset_id},
            order_by='-period',
            organization_id=organization_id,
            user=user,
        )

    def get_period_summary(self, period, organization_id=None, user=None):
        """Get aggregated depreciation summary for a period."""
        records = self.query(
            filters={'period': period, 'status': 'calculated'},
            organization_id=organization_id,
            user=user,
        )
        agg = records.aggregate(
            total_depreciation=Sum('depreciation_amount'),
            total_net_value=Sum('net_value'),
        )
        return {
            'period': period,
            'record_count': records.count(),
            'total_depreciation': agg['total_depreciation'] or Decimal('0'),
            'total_net_value': agg['total_net_value'] or Decimal('0'),
        }


class DepreciationRunService(BaseCRUDService):
    """Service layer for batch depreciation run execution."""

    def __init__(self):
        super().__init__(DepreciationRun)

    @transaction.atomic
    def execute_run(self, run_id, organization_id=None, user=None):
        """Execute a pending depreciation run.

        Iterates all depreciable assets in the organization, calculates
        depreciation for the run's period, and creates DepreciationRecord
        entries. Updates run statistics on completion.
        """
        dep_run = self.get(run_id, organization_id=organization_id, user=user)
        if dep_run.status != 'pending':
            raise ValidationError({
                'status': ['Only pending runs can be executed.']
            })

        dep_run.status = 'in_progress'
        dep_run.save(update_fields=['status', 'updated_at'])

        try:
            records_created = self._calculate_period_depreciation(dep_run)
            dep_run.status = 'completed'
            dep_run.total_assets = records_created
            agg = DepreciationRecord.objects.filter(
                organization=dep_run.organization,
                period=dep_run.period,
                status='calculated',
                is_deleted=False,
            ).aggregate(total=Sum('depreciation_amount'))
            dep_run.total_amount = agg['total'] or Decimal('0')
            dep_run.save(update_fields=[
                'status', 'total_assets', 'total_amount', 'updated_at'
            ])
        except Exception as e:
            dep_run.status = 'failed'
            dep_run.error_message = str(e)
            dep_run.save(update_fields=['status', 'error_message', 'updated_at'])
            raise

        return dep_run

    def _calculate_period_depreciation(self, dep_run):
        """Calculate depreciation for all qualifying assets in a period.

        Returns the number of records created.
        """
        from apps.assets.models import Asset

        assets = Asset.objects.filter(
            organization=dep_run.organization,
            is_deleted=False,
            status__in=['in_use', 'idle'],
        )

        records_created = 0
        for asset in assets:
            # Skip if a record already exists for this asset + period
            exists = DepreciationRecord.objects.filter(
                organization=dep_run.organization,
                asset=asset,
                period=dep_run.period,
                is_deleted=False,
            ).exists()
            if exists:
                continue

            record = self._calculate_single_asset(asset, dep_run)
            if record:
                records_created += 1

        return records_created

    def _calculate_single_asset(self, asset, dep_run):
        """Calculate depreciation for a single asset.

        Uses straight-line depreciation by default. Looks up
        DepreciationConfig for the asset's category if available.
        """
        config_service = DepreciationConfigService()
        config = config_service.get_config_for_category(
            getattr(asset, 'category_id', None),
            organization_id=dep_run.organization_id,
        )

        # Determine depreciation parameters
        original_value = getattr(asset, 'original_value', None) or getattr(
            asset, 'purchase_price', Decimal('0')
        )
        original_value = Decimal(str(original_value or 0))
        if original_value <= 0:
            return None

        if config:
            salvage_rate = config.salvage_value_rate / Decimal('100')
            useful_life = config.useful_life  # months
        else:
            salvage_rate = Decimal('0.05')
            useful_life = 60  # Default 5 years

        salvage_value = original_value * salvage_rate
        depreciable_amount = original_value - salvage_value

        # Monthly depreciation (straight line)
        monthly_depreciation = depreciable_amount / Decimal(str(useful_life))

        # Get accumulated depreciation so far
        accumulated = DepreciationRecord.objects.filter(
            organization=dep_run.organization,
            asset=asset,
            status='calculated',
            is_deleted=False,
        ).aggregate(total=Sum('depreciation_amount'))['total'] or Decimal('0')

        # Don't depreciate past the depreciable amount
        remaining = depreciable_amount - accumulated
        if remaining <= 0:
            return None

        period_amount = min(monthly_depreciation, remaining)
        new_accumulated = accumulated + period_amount
        net_value = original_value - new_accumulated

        return DepreciationRecord.objects.create(
            organization=dep_run.organization,
            asset=asset,
            period=dep_run.period,
            depreciation_amount=period_amount,
            accumulated_amount=new_accumulated,
            net_value=net_value,
            status='calculated',
            created_by=dep_run.created_by,
        )

    def get_run_summary(self, organization_id=None, user=None):
        """Get summary of recent depreciation runs."""
        return self.query(
            order_by='-run_date',
            organization_id=organization_id,
            user=user,
        )[:10]
