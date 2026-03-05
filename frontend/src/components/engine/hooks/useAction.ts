/**
 * useAction Hook
 *
 * Action execution handler for dynamic forms.
 * Supports:
 * - Built-in actions: submit, cancel, reset
 * - Custom actions via API endpoints
 * - Workflow transitions (future extension)
 * - Confirmation dialogs
 * - Success/error feedback
 */

import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import request from '@/utils/request'
import { getErrorMessage } from '@/utils/errorHandler'
import i18n from '@/locales'

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Action type
 */
export type ActionType = 'submit' | 'cancel' | 'reset' | 'custom' | 'workflow'

/**
 * Button type for UI
 */
export type ButtonType = 'primary' | 'default' | 'danger' | 'warning' | 'success' | 'info'

/**
 * Action configuration
 */
export interface Action {
  code: string
  label: string
  type: ButtonType
  actionType: ActionType
  apiEndpoint?: string
  method?: 'POST' | 'GET' | 'PUT' | 'DELETE' | 'PATCH'
  confirmMessage?: string
  successMessage?: string
  errorMessage?: string
  params?: Record<string, any>
  redirectUrl?: string
  emitEvent?: string
}

/**
 * Action execution context
 */
export interface ActionContext {
  formData: Record<string, any>
  formRef?: any
  businessObject?: string
  recordId?: string
}

/**
 * Action execution result
 */
export interface ActionResult {
  success: boolean
  data?: any
  error?: string
}

// ============================================================================
// API Helper
// ============================================================================

/**
 * Make API request for action execution
 */
async function executeActionApi(
  endpoint: string,
  method: string = 'POST',
  data: Record<string, any> = {}
): Promise<ActionResult> {
  const t = i18n.global.t
  try {
    const verb = String(method || 'POST').toLowerCase()
    const url = String(endpoint || '').trim()
    const isAbsolute = /^https?:\/\//i.test(url)
    // Avoid leaking API auth headers to arbitrary absolute URLs.
    // Absolute URLs that still point to our API should include `/api/` (e.g. http://host/api/...).
    const noAuth = isAbsolute && !url.includes('/api/')

    const result = await request({
      url,
      method: verb as any,
      ...(verb === 'get' || verb === 'delete' ? { params: data } : { data }),
      noAuth
    })

    return { success: true, data: result }
  } catch (error: any) {
    return {
      success: false,
      error: getErrorMessage(error) || t('common.messages.operationFailed')
    }
  }
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Composable for action execution
 *
 * @returns Action execution methods
 */
export function useAction() {
  const router = useRouter()
  const t = i18n.global.t

  // Loading state for action execution
  const executing = ref(false)
  const currentAction = ref<string | null>(null)

  /**
   * Execute a built-in or custom action
   *
   * @param action - Action configuration
   * @param context - Action execution context
   * @returns Action execution result
   */
  async function executeAction(
    action: Action,
    context: ActionContext
  ): Promise<ActionResult> {
    // Show confirmation if required
    if (action.confirmMessage) {
      try {
        await ElMessageBox.confirm(
          action.confirmMessage,
          t('common.dialog.confirmTitle'),
          {
            confirmButtonText: t('common.actions.confirm'),
            cancelButtonText: t('common.actions.cancel'),
            type: 'warning'
          }
        )
      } catch {
        // User cancelled
        return { success: false, error: t('common.messages.actionCancelled') }
      }
    }

    executing.value = true
    currentAction.value = action.code

    try {
      let result: ActionResult

      switch (action.actionType) {
        case 'submit':
          result = await executeSubmit(action, context)
          break

        case 'cancel':
          result = await executeCancel(action, context)
          break

        case 'reset':
          result = await executeReset(action, context)
          break

        case 'custom':
          result = await executeCustom(action, context)
          break

        case 'workflow':
          result = await executeWorkflow(action, context)
          break

        default:
          result = { success: false, error: t('common.messages.unknownActionType', { type: action.actionType }) }
      }

      // Show feedback
      if (result.success) {
        if (action.successMessage) {
          ElMessage.success(action.successMessage)
        }
      } else {
        const msg = action.errorMessage || result.error || t('common.messages.operationFailed')
        ElMessage.error(msg)
      }

      // Handle redirect
      if (result.success && action.redirectUrl) {
        await router.push(action.redirectUrl)
      }

      return result

    } catch (error: any) {
      const errorMsg = action.errorMessage || error.message || t('common.messages.operationFailed')
      ElMessage.error(errorMsg)

      return {
        success: false,
        error: errorMsg
      }
    } finally {
      executing.value = false
      currentAction.value = null
    }
  }

  /**
   * Execute submit action
   * Validates form and emits submit event
   */
  async function executeSubmit(
    action: Action,
    context: ActionContext
  ): Promise<ActionResult> {
    // Validate form if ref is provided
    if (context.formRef) {
      try {
        const isValid = await context.formRef.validate()
        if (!isValid) {
          return { success: false, error: t('common.messages.formValidationFailed') }
        }
      } catch (validationError) {
        return { success: false, error: t('common.messages.formValidationFailed') }
      }
    }

    // Execute API if endpoint is specified
    if (action.apiEndpoint) {
      return await executeActionApi(
        action.apiEndpoint,
        action.method || 'POST',
        context.formData
      )
    }

    // Otherwise just return success (let parent component handle submission)
    return { success: true, data: context.formData }
  }

  /**
   * Execute cancel action
   * Navigates back or to specified URL
   */
  async function executeCancel(
    action: Action,
    _context: ActionContext
  ): Promise<ActionResult> {
    if (action.redirectUrl) {
      await router.push(action.redirectUrl)
    } else {
      router.back()
    }
    return { success: true }
  }

  /**
   * Execute reset action
   * Resets form to initial state
   */
  async function executeReset(
    _action: Action,
    context: ActionContext
  ): Promise<ActionResult> {
    if (context.formRef) {
      context.formRef.resetFields()
    }
    return { success: true }
  }

  /**
   * Execute custom action via API
   */
  async function executeCustom(
    action: Action,
    context: ActionContext
  ): Promise<ActionResult> {
    if (!action.apiEndpoint) {
      return { success: false, error: t('common.messages.operationFailed') }
    }

    // Merge form data with action params
    const requestData = {
      ...context.formData,
      ...action.params
    }

    return await executeActionApi(
      action.apiEndpoint,
      action.method || 'POST',
      requestData
    )
  }

  /**
   * Execute workflow transition action
   * Future extension for BPM workflow integration
   */
  async function executeWorkflow(
    _action: Action,
    context: ActionContext
  ): Promise<ActionResult> {
    // Workflow actions will be implemented with BPM integration
    // For now, treat as custom action
    return await executeCustom(_action, context)
  }

  /**
   * Execute multiple actions in sequence
   * Stops on first failure
   */
  async function executeActions(
    actions: Action[],
    context: ActionContext
  ): Promise<ActionResult[]> {
    const results: ActionResult[] = []

    for (const action of actions) {
      const result = await executeAction(action, context)
      results.push(result)

      if (!result.success) {
        break // Stop on first failure
      }
    }

    return results
  }

  // ============================================================================
  // Return Public Interface
  // ============================================================================

  return {
    // State
    executing,
    currentAction,

    // Methods
    executeAction,
    executeActions
  }
}
