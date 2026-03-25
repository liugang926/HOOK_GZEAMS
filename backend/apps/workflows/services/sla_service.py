"""
SLA (Service Level Agreement) Service for Workflow Monitoring.

Provides SLA tracking, compliance monitoring, and bottleneck detection.
"""

from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db.models import Avg, Count, F, Q
from django.contrib.auth import get_user_model

import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SLAService:
    """
    Monitor SLA compliance and track bottlenecks.
    
    Features:
    - SLA threshold configuration per workflow definition
    - Compliance tracking and reporting
    - Bottleneck detection
    - Escalation support
    """
    
    # Default SLA thresholds (in hours)
    DEFAULT_SLA_HOURS = 24
    DEFAULT_ESCALATION_HOURS = 48
    
    def __init__(self):
        """Initialize SLA service."""
        pass


# Alias for backward compatibility
SLATracker = SLAService
    
    def check_sla_compliance(self, task) -> str:
        """
        Check if task is within SLA.
        
        Args:
            task: WorkflowTask instance
            
        Returns:
            Compliance status: 'within_sla', 'approaching_sla', 'overdue', 'escalated'
        """
        if task.status in {'approved', 'rejected', 'returned', 'cancelled', 'terminated'}:
            return 'completed'
        
        if not task.created_at:
            return 'unknown'
        
        # Get SLA configuration
        sla_config = self._get_sla_config(task)
        
        elapsed = timezone.now() - task.created_at
        elapsed_hours = elapsed.total_seconds() / 3600
        
        if elapsed_hours > sla_config['escalation_hours']:
            return 'escalated'
        elif elapsed_hours > sla_config['sla_hours']:
            return 'overdue'
        elif elapsed_hours > sla_config['sla_hours'] * 0.8:  # 80% of SLA
            return 'approaching_sla'
        else:
            return 'within_sla'
    
    def get_sla_status_for_instance(
        self,
        workflow_instance
    ) -> Dict:
        """
        Get SLA status for all tasks in a workflow instance.
        
        Args:
            workflow_instance: WorkflowInstance instance
            
        Returns:
            Dict with SLA status for each task
        """
        tasks = workflow_instance.tasks.all()
        
        result = {
            'instance_id': str(workflow_instance.id),
            'instance_no': workflow_instance.instance_no,
            'status': workflow_instance.status,
            'tasks': [],
            'overall_compliance': 'within_sla'
        }
        
        for task in tasks:
            compliance = self.check_sla_compliance(task)
            
            task_data = {
                'task_id': str(task.id),
                'node_id': task.node_id,
                'node_name': task.node_name,
                'status': task.status,
                'compliance': compliance,
                'created_at': task.created_at,
                'due_date': task.due_date,
                'completed_at': task.completed_at
            }
            
            if task.created_at:
                elapsed = timezone.now() - task.created_at
                task_data['elapsed_hours'] = elapsed.total_seconds() / 3600
            
            result['tasks'].append(task_data)
            
            # Update overall compliance
            if compliance == 'escalated':
                result['overall_compliance'] = 'escalated'
            elif compliance == 'overdue' and result['overall_compliance'] != 'escalated':
                result['overall_compliance'] = 'overdue'
            elif compliance == 'approaching_sla' and result['overall_compliance'] not in ['overdue', 'escalated']:
                result['overall_compliance'] = 'approaching_sla'
        
        return result
    
    def get_bottleneck_report(
        self,
        days: int = 7,
        organization_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate bottleneck report.
        
        Identifies tasks/nodes that are taking longer than expected.
        
        Args:
            days: Number of days to analyze
            organization_id: Optional organization filter
            
        Returns:
            List of bottleneck entries
        """
        from apps.workflows.models import WorkflowTask
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get completed tasks with duration
        tasks = WorkflowTask.objects.filter(
            created_at__gte=start_date,
            completed_at__isnull=False,
            status__in=['approved', 'rejected', 'returned']
        ).select_related(
            'instance__definition'
        )
        
        if organization_id:
            tasks = tasks.filter(
                instance__organization_id=organization_id
            )
        
        # Group by workflow definition and node
        bottlenecks = {}
        
        for task in tasks:
            key = (
                task.instance.definition.id,
                task.node_id
            )
            
            if key not in bottlenecks:
                bottlenecks[key] = {
                    'workflow_definition_id': str(task.instance.definition.id),
                    'workflow_name': task.instance.definition.name,
                    'node_id': task.node_id,
                    'node_name': task.node_name or task.node_id,
                    'durations': [],
                    'task_count': 0
                }
            
            duration = (task.completed_at - task.created_at).total_seconds() / 3600
            bottlenecks[key]['durations'].append(duration)
            bottlenecks[key]['task_count'] += 1
        
        # Calculate statistics and identify bottlenecks
        result = []
        
        for key, data in bottlenecks.items():
            durations = data['durations']
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            # Get SLA threshold for this node
            sla_hours = self._get_sla_hours_for_node(
                data['workflow_definition_id'],
                data['node_id']
            )
            
            # Determine if this is a bottleneck
            is_bottleneck = avg_duration > sla_hours
            severity = 'high' if avg_duration > sla_hours * 1.5 else ('medium' if avg_duration > sla_hours else 'low')
            
            result.append({
                **data,
                'avg_duration_hours': round(avg_duration, 2),
                'max_duration_hours': round(max_duration, 2),
                'min_duration_hours': round(min_duration, 2),
                'sla_hours': sla_hours,
                'is_bottleneck': is_bottleneck,
                'severity': severity if is_bottleneck else 'none',
                'sla_compliance_rate': round(
                    (len([d for d in durations if d <= sla_hours]) / len(durations)) * 100, 1
                ) if durations else 0
            })
        
        # Sort by average duration (descending)
        result.sort(key=lambda x: x['avg_duration_hours'], reverse=True)
        
        return result
    
    def get_sla_compliance_summary(
        self,
        days: int = 7,
        organization_id: Optional[str] = None
    ) -> Dict:
        """
        Get SLA compliance summary.
        
        Args:
            days: Number of days to analyze
            organization_id: Optional organization filter
            
        Returns:
            Dict with compliance summary
        """
        from apps.workflows.models import WorkflowTask
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get all tasks in the period
        tasks = WorkflowTask.objects.filter(
            created_at__gte=start_date
        )
        
        if organization_id:
            tasks = tasks.filter(
                instance__organization_id=organization_id
            )
        
        total_tasks = tasks.count()
        
        # Count by compliance status
        within_sla = 0
        approaching_sla = 0
        overdue = 0
        escalated = 0
        completed = 0
        
        for task in tasks:
            compliance = self.check_sla_compliance(task)
            
            if compliance == 'within_sla':
                within_sla += 1
            elif compliance == 'approaching_sla':
                approaching_sla += 1
            elif compliance == 'overdue':
                overdue += 1
            elif compliance == 'escalated':
                escalated += 1
            elif compliance == 'completed':
                completed += 1
        
        return {
            'period_days': days,
            'total_tasks': total_tasks,
            'within_sla': within_sla,
            'approaching_sla': approaching_sla,
            'overdue': overdue,
            'escalated': escalated,
            'completed': completed,
            'compliance_rate': round(
                (within_sla / total_tasks * 100) if total_tasks > 0 else 0, 1
            ),
            'overall_health': self._calculate_health_score(
                within_sla, approaching_sla, overdue, escalated, total_tasks
            )
        }
    
    def _get_sla_config(self, task) -> Dict:
        """
        Get SLA configuration for a task.
        
        Args:
            task: WorkflowTask instance
            
        Returns:
            Dict with sla_hours and escalation_hours
        """
        workflow_definition = task.instance.definition
        
        # Try to get node-specific SLA from workflow definition
        sla_config = self._get_sla_from_definition(
            workflow_definition,
            task.node_id
        )
        
        if sla_config:
            return sla_config
        
        # Return defaults
        return {
            'sla_hours': self.DEFAULT_SLA_HOURS,
            'escalation_hours': self.DEFAULT_ESCALATION_HOURS
        }
    
    def _get_sla_from_definition(
        self,
        workflow_definition,
        node_id: str
    ) -> Optional[Dict]:
        """
        Get SLA configuration from workflow definition.
        
        Args:
            workflow_definition: WorkflowDefinition instance
            node_id: Node ID
            
        Returns:
            Dict with SLA config or None
        """
        # Check if workflow definition has SLA configuration
        sla_config = workflow_definition.custom_fields.get('sla_config', {})
        
        if node_id in sla_config:
            return sla_config[node_id]
        
        # Check for global workflow SLA
        if 'default' in sla_config:
            return sla_config['default']
        
        return None
    
    def _get_sla_hours_for_node(
        self,
        workflow_definition_id: str,
        node_id: str
    ) -> float:
        """
        Get SLA hours for a specific node.
        
        Args:
            workflow_definition_id: Workflow definition ID
            node_id: Node ID
            
        Returns:
            SLA hours (default 24)
        """
        try:
            from apps.workflows.models import WorkflowDefinition
            
            definition = WorkflowDefinition.objects.get(id=workflow_definition_id)
            sla_config = self._get_sla_from_definition(definition, node_id)
            
            if sla_config:
                return sla_config.get('sla_hours', self.DEFAULT_SLA_HOURS)
        except Exception as e:
            logger.warning(f"Failed to get SLA config: {e}")
        
        return self.DEFAULT_SLA_HOURS
    
    def _calculate_health_score(
        self,
        within_sla: int,
        approaching_sla: int,
        overdue: int,
        escalated: int,
        total: int
    ) -> str:
        """
        Calculate overall health score.
        
        Args:
            within_sla: Tasks within SLA
            approaching_sla: Tasks approaching SLA
            overdue: Overdue tasks
            escalated: Escalated tasks
            total: Total tasks
            
        Returns:
            Health score: 'excellent', 'good', 'fair', 'poor', 'critical'
        """
        if total == 0:
            return 'unknown'
        
        within_rate = within_sla / total
        overdue_rate = overdue / total
        escalated_rate = escalated / total
        
        if within_rate >= 0.9 and escalated_rate < 0.05:
            return 'excellent'
        elif within_rate >= 0.75 and escalated_rate < 0.1:
            return 'good'
        elif within_rate >= 0.5 and escalated_rate < 0.2:
            return 'fair'
        elif within_rate >= 0.25:
            return 'poor'
        else:
            return 'critical'


# Singleton instance
sla_service = SLAService()
