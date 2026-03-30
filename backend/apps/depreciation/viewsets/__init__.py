from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Q, Count, F
from datetime import date
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

    @action(detail=False, methods=['get', 'put'], url_path='categories/(?P<category_id>[^/.]+)')
    def categories(self, request, category_id=None):
        """
        Get/update depreciation config by category id.

        Alias endpoint for frontend compatibility:
        /api/depreciation/config/categories/{category_id}/
        """
        from apps.assets.models import AssetCategory

        if request.method.lower() == 'get':
            config = DepreciationConfig.objects.filter(
                category_id=category_id,
                organization_id=request.organization_id,
                is_deleted=False
            ).first()

            if config:
                return Response({
                    'success': True,
                    'data': {
                        'id': str(config.id),
                        'category_id': str(config.category_id),
                        'depreciation_method': config.depreciation_method,
                        'useful_life': config.useful_life,
                        'residual_rate': config.salvage_value_rate,
                        'is_active': config.is_active,
                        'notes': config.notes
                    }
                })

            try:
                category = AssetCategory.objects.get(
                    id=category_id,
                    organization_id=request.organization_id,
                    is_deleted=False
                )
            except AssetCategory.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': 'Category not found'
                    }
                }, status=status.HTTP_404_NOT_FOUND)

            return Response({
                'success': True,
                'data': {
                    'id': None,
                    'category_id': str(category.id),
                    'depreciation_method': category.depreciation_method or 'straight_line',
                    'useful_life': category.default_useful_life or 60,
                    'residual_rate': category.residual_rate or Decimal('5.00'),
                    'is_active': True,
                    'notes': ''
                }
            })

        payload = request.data
        depreciation_method = payload.get('depreciation_method') or payload.get('depreciationMethod') or 'straight_line'
        useful_life = payload.get('useful_life', payload.get('usefulLife', 60))
        residual_rate = payload.get('salvage_value_rate', payload.get('residual_rate', payload.get('residualRate', 5)))
        is_active = payload.get('is_active', True)
        notes = payload.get('notes', '')

        try:
            category = AssetCategory.objects.get(
                id=category_id,
                organization_id=request.organization_id,
                is_deleted=False
            )
        except AssetCategory.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Category not found'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        config, created = DepreciationConfig.objects.get_or_create(
            category=category,
            organization_id=request.organization_id,
            defaults={
                'created_by': request.user,
                'depreciation_method': depreciation_method,
                'useful_life': int(useful_life),
                'salvage_value_rate': Decimal(str(residual_rate)),
                'is_active': bool(is_active),
                'notes': notes,
            }
        )
        if not created:
            config.depreciation_method = depreciation_method
            config.useful_life = int(useful_life)
            config.salvage_value_rate = Decimal(str(residual_rate))
            config.is_active = bool(is_active)
            config.notes = notes
            config.updated_by = request.user
            config.save()

        # Keep category defaults aligned to the latest category-level depreciation config.
        category.depreciation_method = depreciation_method
        category.default_useful_life = int(useful_life)
        category.residual_rate = Decimal(str(residual_rate))
        category.save(update_fields=['depreciation_method', 'default_useful_life', 'residual_rate', 'updated_at'])

        serializer = DepreciationConfigDetailSerializer(config)
        return Response({
            'success': True,
            'message': 'Category depreciation config updated',
            'data': serializer.data
        })

    @action(detail=False, methods=['get', 'put'], url_path='global')
    def global_config(self, request):
        """
        Get/update global depreciation defaults.

        Alias endpoint for frontend compatibility:
        /api/depreciation/config/global/
        """
        from apps.assets.models import AssetCategory

        configs = DepreciationConfig.objects.filter(
            organization_id=request.organization_id,
            is_deleted=False
        )

        if request.method.lower() == 'get':
            latest_config = configs.order_by('-updated_at').first()
            if latest_config:
                data = {
                    'default_method': latest_config.depreciation_method,
                    'default_useful_life': latest_config.useful_life,
                    'default_residual_rate': latest_config.salvage_value_rate,
                    'total_configs': configs.count()
                }
            else:
                category_defaults = AssetCategory.objects.filter(
                    organization_id=request.organization_id,
                    is_deleted=False
                ).order_by('-updated_at').first()
                data = {
                    'default_method': getattr(category_defaults, 'depreciation_method', 'straight_line'),
                    'default_useful_life': getattr(category_defaults, 'default_useful_life', 60),
                    'default_residual_rate': getattr(category_defaults, 'residual_rate', Decimal('5.00')),
                    'total_configs': 0
                }
            return Response({'success': True, 'data': data})

        payload = request.data
        default_method = payload.get('default_method') or payload.get('defaultMethod') or 'straight_line'
        default_useful_life = int(payload.get('default_useful_life', payload.get('defaultUsefulLife', 60)))
        default_residual_rate = Decimal(str(payload.get('default_residual_rate', payload.get('defaultResidualRate', 5))))

        # Global update semantics: synchronize all existing active configs and category defaults.
        if configs.exists():
            configs.update(
                depreciation_method=default_method,
                useful_life=default_useful_life,
                salvage_value_rate=default_residual_rate,
                updated_by=request.user
            )

        AssetCategory.objects.filter(
            organization_id=request.organization_id,
            is_deleted=False
        ).update(
            depreciation_method=default_method,
            default_useful_life=default_useful_life,
            residual_rate=default_residual_rate
        )

        return Response({
            'success': True,
            'message': 'Global depreciation config updated',
            'data': {
                'default_method': default_method,
                'default_useful_life': default_useful_life,
                'default_residual_rate': default_residual_rate,
                'total_configs': configs.count()
            }
        })


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
    def submit(self, request, pk=None):
        """
        Submit a depreciation record for approval.

        Compatibility endpoint:
        POST /api/depreciation/records/{id}/submit/
        """
        record = self.get_object()
        if record.status == 'posted':
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Posted record cannot be submitted again'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Current model has no "submitted" status; keep status unchanged and record intent in notes.
        submit_note = request.data.get('comment') or request.data.get('notes') or 'Submitted for approval'
        record.notes = f"{record.notes}\n{submit_note}".strip()
        record.save(update_fields=['notes', 'updated_at'])

        serializer = self.get_serializer(record)
        return Response({
            'success': True,
            'message': 'Depreciation record submitted successfully',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve or reject a depreciation record.

        Compatibility endpoint:
        POST /api/depreciation/records/{id}/approve/
        """
        record = self.get_object()
        action_value = request.data.get('action') or request.data.get('decision') or 'approve'
        action_value = action_value.lower()
        comment = request.data.get('comment') or request.data.get('notes') or ''

        if action_value not in ['approve', 'approved', 'reject', 'rejected']:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'action must be approve or reject'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if action_value in ['approve', 'approved']:
            record.status = 'posted'
            record.post_date = date.today()
            msg = 'Depreciation record approved and posted'
        else:
            record.status = 'rejected'
            msg = 'Depreciation record rejected'

        if comment:
            record.notes = f"{record.notes}\n{comment}".strip()
        record.save()

        serializer = self.get_serializer(record)
        return Response({
            'success': True,
            'message': msg,
            'data': serializer.data
        })

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
            'success': failed == 0,
            'message': 'Batch post completed' if failed == 0 else 'Batch post completed with partial failures',
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
        category_ids = request.query_params.getlist('category_ids') or request.query_params.getlist('categoryIds')
        if not category_ids:
            raw_category_ids = request.query_params.get('category_ids') or request.query_params.get('categoryIds')
            if raw_category_ids:
                category_ids = [item for item in str(raw_category_ids).split(',') if item]

        # Build base queryset
        queryset = self.filter_queryset(self.get_queryset())

        if period:
            queryset = queryset.filter(period=period)

        if category_ids:
            queryset = queryset.filter(asset__asset_category_id__in=category_ids)
        elif category_code:
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
        category_breakdown = queryset.values(
            category_name=F('asset__asset_category__name'),
            category_code=F('asset__asset_category__code'),
        ).annotate(
            record_count=Count('id'),
            total_depreciation=Sum('depreciation_amount'),
            total_accumulated=Sum('accumulated_amount'),
            total_net=Sum('net_value')
        ).order_by('-total_depreciation')

        by_asset = queryset.values(
            asset_id=F('asset_id'),
            asset_code=F('asset__asset_code'),
            asset_name=F('asset__asset_name'),
            category_name=F('asset__asset_category__name'),
            purchase_price=F('asset__purchase_price'),
        ).annotate(
            current_depreciation=Sum('depreciation_amount'),
            accumulated_depreciation=Sum('accumulated_amount'),
            net_value=Sum('net_value'),
        ).order_by('asset_code')

        return Response({
            'success': True,
            'data': {
                'summary': summary,
                'category_breakdown': list(category_breakdown),
                'by_asset': list(by_asset),
            }
        })

    def export_report(self, request):
        """
        Export depreciation report file.

        Compatibility endpoint:
        GET /api/depreciation/report/export/
        """
        from io import BytesIO, StringIO
        from django.http import HttpResponse
        import csv

        period = request.query_params.get('period')
        if not period:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'period query parameter is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        requested_format = (
            request.query_params.get('file_format')
            or request.query_params.get('fileFormat')
            or 'xlsx'
        ).lower()
        category_ids = request.query_params.getlist('category_ids') or request.query_params.getlist('categoryIds')
        if not category_ids:
            raw = request.query_params.get('category_ids') or request.query_params.get('categoryIds')
            if raw:
                category_ids = [item for item in str(raw).split(',') if item]

        queryset = self.get_queryset().filter(period=period)
        if category_ids:
            queryset = queryset.filter(asset__asset_category_id__in=category_ids)

        if requested_format == 'pdf':
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'pdf export is not supported yet'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        rows = queryset.values_list(
            'asset__asset_code',
            'asset__asset_name',
            'period',
            'depreciation_amount',
            'accumulated_amount',
            'net_value',
            'status'
        )

        if requested_format == 'xlsx':
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = 'Depreciation Report'
                headers = ['Asset Code', 'Asset Name', 'Period', 'Depreciation Amount', 'Accumulated Amount', 'Net Value', 'Status']
                ws.append(headers)
                for row in rows:
                    ws.append(list(row))
                buffer = BytesIO()
                wb.save(buffer)
                buffer.seek(0)
                response = HttpResponse(
                    buffer.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="depreciation_report_{period}.xlsx"'
                return response
            except ImportError:
                # Fallback to CSV export when openpyxl is unavailable in runtime image.
                requested_format = 'csv'

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['asset_code', 'asset_name', 'period', 'depreciation_amount', 'accumulated_amount', 'net_value', 'status'])
        for row in rows:
            writer.writerow(row)

        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="depreciation_report_{period}.csv"'
        return response

    @action(detail=False, methods=['get'], url_path='report/export')
    def report_export(self, request):
        """
        Unified object router alias.

        GET /api/system/objects/DepreciationRecord/report/export/
        """
        return self.export_report(request)

    def asset_detail(self, request, asset_id=None):
        """
        Get depreciation detail by asset.

        Compatibility endpoint:
        GET /api/depreciation/assets/{id}/detail/
        """
        from apps.assets.models import Asset

        try:
            asset = Asset.objects.get(
                id=asset_id,
                organization_id=request.organization_id,
                is_deleted=False
            )
        except Asset.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Asset not found'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        records = DepreciationRecord.objects.filter(
            organization_id=request.organization_id,
            asset_id=asset.id,
            is_deleted=False
        ).order_by('period')

        record_serializer = DepreciationRecordListSerializer(records, many=True)
        accumulated = records.aggregate(total=Sum('depreciation_amount'))['total'] or Decimal('0.00')
        used_months = records.count()
        useful_life = asset.useful_life or 0
        progress = int(min(100, round((used_months / useful_life) * 100))) if useful_life > 0 else 0
        last_record = records.last()
        net_value = (last_record.net_value if last_record else asset.current_value) or Decimal('0.00')

        return Response({
            'success': True,
            'data': {
                'asset_info': {
                    'id': str(asset.id),
                    'asset_code': asset.asset_code,
                    'asset_name': asset.asset_name,
                    'purchase_price': asset.purchase_price,
                    'current_value': asset.current_value,
                    'accumulated_depreciation': asset.accumulated_depreciation,
                    'useful_life': asset.useful_life,
                    'residual_rate': asset.residual_rate
                },
                'stat': {
                    'used_months': used_months,
                    'accumulated': accumulated,
                    'net_value': net_value,
                    'progress': progress
                },
                'records': record_serializer.data
            }
        })

    @action(detail=False, methods=['get'], url_path='assets/(?P<asset_id>[^/.]+)/detail')
    def assets_detail(self, request, asset_id=None):
        """
        Unified object router alias.

        GET /api/system/objects/DepreciationRecord/assets/{asset_id}/detail/
        """
        return self.asset_detail(request, asset_id=asset_id)


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
        category_ids = request.data.get('category_ids') or request.data.get('categoryIds') or []
        asset_ids = request.data.get('asset_ids') or request.data.get('assetIds') or []
        notes = request.data.get('notes', '')

        if isinstance(category_ids, str):
            category_ids = [item for item in category_ids.split(',') if item]

        if isinstance(asset_ids, str):
            asset_ids = [item for item in asset_ids.split(',') if item]

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

        if category_ids:
            assets = assets.filter(asset_category_id__in=category_ids)
        elif category_code:
            assets = assets.filter(asset_category__code=category_code)

        if asset_ids:
            assets = assets.filter(id__in=asset_ids)

        # Only process assets with purchase price and active status
        assets = assets.exclude(purchase_price__isnull=True).exclude(purchase_price=0)

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
                depreciation_amount = asset.purchase_price * Decimal(str(monthly_rate))

                # Calculate accumulated and net value
                accumulated_amount = previous_accumulated + depreciation_amount
                net_value = asset.purchase_price - accumulated_amount

                # Ensure net value doesn't go below salvage value
                salvage_value = asset.purchase_price * (config.salvage_value_rate / Decimal('100'))
                if net_value < salvage_value:
                    net_value = salvage_value
                    depreciation_amount = salvage_value - (asset.purchase_price - previous_accumulated)
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


__all__ = [
    'DepreciationConfigViewSet',
    'DepreciationRecordViewSet',
    'DepreciationRunViewSet',
]
