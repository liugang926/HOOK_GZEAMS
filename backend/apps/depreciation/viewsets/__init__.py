from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import date, timedelta
from decimal import Decimal
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.permissions.base import IsOrganizationMember
from apps.depreciation.models import DepreciationConfig, DepreciationRecord, DepreciationRun
from apps.depreciation.serializers import (
    DepreciationConfigSerializer, DepreciationConfigListSerializer, DepreciationConfigDetailSerializer,
    DepreciationRecordSerializer, DepreciationRecordListSerializer, DepreciationRecordDetailSerializer,
    DepreciationRunSerializer, DepreciationRunListSerializer, DepreciationRunDetailSerializer
)
from apps.depreciation.filters import DepreciationConfigFilter, DepreciationRecordFilter, DepreciationRunFilter


# Base permission classes
BASE_PERMISSION_CLASSES = [permissions.IsAuthenticated, IsOrganizationMember]


class DepreciationConfigViewSet(BaseModelViewSetWithBatch):
    """
    Depreciation Configuration ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    """

    queryset = DepreciationConfig.objects.select_related(
        'organization', 'category', 'category__parent'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = DepreciationConfigFilter
    search_fields = ['category__name', 'category__code', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'category__name']
    ordering = ['category__name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DepreciationConfigListSerializer
        if self.action == 'retrieve':
            return DepreciationConfigDetailSerializer
        return DepreciationConfigSerializer


class DepreciationRecordViewSet(BaseModelViewSetWithBatch):
    """
    Depreciation Record ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - Custom action: post (post to accounting)
    - Custom action: batch_post (batch post to accounting)
    """

    queryset = DepreciationRecord.objects.select_related(
        'organization', 'asset', 'asset__asset_category', 'created_by'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = DepreciationRecordFilter
    search_fields = ['asset__asset_code', 'asset__asset_name', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'period', 'depreciation_amount']
    ordering = ['-period', '-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DepreciationRecordListSerializer
        if self.action == 'retrieve':
            return DepreciationRecordDetailSerializer
        return DepreciationRecordSerializer

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        """
        Post a single depreciation record to accounting.

        POST /api/depreciation/records/{id}/post/

        Request body:
        {
            "notes": "Optional posting notes"
        }
        """
        record = self.get_object()

        if record.status == 'posted':
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Record is already posted'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update record status
        record.status = 'posted'
        record.post_date = date.today()
        record.notes = request.data.get('notes', record.notes)
        record.save()

        serializer = self.get_serializer(record)
        return Response({
            'success': True,
            'message': 'Depreciation record posted successfully',
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def batch_post(self, request):
        """
        Batch post multiple depreciation records to accounting.

        POST /api/depreciation/records/batch_post/

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"],
            "notes": "Optional posting notes"
        }
        """
        ids = request.data.get('ids', [])
        notes = request.data.get('notes', '')

        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids parameter cannot be empty'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        succeeded = 0
        failed = 0

        for record_id in ids:
            try:
                record = self.get_queryset().get(id=record_id)

                if record.status == 'posted':
                    results.append({
                        'id': str(record_id),
                        'success': False,
                        'error': 'Record is already posted'
                    })
                    failed += 1
                    continue

                record.status = 'posted'
                record.post_date = date.today()
                if notes:
                    record.notes = notes
                record.save()

                results.append({'id': str(record_id), 'success': True})
                succeeded += 1

            except Exception as e:
                results.append({'id': str(record_id), 'success': False, 'error': str(e)})
                failed += 1

        response_data = {
            'success': True,
            'message': 'Batch post completed',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        }

        http_status = status.HTTP_200_OK if failed == 0 else status.HTTP_207_MULTI_STATUS
        return Response(response_data, status=http_status)

    @action(detail=False, methods=['get'])
    def report(self, request):
        """
        Generate depreciation report.

        GET /api/depreciation/records/report/

        Query parameters:
        - period: Filter by period (YYYY-MM)
        - category: Filter by category code

        Returns summary statistics and grouped data.
        """
        period = request.query_params.get('period')
        category_code = request.query_params.get('category')

        # Build base queryset
        queryset = self.get_queryset()

        if period:
            queryset = queryset.filter(period=period)

        if category_code:
            queryset = queryset.filter(asset__asset_category__code=category_code)

        # Calculate summary statistics
        summary = queryset.aggregate(
            total_records=Count('id'),
            total_depreciation_amount=Sum('depreciation_amount'),
            total_accumulated_amount=Sum('accumulated_amount'),
            total_net_value=Sum('net_value'),
            posted_count=Count('id', filter=Q(status='posted')),
            calculated_count=Count('id', filter=Q(status='calculated')),
            rejected_count=Count('id', filter=Q(status='rejected'))
        )

        # Group by category
        category_breakdown = queryset.values('asset__asset_category__name').annotate(
            category_code=F('asset__asset_category__code'),
            record_count=Count('id'),
            total_depreciation=Sum('depreciation_amount'),
            total_accumulated=Sum('accumulated_amount'),
            total_net=Sum('net_value')
        ).order_by('-total_depreciation')

        return Response({
            'success': True,
            'data': {
                'summary': summary,
                'category_breakdown': list(category_breakdown)
            }
        })


class DepreciationRunViewSet(BaseModelViewSetWithBatch):
    """
    Depreciation Run ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - Custom action: calculate (calculate depreciation for assets)
    - Custom action: report (generate depreciation run report)
    """

    queryset = DepreciationRun.objects.select_related(
        'organization', 'created_by'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = DepreciationRunFilter
    search_fields = ['period', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'run_date', 'period']
    ordering = ['-run_date', '-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DepreciationRunListSerializer
        if self.action == 'retrieve':
            return DepreciationRunDetailSerializer
        return DepreciationRunSerializer

    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calculate depreciation for assets in a given period.

        POST /api/depreciation/runs/calculate/

        Request body:
        {
            "period": "2025-01",  // Required: YYYY-MM format
            "category": "2001",   // Optional: category code to filter
            "notes": "Optional notes"
        }

        Creates a DepreciationRun and generates DepreciationRecord entries
        for all active assets with valid depreciation configurations.
        """
        from apps.assets.models import Asset

        period = request.data.get('period')
        category_code = request.data.get('category')
        notes = request.data.get('notes', '')

        # Validate period format (YYYY-MM)
        if not period or len(period) != 7 or period[4] != '-':
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid period format. Use YYYY-MM'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if run already exists for this period
        existing_run = DepreciationRun.objects.filter(
            period=period,
            organization_id=request.organization_id
        ).first()

        if existing_run:
            return Response({
                'success': False,
                'error': {
                    'code': 'CONFLICT',
                    'message': f'Depreciation run already exists for period {period}'
                }
            }, status=status.HTTP_409_CONFLICT)

        # Create depreciation run
        run = DepreciationRun.objects.create(
            period=period,
            run_date=date.today(),
            status='in_progress',
            organization_id=request.organization_id,
            created_by=request.user,
            notes=notes
        )

        # Get assets to depreciate
        assets = Asset.objects.filter(
            organization_id=request.organization_id,
            is_deleted=False
        )

        if category_code:
            assets = assets.filter(asset_category__code=category_code)

        # Only process assets with original_cost and active status
        assets = assets.exclude(original_cost__isnull=True).exclude(original_cost=0)

        records_created = 0
        total_depreciation = Decimal('0.00')
        failed_assets = []

        for asset in assets:
            try:
                # Get depreciation config for asset's category
                config = DepreciationConfig.objects.filter(
                    category=asset.asset_category,
                    organization_id=request.organization_id,
                    is_active=True
                ).first()

                if not config:
                    failed_assets.append({
                        'asset_code': asset.asset_code,
                        'reason': 'No depreciation configuration found'
                    })
                    continue

                # Check if record already exists for this period
                existing_record = DepreciationRecord.objects.filter(
                    asset=asset,
                    period=period,
                    organization_id=request.organization_id
                ).first()

                if existing_record:
                    continue  # Skip if already calculated

                # Get accumulated depreciation from previous periods
                previous_accumulated = DepreciationRecord.objects.filter(
                    asset=asset,
                    period__lt=period,
                    status='posted',
                    organization_id=request.organization_id
                ).aggregate(
                    total=Sum('depreciation_amount')
                )['total'] or Decimal('0.00')

                # Calculate monthly depreciation using straight line method
                monthly_rate = config.get_monthly_rate()
                depreciation_amount = asset.original_cost * Decimal(str(monthly_rate))

                # Calculate accumulated and net value
                accumulated_amount = previous_accumulated + depreciation_amount
                net_value = asset.original_cost - accumulated_amount

                # Ensure net value doesn't go below salvage value
                salvage_value = asset.original_cost * (config.salvage_value_rate / Decimal('100'))
                if net_value < salvage_value:
                    net_value = salvage_value
                    depreciation_amount = salvage_value - (asset.original_cost - previous_accumulated)
                    accumulated_amount = previous_accumulated + depreciation_amount

                # Create depreciation record
                DepreciationRecord.objects.create(
                    asset=asset,
                    period=period,
                    depreciation_amount=depreciation_amount,
                    accumulated_amount=accumulated_amount,
                    net_value=net_value,
                    status='calculated',
                    organization_id=request.organization_id,
                    created_by=request.user
                )

                records_created += 1
                total_depreciation += depreciation_amount

            except Exception as e:
                failed_assets.append({
                    'asset_code': asset.asset_code,
                    'reason': str(e)
                })

        # Update run status
        run.total_assets = records_created
        run.total_amount = total_depreciation

        if failed_assets:
            run.status = 'completed'
            run.notes = f"{notes}\n\nFailed assets ({len(failed_assets)}):\n" + \
                        "\n".join([f"{a['asset_code']}: {a['reason']}" for a in failed_assets])
        else:
            run.status = 'completed'

        run.save()

        serializer = DepreciationRunDetailSerializer(run)
        return Response({
            'success': True,
            'message': f'Depreciation calculation completed. {records_created} records created.',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def report(self, request):
        """
        Generate depreciation run report.

        GET /api/depreciation/runs/report/

        Query parameters:
        - period_from: Filter from period (YYYY-MM)
        - period_to: Filter to period (YYYY-MM)
        - status: Filter by status

        Returns summary statistics.
        """
        period_from = request.query_params.get('period_from')
        period_to = request.query_params.get('period_to')
        status_filter = request.query_params.get('status')

        # Build base queryset
        queryset = self.get_queryset()

        if period_from:
            queryset = queryset.filter(period__gte=period_from)

        if period_to:
            queryset = queryset.filter(period__lte=period_to)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Calculate summary statistics
        summary = queryset.aggregate(
            total_runs=Count('id'),
            total_assets_processed=Sum('total_assets'),
            total_depreciation_amount=Sum('total_amount'),
            completed_runs=Count('id', filter=Q(status='completed')),
            failed_runs=Count('id', filter=Q(status='failed')),
            in_progress_runs=Count('id', filter=Q(status='in_progress'))
        )

        # Get recent runs
        recent_runs = queryset.order_by('-run_date')[:10]
        recent_runs_data = DepreciationRunListSerializer(recent_runs, many=True).data

        return Response({
            'success': True,
            'data': {
                'summary': summary,
                'recent_runs': recent_runs_data
            }
        })


# Import Count and F for aggregations
from django.db.models import Count, F


__all__ = [
    'DepreciationConfigViewSet',
    'DepreciationRecordViewSet',
    'DepreciationRunViewSet',
]
