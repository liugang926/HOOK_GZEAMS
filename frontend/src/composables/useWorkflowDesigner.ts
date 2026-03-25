import { computed, ref } from 'vue'
import { getFieldDefinitions, type FieldDefinition } from '@/api/system'
import { useFieldPermissions } from './useFieldPermissions'
import request from '@/utils/request'
import type {
  FieldPermissionLevel,
  FormPermissionsMap,
  NodeFormPermissions,
} from '@/types/workflow'

interface BusinessObjectInfo {
  code: string
  name: string
  fields: FieldDefinition[]
}

interface WorkflowFormPermissionsResponse {
  formPermissions?: FormPermissionsMap
  form_permissions?: FormPermissionsMap
  availableFields?: FieldDefinition[]
  available_fields?: FieldDefinition[]
}

function normalizeFieldDefinitions(payload: unknown): FieldDefinition[] {
  if (Array.isArray(payload)) {
    return payload as FieldDefinition[]
  }

  if (payload && typeof payload === 'object') {
    const maybePaginated = payload as { results?: FieldDefinition[] }
    if (Array.isArray(maybePaginated.results)) {
      return maybePaginated.results
    }
  }

  return []
}

export function useWorkflowDesigner(workflowId: string) {
  const permissions = ref<FormPermissionsMap>({})
  const availableFields = ref<FieldDefinition[]>([])
  const selectedNode = ref<Record<string, any> | null>(null)
  const selectedNodePermissions = ref<NodeFormPermissions>({})
  const showPermissionsPanel = ref(false)
  const businessObjectInfo = ref<BusinessObjectInfo | null>(null)
  const isLoading = ref(false)
  const loadError = ref<string | null>(null)
  const initialPermissionsSnapshot = ref('{}')
  const permissionCache = new Map<string, NodeFormPermissions>()

  const selectedNodeFieldPermissions = useFieldPermissions(selectedNodePermissions)

  const getNodeCacheKey = (nodeId: string) => `${workflowId}:${nodeId}`

  const syncSelectedNodePermissions = () => {
    const nodeId = selectedNode.value?.id ? String(selectedNode.value.id) : ''
    selectedNodePermissions.value = nodeId ? permissions.value[nodeId] ?? {} : {}
  }

  const cachePermissions = (formPermissions: FormPermissionsMap) => {
    permissionCache.clear()
    Object.entries(formPermissions).forEach(([nodeId, nodePermissions]) => {
      permissionCache.set(getNodeCacheKey(nodeId), { ...nodePermissions })
    })
  }

  async function loadFieldsForBusinessObject(businessObjectCode: string) {
    if (!businessObjectCode) {
      availableFields.value = []
      businessObjectInfo.value = null
      return
    }

    isLoading.value = true
    loadError.value = null

    try {
      const response = await getFieldDefinitions(businessObjectCode)
      const fields = normalizeFieldDefinitions(response)

      availableFields.value = fields
      businessObjectInfo.value = {
        code: businessObjectCode,
        name: businessObjectCode,
        fields,
      }
    } catch (error) {
      console.error('Failed to load business object fields:', error)
      loadError.value = `Failed to load fields for ${businessObjectCode}`
    } finally {
      isLoading.value = false
    }
  }

  async function loadPermissions() {
    if (!workflowId) return

    isLoading.value = true
    loadError.value = null

    try {
      const response = await request.get<WorkflowFormPermissionsResponse>(
        `/workflows/definitions/${workflowId}/form-permissions/`
      )
      const formPermissions = response.formPermissions ?? response.form_permissions ?? {}
      const fields = response.availableFields ?? response.available_fields ?? []

      permissions.value = formPermissions
      cachePermissions(formPermissions)
      initialPermissionsSnapshot.value = JSON.stringify(formPermissions)

      if (fields.length > 0) {
        availableFields.value = fields
        if (businessObjectInfo.value) {
          businessObjectInfo.value = {
            ...businessObjectInfo.value,
            fields,
          }
        }
      }

      syncSelectedNodePermissions()
    } catch (error) {
      console.error('Failed to load permissions:', error)
      loadError.value = 'Failed to load permissions'
    } finally {
      isLoading.value = false
    }
  }

  async function savePermissions() {
    if (!workflowId) return false

    try {
      await request.put(`/workflows/definitions/${workflowId}/form-permissions/`, permissions.value)
      cachePermissions(permissions.value)
      initialPermissionsSnapshot.value = JSON.stringify(permissions.value)
      syncSelectedNodePermissions()
      return true
    } catch (error) {
      console.error('Failed to save permissions:', error)
      return false
    }
  }

  function getPermissionsForNode(nodeId: string): NodeFormPermissions {
    if (!workflowId) return {}

    const cached = permissionCache.get(getNodeCacheKey(nodeId))
    if (cached) {
      return cached
    }

    return permissions.value[nodeId] ?? {}
  }

  function updateNodePermissions(
    nodeId: string,
    fieldCode: string,
    permission: FieldPermissionLevel
  ) {
    permissions.value[nodeId] = {
      ...(permissions.value[nodeId] ?? {}),
      [fieldCode]: permission,
    }

    permissionCache.set(getNodeCacheKey(nodeId), { ...permissions.value[nodeId] })
    syncSelectedNodePermissions()
  }

  function getPermissionBadge(
    fieldPermission: FieldPermissionLevel
  ): { badge: string; color: string; icon: string } {
    switch (fieldPermission) {
      case 'editable':
        return { badge: 'E', color: '#27ae60', icon: 'edit' }
      case 'read_only':
        return { badge: 'RO', color: '#f39c12', icon: 'view' }
      case 'hidden':
        return { badge: 'H', color: '#e74c3c', icon: 'hide' }
      default:
        return { badge: '?', color: '#95a5a6', icon: 'help' }
    }
  }

  function getBusinessFieldValue(fieldCode: string): unknown {
    if (!businessObjectInfo.value) return null

    const field = businessObjectInfo.value.fields.find((entry) => entry.code === fieldCode)
    return field?.defaultValue ?? null
  }

  function setShowPermissionsPanel(show: boolean) {
    showPermissionsPanel.value = show
  }

  function setSelectedNode(node: Record<string, any> | null) {
    selectedNode.value = node
    syncSelectedNodePermissions()
  }

  function isFieldEditable(nodeId: string, fieldCode: string): boolean {
    if (selectedNode.value?.id === nodeId) {
      return selectedNodeFieldPermissions.isEditable(fieldCode)
    }
    return getPermissionsForNode(nodeId)[fieldCode] === 'editable'
  }

  function isFieldHidden(nodeId: string, fieldCode: string): boolean {
    if (selectedNode.value?.id === nodeId) {
      return selectedNodeFieldPermissions.isHidden(fieldCode)
    }
    return getPermissionsForNode(nodeId)[fieldCode] === 'hidden'
  }

  function isFieldReadOnly(nodeId: string, fieldCode: string): boolean {
    if (selectedNode.value?.id === nodeId) {
      return selectedNodeFieldPermissions.isReadOnly(fieldCode)
    }
    return getPermissionsForNode(nodeId)[fieldCode] === 'read_only'
  }

  function resetNodePermissions(nodeId: string) {
    if (!permissions.value[nodeId]) return

    delete permissions.value[nodeId]
    permissionCache.delete(getNodeCacheKey(nodeId))
    syncSelectedNodePermissions()
  }

  function exportPermissions(): string {
    return JSON.stringify(
      {
        workflowId,
        permissions: permissions.value,
        businessObject: businessObjectInfo.value,
        exportedAt: new Date().toISOString(),
      },
      null,
      2
    )
  }

  function importPermissions(configString: string): boolean {
    try {
      const config = JSON.parse(configString) as {
        workflowId?: string
        permissions?: FormPermissionsMap
        businessObject?: BusinessObjectInfo | null
      }

      if (config.workflowId && config.workflowId !== workflowId) {
        console.error('Workflow ID mismatch')
        return false
      }

      permissions.value = config.permissions ?? {}
      businessObjectInfo.value = config.businessObject ?? null
      availableFields.value = businessObjectInfo.value?.fields ?? []
      cachePermissions(permissions.value)
      syncSelectedNodePermissions()
      return true
    } catch (error) {
      console.error('Failed to import permissions:', error)
      return false
    }
  }

  const hasSelectedApprovalNode = computed(() => selectedNode.value?.type === 'approval')

  const hasUnsavedChanges = computed(
    () => JSON.stringify(permissions.value) !== initialPermissionsSnapshot.value
  )

  const permissionSummary = computed(() => {
    const summary = {
      editable: 0,
      readOnly: 0,
      hidden: 0,
      total: 0,
    }

    Object.values(permissions.value).forEach((nodePermissions) => {
      Object.values(nodePermissions).forEach((permission) => {
        summary.total += 1
        if (permission === 'editable') summary.editable += 1
        if (permission === 'read_only') summary.readOnly += 1
        if (permission === 'hidden') summary.hidden += 1
      })
    })

    return summary
  })

  const canSavePermissions = computed(
    () => Boolean(workflowId) && Object.keys(permissions.value).length > 0 && !isLoading.value
  )

  return {
    permissions,
    availableFields,
    selectedNode,
    showPermissionsPanel,
    businessObjectInfo,
    isLoading,
    loadError,
    loadFieldsForBusinessObject,
    loadPermissions,
    savePermissions,
    getPermissionsForNode,
    updateNodePermissions,
    getPermissionBadge,
    getBusinessFieldValue,
    setShowPermissionsPanel,
    setSelectedNode,
    isFieldEditable,
    isFieldHidden,
    isFieldReadOnly,
    resetNodePermissions,
    exportPermissions,
    importPermissions,
    hasSelectedApprovalNode,
    hasUnsavedChanges,
    permissionSummary,
    canSavePermissions,
  }
}
