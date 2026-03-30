"""Unified closure summaries for inventory exception objects."""

from __future__ import annotations

from typing import Any, Dict

from django.utils.translation import gettext_lazy as _

from apps.inventory.models import InventoryDifference, InventoryFollowUp


class InventoryExceptionClosureService:
    """Build normalized closure payloads for inventory exception records."""

    _DIFFERENCE_STATE_CONFIG: Dict[str, Dict[str, str]] = {
        InventoryDifference.STATUS_PENDING: {
            'stage': 'Awaiting confirmation',
            'blocker': 'Difference still needs responsibility confirmation.',
            'next_action_code': 'confirm',
        },
        InventoryDifference.STATUS_CONFIRMED: {
            'stage': 'Awaiting review submission',
            'blocker': 'Handling draft must be completed and submitted for review.',
            'next_action_code': 'submit_review',
        },
        InventoryDifference.STATUS_IN_REVIEW: {
            'stage': 'Awaiting approval',
            'blocker': 'Resolution is waiting for managerial approval.',
            'next_action_code': 'approve_resolution',
        },
        InventoryDifference.STATUS_APPROVED: {
            'stage': 'Awaiting execution',
            'blocker': 'Approved resolution still needs execution or downstream action.',
            'next_action_code': 'execute_resolution',
        },
        InventoryDifference.STATUS_EXECUTING: {
            'stage': 'Executing resolution',
            'blocker': 'Resolution execution is in progress.',
            'next_action_code': 'execute_resolution',
        },
        InventoryDifference.STATUS_RESOLVED: {
            'stage': 'Awaiting closure',
            'blocker': 'Resolution is complete but formal closure is still pending.',
            'next_action_code': 'close_difference',
        },
        InventoryDifference.STATUS_IGNORED: {
            'stage': 'Awaiting closure',
            'blocker': 'Ignored difference still needs formal closure.',
            'next_action_code': 'close_difference',
        },
        InventoryDifference.STATUS_CLOSED: {
            'stage': 'Closed',
            'blocker': '',
            'next_action_code': '',
        },
    }

    _FOLLOW_UP_STATE_CONFIG: Dict[str, Dict[str, str]] = {
        InventoryFollowUp.STATUS_PENDING: {
            'stage': 'Awaiting follow-up',
            'blocker': 'Manual downstream follow-up is still pending completion.',
            'next_action_code': 'complete',
        },
        InventoryFollowUp.STATUS_COMPLETED: {
            'stage': 'Completed',
            'blocker': '',
            'next_action_code': 'reopen',
        },
        InventoryFollowUp.STATUS_CANCELLED: {
            'stage': 'Cancelled',
            'blocker': 'Follow-up was cancelled and should be reviewed before closure.',
            'next_action_code': 'reopen',
        },
    }

    def build_difference_summary(self, diff: InventoryDifference) -> Dict[str, Any]:
        """Build a normalized closure summary for an inventory difference."""
        config = self._DIFFERENCE_STATE_CONFIG.get(
            diff.status,
            {
                'stage': str(diff.get_status_display()),
                'blocker': '',
                'next_action_code': '',
            },
        )
        execution_state = self._get_execution_state(diff)
        open_follow_up = InventoryFollowUp.all_objects.filter(
            difference_id=diff.id,
            is_deleted=False,
            status=InventoryFollowUp.STATUS_PENDING,
        ).order_by('-created_at').first()
        latest_follow_up = open_follow_up or InventoryFollowUp.all_objects.filter(
            difference_id=diff.id,
            is_deleted=False,
        ).order_by('-created_at').first()

        blocker = str(_(config['blocker'])) if config['blocker'] else ''
        next_action_code = config['next_action_code']
        stage = str(_(config['stage']))

        if open_follow_up is not None:
            stage = str(_('Awaiting follow-up'))
            blocker = str(_('Manual downstream follow-up is still pending completion.'))
            next_action_code = 'complete_follow_up'
        elif (
            diff.status in {InventoryDifference.STATUS_RESOLVED, InventoryDifference.STATUS_IGNORED}
            and latest_follow_up is not None
            and latest_follow_up.status == InventoryFollowUp.STATUS_COMPLETED
        ):
            blocker = str(_('Manual downstream follow-up is complete. Formal closure can proceed.'))
            next_action_code = 'close_difference'

        completion_value = ''
        if diff.closure_completed_at:
            completion_value = diff.closure_completed_at.isoformat()
        elif latest_follow_up is not None and latest_follow_up.completed_at:
            completion_value = latest_follow_up.completed_at.isoformat()
        elif diff.resolved_at:
            completion_value = diff.resolved_at.isoformat()

        follow_up_status = ''
        if latest_follow_up is not None:
            follow_up_status = latest_follow_up.status
        else:
            follow_up_status = str(execution_state.get('follow_up_task_status') or '').strip()

        return {
            'stage': stage,
            'stage_code': diff.status,
            'owner': self._get_user_display_name(getattr(diff, 'owner', None) or getattr(diff, 'created_by', None)),
            'blocker': blocker,
            'completion': completion_value,
            'next_action_code': next_action_code,
            'is_closed': diff.status == InventoryDifference.STATUS_CLOSED,
            'exception_type': str(diff.get_difference_type_display()),
            'follow_up_status': follow_up_status,
            'follow_up_task_id': str(latest_follow_up.id) if latest_follow_up else '',
            'follow_up_task_code': latest_follow_up.follow_up_code if latest_follow_up else '',
        }

    def build_follow_up_summary(self, follow_up: InventoryFollowUp) -> Dict[str, Any]:
        """Build a normalized closure summary for a manual inventory follow-up."""
        config = self._FOLLOW_UP_STATE_CONFIG.get(
            follow_up.status,
            {
                'stage': str(follow_up.get_status_display()),
                'blocker': '',
                'next_action_code': '',
            },
        )
        completion_value = ''
        if follow_up.completed_at:
            completion_value = follow_up.completed_at.isoformat()
        elif follow_up.last_notified_at:
            completion_value = follow_up.last_notified_at.isoformat()

        return {
            'stage': str(_(config['stage'])),
            'stage_code': follow_up.status,
            'owner': self._get_user_display_name(
                getattr(follow_up, 'assignee', None) or getattr(follow_up, 'created_by', None)
            ),
            'blocker': str(_(config['blocker'])) if config['blocker'] else '',
            'completion': completion_value,
            'next_action_code': config['next_action_code'],
            'is_closed': follow_up.status == InventoryFollowUp.STATUS_COMPLETED,
            'exception_type': str(
                getattr(getattr(follow_up, 'difference', None), 'get_difference_type_display', lambda: '')()
            ),
            'difference_status': str(
                getattr(getattr(follow_up, 'difference', None), 'get_status_display', lambda: '')()
            ),
            'difference_id': str(follow_up.difference_id or ''),
            'task_id': str(follow_up.task_id or ''),
        }

    @staticmethod
    def _get_execution_state(diff: InventoryDifference) -> Dict[str, Any]:
        if isinstance(diff.custom_fields, dict):
            execution_state = diff.custom_fields.get('linked_action_execution') or {}
            if isinstance(execution_state, dict):
                return dict(execution_state)
        return {}

    @staticmethod
    def _get_user_display_name(user) -> str:
        """Return the best-effort human-readable user name."""
        if user is None:
            return ''
        full_name = str(getattr(user, 'get_full_name', lambda: '')() or '').strip()
        if full_name:
            return full_name
        return str(getattr(user, 'username', '') or getattr(user, 'email', '') or getattr(user, 'id', ''))
