"""
ViewSets for WorkflowTemplate model.

Provides CRUD operations and custom actions for template management.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.workflows.models.workflow_template import WorkflowTemplate
from apps.workflows.serializers.workflow_template_serializers import (
    WorkflowTemplateSerializer,
    WorkflowTemplateListSerializer,
    WorkflowTemplateDetailSerializer,
    WorkflowTemplateInstantiateSerializer,
)


class WorkflowTemplateViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for WorkflowTemplate model.

    Provides standard CRUD operations plus custom actions:
    - instantiate: Create a workflow from this template
    - featured: Get featured templates
    - by_business_object: Get templates by business object
    """

    queryset = WorkflowTemplate.objects.filter(is_deleted=False)
    serializer_class = WorkflowTemplateSerializer
    filterset_fields = ['template_type', 'business_object_code', 'category', 'is_featured', 'is_public']
    search_fields = ['code', 'name', 'description', 'tags']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return WorkflowTemplateListSerializer
        if self.action == 'retrieve':
            return WorkflowTemplateDetailSerializer
        return WorkflowTemplateSerializer

    def perform_create(self, serializer):
        """Create template and log the operation."""
        template = serializer.save()
        # Increment usage count if from another template
        # (handled by model's instantiate method)

    @action(detail=True, methods=['post'])
    def instantiate(self, request, pk=None):
        """
        Create a new WorkflowDefinition from this template.

        Request body:
        - name: Optional name for the new workflow
        - code: Optional code for the new workflow

        Returns the created workflow definition.
        """
        template = self.get_object()
        serializer = WorkflowTemplateInstantiateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': _('Invalid request data.'),
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            workflow = template.instantiate(
                organization=request.user.organization,
                user=request.user,
                name=serializer.validated_data.get('name'),
                code=serializer.validated_data.get('code')
            )

            from apps.workflows.serializers.workflow_definition_serializers import WorkflowDefinitionDetailSerializer
            workflow_serializer = WorkflowDefinitionDetailSerializer(workflow)

            return Response({
                'success': True,
                'message': _('Workflow created from template successfully.'),
                'data': workflow_serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'message': _('Failed to create workflow from template.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured workflow templates.

        Returns templates marked as featured or most used.
        Limit: 10 templates
        """
        business_object_code = request.query_params.get('business_object_code')

        queryset = self.queryset.filter(is_featured=True)

        if business_object_code:
            queryset = queryset.filter(business_object_code=business_object_code)

        queryset = queryset.order_by('-sort_order', '-usage_count')[:10]

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def by_business_object(self, request):
        """
        Get templates by business object code.

        Query params:
        - business_object_code: The business object code
        - template_type: Filter by template type (optional)
        """
        business_object_code = request.query_params.get('business_object_code')

        if not business_object_code:
            return Response({
                'success': False,
                'error': {
                    'code': 'MISSING_PARAM',
                    'message': _('business_object_code parameter is required.')
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(business_object_code=business_object_code)

        if request.query_params.get('template_type'):
            queryset = queryset.filter(template_type=request.query_params.get('template_type'))

        if request.query_params.get('is_public'):
            queryset = queryset.filter(is_public=request.query_params.get('is_public').lower() == 'true')

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Get all template categories.

        Returns distinct category values.
        """
        categories = self.queryset.values_list('category', flat=True).distinct()
        categories = [c for c in categories if c]  # Filter out empty strings

        return Response({
            'success': True,
            'data': {
                'categories': sorted(categories)
            }
        })
