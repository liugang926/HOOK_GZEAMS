"""
Create or refresh demo workflow definition data.

Usage:
    python manage.py create_workflow_demo
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.organizations.models import Organization
from apps.workflows.models import WorkflowDefinition

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update the demo asset approval workflow definition'

    workflow_code = 'asset-approval'

    def handle(self, *args, **options):
        """Create the demo workflow definition."""
        existing_workflow = WorkflowDefinition.all_objects.filter(
            code=self.workflow_code
        ).select_related('organization', 'created_by').first()

        organization = self._get_target_organization(existing_workflow)
        creator = self._get_creator(organization, existing_workflow)
        approver_users = self._get_approver_users(organization, creator)

        graph_data = self._build_graph_data(approver_users)
        workflow = self._build_workflow_instance(
            organization=organization,
            creator=creator,
            graph_data=graph_data,
            existing_workflow=existing_workflow,
        )

        with transaction.atomic():
            workflow.full_clean()
            workflow.save()

        action = 'Created' if existing_workflow is None else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} workflow definition "{workflow.code}" (ID: {workflow.id}).'
            )
        )
        self.stdout.write(f'Organization: {self._format_organization(workflow.organization)}')
        self.stdout.write(f'Creator: {self._format_user(creator)}')
        self.stdout.write(
            'Approval assignees: '
            f'department={self._format_user(approver_users["department"])}, '
            f'finance={self._format_user(approver_users["finance"])}, '
            f'general_manager={self._format_user(approver_users["general_manager"])}'
        )

    def _get_target_organization(self, existing_workflow):
        """Resolve the organization for the workflow definition."""
        if existing_workflow and existing_workflow.organization:
            return existing_workflow.organization

        organization = Organization.objects.filter(
            is_deleted=False,
            is_active=True,
        ).order_by('created_at', 'id').first()

        if organization:
            return organization

        raise CommandError('No active organization found. Please create an organization first.')

    def _get_creator(self, organization, existing_workflow):
        """Resolve the workflow creator."""
        if existing_workflow and existing_workflow.created_by:
            return existing_workflow.created_by

        if organization:
            user = self._get_organization_users(organization).first()
            if user:
                return user

        return User.objects.filter(
            is_active=True,
            is_deleted=False,
        ).order_by('date_joined', 'id').first()

    def _get_organization_users(self, organization):
        """Get active users that belong to the given organization."""
        if not organization:
            return User.objects.none()

        return User.objects.filter(
            Q(user_orgs__organization=organization, user_orgs__is_active=True)
            | Q(current_organization=organization)
            | Q(organization=organization),
            is_active=True,
            is_deleted=False,
        ).distinct().order_by('date_joined', 'id')

    def _get_approver_users(self, organization, creator):
        """Select users for the three approval steps."""
        users = list(self._get_organization_users(organization))

        if creator and all(user.id != creator.id for user in users):
            users.insert(0, creator)

        return {
            'department': self._pick_user(users, index=0, fallback=creator),
            'finance': self._pick_user(users, index=1, fallback=creator),
            'general_manager': self._pick_user(users, index=2, fallback=creator),
        }

    def _pick_user(self, users, index, fallback):
        """Pick a user by index, reusing the last available user when needed."""
        if users:
            if index < len(users):
                return users[index]
            return users[-1]
        return fallback

    def _build_graph_data(self, approver_users):
        """Build LogicFlow-compatible demo graph data."""
        return {
            'nodes': [
                {
                    'id': 'start_1',
                    'type': 'start',
                    'x': 120,
                    'y': 180,
                    'text': 'Start',
                },
                {
                    'id': 'department_approval_1',
                    'type': 'approval',
                    'x': 320,
                    'y': 180,
                    'text': 'Department Approval',
                    'properties': {
                        'approveType': 'or',
                        'approvers': self._build_approver_config(
                            approver_users['department'],
                            'department_approver_ids',
                        ),
                        'timeout': 48,
                    },
                },
                {
                    'id': 'finance_approval_1',
                    'type': 'approval',
                    'x': 520,
                    'y': 180,
                    'text': 'Finance Approval',
                    'properties': {
                        'approveType': 'or',
                        'approvers': self._build_approver_config(
                            approver_users['finance'],
                            'finance_approver_ids',
                        ),
                        'timeout': 48,
                    },
                },
                {
                    'id': 'general_manager_approval_1',
                    'type': 'approval',
                    'x': 720,
                    'y': 180,
                    'text': 'General Manager Approval',
                    'properties': {
                        'approveType': 'or',
                        'approvers': self._build_approver_config(
                            approver_users['general_manager'],
                            'general_manager_approver_ids',
                        ),
                        'timeout': 72,
                    },
                },
                {
                    'id': 'end_1',
                    'type': 'end',
                    'x': 920,
                    'y': 180,
                    'text': 'End',
                },
            ],
            'edges': [
                {
                    'id': 'edge_start_department',
                    'sourceNodeId': 'start_1',
                    'targetNodeId': 'department_approval_1',
                    'type': 'polyline',
                    'properties': {},
                },
                {
                    'id': 'edge_department_finance',
                    'sourceNodeId': 'department_approval_1',
                    'targetNodeId': 'finance_approval_1',
                    'type': 'polyline',
                    'properties': {},
                },
                {
                    'id': 'edge_finance_general_manager',
                    'sourceNodeId': 'finance_approval_1',
                    'targetNodeId': 'general_manager_approval_1',
                    'type': 'polyline',
                    'properties': {},
                },
                {
                    'id': 'edge_general_manager_end',
                    'sourceNodeId': 'general_manager_approval_1',
                    'targetNodeId': 'end_1',
                    'type': 'polyline',
                    'properties': {},
                },
            ],
        }

    def _build_approver_config(self, user, select_key):
        """Build approver configuration for a node."""
        if user:
            return [{'type': 'user', 'user_id': str(user.id)}]
        return [{'type': 'self_select', 'selectKey': select_key}]

    def _build_workflow_instance(self, organization, creator, graph_data, existing_workflow):
        """Create or update the workflow definition instance in memory."""
        workflow = existing_workflow or WorkflowDefinition(code=self.workflow_code)
        now = timezone.now()
        published_at = workflow.published_at or now

        workflow.organization = workflow.organization or organization
        workflow.created_by = workflow.created_by or creator
        workflow.updated_by = creator
        workflow.code = self.workflow_code
        workflow.name = 'Asset Approval Demo'
        workflow.description = (
            'Demo workflow definition for asset approval with department, finance, '
            'and general manager approval steps.'
        )
        workflow.business_object_code = 'asset'
        workflow.graph_data = graph_data
        workflow.form_permissions = {
            'department_approval_1': {
                'asset_name': 'read_only',
                'department': 'editable',
                'amount': 'editable',
                'remarks': 'editable',
            },
            'finance_approval_1': {
                'asset_name': 'read_only',
                'department': 'read_only',
                'amount': 'editable',
                'remarks': 'editable',
            },
            'general_manager_approval_1': {
                'asset_name': 'read_only',
                'department': 'read_only',
                'amount': 'read_only',
                'remarks': 'editable',
            },
        }
        workflow.status = 'published'
        workflow.version = workflow.version or 1
        workflow.is_active = True
        workflow.published_at = published_at
        workflow.published_by = creator
        workflow.category = 'Demo'
        workflow.tags = ['demo', 'asset', 'approval']
        workflow.is_deleted = False
        workflow.deleted_at = None
        workflow.deleted_by = None

        return workflow

    def _format_organization(self, organization):
        """Format organization information for console output."""
        if not organization:
            return 'None'
        return f'{organization.name} ({organization.code})'

    def _format_user(self, user):
        """Format user information for console output."""
        if not user:
            return 'self_select'
        return user.get_full_name() or user.username
