import { ref, watch } from 'vue'
import {
  loadRelationGroupExpandedPreference,
  saveRelationGroupExpandedPreference
} from '@/platform/reference/relationGroupCollapsePreference'

export interface RelationGroupExpansionItem {
  key: string
  defaultExpanded?: boolean
}

interface RelationGroupScope {
  objectCode: string
  scopeId: string
  scope: string
}

export interface UseRelationGroupExpansionOptions {
  groups: () => RelationGroupExpansionItem[]
  objectCode: () => string
  scopeId: () => string
  loadPreference?: (objectCode: string, scopeId: string) => string[] | null
  savePreference?: (objectCode: string, scopeId: string, expandedGroups: string[]) => void
}

const normalize = (value: unknown): string => String(value || '').trim()

const sameArray = (left: string[], right: string[]): boolean => {
  if (left.length !== right.length) return false
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] !== right[index]) return false
  }
  return true
}

const normalizeExpandedNames = (raw: unknown): string[] => {
  if (Array.isArray(raw)) {
    return Array.from(new Set(raw.map((item) => normalize(item)).filter(Boolean)))
  }
  const single = normalize(raw)
  return single ? [single] : []
}

const resolveScope = (objectCode: string, scopeId: string): RelationGroupScope | null => {
  const object = normalize(objectCode)
  const scope = normalize(scopeId)
  if (!object || !scope) return null
  return {
    objectCode: object,
    scopeId: scope,
    scope: `${object}:${scope}`
  }
}

export interface UseRelationGroupExpansionReturn {
  activeGroups: ReturnType<typeof ref<string[]>>
  isExpanded: (groupKey: string) => boolean
  toggle: (groupKey: string) => void
}

export const useRelationGroupExpansion = (
  options: UseRelationGroupExpansionOptions
): UseRelationGroupExpansionReturn => {
  const loadPreference = options.loadPreference || loadRelationGroupExpandedPreference
  const savePreference = options.savePreference || saveRelationGroupExpandedPreference

  const activeGroups = ref<string[]>([])
  const scopeRef = ref('')
  const hydrated = ref(false)
  const preferenceExists = ref(false)

  const persistPreference = (raw: unknown) => {
    if (!hydrated.value) return
    const scope = resolveScope(options.objectCode(), options.scopeId())
    if (!scope) return
    const normalized = normalizeExpandedNames(raw)
    preferenceExists.value = true
    savePreference(scope.objectCode, scope.scopeId, normalized)
  }

  const syncState = (groups: RelationGroupExpansionItem[]) => {
    const validKeys = new Set((groups || []).map((group) => normalize(group.key)).filter(Boolean))
    const defaultKeys = (groups || [])
      .filter((group) => group.defaultExpanded)
      .map((group) => normalize(group.key))
      .filter(Boolean)

    const scope = resolveScope(options.objectCode(), options.scopeId())
    const scopeKey = scope?.scope || ''

    if (!scope) {
      scopeRef.value = ''
      hydrated.value = false
      preferenceExists.value = false
      activeGroups.value = defaultKeys
      return
    }

    if (scopeRef.value !== scopeKey) {
      scopeRef.value = scopeKey
      hydrated.value = false
      preferenceExists.value = false
    }

    if (!hydrated.value) {
      // Delay hydration until group keys are available; runtime relations are async.
      if (validKeys.size === 0) {
        if (activeGroups.value.length > 0) {
          activeGroups.value = []
        }
        return
      }

      const restored = loadPreference(scope.objectCode, scope.scopeId)
      preferenceExists.value = Array.isArray(restored)
      const next = Array.isArray(restored)
        ? restored.map((key) => normalize(key)).filter((key) => validKeys.has(key))
        : defaultKeys
      if (!sameArray(next, activeGroups.value)) {
        activeGroups.value = next
      }
      hydrated.value = true
      return
    }

    if (!preferenceExists.value && activeGroups.value.length === 0 && defaultKeys.length > 0) {
      activeGroups.value = defaultKeys
      return
    }

    const next = activeGroups.value.filter((key) => validKeys.has(key))
    if (!sameArray(next, activeGroups.value)) {
      activeGroups.value = next
    }
  }

  const isExpanded = (groupKey: string): boolean => {
    return activeGroups.value.includes(normalize(groupKey))
  }

  const toggle = (groupKey: string) => {
    const key = normalize(groupKey)
    if (!key) return
    const current = new Set(activeGroups.value)
    if (current.has(key)) {
      current.delete(key)
    } else {
      current.add(key)
    }
    activeGroups.value = Array.from(current)
  }

  watch(
    [
      () => options.groups(),
      () => options.objectCode(),
      () => options.scopeId()
    ],
    ([groups]) => {
      syncState(Array.isArray(groups) ? groups : [])
    },
    { immediate: true }
  )

  watch(
    [() => [...activeGroups.value], () => options.objectCode(), () => options.scopeId()],
    ([expandedGroups]) => {
      persistPreference(expandedGroups)
    }
  )

  return {
    activeGroups,
    isExpanded,
    toggle
  }
}
