/**
 * Layout History Composable
 *
 * Provides undo/redo functionality for the layout designer.
 * Manages history stack with configurable max depth.
 */

import { ref, computed, Ref } from 'vue'
import { cloneLayoutConfig } from '@/utils/layoutValidation'

export interface HistoryEntry {
  id: string
  config: Record<string, unknown>
  timestamp: number
  description?: string
}

export interface UseLayoutHistoryOptions {
  maxHistory?: number
  initialConfig?: Record<string, unknown>
}

export interface UseLayoutHistoryReturn {
  // State
  canUndo: Ref<boolean>
  canRedo: Ref<boolean>
  currentIndex: Ref<number>
  historyLength: Ref<number>

  // Actions
  push: (config: Record<string, unknown>, description?: string) => void
  undo: () => Record<string, unknown> | null
  redo: () => Record<string, unknown> | null
  clear: () => void
  getCurrent: () => Record<string, unknown> | null
  goTo: (index: number) => Record<string, unknown> | null
}

export function useLayoutHistory(
  config: Ref<Record<string, unknown>>,
  options: UseLayoutHistoryOptions = {}
): UseLayoutHistoryReturn {
  const { maxHistory = 50, initialConfig } = options

  const history = ref<HistoryEntry[]>([])
  const currentIndex = ref(0)

  // Initialize with initial config if provided
  if (initialConfig) {
    history.value.push({
      id: 'initial',
      config: cloneLayoutConfig(initialConfig),
      timestamp: Date.now(),
      description: 'Initial state'
    })
    currentIndex.value = 0
  }

  const canUndo = computed(() => currentIndex.value > 0)
  const canRedo = computed(() => currentIndex.value < history.value.length - 1)
  const historyLength = computed(() => history.value.length)

  function push(newConfig: Record<string, unknown>, description?: string) {
    // Remove any future history after current position
    history.value = history.value.slice(0, currentIndex.value + 1)

    // Add new entry
    history.value.push({
      id: `history-${Date.now()}`,
      config: cloneLayoutConfig(newConfig),
      timestamp: Date.now(),
      description
    })

    // Enforce max history length
    if (history.value.length > maxHistory) {
      history.value.shift()
    } else {
      currentIndex.value++
    }
  }

  function undo(): Record<string, unknown> | null {
    if (!canUndo.value) return null

    currentIndex.value--
    const entry = history.value[currentIndex.value]
    config.value = cloneLayoutConfig(entry.config)
    return entry.config
  }

  function redo(): Record<string, unknown> | null {
    if (!canRedo.value) return null

    currentIndex.value++
    const entry = history.value[currentIndex.value]
    config.value = cloneLayoutConfig(entry.config)
    return entry.config
  }

  function clear() {
    history.value = []
    currentIndex.value = 0
  }

  function getCurrent(): Record<string, unknown> | null {
    if (history.value.length === 0) return null
    return history.value[currentIndex.value]?.config || null
  }

  function goTo(index: number): Record<string, unknown> | null {
    if (index < 0 || index >= history.value.length) return null

    currentIndex.value = index
    const entry = history.value[index]
    config.value = cloneLayoutConfig(entry.config)
    return entry.config
  }

  return {
    canUndo,
    canRedo,
    currentIndex,
    historyLength,
    push,
    undo,
    redo,
    clear,
    getCurrent,
    goTo
  }
}
