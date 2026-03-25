"""
Workflow onboarding checklist service.

Tracks lightweight onboarding progress for workflow-related user experience.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from django.utils import timezone

from apps.accounts.models import User


class OnboardingService:
    """
    Manage workflow onboarding state for users.
    """

    STORAGE_KEY = 'workflow_onboarding'
    EVENT_STEP_MAP = {
        'workflow_workspace_opened': 'open_workflow_workspace',
        'workflow_display_configured': 'personalize_workflow_view',
        'workflow_notifications_configured': 'configure_notifications',
        'workflow_definition_reviewed': 'review_first_definition',
        'workflow_started': 'start_first_workflow',
        'workflow_task_completed': 'complete_first_task',
    }

    DEFAULT_STEPS = [
        {
            'code': 'open_workflow_workspace',
            'title': 'Open the workflow workspace',
            'description': 'Review pending approvals, current workload, and recent workflow activity.',
            'route': '/workflows',
            'action_label': 'Open workflows',
        },
        {
            'code': 'personalize_workflow_view',
            'title': 'Personalize your workflow view',
            'description': 'Choose the default view, grouping, and timeline display that fits daily review work.',
            'route': '/settings/preferences',
            'action_label': 'Adjust display settings',
        },
        {
            'code': 'configure_notifications',
            'title': 'Configure workflow notifications',
            'description': 'Enable the channels and quiet hours you want before approvals start arriving.',
            'route': '/notifications/preferences',
            'action_label': 'Set notification preferences',
        },
        {
            'code': 'review_first_definition',
            'title': 'Review a workflow definition',
            'description': 'Inspect the approval path, due date expectations, and participant assignment.',
            'route': '/workflows/definitions',
            'action_label': 'Review definitions',
        },
        {
            'code': 'start_first_workflow',
            'title': 'Start your first workflow',
            'description': 'Launch one real workflow instance so the approval route is visible end to end.',
            'route': '/workflows/instances',
            'action_label': 'Start a workflow',
        },
        {
            'code': 'complete_first_task',
            'title': 'Complete a workflow task',
            'description': 'Approve, reject, or transfer one task to confirm the full workflow experience.',
            'route': '/workflows/tasks',
            'action_label': 'Process a task',
        },
    ]

    def get_checklist(self, user: User) -> Dict[str, Any]:
        """
        Return onboarding checklist with completion progress.
        """
        state = self._get_state(user)
        steps = []
        completed_count = 0

        for position, step in enumerate(self.DEFAULT_STEPS, start=1):
            completion = state.get('completed_steps', {}).get(step['code'], {})
            is_completed = isinstance(completion, dict) and bool(completion.get('completed_at'))
            if is_completed:
                completed_count += 1

            steps.append({
                **step,
                'position': position,
                'is_completed': is_completed,
                'completed_at': completion.get('completed_at'),
                'metadata': completion.get('metadata', {}),
            })

        total_steps = len(steps)
        next_step = next((step for step in steps if not step['is_completed']), None)
        is_completed = completed_count == total_steps if total_steps else True

        return {
            'is_completed': is_completed,
            'completed_at': state.get('completed_at'),
            'started_at': state.get('started_at'),
            'steps': steps,
            'summary': {
                'total_steps': total_steps,
                'completed_steps': completed_count,
                'remaining_steps': max(total_steps - completed_count, 0),
                'progress_percent': round((completed_count / total_steps) * 100) if total_steps else 100,
            },
            'next_step': next_step,
        }

    def mark_step_complete(
        self,
        user: User,
        step_code: str,
        metadata: Optional[Dict[str, Any]] = None,
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        Mark a checklist step as complete.
        """
        self._validate_step_code(step_code)
        state = self._get_state(user)
        completed_steps = dict(state.get('completed_steps', {}))
        completed_steps[step_code] = {
            'completed_at': timezone.now().isoformat(),
            'metadata': metadata or {},
        }
        state['completed_steps'] = completed_steps
        state['started_at'] = state.get('started_at') or timezone.now().isoformat()

        checklist_preview = self._build_preview(state)
        state['completed_at'] = timezone.now().isoformat() if checklist_preview['is_completed'] else None

        self._save_state(user, state, actor=actor)
        return self.get_checklist(user)

    def mark_step_incomplete(
        self,
        user: User,
        step_code: str,
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        Remove completion state from a checklist step.
        """
        self._validate_step_code(step_code)
        state = self._get_state(user)
        completed_steps = dict(state.get('completed_steps', {}))
        completed_steps.pop(step_code, None)
        state['completed_steps'] = completed_steps
        state['completed_at'] = None
        self._save_state(user, state, actor=actor)
        return self.get_checklist(user)

    def record_event(
        self,
        user: User,
        event_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        Map a product event to an onboarding step and complete it if known.
        """
        step_code = self.EVENT_STEP_MAP.get(event_name)
        if not step_code:
            return self.get_checklist(user)
        return self.mark_step_complete(user, step_code, metadata=metadata, actor=actor)

    def reset_progress(
        self,
        user: User,
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        Reset onboarding progress for a user.
        """
        state = self._get_state(user)
        state['completed_steps'] = {}
        state['started_at'] = None
        state['completed_at'] = None
        self._save_state(user, state, actor=actor)
        return self.get_checklist(user)

    def _get_state(self, user: User) -> Dict[str, Any]:
        """Get persisted onboarding state."""
        custom_fields = user.custom_fields or {}
        state = custom_fields.get(self.STORAGE_KEY, {})
        if not isinstance(state, dict):
            state = {}
        return {
            'started_at': state.get('started_at'),
            'completed_at': state.get('completed_at'),
            'completed_steps': dict(state.get('completed_steps', {})),
        }

    def _save_state(
        self,
        user: User,
        state: Dict[str, Any],
        actor: Optional[User] = None,
    ) -> None:
        """Persist onboarding state to user.custom_fields."""
        payload = dict(user.custom_fields or {})
        payload[self.STORAGE_KEY] = state
        user.custom_fields = payload

        update_fields = ['custom_fields', 'updated_at']
        if actor is not None:
            user.updated_by = actor
            update_fields.append('updated_by')
        user.save(update_fields=update_fields)

    def _build_preview(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Build a checklist preview without saving."""
        preview_user = type('PreviewUser', (), {'custom_fields': {self.STORAGE_KEY: deepcopy(state)}})()
        return self.get_checklist(preview_user)  # type: ignore[arg-type]

    def _validate_step_code(self, step_code: str) -> None:
        """Validate a step code."""
        valid_codes = {step['code'] for step in self.DEFAULT_STEPS}
        if step_code not in valid_codes:
            raise ValueError(f'Unknown onboarding step: {step_code}')


onboarding_service = OnboardingService()
