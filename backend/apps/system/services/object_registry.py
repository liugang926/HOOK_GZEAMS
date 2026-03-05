"""
Object Registry - Central service for business object registration and management.

This service provides:
1. Auto-registration of standard business objects on app startup
2. Runtime metadata caching for fast object lookup
3. Mapping between object codes and their model/viewset classes
4. Field synchronization for hardcoded Django models
"""
from typing import Dict, Optional, Type, List
from django.core.cache import cache
from django.utils.module_loading import import_string
from apps.system.models import BusinessObject, FieldDefinition, ModelFieldDefinition


class ObjectMeta:
    """
    Business object metadata container.

    Attributes:
        code: Unique object code (e.g., 'Asset', 'AssetPickup')
        name: Human-readable object name
        model_class: Django model class (if hardcoded)
        viewset_class: DRF ViewSet class (if exists)
        is_hardcoded: Whether this is a hardcoded Django model
        django_model_path: Python path to Django model
    """

    def __init__(
        self,
        code: str,
        name: str,
        model_class: Optional[Type] = None,
        viewset_class: Optional[Type] = None,
        is_hardcoded: bool = False,
        django_model_path: Optional[str] = None,
    ):
        self.code = code
        self.name = name
        self.model_class = model_class
        self.viewset_class = viewset_class
        self.is_hardcoded = is_hardcoded
        self.django_model_path = django_model_path

    def __repr__(self):
        return f"ObjectMeta(code='{self.code}', name='{self.name}', hardcoded={self.is_hardcoded})"


class ObjectRegistry:
    """
    Central registry for all business objects in the system.

    This registry maintains a mapping of object codes to their metadata,
    enabling dynamic routing without hardcoded URL configurations.

    Usage:
        # Get object metadata
        meta = ObjectRegistry.get('Asset')

        # Get from database with caching
        meta = ObjectRegistry.get_or_create_from_db('Asset')
    """

    # In-memory registry for fast lookup
    _registry: Dict[str, ObjectMeta] = {}

    # ViewSet class path mapping for hardcoded objects
    _viewset_map: Dict[str, str] = {
        # Asset module
        'Asset': 'apps.assets.viewsets.AssetViewSet',
        'AssetCategory': 'apps.assets.viewsets.AssetCategoryViewSet',
        'AssetPickup': 'apps.assets.viewsets.AssetPickupViewSet',
        'AssetTransfer': 'apps.assets.viewsets.AssetTransferViewSet',
        'AssetReturn': 'apps.assets.viewsets.AssetReturnViewSet',
        'AssetLoan': 'apps.assets.viewsets.AssetLoanViewSet',
        'Supplier': 'apps.assets.viewsets.SupplierViewSet',
        'Location': 'apps.assets.viewsets.LocationViewSet',
        'AssetStatusLog': 'apps.assets.viewsets.AssetStatusLogViewSet',
        # Consumables module
        'Consumable': 'apps.consumables.viewsets.ConsumableViewSet',
        'ConsumableCategory': 'apps.consumables.viewsets.ConsumableCategoryViewSet',
        'ConsumableStock': 'apps.consumables.viewsets.ConsumableStockViewSet',
        'ConsumablePurchase': 'apps.consumables.viewsets.ConsumablePurchaseViewSet',
        'ConsumableIssue': 'apps.consumables.viewsets.ConsumableIssueViewSet',
        # Lifecycle module
        'PurchaseRequest': 'apps.lifecycle.viewsets.PurchaseRequestViewSet',
        'AssetReceipt': 'apps.lifecycle.viewsets.AssetReceiptViewSet',
        'Maintenance': 'apps.lifecycle.viewsets.MaintenanceViewSet',
        'MaintenancePlan': 'apps.lifecycle.viewsets.MaintenancePlanViewSet',
        'MaintenanceTask': 'apps.lifecycle.viewsets.MaintenanceTaskViewSet',
        'DisposalRequest': 'apps.lifecycle.viewsets.DisposalRequestViewSet',
        # Inventory module
        'InventoryTask': 'apps.inventory.viewsets.InventoryTaskViewSet',
        'InventorySnapshot': 'apps.inventory.viewsets.InventorySnapshotViewSet',
        'InventoryItem': 'apps.inventory.viewsets.InventoryDifferenceViewSet',
        # IT Assets
        'ITAsset': 'apps.it_assets.viewsets.ITAssetInfoViewSet',
        'ITSoftware': 'apps.it_assets.viewsets.SoftwareViewSet',
        'ITSoftwareLicense': 'apps.it_assets.viewsets.SoftwareLicenseViewSet',
        'ITLicenseAllocation': 'apps.it_assets.viewsets.LicenseAllocationViewSet',
        'ITMaintenanceRecord': 'apps.it_assets.viewsets.ITMaintenanceRecordViewSet',
        'ConfigurationChange': 'apps.it_assets.viewsets.ConfigurationChangeViewSet',
        # Software Licenses
        'Software': 'apps.software_licenses.viewsets.SoftwareViewSet',
        'SoftwareLicense': 'apps.software_licenses.viewsets.SoftwareLicenseViewSet',
        'LicenseAllocation': 'apps.software_licenses.viewsets.LicenseAllocationViewSet',
        # Leasing
        'LeasingContract': 'apps.leasing.viewsets.LeaseContractViewSet',
        'LeaseItem': 'apps.leasing.viewsets.LeaseItemViewSet',
        'RentPayment': 'apps.leasing.viewsets.RentPaymentViewSet',
        'LeaseReturn': 'apps.leasing.viewsets.LeaseReturnViewSet',
        'LeaseExtension': 'apps.leasing.viewsets.LeaseExtensionViewSet',
        # Insurance
        'InsuranceCompany': 'apps.insurance.viewsets.InsuranceCompanyViewSet',
        'InsurancePolicy': 'apps.insurance.viewsets.InsurancePolicyViewSet',
        'InsuredAsset': 'apps.insurance.viewsets.InsuredAssetViewSet',
        'PremiumPayment': 'apps.insurance.viewsets.PremiumPaymentViewSet',
        'ClaimRecord': 'apps.insurance.viewsets.ClaimRecordViewSet',
        'PolicyRenewal': 'apps.insurance.viewsets.PolicyRenewalViewSet',
        # Finance
        'DepreciationConfig': 'apps.depreciation.viewsets.DepreciationConfigViewSet',
        'DepreciationRecord': 'apps.depreciation.viewsets.DepreciationRecordViewSet',
        'DepreciationRun': 'apps.depreciation.viewsets.DepreciationRunViewSet',
        'FinanceVoucher': 'apps.finance.viewsets.FinanceVoucherViewSet',
        'VoucherTemplate': 'apps.finance.viewsets.VoucherTemplateViewSet',
        # Workflows
        'WorkflowDefinition': 'apps.workflows.viewsets.WorkflowDefinitionViewSet',
        'WorkflowTemplate': 'apps.workflows.viewsets.WorkflowTemplateViewSet',
        'WorkflowInstance': 'apps.workflows.viewsets.WorkflowInstanceViewSet',
        'WorkflowTask': 'apps.workflows.viewsets.WorkflowTaskViewSet',
        'WorkflowApproval': 'apps.workflows.viewsets.WorkflowApprovalViewSet',
        'WorkflowOperationLog': 'apps.workflows.viewsets.WorkflowOperationLogViewSet',
        # Organizations
        'Department': 'apps.organizations.viewsets.DepartmentViewSet',
        'Organization': 'apps.organizations.viewsets.OrganizationViewSet',

        # Accounts (needed for reference resolution in low-code runtime)
        'User': 'apps.accounts.viewsets.UserViewSet',
    }

    @classmethod
    def register(cls, code: str, **metadata) -> ObjectMeta:
        """
        Register a business object in the in-memory registry.

        Args:
            code: Unique object code
            **metadata: Additional metadata (name, model_class, etc.)

        Returns:
            ObjectMeta instance
        """
        meta = ObjectMeta(code=code, **metadata)
        cls._registry[code] = meta
        return meta

    @classmethod
    def get(cls, code: str) -> Optional[ObjectMeta]:
        """
        Get object metadata from in-memory registry.

        Args:
            code: Object code

        Returns:
            ObjectMeta instance or None if not found
        """
        return cls._registry.get(code)

    @classmethod
    def get_viewset_class(cls, code: str) -> Optional[Type]:
        """
        Get ViewSet class for a given object code.

        Args:
            code: Object code

        Returns:
            ViewSet class or None if not configured
        """
        viewset_path = cls._viewset_map.get(code)
        if viewset_path:
            try:
                return import_string(viewset_path)
            except ImportError:
                pass
        return None

    @classmethod
    def get_or_create_from_db(cls, code: str) -> Optional[ObjectMeta]:
        """
        Get object metadata from database with caching.

        This method first checks the cache, then the database,
        creating ObjectMeta from BusinessObject record.

        Args:
            code: Object code

        Returns:
            ObjectMeta instance or None if BusinessObject doesn't exist
        """
        # Check cache first (with fallback for Redis unavailability)
        cache_key = f"object_meta:{code}"
        try:
            cached = cache.get(cache_key)
            if cached:
                # Hot-fix: viewset mappings evolve over time, but cached ObjectMeta may lag behind.
                # Refresh critical hardcoded bindings to avoid routing to MetadataDrivenViewSet by mistake.
                try:
                    mapped_viewset = cls.get_viewset_class(code)
                    if mapped_viewset:
                        # Hardcoded mappings take precedence over stale cache payloads.
                        # This prevents old cache entries (is_hardcoded=False) from breaking custom actions.
                        cached.is_hardcoded = True
                        cached.viewset_class = mapped_viewset

                    if getattr(cached, "is_hardcoded", False):
                        if getattr(cached, "viewset_class", None) is None:
                            cached.viewset_class = cls.get_viewset_class(code)
                        if getattr(cached, "model_class", None) is None and getattr(cached, "django_model_path", None):
                            cached.model_class = import_string(cached.django_model_path)
                except Exception:
                    pass
                return cached
        except Exception:
            # Redis unavailable, continue to database query
            pass

        # Query database - BusinessObject uses GlobalMetadataManager
        # which does NOT filter by organization (metadata is global)
        try:
            bo = BusinessObject.objects.get(code=code)
            meta = cls._build_meta_from_business_object(bo)
            # Try to cache for 1 hour (ignore failures)
            try:
                cache.set(cache_key, meta, timeout=3600)
            except Exception:
                pass
            return meta
        except BusinessObject.DoesNotExist:
            return None

    @classmethod
    def _build_meta_from_business_object(cls, bo: BusinessObject) -> ObjectMeta:
        """
        Build ObjectMeta from BusinessObject database record.

        Args:
            bo: BusinessObject instance

        Returns:
            ObjectMeta instance
        """
        model_class = None
        viewset_class = cls.get_viewset_class(bo.code)

        # Hardcoded status is derived from DB flag OR hardcoded viewset mapping.
        # This makes routing resilient when BusinessObject seed data has stale flags.
        is_hardcoded = bool(bo.is_hardcoded or viewset_class)

        # Import model class when it is a hardcoded object and model path is available.
        if is_hardcoded and bo.django_model_path:
            try:
                model_class = import_string(bo.django_model_path)
            except ImportError:
                pass

        return ObjectMeta(
            code=bo.code,
            name=bo.name,
            model_class=model_class,
            viewset_class=viewset_class,
            is_hardcoded=is_hardcoded,
            django_model_path=bo.django_model_path,
        )

    @classmethod
    def auto_register_standard_objects(cls) -> int:
        """
        Automatically register standard business objects on app startup.

        This ensures BusinessObject records exist for all hardcoded models,
        and syncs their field definitions to ModelFieldDefinition.

        Returns:
            Number of objects registered/updated
        """
        standard_objects = [
            # Asset module
            {'code': 'Asset', 'name': '资产卡片', 'model': 'apps.assets.models.Asset'},
            {'code': 'AssetCategory', 'name': '资产分类', 'model': 'apps.assets.models.AssetCategory'},
            {'code': 'AssetPickup', 'name': '资产领用单', 'model': 'apps.assets.models.AssetPickup'},
            {'code': 'AssetTransfer', 'name': '资产调拨单', 'model': 'apps.assets.models.AssetTransfer'},
            {'code': 'AssetReturn', 'name': '资产归还单', 'model': 'apps.assets.models.AssetReturn'},
            {'code': 'AssetLoan', 'name': '资产借用单', 'model': 'apps.assets.models.AssetLoan'},
            {'code': 'Supplier', 'name': '供应商', 'model': 'apps.assets.models.Supplier'},
            {'code': 'Location', 'name': '存放地点', 'model': 'apps.assets.models.Location'},
            {'code': 'AssetStatusLog', 'name': '资产状态日志', 'model': 'apps.assets.models.AssetStatusLog'},
            # Consumables module
            {'code': 'Consumable', 'name': '低值易耗品', 'model': 'apps.consumables.models.Consumable'},
            {'code': 'ConsumableCategory', 'name': '易耗品分类', 'model': 'apps.consumables.models.ConsumableCategory'},
            {'code': 'ConsumableStock', 'name': '易耗品库存', 'model': 'apps.consumables.models.ConsumableStock'},
            {'code': 'ConsumablePurchase', 'name': '易耗品采购', 'model': 'apps.consumables.models.ConsumablePurchase'},
            {'code': 'ConsumableIssue', 'name': '易耗品领用', 'model': 'apps.consumables.models.ConsumableIssue'},
            # Lifecycle module
            {'code': 'PurchaseRequest', 'name': '采购申请', 'model': 'apps.lifecycle.models.PurchaseRequest'},
            {'code': 'AssetReceipt', 'name': '资产入库单', 'model': 'apps.lifecycle.models.AssetReceipt'},
            {'code': 'Maintenance', 'name': '维修记录', 'model': 'apps.lifecycle.models.Maintenance'},
            {'code': 'MaintenancePlan', 'name': '维修计划', 'model': 'apps.lifecycle.models.MaintenancePlan'},
            {'code': 'MaintenanceTask', 'name': '维修任务', 'model': 'apps.lifecycle.models.MaintenanceTask'},
            {'code': 'DisposalRequest', 'name': '处置申请', 'model': 'apps.lifecycle.models.DisposalRequest'},
            # Inventory module
            {'code': 'InventoryTask', 'name': '盘点任务', 'model': 'apps.inventory.models.InventoryTask'},
            {'code': 'InventorySnapshot', 'name': '盘点快照', 'model': 'apps.inventory.models.InventorySnapshot'},
            {'code': 'InventoryItem', 'name': '盘点明细', 'model': 'apps.inventory.models.InventoryDifference'},
            # IT Assets
            {'code': 'ITAsset', 'name': 'IT设备', 'model': 'apps.it_assets.models.ITAssetInfo'},
            {'code': 'ITSoftware', 'name': 'IT软件目录', 'model': 'apps.it_assets.models.Software'},
            {'code': 'ITSoftwareLicense', 'name': 'IT软件许可', 'model': 'apps.it_assets.models.SoftwareLicense'},
            {'code': 'ITLicenseAllocation', 'name': 'IT许可证分配', 'model': 'apps.it_assets.models.LicenseAllocation'},
            {'code': 'ITMaintenanceRecord', 'name': 'IT维护记录', 'model': 'apps.it_assets.models.ITMaintenanceRecord'},
            {'code': 'ConfigurationChange', 'name': '配置变更', 'model': 'apps.it_assets.models.ConfigurationChange'},
            # Software Licenses
            {'code': 'Software', 'name': '软件目录', 'model': 'apps.software_licenses.models.Software'},
            {'code': 'SoftwareLicense', 'name': '软件许可', 'model': 'apps.software_licenses.models.SoftwareLicense'},
            {'code': 'LicenseAllocation', 'name': '许可证分配', 'model': 'apps.software_licenses.models.LicenseAllocation'},
            # Leasing
            {'code': 'LeasingContract', 'name': '租赁合同', 'model': 'apps.leasing.models.LeaseContract'},
            {'code': 'LeaseItem', 'name': '租赁明细', 'model': 'apps.leasing.models.LeaseItem'},
            {'code': 'RentPayment', 'name': '租金支付', 'model': 'apps.leasing.models.RentPayment'},
            {'code': 'LeaseReturn', 'name': '租赁归还', 'model': 'apps.leasing.models.LeaseReturn'},
            {'code': 'LeaseExtension', 'name': '租赁续租', 'model': 'apps.leasing.models.LeaseExtension'},
            # Insurance
            {'code': 'InsurancePolicy', 'name': '保险单', 'model': 'apps.insurance.models.InsurancePolicy'},
            {'code': 'InsuranceCompany', 'name': '保险公司', 'model': 'apps.insurance.models.InsuranceCompany'},
            {'code': 'InsuredAsset', 'name': '投保资产', 'model': 'apps.insurance.models.InsuredAsset'},
            {'code': 'PremiumPayment', 'name': '保费支付', 'model': 'apps.insurance.models.PremiumPayment'},
            {'code': 'ClaimRecord', 'name': '理赔记录', 'model': 'apps.insurance.models.ClaimRecord'},
            {'code': 'PolicyRenewal', 'name': '保单续保', 'model': 'apps.insurance.models.PolicyRenewal'},
            # Finance
            {'code': 'DepreciationConfig', 'name': '折旧配置', 'model': 'apps.depreciation.models.DepreciationConfig'},
            {'code': 'DepreciationRecord', 'name': '折旧记录', 'model': 'apps.depreciation.models.DepreciationRecord'},
            {'code': 'DepreciationRun', 'name': '折旧运行', 'model': 'apps.depreciation.models.DepreciationRun'},
            {'code': 'FinanceVoucher', 'name': '财务凭证', 'model': 'apps.finance.models.FinanceVoucher'},
            {'code': 'VoucherTemplate', 'name': '凭证模板', 'model': 'apps.finance.models.VoucherTemplate'},
            # Workflows
            {'code': 'WorkflowDefinition', 'name': '工作流定义', 'model': 'apps.workflows.models.WorkflowDefinition'},
            {'code': 'WorkflowTemplate', 'name': '工作流模板', 'model': 'apps.workflows.models.WorkflowTemplate'},
            {'code': 'WorkflowInstance', 'name': '工作流实例', 'model': 'apps.workflows.models.WorkflowInstance'},
            {'code': 'WorkflowTask', 'name': '工作流任务', 'model': 'apps.workflows.models.WorkflowTask'},
            {'code': 'WorkflowApproval', 'name': '工作流审批记录', 'model': 'apps.workflows.models.WorkflowApproval'},
            {'code': 'WorkflowOperationLog', 'name': '工作流操作日志', 'model': 'apps.workflows.models.WorkflowOperationLog'},
            # Organizations
            {'code': 'Department', 'name': '部门', 'model': 'apps.organizations.models.Department'},
            {'code': 'Organization', 'name': '组织', 'model': 'apps.organizations.models.Organization'},
            # Accounts (needed for reference resolution via unified object router)
            {'code': 'User', 'name': '用户', 'model': 'apps.accounts.models.User'},
        ]

        count = 0
        for obj_def in standard_objects:
            if cls._ensure_business_object_exists(obj_def):
                count += 1

        return count

    @classmethod
    def _ensure_business_object_exists(cls, obj_def: dict) -> bool:
        """
        Ensure BusinessObject record exists for a standard object.

        Creates the BusinessObject if it doesn't exist,
        and syncs field definitions for hardcoded models.

        Args:
            obj_def: Dictionary with 'code', 'name', 'model' keys

        Returns:
            True if object was created or updated, False on error
        """
        try:
            bo, created = BusinessObject.objects.get_or_create(
                code=obj_def['code'],
                defaults={
                    'name': obj_def['name'],
                    'is_hardcoded': True,
                    'django_model_path': obj_def['model'],
                    'enable_workflow': True,
                    'enable_version': True,
                    'enable_soft_delete': True,
                }
            )

            # Update if exists but was modified
            if not created:
                bo.name = obj_def['name']
                bo.is_hardcoded = True
                bo.django_model_path = obj_def['model']
                bo.save()

            # Sync field definitions for hardcoded models
            if bo.is_hardcoded:
                cls._sync_model_fields(bo)

            # Also register in memory
            cls.register(
                bo.code,
                name=bo.name,
                is_hardcoded=bo.is_hardcoded,
                django_model_path=bo.django_model_path,
            )

            return True

        except Exception:
            return False

    @classmethod
    def _sync_model_fields(cls, business_object: BusinessObject) -> int:
        """
        Sync Django model fields to ModelFieldDefinition.

        This ensures that hardcoded Django models have their fields
        exposed in the metadata system for layout configuration.

        Args:
            business_object: BusinessObject instance with is_hardcoded=True

        Returns:
            Number of fields synced
        """
        if not business_object.is_hardcoded or not business_object.django_model_path:
            return 0

        try:
            model_class = import_string(business_object.django_model_path)
        except ImportError:
            return 0

        count = 0
        existing_fields = set(
            ModelFieldDefinition.objects.filter(
                business_object=business_object
            ).values_list('field_name', flat=True)
        )

        for field in model_class._meta.get_fields():
            # Skip private fields and reverse relations
            if field.name.startswith('_'):
                continue

            # Skip auto-created reverse relations
            if field.auto_created:
                continue

            try:
                # Create or update field definition
                ModelFieldDefinition.objects.get_or_create(
                    business_object=business_object,
                    field_name=field.name,
                    defaults={
                        **cls._model_field_to_dict(business_object, field)
                    }
                )
                count += 1
            except Exception:
                continue

        # Remove fields that no longer exist in model
        ModelFieldDefinition.objects.filter(
            business_object=business_object,
            field_name__in=existing_fields - set(
                f.name for f in model_class._meta.get_fields()
                if not f.name.startswith('_') and not f.auto_created
            )
        ).delete()

        return count

    @classmethod
    def _model_field_to_dict(cls, business_object: BusinessObject, field) -> dict:
        """
        Convert Django model field to ModelFieldDefinition dict.

        Args:
            business_object: BusinessObject instance
            field: Django model field instance

        Returns:
            Dictionary for ModelFieldDefinition creation
        """
        from apps.system.models import ModelFieldDefinition

        # Get verbose name
        display_name = getattr(field, 'verbose_name', field.name) or field.name

        # Map Django field type to metadata field type
        field_type = ModelFieldDefinition.DJANGO_FIELD_TYPE_MAP.get(
            field.__class__.__name__,
            'text'
        )

        # Check if required
        is_required = not field.null and not field.blank

        # Check if editable
        is_editable = getattr(field, 'editable', True)

        # Get max length for text fields
        max_length = getattr(field, 'max_length', None)

        return {
            'display_name': str(display_name),
            'display_name_en': '',
            'field_type': field_type,
            'django_field_type': field.__class__.__name__,
            'is_required': is_required,
            'is_readonly': not is_editable,
            'is_editable': is_editable,
            'is_unique': getattr(field, 'unique', False),
            'show_in_list': True,
            'show_in_detail': True,
            'show_in_form': is_editable,
            'sort_order': 0,
            'max_length': max_length,
            'decimal_places': getattr(field, 'decimal_places', None),
            'max_digits': getattr(field, 'max_digits', None),
        }

    @classmethod
    def invalidate_cache(cls, code: str) -> None:
        """
        Invalidate cached metadata for a specific object.

        Args:
            code: Object code
        """
        try:
            cache.delete(f"object_meta:{code}")
        except Exception:
            pass

    @classmethod
    def invalidate_all_cache(cls) -> None:
        """Invalidate all cached metadata."""
        # This would require cache key pattern deletion
        # For now, objects expire after 1 hour automatically
        pass

    @classmethod
    def get_all_codes(cls) -> List[str]:
        """
        Get list of all registered object codes.

        Returns:
            List of object codes
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, code: str) -> bool:
        """
        Check if an object code is registered.

        Args:
            code: Object code

        Returns:
            True if registered, False otherwise
        """
        return code in cls._registry
