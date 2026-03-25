"""
Django signals for workflow lifecycle events.

These signals are emitted by the WorkflowEngine at key state transitions,
allowing decoupled services (e.g., BusinessStateSyncService) to react
without tight coupling to the engine code.
"""
import django.dispatch


# Fired after WorkflowEngine.start_workflow() succeeds.
# sender: WorkflowInstance class
# instance: the WorkflowInstance that was started
# initiator: the User who started the workflow
workflow_started = django.dispatch.Signal()

# Fired after WorkflowInstance.complete() succeeds (all approvals done).
# sender: WorkflowInstance class
# instance: the completed WorkflowInstance
workflow_completed = django.dispatch.Signal()

# Fired after WorkflowInstance.reject() succeeds.
# sender: WorkflowInstance class
# instance: the rejected WorkflowInstance
# reason: optional rejection reason string
workflow_rejected = django.dispatch.Signal()

# Fired after WorkflowInstance.cancel() or WorkflowInstance.terminate() succeeds.
# sender: WorkflowInstance class
# instance: the cancelled/terminated WorkflowInstance
# user: the User who performed the cancellation
workflow_cancelled = django.dispatch.Signal()
