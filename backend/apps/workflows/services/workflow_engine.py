"""
Workflow Execution Engine

Core engine for executing workflow definitions and managing workflow instances.
Handles node traversal, task creation, and workflow state transitions.
"""
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

import uuid
from collections import deque

from apps.workflows.models import (
    WorkflowDefinition, WorkflowInstance, WorkflowTask, WorkflowApproval
)
from apps.workflows.services.approver_resolver import ApproverResolver
from apps.workflows.services.condition_evaluator import ConditionEvaluator


class WorkflowEngine:
    """
    Workflow Execution Engine.

    Manages the execution of workflow instances:
    - Starting workflows from definitions
    - Processing node transitions
    - Creating and managing tasks
    - Evaluating conditions
    - Completing workflows

    The engine processes LogicFlow graph definitions and manages
    the lifecycle of workflow instances through their various states.
    """

    def __init__(self, definition=None):
        """
        Initialize the workflow engine.

        Args:
            definition: Optional WorkflowDefinition to execute
        """
        self.definition = definition
        self.approver_resolver = ApproverResolver()
        self.condition_evaluator = ConditionEvaluator()

    def start_workflow(self, definition, business_object_code, business_id,
                      business_no=None, initiator=None, variables=None,
                      title=None, description=None, priority='normal'):
        """
        Start a new workflow instance from a definition.

        Args:
            definition: The WorkflowDefinition to execute
            business_object_code: Type of business object (e.g., 'asset_pickup')
            business_id: ID of the business data
            business_no: Optional business document number
            initiator: User starting the workflow
            variables: Initial workflow variables
            title: Optional title for the instance
            description: Optional description
            priority: Priority level (low, normal, high, urgent)

        Returns:
            tuple: (success: bool, instance: WorkflowInstance or None, error: str or None)

        Raises:
            ValueError: If definition is not valid for starting
        """
        # Validate definition
        if definition.status != 'published':
            return False, None, _('Only published workflows can be started.')

        # Validate graph structure
        from apps.workflows.services.workflow_validation import WorkflowValidationService
        validator = WorkflowValidationService()
        is_valid, errors, warnings = validator.validate(definition.graph_data)
        if not is_valid:
            return False, None, _('Workflow definition is invalid: %(errors)s') % {
                'errors': '; '.join(errors)
            }

        try:
            with transaction.atomic():
                # Generate instance number
                instance_no = self._generate_instance_no(definition)

                # Get start node
                graph_data = definition.graph_data
                nodes = graph_data.get('nodes', [])
                start_node = next((n for n in nodes if n.get('type') == 'start'), None)

                if not start_node:
                    return False, None, _('Workflow must have a start node.')

                # Create workflow instance
                instance = WorkflowInstance.objects.create(
                    definition=definition,
                    instance_no=instance_no,
                    business_object_code=business_object_code,
                    business_id=business_id,
                    business_no=business_no,
                    initiator=initiator,
                    status=WorkflowInstance.STATUS_RUNNING,
                    variables=variables or {},
                    graph_snapshot=graph_data,
                    title=title,
                    description=description,
                    priority=priority,
                    started_at=timezone.now(),
                    organization=definition.organization,
                    created_by=initiator
                )

                # Log the start
                from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
                WorkflowOperationLog.log_operation(
                    operation_type='start',
                    actor=initiator,
                    workflow_instance=instance,
                    result='success',
                    details={'business_object': business_object_code, 'business_id': business_id},
                    organization=instance.organization
                )

                # Get next nodes after start
                next_nodes = self._get_next_nodes(graph_data, start_node['id'])

                # Create tasks for next nodes
                self._create_tasks_for_nodes(instance, next_nodes, graph_data)

                # Update instance progress
                instance.update_progress()

                # Update current node
                if next_nodes:
                    instance.current_node_id = next_nodes[0]['id']
                    instance.current_node_name = next_nodes[0].get('text', next_nodes[0]['id'])
                    instance.save(update_fields=['current_node_id', 'current_node_name', 'updated_at'])

                # Check if workflow completes immediately (no approval nodes)
                if not instance.tasks.filter(status='pending').exists():
                    instance.complete()
                else:
                    instance.status = WorkflowInstance.STATUS_PENDING_APPROVAL
                    instance.save(update_fields=['status', 'updated_at'])

                return True, instance, None

        except Exception as e:
            return False, None, _('Failed to start workflow: %(error)s') % {'error': str(e)}

    def execute_task(self, task, action, actor, comment=None):
        """
        Execute a task (approve, reject, return).

        Args:
            task: The WorkflowTask to execute
            action: The action to take ('approve', 'reject', 'return')
            actor: User performing the action
            comment: Optional comment

        Returns:
            tuple: (success: bool, instance: WorkflowInstance or None, error: str or None)
        """
        # Validate task state
        if task.status != WorkflowTask.STATUS_PENDING:
            return False, None, _('Task is not pending.')

        # Validate user is the assignee
        if task.assignee != actor:
            return False, None, _('You are not authorized to perform this action.')

        instance = task.instance

        try:
            with transaction.atomic():
                # Get node info
                graph_data = instance.graph_snapshot
                node = self._get_node_by_id(graph_data, task.node_id)

                if not node:
                    return False, None, _('Node not found in workflow graph.')

                # Execute action based on type
                if action == 'approve':
                    approval = task.approve(actor, comment)
                elif action == 'reject':
                    approval = task.reject(actor, comment)
                    # Rejecting terminates the workflow
                    instance.reject(comment)
                    return True, instance, None
                elif action == 'return':
                    approval = task.return_task(actor, comment)
                    # Return sends workflow back to previous state
                    return self._handle_return_task(instance, task, actor, comment)
                else:
                    return False, None, _('Invalid action: %(action)s') % {'action': action}

                # Check if all tasks for this node are complete
                node_tasks = instance.tasks.filter(node_id=task.node_id)
                approve_type = node.get('properties', {}).get('approveType', 'or')

                should_proceed = self._should_proceed_after_task(node_tasks, approve_type)

                if should_proceed:
                    # Get next nodes
                    next_nodes = self._get_next_nodes(graph_data, task.node_id)

                    if not next_nodes:
                        # No more nodes, workflow is complete
                        instance.complete()
                    else:
                        # Process next nodes
                        pending_created = self._process_next_nodes(
                            instance, next_nodes, graph_data, task.node_id
                        )

                        if not pending_created:
                            # No pending tasks created, workflow complete
                            instance.complete()
                        else:
                            instance.update_progress()

                else:
                    # Update progress but stay in pending status
                    instance.update_progress()

                return True, instance, None

        except Exception as e:
            return False, None, _('Failed to execute task: %(error)s') % {'error': str(e)}

    def withdraw_instance(self, instance, user):
        """
        Withdraw a workflow instance.

        Args:
            instance: The WorkflowInstance to withdraw
            user: User withdrawing the workflow

        Returns:
            tuple: (success: bool, error: str or None)
        """
        # Validate user is the initiator
        if instance.initiator != user:
            return False, _('Only the initiator can withdraw the workflow.')

        # Validate instance can be withdrawn
        if instance.status not in instance.ACTIVE_STATUSES:
            return False, _('Workflow cannot be withdrawn in current status.')

        try:
            instance.cancel(user)
            return True, None
        except Exception as e:
            return False, _('Failed to withdraw workflow: %(error)s') % {'error': str(e)}

    def terminate_instance(self, instance, user, reason=None):
        """
        Terminate a workflow instance (admin action).

        Args:
            instance: The WorkflowInstance to terminate
            user: User terminating the workflow (should be admin)
            reason: Optional reason for termination

        Returns:
            tuple: (success: bool, error: str or None)
        """
        try:
            instance.terminate(user, reason)
            return True, None
        except Exception as e:
            return False, _('Failed to terminate workflow: %(error)s') % {'error': str(e)}

    def reassign_task(self, task, new_assignee, actor, reason=None):
        """
        Reassign a task to a different user.

        Args:
            task: The WorkflowTask to reassign
            new_assignee: User to assign the task to
            actor: User performing the reassignment
            reason: Optional reason for reassignment

        Returns:
            tuple: (success: bool, error: str or None)
        """
        if task.status != WorkflowTask.STATUS_PENDING:
            return False, _('Can only reassign pending tasks.')

        try:
            old_assignee = task.assignee
            task.assignee = new_assignee
            task.save(update_fields=['assignee', 'updated_at'])

            # Log the reassignment
            from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
            WorkflowOperationLog.log_operation(
                operation_type='delegate',
                actor=actor,
                workflow_instance=task.instance,
                workflow_task=task,
                result='success',
                details={
                    'from': old_assignee.get_full_name() or old_assignee.username,
                    'to': new_assignee.get_full_name() or new_assignee.username,
                    'reason': reason
                },
                organization=task.organization
            )

            return True, None
        except Exception as e:
            return False, _('Failed to reassign task: %(error)s') % {'error': str(e)}

    # === Private Helper Methods ===

    def _generate_instance_no(self, definition):
        """Generate a unique instance number."""
        prefix = definition.business_object_code.upper()[:3]
        timestamp = timezone.now().strftime('%Y%m%d')
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f'WI-{prefix}-{timestamp}-{random_suffix}'

    def _get_node_by_id(self, graph_data, node_id):
        """Get a node from graph data by ID."""
        nodes = graph_data.get('nodes', [])
        return next((n for n in nodes if n.get('id') == node_id), None)

    def _get_next_nodes(self, graph_data, node_id):
        """Get the next nodes after a given node."""
        edges = graph_data.get('edges', [])
        next_node_ids = [
            e.get('targetNodeId') for e in edges
            if e.get('sourceNodeId') == node_id
        ]

        nodes = graph_data.get('nodes', [])
        return [n for n in nodes if n.get('id') in next_node_ids]

    def _create_tasks_for_nodes(self, instance, nodes, graph_data):
        """Create workflow tasks for the given nodes."""
        for node in nodes:
            node_type = node.get('type')

            if node_type == 'end':
                # End node, no task needed
                continue

            elif node_type == 'approval':
                # Create approval task(s)
                self._create_approval_tasks(instance, node, graph_data)

            elif node_type == 'condition':
                # Evaluate condition and create tasks for matching branch
                self._process_condition_node(instance, node, graph_data)

            elif node_type == 'cc':
                # Carbon copy - create notification task
                self._create_cc_tasks(instance, node, graph_data)

            elif node_type == 'parallel':
                # Parallel gateway - create tasks for all branches
                self._process_parallel_node(instance, node, graph_data)

            elif node_type == 'notify':
                # Notification - no task needed, just log
                continue

    def _create_approval_tasks(self, instance, node, graph_data):
        """Create approval tasks for an approval node."""
        properties = node.get('properties', {})
        approve_type = properties.get('approveType', 'or')
        approvers_config = properties.get('approvers', [])

        # Resolve approvers
        assignees = self.approver_resolver.resolve(
            approvers_config, instance, graph_data
        )

        if not assignees:
            # No assignees found, skip this node
            return

        # Determine task creation strategy based on approve type
        if approve_type == 'or':
            # Create task for first assignee only
            self._create_single_task(instance, node, assignees[0], approve_type)
        elif approve_type == 'and':
            # Create task for all assignees
            for assignee in assignees:
                self._create_single_task(instance, node, assignee, approve_type)
        elif approve_type == 'sequence':
            # Create tasks in sequence with sequence numbers
            for idx, assignee in enumerate(assignees):
                self._create_single_task(
                    instance, node, assignee, approve_type, sequence=idx
                )

    def _create_single_task(self, instance, node, assignee, approve_type, sequence=0):
        """Create a single workflow task."""
        properties = node.get('properties', {})
        timeout_hours = properties.get('timeout', 72)

        # Calculate due date
        due_date = None
        if timeout_hours:
            due_date = timezone.now() + timezone.timedelta(hours=timeout_hours)

        task = WorkflowTask.objects.create(
            instance=instance,
            node_id=node['id'],
            node_name=node.get('text', node['id']),
            node_type=node.get('type', 'approval'),
            approve_type=approve_type,
            assignee=assignee,
            sequence=sequence,
            due_date=due_date,
            status=WorkflowTask.STATUS_PENDING,
            node_properties=properties,
            organization=instance.organization
        )

        return task

    def _create_cc_tasks(self, instance, node, graph_data):
        """Create carbon copy tasks (for informational purposes)."""
        properties = node.get('properties', {})
        cc_users_config = properties.get('ccUsers', [])

        assignees = self.approver_resolver.resolve(
            cc_users_config, instance, graph_data
        )

        for assignee in assignees:
            # CC tasks are just for notification, no approval needed
            # They auto-complete
            task = WorkflowTask.objects.create(
                instance=instance,
                node_id=node['id'],
                node_name=node.get('text', node['id']),
                node_type='cc',
                approve_type='or',
                assignee=assignee,
                status=WorkflowTask.STATUS_APPROVED,  # Auto-complete
                completed_at=timezone.now(),
                node_properties=properties,
                organization=instance.organization
            )

    def _process_condition_node(self, instance, node, graph_data):
        """Process a condition node and create tasks for matching branches."""
        properties = node.get('properties', {})
        branches = properties.get('branches', [])

        # Evaluate each branch
        for branch in branches:
            conditions = branch.get('conditions', [])
            if self.condition_evaluator.evaluate_conditions(conditions, instance):
                # Branch matched, get next nodes for this branch
                # Find edges from this condition node that have the branch ID
                edges = graph_data.get('edges', [])
                branch_edges = [
                    e for e in edges
                    if e.get('sourceNodeId') == node['id'] and
                    e.get('properties', {}).get('branchId') == branch.get('id')
                ]

                for edge in branch_edges:
                    next_node = self._get_node_by_id(graph_data, edge.get('targetNodeId'))
                    if next_node:
                        self._create_tasks_for_nodes(instance, [next_node], graph_data)

                return True  # Branch found and processed

        # No branch matched, check for default flow
        if properties.get('defaultFlow'):
            # Use first edge as default
            edges = self._get_next_nodes(graph_data, node['id'])
            if edges:
                self._create_tasks_for_nodes(instance, [edges[0]], graph_data)
                return True

        return False

    def _process_parallel_node(self, instance, node, graph_data):
        """Process a parallel gateway node."""
        # Get all next nodes and create tasks for all
        next_nodes = self._get_next_nodes(graph_data, node['id'])
        for next_node in next_nodes:
            self._create_tasks_for_nodes(instance, [next_node], graph_data)

    def _process_next_nodes(self, instance, next_nodes, graph_data, current_node_id):
        """Process next nodes and return True if pending tasks were created."""
        for node in next_nodes:
            node_type = node.get('type')

            if node_type == 'end':
                # End node, workflow completes
                continue

            elif node_type == 'approval':
                # Create approval tasks
                self._create_approval_tasks(instance, node, graph_data)

            elif node_type == 'condition':
                # Process condition
                self._process_condition_node(instance, node, graph_data)

            elif node_type == 'cc':
                # Create CC tasks
                self._create_cc_tasks(instance, node, graph_data)

            elif node_type == 'parallel':
                # Process parallel
                self._process_parallel_node(instance, node, graph_data)

        # Check if any pending tasks were created
        return instance.tasks.filter(status='pending').exists()

    def _should_proceed_after_task(self, node_tasks, approve_type):
        """Check if workflow should proceed after a task completion."""
        if approve_type == 'or':
            # Any approval allows proceeding
            approved_count = node_tasks.filter(status=WorkflowTask.STATUS_APPROVED).count()
            return approved_count >= 1

        elif approve_type == 'and':
            # All must approve (and none rejected)
            total_count = node_tasks.count()
            approved_count = node_tasks.filter(status=WorkflowTask.STATUS_APPROVED).count()
            rejected_count = node_tasks.filter(status=WorkflowTask.STATUS_REJECTED).count()
            return approved_count == total_count and rejected_count == 0

        elif approve_type == 'sequence':
            # Current task must be approved
            # Get tasks ordered by sequence
            approved_tasks = node_tasks.filter(status=WorkflowTask.STATUS_APPROVED).order_by('sequence')
            if approved_tasks.count() == 0:
                return False

            # Check if we have consecutive approvals
            sequences = list(approved_tasks.values_list('sequence', flat=True))
            for i, seq in enumerate(sorted(sequences)):
                if seq != i:
                    return False
            return True

        return False

    def _handle_return_task(self, instance, task, actor, comment):
        """Handle a returned task by going back to previous state."""
        # Find the previous approval node
        graph_data = instance.graph_snapshot
        current_edges = [
            e for e in graph_data.get('edges', [])
            if e.get('targetNodeId') == task.node_id
        ]

        if not current_edges:
            return False, None, _('Cannot return: no previous node found.')

        # Get previous node
        prev_node_id = current_edges[0].get('sourceNodeId')
        prev_node = self._get_node_by_id(graph_data, prev_node_id)

        if not prev_node or prev_node.get('type') != 'approval':
            return False, None, _('Cannot return: previous node is not an approval node.')

        # Reset previous tasks to pending
        prev_tasks = instance.tasks.filter(node_id=prev_node_id)
        prev_tasks.update(
            status=WorkflowTask.STATUS_PENDING,
            completed_at=None,
            completed_by=None
        )

        # Update instance status
        instance.status = WorkflowInstance.STATUS_PENDING_APPROVAL
        instance.current_node_id = prev_node_id
        instance.current_node_name = prev_node.get('text', prev_node_id)
        instance.save(update_fields=['status', 'current_node_id', 'current_node_name', 'updated_at'])

        # Recalculate progress
        instance.update_progress()

        return True, instance, None
