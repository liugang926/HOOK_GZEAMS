import { computed, ref, watch } from 'vue'

type BoolGetter = boolean | (() => boolean)

const toBoolGetter = (enabled: BoolGetter | undefined, fallback: boolean): (() => boolean) => {
  if (typeof enabled === 'function') {
    return enabled
  }
  if (typeof enabled === 'boolean') {
    return () => enabled
  }
  return () => fallback
}

export interface UseShortcutPopoverOptions {
  enabled?: BoolGetter
  defaultPinned?: BoolGetter
}

export interface UseShortcutPopoverReturn {
  visible: ReturnType<typeof ref<boolean>>
  pinned: ReturnType<typeof ref<boolean>>
  close: () => void
  toggle: () => void
  togglePinned: () => void
  handleEscape: () => boolean
}

export const useShortcutPopover = (
  options: UseShortcutPopoverOptions = {}
): UseShortcutPopoverReturn => {
  const enabledGetter = toBoolGetter(options.enabled, true)
  const defaultPinnedGetter = toBoolGetter(options.defaultPinned, false)
  const isEnabled = computed(() => enabledGetter())
  const isDefaultPinned = computed(() => defaultPinnedGetter())

  const visible = ref(false)
  const pinned = ref(false)

  const close = () => {
    visible.value = false
    pinned.value = false
  }

  const toggle = () => {
    if (!isEnabled.value) return
    visible.value = !visible.value
    if (!visible.value) {
      pinned.value = false
    }
  }

  const togglePinned = () => {
    if (!isEnabled.value) return
    pinned.value = !pinned.value
    if (pinned.value) {
      visible.value = true
    }
  }

  const handleEscape = (): boolean => {
    if (!visible.value) return false
    close()
    return true
  }

  watch([isEnabled, isDefaultPinned], ([enabled, defaultPinned]) => {
    if (!enabled) {
      close()
      return
    }
    if (defaultPinned) {
      pinned.value = true
      visible.value = true
    }
  }, { immediate: true })

  return {
    visible,
    pinned,
    close,
    toggle,
    togglePinned,
    handleEscape
  }
}
