import type { Directive, DirectiveBinding } from 'vue'

const FOCUSABLE_ELEMENTS_SELECTOR =
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

interface FocusTrapElement extends HTMLElement {
    __focusTrapHandler?: (e: KeyboardEvent) => void
    __focusTrapAutofocusTimer?: number
}

const getFocusableElements = (el: HTMLElement): HTMLElement[] =>
    Array.from(el.querySelectorAll<HTMLElement>(FOCUSABLE_ELEMENTS_SELECTOR))
        .filter((node) => node.tabIndex >= 0 && (node.offsetWidth > 0 || node.offsetHeight > 0))

const clearAutofocusTimer = (el: FocusTrapElement) => {
    if (typeof el.__focusTrapAutofocusTimer === 'number') {
        window.clearTimeout(el.__focusTrapAutofocusTimer)
        delete el.__focusTrapAutofocusTimer
    }
}

const scheduleAutofocus = (el: FocusTrapElement) => {
    clearAutofocusTimer(el)
    el.__focusTrapAutofocusTimer = window.setTimeout(() => {
        const focusableElements = getFocusableElements(el)
        if (focusableElements.length > 0) {
            focusableElements[0].focus()
        }
        clearAutofocusTimer(el)
    }, 150)
}

const activateFocusTrap = (el: FocusTrapElement, binding: DirectiveBinding) => {
    if (el.__focusTrapHandler) return

    const handleKeyDown = (e: KeyboardEvent) => {
        const isTabPressed = e.key === 'Tab' || e.keyCode === 9
        if (!isTabPressed) return

        const focusableElements = getFocusableElements(el)

        if (focusableElements.length === 0) {
            e.preventDefault()
            return
        }

        const firstElement = focusableElements[0]
        const lastElement = focusableElements[focusableElements.length - 1]

        if (e.shiftKey) {
            if (document.activeElement === firstElement || document.activeElement === el) {
                lastElement.focus()
                e.preventDefault()
            }
            return
        }

        if (document.activeElement === lastElement) {
            firstElement.focus()
            e.preventDefault()
        }
    }

    el.__focusTrapHandler = handleKeyDown
    el.addEventListener('keydown', handleKeyDown)

    if (binding.modifiers.autofocus) {
        scheduleAutofocus(el)
    }
}

const deactivateFocusTrap = (el: FocusTrapElement) => {
    if (el.__focusTrapHandler) {
        el.removeEventListener('keydown', el.__focusTrapHandler)
        delete el.__focusTrapHandler
    }
    clearAutofocusTimer(el)
}

/**
 * v-focus-trap directive
 * Traps the keyboard focus (Tab/Shift+Tab) within the bound element.
 * Usage: <div v-focus-trap>...</div> or <el-drawer v-focus-trap.autofocus>...</div>
 */
export const vFocusTrap: Directive = {
    mounted(el: FocusTrapElement, binding: DirectiveBinding) {
        if (binding.value === false) {
            deactivateFocusTrap(el)
            return
        }

        activateFocusTrap(el, binding)
    },

    updated(el: FocusTrapElement, binding: DirectiveBinding) {
        if (binding.value === false) {
            deactivateFocusTrap(el)
            return
        }

        activateFocusTrap(el, binding)
    },

    unmounted(el: FocusTrapElement) {
        deactivateFocusTrap(el)
    }
}

export default vFocusTrap
