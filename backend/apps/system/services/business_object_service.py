"""
Business Object Service for hybrid architecture.

Provides unified access to both hardcoded Django models and low-code
custom business objects.
"""
from typing import Dict, List, Optional, Any
from django.db.models import QuerySet
from django.utils.module_loading import import_string

from apps.common.models import BaseModel
from apps.common.services.base_crud import BaseCRUDService
from apps.system.models import (
    BusinessObject,
    ModelFieldDefinition,
    FieldDefinition,
)


# Core hardcoded model display names (for display name mapping)
HARDCODED_OBJECT_NAMES = {
    'Asset': ('资产', 'Asset'),
    'AssetCategory': ('资产分类', 'Asset Category'),
    'Supplier': ('供应商', 'Supplier'),
    'Location': ('位置', 'Location'),
    'AssetStatusLog': ('资产状态日志', 'Asset Status Log'),
    'AssetPickup': ('资产领用', 'Asset Pickup'),
    'PickupItem': ('领用明细', 'Pickup Item'),
    'AssetTransfer': ('资产调拨', 'Asset Transfer'),
    'TransferItem': ('调拨明细', 'Transfer Item'),
    'AssetReturn': ('资产归还', 'Asset Return'),
    'ReturnItem': ('归还明细', 'Return Item'),
    'AssetLoan': ('资产借用', 'Asset Loan'),
    'LoanItem': ('借用明细', 'Loan Item'),
    'Consumable': ('耗材', 'Consumable'),
    'ConsumableCategory': ('耗材分类', 'Consumable Category'),
    'ConsumableStock': ('耗材库存', 'Consumable Stock'),
    'ConsumablePurchase': ('耗材采购', 'Consumable Purchase'),
    'ConsumableIssue': ('耗材领用', 'Consumable Issue'),
    'PurchaseRequest': ('采购申请', 'Purchase Request'),
    'AssetReceipt': ('资产入库', 'Asset Receipt'),
    'Maintenance': ('维修记录', 'Maintenance'),
    'MaintenanceTask': ('维修任务', 'Maintenance Task'),
    'MaintenancePlan': ('维修计划', 'Maintenance Plan'),
    'DisposalRequest': ('报废申请', 'Disposal Request'),
    'InventoryTask': ('盘点任务', 'Inventory Task'),
    'InventorySnapshot': ('资产快照', 'Inventory Snapshot'),
    'InventoryItem': ('盘点明细', 'Inventory Item'),
    'Organization': ('组织', 'Organization'),
    'Department': ('部门', 'Department'),
    'User': ('用户', 'User'),
    'WorkflowDefinition': ('工作流定义', 'Workflow Definition'),
    'WorkflowInstance': ('工作流实例', 'Workflow Instance'),
    'FinanceVoucher': ('财务凭证', 'Finance Voucher'),
    'VoucherTemplate': ('凭证模板', 'Voucher Template'),
    'DepreciationConfig': ('折旧配置', 'Depreciation Config'),
    'DepreciationRecord': ('折旧记录', 'Depreciation Record'),
    'DepreciationRun': ('折旧运行', 'Depreciation Run'),
    'ITAsset': ('IT资产', 'IT Asset'),
    'ITMaintenanceRecord': ('IT维护记录', 'IT Maintenance Record'),
    'ConfigurationChange': ('配置变更', 'Configuration Change'),
    'ITSoftware': ('IT软件目录', 'IT Software Catalog'),
    'ITSoftwareLicense': ('IT软件许可', 'IT Software License'),
    'ITLicenseAllocation': ('IT许可证分配', 'IT License Allocation'),
    'Software': ('软件目录', 'Software Catalog'),
    'SoftwareLicense': ('软件许可', 'Software License'),
    'LicenseAllocation': ('许可证分配', 'License Allocation'),
    'LeasingContract': ('Lease Contract', 'Lease Contract'),
    'LeaseItem': ('Lease Item', 'Lease Item'),
    'RentPayment': ('Rent Payment', 'Rent Payment'),
    'LeaseReturn': ('Lease Return', 'Lease Return'),
    'LeaseExtension': ('Lease Extension', 'Lease Extension'),
    'InsuranceCompany': ('Insurance Company', 'Insurance Company'),
    'InsurancePolicy': ('Insurance Policy', 'Insurance Policy'),
    'InsuredAsset': ('Insured Asset', 'Insured Asset'),
    'PremiumPayment': ('Premium Payment', 'Premium Payment'),
    'ClaimRecord': ('Claim Record', 'Claim Record'),
    'PolicyRenewal': ('Policy Renewal', 'Policy Renewal'),
}


# Core hardcoded model registry
# Maps object codes to their Django model paths
CORE_HARDcoded_MODELS = {
    # Assets Module
    'Asset': 'apps.assets.models.Asset',
    'AssetCategory': 'apps.assets.models.AssetCategory',
    'Supplier': 'apps.assets.models.Supplier',
    'Location': 'apps.assets.models.Location',
    'AssetStatusLog': 'apps.assets.models.AssetStatusLog',
    'AssetPickup': 'apps.assets.models.AssetPickup',
    'AssetTransfer': 'apps.assets.models.AssetTransfer',
    'AssetReturn': 'apps.assets.models.AssetReturn',
    'AssetLoan': 'apps.assets.models.AssetLoan',

    # Consumables Module
    'Consumable': 'apps.consumables.models.Consumable',
    'ConsumableCategory': 'apps.consumables.models.ConsumableCategory',
    'ConsumableStock': 'apps.consumables.models.ConsumableStock',
    'ConsumablePurchase': 'apps.consumables.models.ConsumablePurchase',
    'ConsumableIssue': 'apps.consumables.models.ConsumableIssue',

    # Lifecycle Module
    'PurchaseRequest': 'apps.lifecycle.models.PurchaseRequest',
    'AssetReceipt': 'apps.lifecycle.models.AssetReceipt',
    'Maintenance': 'apps.lifecycle.models.Maintenance',
    'MaintenanceTask': 'apps.lifecycle.models.MaintenanceTask',
    'MaintenancePlan': 'apps.lifecycle.models.MaintenancePlan',
    'DisposalRequest': 'apps.lifecycle.models.DisposalRequest',

    # Inventory Module
    'InventoryTask': 'apps.inventory.models.InventoryTask',
    'InventorySnapshot': 'apps.inventory.models.InventorySnapshot',
    'InventoryItem': 'apps.inventory.models.InventoryDifference',

    # Organizations Module
    'Organization': 'apps.organizations.models.Organization',
    'Department': 'apps.organizations.models.Department',

    # Accounts Module
    'User': 'apps.accounts.models.User',

    # Workflows Module
    'WorkflowDefinition': 'apps.workflows.models.WorkflowDefinition',
    'WorkflowInstance': 'apps.workflows.models.WorkflowInstance',

    # Finance / Depreciation Module
    'FinanceVoucher': 'apps.finance.models.FinanceVoucher',
    'VoucherTemplate': 'apps.finance.models.VoucherTemplate',
    'DepreciationConfig': 'apps.depreciation.models.DepreciationConfig',
    'DepreciationRecord': 'apps.depreciation.models.DepreciationRecord',
    'DepreciationRun': 'apps.depreciation.models.DepreciationRun',

    # IT Assets Module
    'ITAsset': 'apps.it_assets.models.ITAssetInfo',
    'ITMaintenanceRecord': 'apps.it_assets.models.ITMaintenanceRecord',
    'ConfigurationChange': 'apps.it_assets.models.ConfigurationChange',
    'ITSoftware': 'apps.it_assets.models.Software',
    'ITSoftwareLicense': 'apps.it_assets.models.SoftwareLicense',
    'ITLicenseAllocation': 'apps.it_assets.models.LicenseAllocation',

    # Software Licenses Module
    'Software': 'apps.software_licenses.models.Software',
    'SoftwareLicense': 'apps.software_licenses.models.SoftwareLicense',
    'LicenseAllocation': 'apps.software_licenses.models.LicenseAllocation',

    # Leasing Module
    'LeasingContract': 'apps.leasing.models.LeaseContract',
    'LeaseItem': 'apps.leasing.models.LeaseItem',
    'RentPayment': 'apps.leasing.models.RentPayment',
    'LeaseReturn': 'apps.leasing.models.LeaseReturn',
    'LeaseExtension': 'apps.leasing.models.LeaseExtension',

    # Insurance Module
    'InsuranceCompany': 'apps.insurance.models.InsuranceCompany',
    'InsurancePolicy': 'apps.insurance.models.InsurancePolicy',
    'InsuredAsset': 'apps.insurance.models.InsuredAsset',
    'PremiumPayment': 'apps.insurance.models.PremiumPayment',
    'ClaimRecord': 'apps.insurance.models.ClaimRecord',
    'PolicyRenewal': 'apps.insurance.models.PolicyRenewal',
}


class BusinessObjectService:
    """
    Service for managing business objects in the hybrid architecture.

    Handles both hardcoded Django models and low-code custom objects,
    providing a unified interface for the metadata engine.
    """

    def get_all_objects(
        self,
        organization_id: Optional[str] = None,
        include_hardcoded: bool = True,
        include_custom: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all business objects, grouped by type.

        Args:
            organization_id: Filter by organization (for custom objects)
            include_hardcoded: Include hardcoded Django models
            include_custom: Include low-code custom objects

        Returns:
            Dict with 'hardcoded' and 'custom' lists
        """
        result = {
            'hardcoded': [],
            'custom': []
        }

        if include_hardcoded:
            result['hardcoded'] = self._get_hardcoded_objects()

        if include_custom:
            queryset = BusinessObject.objects.filter(is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            result['custom'] = self._format_custom_objects(
                queryset.filter(is_hardcoded=False)
            )

        return result

    def get_reference_options(
        self,
        organization_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get objects available for reference field selection.

        Returns a flat list with type indicator for UI display.

        Args:
            organization_id: Filter by organization (for custom objects)

        Returns:
            List of objects with 'value', 'label', and 'type' keys
        """
        result = []

        # Add hardcoded objects
        hardcoded = self._get_hardcoded_objects()
        for obj in hardcoded:
            result.append({
                'value': obj['code'],
                'label': obj['name'],
                'label_en': obj.get('name_en', ''),
                'type': 'hardcoded',
                'app_label': obj.get('app_label', ''),
                'icon': self._get_object_icon(obj['code'])
            })

        # Add custom objects
        queryset = BusinessObject.objects.filter(
            is_deleted=False,
            is_hardcoded=False
        )
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        for obj in queryset:
            result.append({
                'value': obj.code,
                'label': obj.name,
                'label_en': obj.name_en or '',
                'type': 'custom',
                'icon': 'document'
            })

        return result

    def get_object_fields(
        self,
        object_code: str,
        organization_id: Optional[str] = None,
        *,
        context: str = 'form',
        include_relations: bool = False,
    ) -> Dict[str, Any]:
        """
        Get field definitions for a specific business object.

        Args:
            object_code: Business object code
            organization_id: Organization context

        Returns:
            Dict with object info and fields list
        """
        # Check if it's a hardcoded model
        if object_code in CORE_HARDcoded_MODELS:
            return self._get_hardcoded_object_fields(
                object_code,
                context=context,
                include_relations=include_relations,
            )

        # Otherwise, it's a custom low-code object
        try:
            obj = BusinessObject.objects.get(code=object_code, is_deleted=False)
            return self._get_custom_object_fields(
                obj,
                context=context,
                include_relations=include_relations,
            )
        except BusinessObject.DoesNotExist:
            return {
                'error': f'Business object "{object_code}" not found'
            }

    def get_object_by_code(
        self,
        code: str,
        organization_id: Optional[str] = None
    ) -> Optional[BusinessObject]:
        """
        Get a business object by code.

        For hardcoded models, returns the BusinessObject metadata.
        For custom objects, returns the actual BusinessObject instance.

        Args:
            code: Object code
            organization_id: Organization context

        Returns:
            BusinessObject instance or None
        """
        try:
            return BusinessObject.objects.get(code=code, is_deleted=False)
        except BusinessObject.DoesNotExist:
            return None

    def is_hardcoded_model(self, object_code: str) -> bool:
        """Check if an object code refers to a hardcoded model."""
        return object_code in CORE_HARDcoded_MODELS

    def get_django_model(self, object_code: str):
        """
        Get the Django model class for a hardcoded object.

        Args:
            object_code: Object code

        Returns:
            Django model class or None
        """
        if not self.is_hardcoded_model(object_code):
            return None

        model_path = CORE_HARDcoded_MODELS.get(object_code)
        if not model_path:
            return None

        try:
            return import_string(model_path)
        except ImportError:
            return None

    def register_hardcoded_object(
        self,
        code: str,
        name: str,
        name_en: str = '',
        organization_id: Optional[str] = None
    ) -> BusinessObject:
        """
        Register a hardcoded model as a BusinessObject.

        Args:
            code: Object code (must be in CORE_HARDcoded_MODELS)
            name: Display name
            name_en: English display name
            organization_id: Organization (None for system-wide)

        Returns:
            Created or updated BusinessObject
        """
        if code not in CORE_HARDcoded_MODELS:
            raise ValueError(f'Unknown hardcoded model: {code}')

        obj, created = BusinessObject.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'name_en': name_en,
                'is_hardcoded': True,
                'django_model_path': CORE_HARDcoded_MODELS[code],
                'organization_id': organization_id,
            }
        )

        if not created:
            # Update existing
            obj.name = name
            obj.name_en = name_en
            obj.is_hardcoded = True
            obj.django_model_path = CORE_HARDcoded_MODELS[code]
            obj.save()

        return obj

    def sync_model_fields(
        self,
        object_code: str,
        organization_id: Optional[str] = None
    ) -> int:
        """
        Sync model fields for a hardcoded object.

        Creates/updates ModelFieldDefinition entries based on
        Django model metadata.

        Args:
            object_code: Object code (must be hardcoded)
            organization_id: Organization context

        Returns:
            Number of fields synced
        """
        model_class = self.get_django_model(object_code)
        if not model_class:
            raise ValueError(f'Cannot find Django model for: {object_code}')

        # Get or create BusinessObject
        obj = self.get_object_by_code(object_code)
        if not obj:
            raise ValueError(f'Business object not registered: {object_code}')

        # Get fields from the model
        fields = []
        for field in model_class._meta.get_fields():
            # Skip reverse relations and auto-generated fields
            if field.auto_created or field.is_relation:
                if not field.one_to_many and not field.many_to_one:
                    continue
            fields.append(field)

        # Sync each field
        count = 0
        for field in fields:
            field_def = ModelFieldDefinition.from_django_field(obj, field)

            # Special handling for JSONField-based file/image fields
            # Fields named 'images' or containing 'image' should use 'image' type
            # Fields named 'attachments' or containing 'attachment' should use 'file' type
            field_name_lower = field.name.lower()
            if field_name_lower in ('images', 'image') or field_name_lower.endswith('_image') or field_name_lower.endswith('_images'):
                field_def.field_type = 'image'
            elif field_name_lower in ('attachments', 'attachment') or field_name_lower.endswith('_attachment') or field_name_lower.endswith('_attachments'):
                field_def.field_type = 'file'

            # Get or update
            existing = ModelFieldDefinition.objects.filter(
                business_object=obj,
                field_name=field.name
            ).first()

            if existing:
                # Update only mutable fields (including field_type for correct mapping)
                existing.display_name = field_def.display_name
                existing.display_name_en = field_def.display_name_en
                existing.field_type = field_def.field_type
                existing.sort_order = field_def.sort_order
                existing.save()
            else:
                # Set organization if provided
                if organization_id:
                    field_def.organization_id = organization_id
                field_def.save()

            count += 1

        return count

    def _get_hardcoded_objects(self) -> List[Dict[str, Any]]:
        """Get list of hardcoded objects from registry."""
        result = []
        for code, model_path in CORE_HARDcoded_MODELS.items():
            # Try to get name from BusinessObject if registered
            name = code  # Default
            name_en = ''
            app_label = model_path.split('.')[2] if len(model_path.split('.')) > 2 else ''

            try:
                obj = BusinessObject.objects.get(code=code)
                name = obj.name
                name_en = obj.name_en or ''
            except BusinessObject.DoesNotExist:
                pass

            result.append({
                'code': code,
                'name': name,
                'name_en': name_en,
                'app_label': app_label,
                'model_path': model_path,
                'type': 'hardcoded'
            })

        return sorted(result, key=lambda x: x['code'])

    def _format_custom_objects(
        self,
        queryset: QuerySet
    ) -> List[Dict[str, Any]]:
        """Format custom low-code objects for API response."""
        return [{
            'code': obj.code,
            'name': obj.name,
            'name_en': obj.name_en or '',
            'table_name': obj.table_name,
            'field_count': obj.field_definitions.count(),
            'layout_count': obj.page_layouts.count(),
            'type': 'custom',
            'enable_workflow': obj.enable_workflow,
        } for obj in queryset]

    def _should_show_model_field_in_context(self, field_def: ModelFieldDefinition, context: str) -> bool:
        if context == 'list':
            return bool(getattr(field_def, 'show_in_list', True))
        if context == 'detail':
            return bool(getattr(field_def, 'show_in_detail', True))
        return bool(getattr(field_def, 'show_in_form', True))

    def _should_show_custom_field_in_context(self, field_def: FieldDefinition, context: str) -> bool:
        if context == 'list':
            return bool(getattr(field_def, 'show_in_list', False))
        if context == 'detail':
            return bool(getattr(field_def, 'show_in_detail', True))
        return bool(getattr(field_def, 'show_in_form', True))

    def _get_hardcoded_object_fields(
        self,
        object_code: str,
        *,
        context: str = 'form',
        include_relations: bool = False,
    ) -> Dict[str, Any]:
        """Get fields for a hardcoded object."""
        # Get BusinessObject metadata
        try:
            obj = BusinessObject.objects.get(code=object_code)
        except BusinessObject.DoesNotExist:
            return {
                'error': f'Business object "{object_code}" not registered'
            }

        # Get the Django model class
        model_class = self.get_django_model(object_code)
        if not model_class:
            return {
                'error': f'Django model not found for: {object_code}'
            }

        normalized_context = context if context in {'form', 'detail', 'list'} else 'form'

        # Generate field definitions directly from Django model (real-time)
        # This ensures field type detection fixes are applied immediately
        fields = []
        for field in model_class._meta.get_fields():
            # Skip auto-generated relations unless explicitly requested.
            is_reverse_relation = bool(field.auto_created and getattr(field, 'one_to_many', False))
            if field.auto_created and not is_reverse_relation:
                continue
            if is_reverse_relation:
                if not include_relations:
                    continue
                relation_code = getattr(field, 'get_accessor_name', lambda: field.name)() or field.name
                fields.append({
                    'fieldName': relation_code,
                    'displayName': relation_code,
                    'displayNameEn': relation_code,
                    'fieldType': 'sub_table',
                    'djangoFieldType': field.__class__.__name__,
                    'isRequired': False,
                    'isReadonly': True,
                    'isEditable': False,
                    'isUnique': False,
                    'showInList': False,
                    'showInDetail': True,
                    'showInForm': False,
                    'sortOrder': 0,
                    'referenceModelPath': '',
                    'maxLength': None,
                    'decimalPlaces': None,
                    'isReverseRelation': True,
                    'reverseRelationModel': '',
                    'reverseRelationField': '',
                    'relationDisplayMode': 'tab_readonly',
                })
                continue

            if field.is_relation and not field.many_to_one and not field.one_to_many:
                continue

            # Use ModelFieldDefinition.from_django_field to get correct field type
            field_def = ModelFieldDefinition.from_django_field(obj, field)

            if not self._should_show_model_field_in_context(field_def, normalized_context):
                continue

            fields.append({
                'fieldName': field_def.field_name,
                'displayName': field_def.display_name,
                'displayNameEn': field_def.display_name_en or '',
                'fieldType': field_def.field_type,
                'djangoFieldType': field_def.django_field_type,
                'isRequired': field_def.is_required,
                'isReadonly': field_def.is_readonly,
                'isEditable': field_def.is_editable,
                'isUnique': field_def.is_unique,
                'showInList': field_def.show_in_list,
                'showInDetail': field_def.show_in_detail,
                'showInForm': field_def.show_in_form,
                'sortOrder': field_def.sort_order,
                'referenceModelPath': field_def.reference_model_path,
                'maxLength': field_def.max_length,
                'decimalPlaces': field_def.decimal_places,
                'isReverseRelation': False,
            })

        return {
            'objectCode': obj.code,
            'objectName': obj.name,
            'objectNameEn': obj.name_en or '',
            'isHardcoded': True,
            'modelPath': obj.django_model_path,
            'fields': fields
        }

    def _get_custom_object_fields(
        self,
        obj: BusinessObject,
        *,
        context: str = 'form',
        include_relations: bool = False,
    ) -> Dict[str, Any]:
        """Get fields for a custom low-code object."""
        normalized_context = context if context in {'form', 'detail', 'list'} else 'form'
        rows = []
        queryset = obj.field_definitions.filter(is_deleted=False).order_by('sort_order')
        for f in queryset:
            if getattr(f, 'is_reverse_relation', False) and not include_relations:
                continue
            if not self._should_show_custom_field_in_context(f, normalized_context):
                continue
            rows.append(
                {
                    'field_name': f.code,
                    'display_name': f.name,
                    'field_type': f.field_type,
                    'is_required': f.is_required,
                    'is_readonly': f.is_readonly,
                    'is_unique': f.is_unique,
                    'show_in_list': f.show_in_list,
                    'show_in_detail': f.show_in_detail,
                    'show_in_form': f.show_in_form,
                    'sort_order': f.sort_order,
                    'options': f.options,
                    'reference_object': f.reference_object,
                    'formula': f.formula,
                    'is_reverse_relation': getattr(f, 'is_reverse_relation', False),
                    'reverse_relation_model': getattr(f, 'reverse_relation_model', ''),
                    'reverse_relation_field': getattr(f, 'reverse_relation_field', ''),
                    'relation_display_mode': getattr(f, 'relation_display_mode', 'tab_readonly'),
                }
            )

        return {
            'object_code': obj.code,
            'object_name': obj.name,
            'object_name_en': obj.name_en or '',
            'is_hardcoded': False,
            'table_name': obj.table_name,
            'fields': rows
        }

    def _get_object_icon(self, code: str) -> str:
        """Get icon name for an object code."""
        icon_map = {
            'Asset': 'box',
            'AssetCategory': 'folder',
            'Supplier': 'office-building',
            'Location': 'location',
            'AssetPickup': 'hand',
            'AssetTransfer': 'switch',
            'AssetReturn': 'back',
            'Consumable': 'files',
            'ConsumableCategory': 'folder',
            'PurchaseRequest': 'document',
            'Maintenance': 'tools',
            'InventoryTask': 'clipboard',
            'Organization': 'office-building',
            'Department': 'office-building',
            'User': 'user',
        }
        return icon_map.get(code, 'document')

