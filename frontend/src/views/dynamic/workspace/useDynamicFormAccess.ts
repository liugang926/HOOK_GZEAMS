import { computed, type ComputedRef, type Ref } from 'vue'
import type { ObjectMetadata } from '@/api/dynamic'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'

interface Params {
  isEdit: ComputedRef<boolean>
  loadError: Ref<string | null>
  metadataPermissions: Ref<ObjectMetadata['permissions'] | null>
  runtimePermissions: Ref<RuntimePermissions | null>
}

export const useDynamicFormAccess = ({
  isEdit,
  loadError,
  metadataPermissions,
  runtimePermissions,
}: Params) => {
  const effectivePermissions = computed<RuntimePermissions>(() => {
    return runtimePermissions.value || metadataPermissions.value || {
      view: true,
      add: true,
      change: true,
      delete: true,
    }
  })

  const canEdit = computed(() => {
    return isEdit.value
      ? effectivePermissions.value.change
      : effectivePermissions.value.add
  })

  const canView = computed(() => {
    return effectivePermissions.value.view !== false
  })

  const canAccessForm = computed(() => {
    return isEdit.value ? canView.value : effectivePermissions.value.add !== false
  })

  const showPermissionDenied = computed(() => {
    return !loadError.value && !canAccessForm.value
  })

  return {
    canAccessForm,
    canEdit,
    canView,
    effectivePermissions,
    showPermissionDenied,
  }
}
