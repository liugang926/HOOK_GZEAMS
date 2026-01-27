"""
Maintenance Services

Business services for maintenance operations including:
- CRUD operations via BaseCRUDService
- Maintenance workflow management
- Maintenance plan scheduling
- Task generation and execution
"""
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
from apps.common.services.base_crud import BaseCRUDService
from apps.lifecycle.models import (
    Maintenance,
    MaintenanceStatus,
    MaintenancePriority,
    MaintenancePlan,
    MaintenancePlanStatus,
    MaintenancePlanCycle,
    MaintenanceTask,
    MaintenanceTaskStatus,
)


# ========== Maintenance Service ==========

class MaintenanceService(BaseCRUDService):
    """
    Service for Maintenance Record operations.

    Extends BaseCRUDService with maintenance workflow methods.
    """

    def __init__(self):
        super().__init__(Maintenance)

    def create(self, data: dict, user):
        """
        Create maintenance record with reporter from user.

        Args:
            data: Maintenance record data
            user: Current user reporting the issue

        Returns:
            Created Maintenance instance
        """
        data['reporter'] = user
        data['organization_id'] = user.organization_id

        if 'report_time' not in data:
            data['report_time'] = timezone.now()

        return super().create(data, user)

    def assign_technician(self, maintenance_id: str, technician):
        """
        Assign technician to maintenance record.

        Args:
            maintenance_id: Maintenance record ID
            technician: User to assign as technician

        Returns:
            Updated Maintenance instance
        """
        maintenance = self.get(maintenance_id)

        if maintenance.status not in [MaintenanceStatus.REPORTED, MaintenanceStatus.ASSIGNED]:
            raise ValidationError({
                'status': f'Cannot assign technician to record with status {maintenance.get_status_display()}'
            })

        maintenance.technician = technician
        maintenance.assigned_at = timezone.now()
        maintenance.status = MaintenanceStatus.ASSIGNED
        maintenance.save()

        return maintenance

    def start_work(self, maintenance_id: str):
        """
        Mark maintenance as in progress.

        Args:
            maintenance_id: Maintenance record ID

        Returns:
            Updated Maintenance instance
        """
        maintenance = self.get(maintenance_id)

        if maintenance.status != MaintenanceStatus.ASSIGNED:
            raise ValidationError({
                'status': f'Cannot start work on record with status {maintenance.get_status_display()}'
            })

        maintenance.status = MaintenanceStatus.PROCESSING
        maintenance.start_time = timezone.now()
        maintenance.save()

        return maintenance

    def complete_work(self, maintenance_id: str, completion_data: dict):
        """
        Complete maintenance work.

        Args:
            maintenance_id: Maintenance record ID
            completion_data: Dictionary with completion details

        Returns:
            Updated Maintenance instance
        """
        maintenance = self.get(maintenance_id)

        if maintenance.status != MaintenanceStatus.PROCESSING:
            raise ValidationError({
                'status': f'Cannot complete work on record with status {maintenance.get_status_display()}'
            })

        # Update completion data
        maintenance.end_time = timezone.now()
        maintenance.fault_cause = completion_data.get('fault_cause', '')
        maintenance.repair_method = completion_data.get('repair_method', '')
        maintenance.replaced_parts = completion_data.get('replaced_parts', '')
        maintenance.repair_result = completion_data.get('repair_result', '')
        maintenance.labor_cost = completion_data.get('labor_cost', 0)
        maintenance.material_cost = completion_data.get('material_cost', 0)
        maintenance.other_cost = completion_data.get('other_cost', 0)

        # Calculate work hours
        if maintenance.start_time:
            duration = maintenance.end_time - maintenance.start_time
            maintenance.work_hours = duration.total_seconds() / 3600

        # Calculate total cost
        maintenance.calculate_total_cost()
        maintenance.status = MaintenanceStatus.COMPLETED
        maintenance.save()

        return maintenance

    def verify(self, maintenance_id: str, verifier, result: str):
        """
        Verify completed maintenance work.

        Args:
            maintenance_id: Maintenance record ID
            verifier: User verifying the work
            result: Verification result

        Returns:
            Updated Maintenance instance
        """
        maintenance = self.get(maintenance_id)

        if maintenance.status != MaintenanceStatus.COMPLETED:
            raise ValidationError({
                'status': f'Cannot verify record with status {maintenance.get_status_display()}'
            })

        maintenance.verified_by = verifier
        maintenance.verified_at = timezone.now()
        maintenance.verification_result = result
        maintenance.save()

        return maintenance

    def cancel(self, maintenance_id: str, reason: str = None):
        """
        Cancel maintenance record.

        Args:
            maintenance_id: Maintenance record ID
            reason: Cancellation reason

        Returns:
            Updated Maintenance instance
        """
        maintenance = self.get(maintenance_id)

        if maintenance.status == MaintenanceStatus.COMPLETED:
            raise ValidationError({
                'status': 'Cannot cancel completed maintenance record'
            })

        maintenance.status = MaintenanceStatus.CANCELLED
        maintenance.save()

        return maintenance

    def get_by_status(self, status: str, organization_id: str = None):
        """
        Get maintenance records by status.

        Args:
            status: Status to filter by
            organization_id: Filter by organization

        Returns:
            QuerySet of maintenance records with given status
        """
        queryset = Maintenance.objects.filter(
            status=status,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('-created_at')

    def get_by_priority(self, priority: str, organization_id: str = None):
        """
        Get maintenance records by priority.

        Args:
            priority: Priority to filter by
            organization_id: Filter by organization

        Returns:
            QuerySet of maintenance records with given priority
        """
        queryset = Maintenance.objects.filter(
            priority=priority,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('-created_at')

    def get_assigned_to_technician(self, technician_id: str, status: str = None):
        """
        Get maintenance records assigned to a technician.

        Args:
            technician_id: Technician user ID
            status: Optional status filter

        Returns:
            QuerySet of assigned maintenance records
        """
        queryset = Maintenance.objects.filter(
            technician_id=technician_id,
            is_deleted=False
        )

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('-created_at')

    def get_urgent_maintenance(self, organization_id: str = None):
        """
        Get all urgent priority maintenance records.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of urgent maintenance records
        """
        return self.get_by_priority(MaintenancePriority.URGENT, organization_id)

    def get_pending_assignment(self, organization_id: str = None):
        """
        Get all maintenance records pending technician assignment.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of unassigned maintenance records
        """
        queryset = Maintenance.objects.filter(
            status=MaintenanceStatus.REPORTED,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('priority', '-created_at')

    def get_maintenance_statistics(self, organization_id: str = None):
        """
        Get maintenance statistics summary.

        Args:
            organization_id: Filter by organization

        Returns:
            Dictionary with maintenance statistics
        """
        queryset = Maintenance.objects.filter(is_deleted=False)

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return {
            'total': queryset.count(),
            'reported': queryset.filter(status=MaintenanceStatus.REPORTED).count(),
            'assigned': queryset.filter(status=MaintenanceStatus.ASSIGNED).count(),
            'processing': queryset.filter(status=MaintenanceStatus.PROCESSING).count(),
            'completed': queryset.filter(status=MaintenanceStatus.COMPLETED).count(),
            'cancelled': queryset.filter(status=MaintenanceStatus.CANCELLED).count(),
            'urgent': queryset.filter(priority=MaintenancePriority.URGENT).count(),
            'high': queryset.filter(priority=MaintenancePriority.HIGH).count(),
        }


# ========== Maintenance Plan Service ==========

class MaintenancePlanService(BaseCRUDService):
    """
    Service for Maintenance Plan operations.

    Extends BaseCRUDService with plan management methods.
    """

    def __init__(self):
        super().__init__(MaintenancePlan)

    def create(self, data: dict, user):
        """Create maintenance plan with organization from user."""
        data['organization_id'] = user.organization_id
        return super().create(data, user)

    def activate(self, plan_id: str):
        """Activate maintenance plan."""
        plan = self.get(plan_id)
        plan.status = MaintenancePlanStatus.ACTIVE
        plan.save()
        return plan

    def pause(self, plan_id: str):
        """Pause maintenance plan."""
        plan = self.get(plan_id)
        plan.status = MaintenancePlanStatus.PAUSED
        plan.save()
        return plan

    def archive(self, plan_id: str):
        """Archive maintenance plan."""
        plan = self.get(plan_id)
        plan.status = MaintenancePlanStatus.ARCHIVED
        plan.save()
        return plan

    def get_active_plans(self, organization_id: str = None):
        """Get all active maintenance plans."""
        queryset = MaintenancePlan.objects.filter(
            status=MaintenancePlanStatus.ACTIVE,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('plan_code')

    def generate_tasks(self, plan_id: str):
        """
        Generate maintenance tasks from plan.

        STUB IMPLEMENTATION: Returns empty list.

        Args:
            plan_id: Maintenance plan ID

        Returns:
            List of generated MaintenanceTask instances
        """
        plan = self.get(plan_id)

        # STUB: Task generation would happen here
        # In production, this would:
        # 1. Get all target assets based on target_type
        # 2. Calculate next scheduled date based on cycle_type
        # 3. Create MaintenanceTask records for each asset

        return []

    def get_due_tasks(self, organization_id: str = None, days: int = 7):
        """
        Get tasks due within specified days.

        Args:
            organization_id: Filter by organization
            days: Number of days ahead to check

        Returns:
            QuerySet of due maintenance tasks
        """
        due_date = timezone.now().date() + timedelta(days=days)

        queryset = MaintenanceTask.objects.filter(
            scheduled_date__lte=due_date,
            status__in=[MaintenanceTaskStatus.PENDING, MaintenanceTaskStatus.OVERDUE],
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('scheduled_date')

    def mark_overdue_tasks(self, organization_id: str = None):
        """
        Mark pending tasks past deadline as overdue.

        Args:
            organization_id: Filter by organization

        Returns:
            Number of tasks marked as overdue
        """
        queryset = MaintenanceTask.objects.filter(
            status=MaintenanceTaskStatus.PENDING,
            deadline_date__lt=timezone.now().date(),
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        count = queryset.count()
        queryset.update(status=MaintenanceTaskStatus.OVERDUE)

        return count


# ========== Maintenance Task Service ==========

class MaintenanceTaskService(BaseCRUDService):
    """
    Service for Maintenance Task operations.

    Extends BaseCRUDService with task execution methods.
    """

    def __init__(self):
        super().__init__(MaintenanceTask)

    def assign_executor(self, task_id: str, executor):
        """Assign executor to maintenance task."""
        task = self.get(task_id)
        task.executor = executor
        task.status = MaintenanceTaskStatus.IN_PROGRESS
        task.start_time = timezone.now()
        task.save()
        return task

    def complete_execution(self, task_id: str, execution_data: dict, user):
        """Complete maintenance task execution."""
        task = self.get(task_id)

        task.status = MaintenanceTaskStatus.COMPLETED
        task.end_time = timezone.now()
        task.execution_content = execution_data.get('execution_content', '')
        task.execution_photo_urls = execution_data.get('execution_photo_urls', [])
        task.finding = execution_data.get('finding', '')
        task.next_maintenance_suggestion = execution_data.get('next_maintenance_suggestion', '')

        task.save()
        return task

    def verify(self, task_id: str, verifier, result: str):
        """Verify completed maintenance task."""
        task = self.get(task_id)
        task.verified_by = verifier
        task.verified_at = timezone.now()
        task.save()
        return task

    def skip(self, task_id: str, reason: str):
        """Skip maintenance task."""
        task = self.get(task_id)

        if task.status != MaintenanceTaskStatus.PENDING:
            raise ValidationError({
                'status': 'Can only skip pending tasks'
            })

        task.status = MaintenanceTaskStatus.SKIPPED
        task.remark = reason
        task.save()
        return task

    def get_by_status(self, status: str, organization_id: str = None):
        """Get maintenance tasks by status."""
        queryset = MaintenanceTask.objects.filter(
            status=status,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('scheduled_date')

    def get_assigned_to_executor(self, executor_id: str, status: str = None):
        """Get tasks assigned to an executor."""
        queryset = MaintenanceTask.objects.filter(
            executor_id=executor_id,
            is_deleted=False
        )

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('scheduled_date')

    def get_overdue_tasks(self, organization_id: str = None):
        """Get all overdue maintenance tasks."""
        return self.get_by_status(MaintenanceTaskStatus.OVERDUE, organization_id)

    def get_today_tasks(self, organization_id: str = None):
        """Get tasks scheduled for today."""
        today = timezone.now().date()

        queryset = MaintenanceTask.objects.filter(
            scheduled_date=today,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('scheduled_date')
