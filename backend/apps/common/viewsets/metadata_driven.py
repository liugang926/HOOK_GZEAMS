"""
Metadata-driven ViewSet for zero-code CRUD API.

Dynamically generates ViewSet based on BusinessObject configuration.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from typing import Optional, Type
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist

from apps.common.serializers.metadata_driven import MetadataDrivenSerializer, DynamicDataSerializer
from apps.common.viewsets.base import BaseModelViewSet, BatchOperationMixin
from apps.common.responses.base import BaseResponse


class MetadataDrivenViewSet(BatchOperationMixin, viewsets.ModelViewSet):
    """
    ViewSet that dynamically configures itself from BusinessObject metadata.

    Features:
    - Dynamic serializer generation
    - Auto-configured search/filter/ordering
    - Support for DynamicData or traditional models
    - Metadata endpoint for frontend

    Usage:
        # In urls.py
        router.register(
            r'dynamic/(?P<object_code>\w+)',
            MetadataDrivenViewSet,
            basename='dynamic'
        )
    """

    # Runtime configuration
    business_object_code: Optional[str] = None
    _business_object = None
    _field_definitions = None

    # Search and filter configuration (auto-populated)
    search_fields = []
    filterset_fields = []
    ordering_fields = []
    ordering = ['-created_at']

    def initial(self, request, *args, **kwargs):
        """Initialize ViewSet with business object metadata."""
        super().initial(request, *args, **kwargs)

        # Get business object code from URL
        object_code = kwargs.get('object_code') or self.business_object_code
        if object_code:
            self._load_metadata(object_code)

    def _load_metadata(self, object_code: str):
        """Load metadata for the business object."""
        try:
            from apps.system.models import BusinessObject
            self._business_object = BusinessObject.objects.get(
                code=object_code,
                is_active=True
            )
            self._field_definitions = self._business_object.field_definitions.filter(
                is_active=True
            ).order_by('sort_order')

            # Configure search fields
            self.search_fields = [
                f'custom_fields__{fd.code}'
                for fd in self._field_definitions
                if fd.is_searchable
            ]

            # Configure ordering fields
            self.ordering_fields = [
                fd.code for fd in self._field_definitions
                if fd.sortable
            ]

            # Set default ordering from business object
            if self._business_object.default_ordering:
                self.ordering = [self._business_object.default_ordering]

        except ObjectDoesNotExist:
            pass

    def get_queryset(self) -> QuerySet:
        """Get queryset for DynamicData filtered by business object."""
        from apps.system.models import DynamicData

        if not self._business_object:
            return DynamicData.objects.none()

        queryset = DynamicData.objects.filter(
            business_object=self._business_object,
            is_deleted=False
        ).select_related('organization', 'created_by')

        # Apply organization filter from middleware
        org_id = getattr(self.request, 'organization_id', None)
        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        return queryset

    def get_serializer_class(self) -> Type[MetadataDrivenSerializer]:
        """Get dynamically generated serializer class."""
        if not self._business_object:
            return DynamicDataSerializer

        layout_type = 'list' if self.action == 'list' else 'form'
        return DynamicDataSerializer.for_business_object(
            self._business_object.code,
            layout_type=layout_type
        )

    def perform_create(self, serializer):
        """Set organization, user, and business object on create."""
        org_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            business_object=self._business_object,
            organization_id=org_id,
            created_by=self.request.user
        )

    @action(detail=False, methods=['get'])
    def metadata(self, request, **kwargs):
        """
        Get metadata for the business object.

        Returns field definitions and layout configurations
        for frontend form/list rendering.
        """
        if not self._business_object:
            return BaseResponse.not_found('BusinessObject')

        # Build field definitions
        fields = []
        for fd in self._field_definitions:
            fields.append({
                'code': fd.code,
                'name': fd.name,
                'field_type': fd.field_type,
                'is_required': fd.is_required,
                'is_readonly': fd.is_readonly,
                'is_searchable': fd.is_searchable,
                'sortable': fd.sortable,
                'show_in_filter': fd.show_in_filter,
                'options': fd.options,
                'placeholder': fd.placeholder,
                'description': fd.description,
                'default_value': fd.default_value,
                'max_length': fd.max_length,
                'min_value': str(fd.min_value) if fd.min_value else None,
                'max_value': str(fd.max_value) if fd.max_value else None,
            })

        # Get layouts
        list_layout = None
        form_layout = None

        try:
            from apps.system.models import PageLayout
            layouts = PageLayout.objects.filter(
                business_object=self._business_object,
                is_deleted=False
            )
            for layout in layouts:
                if layout.layout_type == 'list':
                    list_layout = layout.layout_config
                elif layout.layout_type == 'form':
                    form_layout = layout.layout_config
        except Exception:
            pass

        return BaseResponse.success({
            'business_object': {
                'id': str(self._business_object.id),
                'code': self._business_object.code,
                'name': self._business_object.name,
                'description': self._business_object.description,
                'enable_workflow': self._business_object.enable_workflow,
                'enable_version': getattr(self._business_object, 'enable_version', False),
            },
            'field_definitions': fields,
            'list_layout': list_layout,
            'form_layout': form_layout,
        })

    @action(detail=False, methods=['get'])
    def schema(self, request, **kwargs):
        """
        Get JSON Schema for the business object.

        Useful for frontend form validation.
        """
        if not self._business_object:
            return BaseResponse.not_found('BusinessObject')

        properties = {}
        required = []

        type_mapping = {
            'text': 'string',
            'textarea': 'string',
            'number': 'number',
            'integer': 'integer',
            'float': 'number',
            'boolean': 'boolean',
            'date': 'string',
            'datetime': 'string',
            'email': 'string',
            'url': 'string',
            'choice': 'string',
            'multi_choice': 'array',
            'reference': 'string',
            'user': 'string',
            'department': 'string',
            'json': 'object',
        }

        for fd in self._field_definitions:
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

            if fd.field_type in ['choice', 'multi_choice'] and fd.options:
                if isinstance(fd.options, dict):
                    prop['enum'] = list(fd.options.keys())
                elif isinstance(fd.options, list):
                    prop['enum'] = fd.options

            if fd.field_type == 'multi_choice':
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
