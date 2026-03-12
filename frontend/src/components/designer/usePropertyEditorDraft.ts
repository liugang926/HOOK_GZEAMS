import { ref, watch } from 'vue'

type PropertyRecord = Record<string, any>

export function usePropertyEditorDraft(getModelValue: () => PropertyRecord | undefined) {
  const modelDraft = ref<PropertyRecord>({})

  watch(
    getModelValue,
    (value) => {
      modelDraft.value = { ...(value || {}) }
    },
    { immediate: true, deep: true }
  )

  const updateDraft = (updater: (draft: PropertyRecord) => PropertyRecord) => {
    const next = updater({ ...modelDraft.value })
    modelDraft.value = next
    return next
  }

  const propertyValue = (key: string): any => modelDraft.value?.[key]
  const stringValue = (key: string): string => String(propertyValue(key) ?? '')
  const numberValue = (key: string): number | undefined => {
    const value = propertyValue(key)
    if (value === null || value === undefined || value === '') return undefined
    const num = Number(value)
    return Number.isFinite(num) ? num : undefined
  }
  const booleanValue = (key: string): boolean => Boolean(propertyValue(key))

  return {
    modelDraft,
    updateDraft,
    propertyValue,
    stringValue,
    numberValue,
    booleanValue
  }
}
