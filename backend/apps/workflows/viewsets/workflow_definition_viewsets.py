"""
ViewSets for WorkflowDefinition model.

Provides CRUD operations and custom actions for workflow management.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.workflows.models.workflow_definition import WorkflowDefinition
from apps.workflows.serializers.workflow_definition_serializers import (
    WorkflowDefinitionSerializer,
    WorkflowDefinitionListSerializer,
    WorkflowDefinitionDetailSerializer,
    WorkflowDefinitionCreateSerializer,
    WorkflowDefinitionUpdateSerializer,
    WorkflowValidationSerializer,
    WorkflowPublishSerializer,
)


class WorkflowDefinitionViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for WorkflowDefinition model.

    Provides standard CRUD operations plus custom actions:
    - validate: Validate workflow graph data
    - publish: Publish workflow definition
    - unpublish: Unpublish workflow definition
    - duplicate: Clone workflow definition
    - versions: Get version history
    - by_business_object: Get workflows by business object
    """

    queryset = WorkflowDefinition.objects.filter(is_deleted=False)
    serializer_class = WorkflowDefinitionSerializer
    filterset_fields = ['status', 'is_active', 'business_object_code', 'category']
    search_fields = ['code', 'name', 'description', 'tags']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return WorkflowDefinitionListSerializer
        if self.action == 'retrieve':
            return WorkflowDefinitionDetailSerializer
        if self.action == 'create':
            return WorkflowDefinitionCreateSerializer
        return WorkflowDefinitionSerializer

    def perform_create(self, serializer):
        """Create workflow and log the operation."""
        workflow = serializer.save()
        # Log the creation
        from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
        WorkflowOperationLog.log_create(
            actor=self.request.user,
            workflow_definition=workflow,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def perform_update(self, serializer):
        """Update workflow and log the operation."""
        # Get previous state for logging
        previous_state = {
            'name': self.get_object().name,
            'description': self.get_object().description,
            'status': self.get_object().status,
        }

        workflow = serializer.save()

        # Log the update
        from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
        WorkflowOperationLog.log_update(
            actor=self.request.user,
            workflow_definition=workflow,
            changes={},
            previous_state=previous_state,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def get_client_ip(self):
        """Get client IP address from request."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=False, methods=['get'])
    def by_business_object(self, request):
        """
        Get workflows by business object code.

        Query params:
        - business_object_code: The business object code
        - is_active: Filter by active status (optional)
        - status: Filter by status (optional)
        """
        business_object_code = request.query_params.get('business_object_code')
        is_active = request.query_params.get('is_active')

        if not business_object_code:
            return Response({
                'success': False,
                'error': {
                    'code': 'MISSING_PARAM',
                    'message': _('business_object_code parameter is required.')
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(business_object_code=business_object_code)

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        if request.query_params.get('status'):
            queryset = queryset.filter(status=request.query_params.get('status'))

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """
        Validate workflow graph data.

        Validates the workflow structure including:
        - Required nodes (start, end)
        - Node ID uniqueness
        - Edge references
        - Approval node configuration
        """
        workflow = self.get_object()
        serializer = WorkflowValidationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': _('Invalid request data.'),
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        graph_data = serializer.validated_data['graph_data']
        errors = []

        try:
            # Validate structure
            nodes = graph_data.get('nodes', [])
            edges = graph_data.get('edges', [])

            # Check required nodes
            node_types = {node.get('type') for node in nodes}
            if 'start' not in node_types:
                errors.append(_('Missing required start node.'))
            if 'end' not in node_types:
                errors.append(_('Missing required end node.'))

            # Check node ID uniqueness
            node_ids = [node.get('id') for node in nodes]
            if len(node_ids) != len(set(node_ids)):
                errors.append(_('Node IDs must be unique.'))

            # Check edge references
            node_id_set = set(node_ids)
            for edge in edges:
                source = edge.get('sourceNodeId')
                target = edge.get('targetNodeId')

                if source not in node_id_set:
                    errors.append(_(f'Edge references non-existent source node: {source}'))
                if target not in node_id_set:
                    errors.append(_(f'Edge references non-existent target node: {target}'))

            # Check approval nodes have approvers
            for node in nodes:
                if node.get('type') == 'approval':
                    properties = node.get('properties', {})
                    approvers = properties.get('approvers', [])
                    if not approvers:
                        errors.append(_(f'Approval node "{node.get("id")}" has no approvers configured.'))

            # Log validation
            from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
            WorkflowOperationLog.log_validate(
                actor=request.user,
                workflow_definition=workflow,
                is_valid=len(errors) == 0,
                errors=errors
            )

            if errors:
                return Response({
                    'success': False,
                    'message': _('Workflow validation failed.'),
                    'errors': errors
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'success': True,
                'message': _('Workflow validation passed.')
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': _('Validation error occurred.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Publish the workflow definition.

        Makes the workflow available for use.
        Increments version if already published.
        """
        workflow = self.get_object()
        serializer = WorkflowPublishSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': _('Invalid request data.'),
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        if workflow.status == 'published' and not serializer.validated_data.get('force', False):
            return Response({
                'success': False,
                'message': _('Workflow is already published.'),
                'error': {
                    'code': 'ALREADY_PUBLISHED',
                    'message': _('Set force=true to create a new version.')
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # If already published, create new version
            if workflow.status == 'published':
                workflow.version += 1

            workflow.status = 'published'
            workflow.published_at = timezone.now()
            workflow.published_by = request.user
            workflow.save()

            # Log publish
            from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
            WorkflowOperationLog.log_publish(
                actor=request.user,
                workflow_definition=workflow
            )

            return Response({
                'success': True,
                'message': _('Workflow published successfully.'),
                'data': {
                    'id': str(workflow.id),
                    'version': workflow.version,
                    'status': workflow.status,
                    'published_at': workflow.published_at.isoformat() if workflow.published_at else None
                }
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': _('Failed to publish workflow.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """
        Unpublish the workflow definition.

        Makes the workflow unavailable for new instances.
        """
        workflow = self.get_object()

        if workflow.status != 'published':
            return Response({
                'success': False,
                'message': _('Workflow is not published.')
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            workflow.status = 'draft'
            workflow.save()

            return Response({
                'success': True,
                'message': _('Workflow unpublished successfully.'),
                'data': {
                    'id': str(workflow.id),
                    'status': workflow.status
                }
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': _('Failed to unpublish workflow.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate/clone the workflow definition.

        Creates a copy of the workflow with a new code.
        """
        workflow = self.get_object()

        try:
            cloned = workflow.clone(
                new_name=request.data.get('name', f'{workflow.name} (copy)'),
                new_code=request.data.get('code', f'{workflow.code}_copy')
            )

            # Log duplication
            from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
            WorkflowOperationLog.log_duplicate(
                actor=request.user,
                source_workflow=workflow,
                new_workflow=cloned
            )

            serializer = self.get_serializer(cloned)
            return Response({
                'success': True,
                'message': _('Workflow duplicated successfully.'),
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'message': _('Failed to duplicate workflow.'),
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """
        Get version history of the workflow.

        Returns all versions of workflows with the same code.
        """
        workflow = self.get_object()

        # Get all workflows with same base code
        versions = WorkflowDefinition.objects.filter(
            code=workflow.code,
            is_deleted=False
        ).order_by('-version')

        serializer = WorkflowDefinitionListSerializer(versions, many=True)
        return Response({
            'success': True,
            'data': {
                'current_version': workflow.version,
                'versions': serializer.data
            }
        })

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Get all workflow categories.

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

    @action(detail=False, methods=['get'])
    def business_objects(self, request):
        """
        Get all business objects that have workflows.

        Returns distinct business_object_code values.
        """
        business_objects = self.queryset.values_list(
            'business_object_code', flat=True
        ).distinct()

        return Response({
            'success': True,
            'data': {
                'business_objects': sorted(business_objects)
            }
        })
