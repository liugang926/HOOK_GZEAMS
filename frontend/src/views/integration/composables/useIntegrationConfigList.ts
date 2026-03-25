import { proxyRefs, type ShallowUnwrapRef } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  useIntegrationConfigQuery,
  type UseIntegrationConfigQueryReturn
} from '@/views/integration/composables/useIntegrationConfigQuery'
import {
  useIntegrationConfigActions,
  type UseIntegrationConfigActionsReturn
} from '@/views/integration/composables/useIntegrationConfigActions'
import {
  useIntegrationLogViewer,
  type UseIntegrationLogViewerReturn
} from '@/views/integration/composables/useIntegrationLogViewer'

type IntegrationConfigListGroups = {
  query: ShallowUnwrapRef<UseIntegrationConfigQueryReturn>
  actions: ShallowUnwrapRef<UseIntegrationConfigActionsReturn>
  logViewer: ShallowUnwrapRef<UseIntegrationLogViewerReturn>
}

export type UseIntegrationConfigListReturn =
  IntegrationConfigListGroups &
  UseIntegrationConfigQueryReturn &
  UseIntegrationConfigActionsReturn &
  UseIntegrationLogViewerReturn

export const useIntegrationConfigList = (): UseIntegrationConfigListReturn => {
  const { t } = useI18n()

  const queryCore = useIntegrationConfigQuery({ t })

  const logViewerCore = useIntegrationLogViewer({ t })

  const actionsCore = useIntegrationConfigActions({
    t,
    refresh: queryCore.fetchData
  })

  const query = proxyRefs(queryCore)
  const actions = proxyRefs(actionsCore)
  const logViewer = proxyRefs(logViewerCore)

  return {
    query,
    actions,
    logViewer,
    ...queryCore,
    ...actionsCore,
    ...logViewerCore
  }
}
