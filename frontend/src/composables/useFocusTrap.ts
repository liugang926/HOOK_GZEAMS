/**
 * useFocusTrap — Composable wrapper around the existing v-focus-trap directive.
 *
 * Provides programmatic control for focus trapping within Vue components,
 * complementing the v-focus-trap directive for cases where imperative control
 * is needed (e.g., complex nested dialogs or dynamic content).
 *
 * For most use cases, prefer the v-focus-trap directive directly on the
 * container element. This composable is for advanced scenarios.
 *
 * Usage:
 *   const { activate, deactivate, isActive } = useFocusTrap(containerRef)
 */

import { ref, onUnmounted, watch, type Ref } from 'vue'

export interface FocusTrapOptions {
  /** Automatically focus the first focusable element when activated. Default: true. */
  autofocus?: boolean
  /** Return focus to the previously focused element when deactivated. Default: true. */
  returnFocusOnDeactivate?: boolean
  /** Prevent focus from leaving the trap via Tab. Default: true. */
  escapeDeactivates?: boolean
}

const FOCUSABLE_SELECTORS = [
  'a[href]',
  'button:not(:disabled)',
  'input:not(:disabled)',
  'select:not(:disabled)',
  'textarea:not(:disabled)',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable]',
].join(', ')

export function useFocusTrap(
  containerRef: Ref<HTMLElement | null | undefined>,
  options: FocusTrapOptions = {}
) {
  const {
    autofocus = true,
    returnFocusOnDeactivate = true,
    escapeDeactivates = true
  } = options

  const isActive = ref(false)
  let previouslyFocused: HTMLElement | null = null
  let keydownHandler: ((e: KeyboardEvent) => void) | null = null

  function getFocusableElements(): HTMLElement[] {
    if (!containerRef.value) return []
    return Array.from(containerRef.value.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS))
      .filter(el => el.offsetParent !== null) // Exclude hidden elements
  }

  function handleKeydown(e: KeyboardEvent) {
    if (!isActive.value || !containerRef.value) return

    if (e.key === 'Escape' && escapeDeactivates) {
      deactivate()
      return
    }

    if (e.key !== 'Tab') return

    const focusable = getFocusableElements()
    if (focusable.length === 0) {
      e.preventDefault()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    if (e.shiftKey) {
      if (document.activeElement === first || !containerRef.value.contains(document.activeElement)) {
        e.preventDefault()
        last.focus()
      }
    } else {
      if (document.activeElement === last || !containerRef.value.contains(document.activeElement)) {
        e.preventDefault()
        first.focus()
      }
    }
  }

  function activate() {
    if (isActive.value || !containerRef.value) return

    previouslyFocused = document.activeElement as HTMLElement
    isActive.value = true

    keydownHandler = handleKeydown
    document.addEventListener('keydown', keydownHandler, true)

    if (autofocus) {
      const focusable = getFocusableElements()
      if (focusable.length > 0) {
        requestAnimationFrame(() => focusable[0].focus())
      }
    }
  }

  function deactivate() {
    if (!isActive.value) return

    isActive.value = false

    if (keydownHandler) {
      document.removeEventListener('keydown', keydownHandler, true)
      keydownHandler = null
    }

    if (returnFocusOnDeactivate && previouslyFocused) {
      requestAnimationFrame(() => previouslyFocused?.focus())
      previouslyFocused = null
    }
  }

  onUnmounted(deactivate)

  return {
    isActive,
    activate,
    deactivate
  }
}
