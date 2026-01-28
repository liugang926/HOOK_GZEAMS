"""
Object Router ViewSet - Unified dynamic routing for all business objects.

This ViewSet provides a single entry point (/api/objects/{code}/) for all
business objects, routing requests to the appropriate ViewSet based on the
object code.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from typing import Optional

from apps.system.services.object_registry import ObjectRegistry
from apps.common.viewsets.metadata_driven import MetadataDrivenViewSet
from apps.common.responses.base import BaseResponse


class ObjectRouterViewSet(viewsets.ViewSet):
    """
    Unified dynamic object router ViewSet.

    URL Pattern: /api/objects/{code}/

    This ViewSet dynamically routes requests to the appropriate business object
    based on the object_code in the URL. It supports both hardcoded Django models
    (with existing ViewSets) and dynamic metadata-driven objects.

    Examples:
        GET /api/objects/Asset/              # List assets
        POST /api/objects/Asset/             # Create asset
        GET /api/objects/Asset/{id}/         # Get asset detail
        GET /api/objects/Asset/metadata/     # Get asset metadata

    Standard objects automatically supported:
        - Asset, AssetCategory, AssetPickup, AssetTransfer, AssetReturn, AssetLoan
        - Consumable, ConsumableCategory, ConsumableStock
        - PurchaseRequest, AssetReceipt, Maintenance, DisposalRequest
        - InventoryTask, InventorySnapshot
        - And many more...
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._delegate_viewset: Optional[viewsets.ModelViewSet] = None
        self._object_meta = None

    def initial(self, request, *args, **kwargs):
        """
        Initialize ViewSet by loading object metadata and creating delegate.

        This method is called before any action to set up the appropriate
        ViewSet based on the object_code in the URL.
        """
        super().initial(request, *args, **kwargs)

        object_code = kwargs.get('code')
        if not object_code:
            raise ValidationError({"code": ["object_code is required"]})

        # Get object metadata from registry or database
        self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
        if not self._object_meta:
            raise NotFound(f"Business object '{object_code}' not found")

        # Create the delegate ViewSet that will handle the actual request
        self._delegate_viewset = self._create_delegate_viewset(
            self._object_meta, request
        )

    def _create_delegate_viewset(self, meta, request):
        """
        Create the delegate ViewSet based on object type.

        For hardcoded objects, uses the existing ViewSet.
        For dynamic objects, uses MetadataDrivenViewSet.

        Args:
            meta: ObjectMeta instance
            request: Current HTTP request

        Returns:
            ViewSet instance configured for this object
        """
        if meta.is_hardcoded and meta.viewset_class:
            return self._get_hardcoded_viewset(meta, request)
        else:
            return self._get_dynamic_viewset(meta, request)

    def _get_hardcoded_viewset(self, meta, request):
        """
        Get ViewSet for hardcoded Django models.

        Args:
            meta: ObjectMeta with is_hardcoded=True
            request: Current HTTP request

        Returns:
            Configured ViewSet instance
        """
        viewset_class = meta.viewset_class
        if not viewset_class:
            # Fallback to dynamic viewset if no viewset configured
            return self._get_dynamic_viewset(meta, request)

        # Instantiate and configure the ViewSet
        viewset = viewset_class()
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = getattr(self, 'action', None)

        # Initialize the ViewSet
        if hasattr(viewset, 'initial'):
            viewset.initial(request, *self.args, **self.kwargs)

        return viewset

    def _get_dynamic_viewset(self, meta, request):
        """
        Get ViewSet for dynamic metadata-driven objects.

        Args:
            meta: ObjectMeta
            request: Current HTTP request

        Returns:
            Configured MetadataDrivenViewSet instance
        """
        viewset = MetadataDrivenViewSet()
        viewset.business_object_code = meta.code
        viewset.request = request
        viewset.format_kwarg = None
        viewset.action = getattr(self, 'action', None)
        viewset.initial(request, *self.args, **self.kwargs)
        return viewset

    # Delegate all standard CRUD methods to the delegate ViewSet

    def list(self, request, *args, **kwargs):
        """
        List objects with pagination, filtering, and search.

        GET /api/objects/{code}/
        """
        return self._delegate_viewset.list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Get a single object by ID.

        GET /api/objects/{code}/{id}/
        """
        return self._delegate_viewset.retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Create a new object.

        POST /api/objects/{code}/
        """
        return self._delegate_viewset.create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Full update of an object.

        PUT /api/objects/{code}/{id}/
        """
        return self._delegate_viewset.update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Partial update of an object.

        PATCH /api/objects/{code}/{id}/
        """
        return self._delegate_viewset.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete (soft delete) an object.

        DELETE /api/objects/{code}/{id}/
        """
        return self._delegate_viewset.destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='metadata')
    def metadata(self, request, *args, **kwargs):
        """
        Get object metadata for frontend dynamic rendering.

        GET /api/objects/{code}/metadata/

        Returns field definitions, layout configurations,
        permissions, and other metadata needed for the frontend
        to dynamically render forms and lists.

        Response structure:
        {
            "success": true,
            "data": {
                "code": "Asset",
                "name": "资产卡片",
                "is_hardcoded": true,
                "fields": [...],
                "layouts": {
                    "form": {...},
                    "list": {...}
                },
                "permissions": {...}
            }
        }
        """
        # Initialize object_meta if not already done
        # This is needed because as_view() doesn't call initial() for custom actions
        if not self._object_meta:
            object_code = kwargs.get('code')

            if not object_code:
                return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)

            self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
            if not self._object_meta:
                return BaseResponse.not_found(f"Business object '{object_code}' not found")

        from apps.system.models import FieldDefinition, ModelFieldDefinition, PageLayout

        # Get field definitions from both sources:
        # 1. FieldDefinition for low-code custom fields
        # 2. ModelFieldDefinition for hardcoded Django model fields
        fields = []

        # For hardcoded objects, get fields from ModelFieldDefinition
        if self._object_meta.is_hardcoded:
            # BusinessObject uses GlobalMetadataManager (no org filtering)
            from apps.system.models import BusinessObject
            bo = BusinessObject.objects.filter(code=self._object_meta.code).first()

            model_fields = ModelFieldDefinition.objects.filter(
                business_object__code=self._object_meta.code
            ).order_by('sort_order')

            for fd in model_fields:
                # Map ModelFieldDefinition fields to common format
                # Note: ModelFieldDefinition has different field names than FieldDefinition
                fields.append({
                    'code': fd.field_name,
                    'name': fd.display_name or fd.field_name,
                    'field_type': fd.field_type,
                    'is_required': fd.is_required,
                    'is_readonly': fd.is_readonly,
                    'is_system': False,  # Model fields are not system fields
                    'is_searchable': True,  # Default to True for model fields
                    'sortable': True,  # Default to True
                    'show_in_filter': False,  # Not defined in ModelFieldDefinition
                    'show_in_list': fd.show_in_list,
                    'show_in_detail': fd.show_in_detail,
                    'sort_order': fd.sort_order,
                    'column_width': None,  # Not defined in ModelFieldDefinition
                    'min_column_width': None,  # Not defined
                    'fixed': False,  # Not defined
                    'options': None,  # Not defined
                    'placeholder': None,  # Not defined
                    'default_value': None,  # Not defined
                    'reference_object': fd.reference_model_path if fd.field_type == 'reference' else None,
                })
        else:
            # For dynamic objects, get fields from FieldDefinition
            # FieldDefinition uses GlobalMetadataManager (no org filtering)
            fields_query = FieldDefinition.objects.filter(
                business_object__code=self._object_meta.code
            ).order_by('sort_order')

            for fd in fields_query:
                fields.append({
                    'code': fd.code,
                    'name': fd.name,
                    'field_type': fd.field_type,
                    'is_required': fd.is_required,
                    'is_readonly': fd.is_readonly,
                    'is_system': fd.is_system,
                    'is_searchable': fd.is_searchable,
                    'sortable': fd.sortable,
                    'show_in_filter': fd.show_in_filter,
                    'show_in_list': fd.show_in_list,
                    'show_in_detail': fd.show_in_detail,
                    'sort_order': fd.sort_order,
                    'column_width': fd.column_width,
                    'min_column_width': fd.min_column_width,
                    'fixed': fd.fixed,
                    'options': fd.options,
                    'placeholder': fd.placeholder,
                    'default_value': fd.default_value,
                    'reference_object': fd.reference_object,
                })

        # Get layouts
        layouts = {}
        # PageLayout uses GlobalMetadataManager (no org filtering)
        layout_records = PageLayout.objects.filter(
            business_object__code=self._object_meta.code
        )

        for layout in layout_records:
            layouts[layout.layout_type] = layout.layout_config

        # Get permissions for current user
        permissions = self._get_user_permissions(request.user, self._object_meta.code)

        return BaseResponse.success({
            'code': self._object_meta.code,
            'name': self._object_meta.name,
            'is_hardcoded': self._object_meta.is_hardcoded,
            'django_model_path': self._object_meta.django_model_path,
            'enable_workflow': self._get_business_object_flag('enable_workflow'),
            'enable_version': self._get_business_object_flag('enable_version'),
            'fields': fields,
            'layouts': layouts,
            'permissions': permissions,
        })

    def _get_business_object_flag(self, flag_name: str) -> bool:
        """Get a flag value from the BusinessObject."""
        try:
            from apps.system.models import BusinessObject
            # BusinessObject uses GlobalMetadataManager (no org filtering)
            bo = BusinessObject.objects.filter(code=self._object_meta.code).first()
            if not bo:
                return False
            return getattr(bo, flag_name, False)
        except Exception:
            return False

    def _get_user_permissions(self, user, object_code: str) -> dict:
        """
        Get user permissions for this object.

        Args:
            user: Current user
            object_code: Business object code

        Returns:
            Dictionary of permission flags
        """
        # Build permission codes
        permissions = {
            'view': self._check_user_permission(user, object_code, 'view'),
            'add': self._check_user_permission(user, object_code, 'add'),
            'change': self._check_user_permission(user, object_code, 'change'),
            'delete': self._check_user_permission(user, object_code, 'delete'),
        }

        return permissions

    def _check_user_permission(self, user, object_code: str, action: str) -> bool:
        """
        Check if user has permission for an action on an object.

        Args:
            user: User instance
            object_code: Business object code
            action: Action name (view, add, change, delete)

        Returns:
            True if user has permission, False otherwise
        """
        if user.is_superuser:
            return True

        perm_code = f"{object_code.lower()}_{action}"
        return user.has_perm(perm_code)

    @action(detail=False, methods=['post'], url_path='batch-delete')
    def batch_delete(self, request, *args, **kwargs):
        """
        Batch delete objects.

        POST /api/objects/{code}/batch-delete/

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }
        """
        return self._delegate_viewset.batch_delete(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='batch-restore')
    def batch_restore(self, request, *args, **kwargs):
        """
        Batch restore soft-deleted objects.

        POST /api/objects/{code}/batch-restore/
        """
        return self._delegate_viewset.batch_restore(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='batch-update')
    def batch_update(self, request, *args, **kwargs):
        """
        Batch update objects.

        POST /api/objects/{code}/batch-update/
        """
        return self._delegate_viewset.batch_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='deleted')
    def deleted(self, request, *args, **kwargs):
        """
        List soft-deleted objects.

        GET /api/objects/{code}/deleted/
        """
        return self._delegate_viewset.deleted(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, *args, **kwargs):
        """
        Restore a soft-deleted object.

        POST /api/objects/{code}/{id}/restore/
        """
        return self._delegate_viewset.restore(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request, *args, **kwargs):
        """
        Get JSON Schema for the business object.

        GET /api/objects/{code}/schema/

        Returns a JSON Schema suitable for frontend form validation.
        """
        # Initialize object_meta if not already done
        if not self._object_meta:
            object_code = kwargs.get('code')
            if not object_code:
                return BaseResponse.error('VALIDATION_ERROR', 'object_code is required', http_status=status.HTTP_400_BAD_REQUEST)

            self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
            if not self._object_meta:
                return BaseResponse.not_found(f"Business object '{object_code}' not found")

        from apps.system.models import FieldDefinition

        fields = FieldDefinition.objects.filter(
            business_object__code=self._object_meta.code,
            is_deleted=False
        )

        properties = {}
        required = []

        type_mapping = {
            'text': 'string',
            'textarea': 'string',
            'number': 'number',
            'currency': 'number',
            'percent': 'number',
            'integer': 'integer',
            'float': 'number',
            'boolean': 'boolean',
            'date': 'string',
            'datetime': 'string',
            'email': 'string',
            'url': 'string',
            'select': 'string',
            'multi_select': 'array',
            'radio': 'string',
            'checkbox': 'boolean',
            'user': 'string',
            'department': 'string',
            'reference': 'string',
            'asset': 'string',
            'formula': 'number',
            'file': 'string',
            'image': 'string',
            'qr_code': 'string',
            'barcode': 'string',
            'location': 'object',
            'json': 'object',
        }

        for fd in fields:
            prop = {
                'type': type_mapping.get(fd.field_type, 'string'),
                'title': fd.name,
            }

            if fd.description:
                prop['description'] = fd.description

            if fd.max_length:
                prop['maxLength'] = fd.max_length

            if fd.min_value is not None:
                prop['minimum'] = float(fd.min_value)

            if fd.max_value is not None:
                prop['maximum'] = float(fd.max_value)

            if fd.field_type in ['select', 'multi_select'] and fd.options:
                if isinstance(fd.options, dict):
                    prop['enum'] = list(fd.options.keys())
                elif isinstance(fd.options, list):
                    prop['enum'] = fd.options

            if fd.field_type == 'multi_select':
                prop['items'] = {'type': 'string'}
                if 'enum' in prop:
                    prop['items']['enum'] = prop.pop('enum')

            properties[fd.code] = prop

            if fd.is_required:
                required.append(fd.code)

        return BaseResponse.success({
            'type': 'object',
            'properties': properties,
            'required': required,
        })
