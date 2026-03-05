import type { Ref } from 'vue'
import type { IntegrationConfig, IntegrationFormData } from '@/types/integration'
import {
  emitActionResultMessage,
  runAction,
  runFlagAction,
  runRowAction,
  withFlagLoading as withFlagLoadingBase,
  withRowLoading as withRowLoadingBase,
  type ActionMessageOptions,
  type ActionOutcome,
  type ActionResultLike,
  type RunActionOptions,
  type RunFlagActionOptions,
  type RunRowActionOptions
} from '@/composables/actionRunner'

type IntegrationActionResult = ActionResultLike
type IntegrationActionMessageOptions = ActionMessageOptions<IntegrationActionResult>
type RunIntegrationActionOptions<T extends IntegrationActionResult> = RunActionOptions<T>
type RunFlagIntegrationActionOptions<T extends IntegrationActionResult> = RunFlagActionOptions<T>
type RunRowIntegrationActionOptions<T extends IntegrationActionResult> = RunRowActionOptions<T>
type IntegrationActionOutcome = ActionOutcome

export const buildIntegrationFormDataFromConfig = (row: IntegrationConfig): IntegrationFormData => ({
  systemType: row.systemType,
  systemName: row.systemName,
  isEnabled: row.isEnabled,
  enabledModules: row.enabledModules || [],
  connectionConfig: {
    apiUrl: '',
    apiKey: '',
    apiSecret: '',
    timeout: 30,
    ...(row.connectionConfig || {})
  },
  syncConfig: {
    autoSync: false,
    interval: 60,
    ...(row.syncConfig || {})
  }
})

export const withFlagLoading = async <T>(
  flag: Ref<boolean>,
  runner: () => Promise<T>,
  options?: { skipIfLoading?: boolean }
): Promise<T | undefined> => withFlagLoadingBase<T>(flag, runner, options)

export const withRowLoading = async <T>(
  loadingMap: Ref<Record<string, boolean>>,
  rowId: string,
  runner: () => Promise<T>,
  options?: { skipIfLoading?: boolean }
): Promise<T | undefined> => withRowLoadingBase<T>(loadingMap, rowId, runner, options)

export const emitIntegrationActionMessage = (
  options: IntegrationActionMessageOptions
): boolean => emitActionResultMessage(options)

export const runIntegrationAction = async <T extends IntegrationActionResult>(
  options: RunIntegrationActionOptions<T>
): Promise<IntegrationActionOutcome> => runAction(options)

export const runFlagIntegrationAction = async <T extends IntegrationActionResult>(
  options: RunFlagIntegrationActionOptions<T>
): Promise<IntegrationActionOutcome> => runFlagAction(options)

export const runRowIntegrationAction = async <T extends IntegrationActionResult>(
  options: RunRowIntegrationActionOptions<T>
): Promise<IntegrationActionOutcome> => runRowAction(options)
