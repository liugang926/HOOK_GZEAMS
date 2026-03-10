/**
 * useDesignerDraftPersistence — Auto-saves unsaved layout designer state to IndexedDB.
 *
 * Features:
 *   - Debounced save (≤ 2 s) triggered by layout changes
 *   - Restores draft on mount if one exists for the same layout
 *   - Clear on explicit "save / publish" from the designer
 *
 * Usage:
 *   const { hasDraft, restoreDraft, clearDraft } = useDesignerDraftPersistence({
 *     layoutId: () => route.query.layoutId as string,
 *     layoutConfig,
 *   })
 */

import { watch, ref, onUnmounted } from 'vue'
import { storage } from '@/utils/storage'
import { cloneLayoutConfig } from '@/utils/layoutValidation'
import type { LayoutConfig } from '@/components/designer/designerTypes'

interface DraftEntry {
  config: LayoutConfig
  savedAt: number
}

const DRAFT_PREFIX = 'layout_draft_'
const DEBOUNCE_MS = 2000

interface UseDesignerDraftPersistenceOptions {
  /** Reactive getter for the unique layout identifier (id or code). */
  layoutId: () => string
  /** The reactive layout config ref to observe. */
  layoutConfig: () => LayoutConfig
  /** Whether auto-save is enabled. Default: true. */
  enabled?: () => boolean
}

export function useDesignerDraftPersistence(options: UseDesignerDraftPersistenceOptions) {
  const { layoutId, layoutConfig, enabled = () => true } = options

  const hasDraft = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  const draftKey = () => `${DRAFT_PREFIX}${layoutId()}`

  /** Persist current config as draft (debounced). */
  function scheduleSave() {
    if (timer) clearTimeout(timer)
    timer = setTimeout(async () => {
      if (!layoutId() || !enabled()) return
      try {
        const entry: DraftEntry = {
          config: cloneLayoutConfig(layoutConfig()) as LayoutConfig,
          savedAt: Date.now()
        }
        await storage.set(draftKey(), entry)
        hasDraft.value = true
      } catch (e) {
        console.warn('[DraftPersistence] Save failed', e)
      }
    }, DEBOUNCE_MS)
  }

  /** Check if a draft exists for the current layout. */
  async function checkDraft(): Promise<boolean> {
    if (!layoutId()) return false
    try {
      const entry = await storage.get<DraftEntry>(draftKey())
      hasDraft.value = !!entry?.config
      return hasDraft.value
    } catch {
      return false
    }
  }

  /** Restore last saved draft. Returns the config or null. */
  async function restoreDraft(): Promise<LayoutConfig | null> {
    if (!layoutId()) return null
    try {
      const entry = await storage.get<DraftEntry>(draftKey())
      if (entry?.config) {
        hasDraft.value = false
        return entry.config
      }
    } catch {
      // Ignore
    }
    return null
  }

  /** Explicitly clear the draft (after save/publish). */
  async function clearDraft(): Promise<void> {
    if (timer) clearTimeout(timer)
    try {
      await storage.remove(draftKey())
    } catch {
      // Ignore
    }
    hasDraft.value = false
  }

  // Watch config changes and auto-save
  const stopWatch = watch(
    layoutConfig,
    () => {
      if (enabled()) scheduleSave()
    },
    { deep: true }
  )

  // Check on init
  void checkDraft()

  onUnmounted(() => {
    if (timer) clearTimeout(timer)
    stopWatch()
  })

  return {
    hasDraft,
    checkDraft,
    restoreDraft,
    clearDraft
  }
}
