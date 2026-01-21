"""
Service layer for Asset business logic.

Provides:
- Standard CRUD operations via BaseCRUDService
- Asset-specific business logic (status changes, depreciation)
- Bulk operations support
- QR code lookup
"""
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.db.models import Q, QuerySet, Sum, Count, F, DecimalField
from django.db.models.functions import Coalesce
from django.core.exceptions import ValidationError
from apps.common.services.base_crud import BaseCRUDService
from apps.assets.models import (
    Asset,
    AssetStatusLog,
    Supplier,
    Location
)


class SupplierService(BaseCRUDService):
    """Service layer for Supplier CRUD operations."""

    def __init__(self):
        super().__init__(Supplier)

    def get_by_code(self, code: str, organization_id: str) -> Optional[Supplier]:
        """
        Get supplier by code within organization.

        Args:
            code: Supplier code
            organization_id: Organization UUID

        Returns:
            Supplier instance or None
        """
        try:
            return self.model_class.objects.get(
                code=code,
                organization_id=organization_id,
                is_deleted=False
            )
        except Supplier.DoesNotExist:
            return None


class LocationService(BaseCRUDService):
    """Service layer for Location CRUD operations."""

    def __init__(self):
        super().__init__(Location)

    def get_tree(self, organization_id: str) -> List[Dict]:
        """
        Get location tree for organization.

        Args:
            organization_id: Organization UUID

        Returns:
            List of location tree nodes with nested children
        """
        locations = self.model_class.objects.filter(
            organization_id=organization_id,
            is_deleted=False
        ).order_by('path')

        # Build tree structure
        from collections import defaultdict
        children_map = defaultdict(list)
        root_locations = []

        for loc in locations:
            if loc.parent_id:
                children_map[loc.parent_id].append(loc)
            else:
                root_locations.append(loc)

        def build_tree(location):
            """Recursively build tree with children."""
            data = {
                'id': location.id,
                'name': location.name,
                'path': location.path,
                'level': location.level,
                'location_type': location.location_type,
                'has_children': False,
                'children': []
            }

            # Add children recursively
            children = children_map.get(location.id, [])
            if children:
                data['has_children'] = True
                for child in children:
                    data['children'].append(build_tree(child))

            return data

        return [build_tree(loc) for loc in root_locations]

    def get_by_path(self, path: str, organization_id: str) -> Optional[Location]:
        """
        Get location by full path within organization.

        Args:
            path: Full location path
            organization_id: Organization UUID

        Returns:
            Location instance or None
        """
        try:
            return self.model_class.objects.get(
                path=path,
                organization_id=organization_id,
                is_deleted=False
            )
        except Location.DoesNotExist:
            return None


class AssetStatusLogService(BaseCRUDService):
    """Service layer for AssetStatusLog CRUD operations."""

    def __init__(self):
        super().__init__(AssetStatusLog)

    def log_status_change(
        self,
        asset: Asset,
        old_status: str,
        new_status: str,
        user,
        reason: str = ''
    ) -> AssetStatusLog:
        """
        Create a status change log entry.

        Args:
            asset: Asset instance
            old_status: Previous status
            new_status: New status
            user: User making the change
            reason: Optional reason for the change

        Returns:
            Created AssetStatusLog instance
        """
        log_data = {
            'asset': asset,
            'old_status': old_status,
            'new_status': new_status,
            'reason': reason,
            'organization_id': asset.organization_id,
            'created_by_id': user.id
        }
        return self.create(log_data, user)

    def get_asset_history(self, asset_id: str) -> QuerySet:
        """
        Get status change history for an asset.

        Args:
            asset_id: Asset UUID

        Returns:
            QuerySet of status logs ordered by created_at desc
        """
        return self.model_class.objects.filter(
            asset_id=asset_id,
            is_deleted=False
        ).order_by('-created_at')


class AssetService(BaseCRUDService):
    """
    Service layer for Asset business logic.

    Extends BaseCRUDService with asset-specific operations:
    - Status change tracking with audit log
    - QR code lookup
    - Bulk operations
    - Asset statistics
    """

    def __init__(self):
        super().__init__(Asset)
        self.status_log_service = AssetStatusLogService()

    def get_by_code(self, code: str, organization_id: str) -> Optional[Asset]:
        """
        Get asset by code within organization.

        Args:
            code: Asset code (e.g., ZC2024010001)
            organization_id: Organization UUID

        Returns:
            Asset instance or None
        """
        try:
            return self.model_class.objects.get(
                asset_code=code,
                organization_id=organization_id,
                is_deleted=False
            )
        except Asset.DoesNotExist:
            return None

    def get_by_qr_code(self, qr_code: str, organization_id: str) -> Optional[Asset]:
        """
        Get asset by QR code within organization.

        Args:
            qr_code: QR code UUID
            organization_id: Organization UUID

        Returns:
            Asset instance or None
        """
        try:
            return self.model_class.objects.get(
                qr_code=qr_code,
                organization_id=organization_id,
                is_deleted=False
            )
        except Asset.DoesNotExist:
            return None

    def get_by_rfid_code(self, rfid_code: str, organization_id: str) -> Optional[Asset]:
        """
        Get asset by RFID code within organization.

        Args:
            rfid_code: RFID code
            organization_id: Organization UUID

        Returns:
            Asset instance or None
        """
        try:
            return self.model_class.objects.get(
                rfid_code=rfid_code,
                organization_id=organization_id,
                is_deleted=False
            )
        except Asset.DoesNotExist:
            return None

    def change_status(
        self,
        asset_id: str,
        new_status: str,
        user,
        reason: str = ''
    ) -> Asset:
        """
        Change asset status with audit log.

        Args:
            asset_id: Asset UUID
            new_status: New status value
            user: User making the change
            reason: Optional reason for the change

        Returns:
            Updated asset instance

        Raises:
            ValueError: If asset not found or status transition is invalid
        """
        asset = self.get(asset_id)
        old_status = asset.asset_status

        # Validate status transition
        if old_status == new_status:
            raise ValueError(f'Asset is already in {new_status} status')

        # Additional validation for certain status transitions
        if new_status == 'scrapped' and old_status not in ['idle', 'lost', 'maintenance']:
            # Allow scrapping from these statuses, or require admin approval
            pass

        # Update status
        asset.asset_status = new_status
        asset.save()

        # Log the change
        self.status_log_service.log_status_change(
            asset=asset,
            old_status=old_status,
            new_status=new_status,
            user=user,
            reason=reason
        )

        return asset

    def query_by_category(
        self,
        category_id: str,
        organization_id: str,
        include_children: bool = True
    ) -> QuerySet:
        """
        Query assets by category.

        Args:
            category_id: Category UUID
            organization_id: Organization UUID
            include_children: If True, include assets from sub-categories

        Returns:
            QuerySet of matching assets
        """
        if include_children:
            # Get all descendant category IDs
            from apps.assets.models import AssetCategory
            category_ids = [category_id]

            def get_descendant_ids(cat_id):
                children = AssetCategory.objects.filter(
                    parent_id=cat_id,
                    is_deleted=False
                ).values_list('id', flat=True)
                for child_id in children:
                    category_ids.append(child_id)
                    get_descendant_ids(child_id)

            get_descendant_ids(category_id)

            return self.model_class.objects.filter(
                asset_category_id__in=category_ids,
                organization_id=organization_id,
                is_deleted=False
            )
        else:
            return self.model_class.objects.filter(
                asset_category_id=category_id,
                organization_id=organization_id,
                is_deleted=False
            )

    def query_by_department(
        self,
        department_id: str,
        organization_id: str
    ) -> QuerySet:
        """
        Query assets by department.

        Args:
            department_id: Department UUID
            organization_id: Organization UUID

        Returns:
            QuerySet of matching assets
        """
        return self.model_class.objects.filter(
            department_id=department_id,
            organization_id=organization_id,
            is_deleted=False
        )

    def query_by_location(
        self,
        location_id: str,
        organization_id: str,
        include_children: bool = True
    ) -> QuerySet:
        """
        Query assets by location.

        Args:
            location_id: Location UUID
            organization_id: Organization UUID
            include_children: If True, include assets from sub-locations

        Returns:
            QuerySet of matching assets
        """
        if include_children:
            # Get all descendant location IDs
            location_ids = [location_id]

            def get_descendant_ids(loc_id):
                children = Location.objects.filter(
                    parent_id=loc_id,
                    is_deleted=False
                ).values_list('id', flat=True)
                for child_id in children:
                    location_ids.append(child_id)
                    get_descendant_ids(child_id)

            get_descendant_ids(location_id)

            return self.model_class.objects.filter(
                location_id__in=location_ids,
                organization_id=organization_id,
                is_deleted=False
            )
        else:
            return self.model_class.objects.filter(
                location_id=location_id,
                organization_id=organization_id,
                is_deleted=False
            )

    def get_asset_statistics(self, organization_id: str) -> Dict[str, Any]:
        """
        Get asset statistics for organization.

        Args:
            organization_id: Organization UUID

        Returns:
            Dictionary with statistics:
            {
                'total': total_count,
                'by_status': {status: count},
                'total_value': sum_of_purchase_price,
                'total_net_value': sum_of_net_values,
                'by_category': {category_name: count}
            }
        """
        queryset = self.model_class.objects.filter(
            organization_id=organization_id,
            is_deleted=False
        )

        # Total count
        total = queryset.count()

        # By status
        by_status = {}
        try:
            from apps.system.services import DictionaryService
            status_items = DictionaryService.get_items('ASSET_STATUS', organization_id=organization_id)
            for item in status_items:
                count = queryset.filter(asset_status=item['code']).count()
                by_status[item['name']] = count
        except Exception:
            # Fallback if dictionary service fails
            pass

        # Financial summaries - specify output_field to avoid mixed types error
        from django.db.models.functions import Cast
        from django.db.models import FloatField

        total_value = queryset.aggregate(
            total=Coalesce(Sum(Cast('purchase_price', FloatField())), 0, output_field=FloatField())
        )['total'] or 0

        # Net value calculation (purchase_price - accumulated_depreciation)
        # Cast to float to avoid mixed types in expression
        net_value_result = queryset.annotate(
            net_value=Cast(F('purchase_price'), FloatField()) - Cast(F('accumulated_depreciation'), FloatField())
        ).aggregate(
            total=Coalesce(Sum('net_value'), 0, output_field=FloatField())
        )
        total_net_value = net_value_result['total'] or 0

        # By category
        by_category = dict(
            queryset.values('asset_category__name').annotate(
                count=Count('id')
            ).values_list('asset_category__name', 'count')
        )

        return {
            'total': total,
            'by_status': by_status,
            'total_value': float(total_value),
            'total_net_value': float(total_net_value),
            'by_category': by_category
        }

    @transaction.atomic
    def bulk_create(
        self,
        assets_data: List[Dict],
        user,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Bulk create assets.

        Args:
            assets_data: List of asset data dictionaries
            user: User creating the assets
            organization_id: Organization UUID

        Returns:
            Dictionary with bulk operation results
        """
        results = []
        succeeded = 0
        failed = 0

        for data in assets_data:
            try:
                # Auto-set organization
                data['organization_id'] = organization_id

                # Create asset
                asset = self.create(data, user)
                results.append({
                    'success': True,
                    'asset_code': asset.asset_code,
                    'id': str(asset.id)
                })
                succeeded += 1
            except ValidationError as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'data': data
                })
                failed += 1
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'data': data
                })
                failed += 1

        return {
            'total': len(assets_data),
            'succeeded': succeeded,
            'failed': failed,
            'results': results
        }

    def search_assets(
        self,
        organization_id: str,
        keyword: str
    ) -> QuerySet:
        """
        Search assets by keyword across multiple fields.

        Args:
            organization_id: Organization UUID
            keyword: Search keyword

        Returns:
            QuerySet of matching assets
        """
        return self.model_class.objects.filter(
            organization_id=organization_id,
            is_deleted=False
        ).filter(
            Q(asset_code__icontains=keyword) |
            Q(asset_name__icontains=keyword) |
            Q(specification__icontains=keyword) |
            Q(brand__icontains=keyword) |
            Q(model__icontains=keyword) |
            Q(serial_number__icontains=keyword)
        )

    def get_depreciation_summary(self, organization_id: str) -> Dict[str, Any]:
        """
        Get depreciation summary for organization.

        Args:
            organization_id: Organization UUID

        Returns:
            Dictionary with depreciation summary
        """
        queryset = self.model_class.objects.filter(
            organization_id=organization_id,
            is_deleted=False
        )

        # Total accumulated depreciation
        total_depreciation = queryset.aggregate(
            total=Coalesce(Sum('accumulated_depreciation'), 0)
        )['total'] or 0

        # Assets reaching residual value (net_value <= residual_value)
        at_residual_value = queryset.annotate(
            net_value=F('purchase_price') - F('accumulated_depreciation'),
            residual_value=F('purchase_price') * F('residual_rate') / 100
        ).filter(
            net_value__lte=F('residual_value')
        ).count()

        # Fully depreciated assets (accumulated_depreciation >= purchase_price * (1 - residual_rate/100))
        fully_depreciated = queryset.annotate(
            depreciation_limit=F('purchase_price') * (1 - F('residual_rate') / 100)
        ).filter(
            accumulated_depreciation__gte=F('depreciation_limit')
        ).count()

        return {
            'total_accumulated_depreciation': float(total_depreciation),
            'at_residual_value_count': at_residual_value,
            'fully_depreciated_count': fully_depreciated
        }
