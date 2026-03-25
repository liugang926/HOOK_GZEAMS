import { getCurrentInstance, onMounted, onUnmounted } from 'vue'

type KeyCombo = string
type HotkeyCallback = (e: KeyboardEvent) => void | boolean
type BoolGetter = boolean | (() => boolean)

export interface HotkeyOptions {
    preventDefault?: boolean
    stopPropagation?: boolean
    // If true, the hotkey will trigger even if an input or textarea is focused
    allowInInputs?: boolean
    // Optional context. Only handlers in the active context are dispatched.
    context?: string
    // Optional runtime switch to enable/disable the hotkey.
    enabled?: BoolGetter
}

export interface HotkeyContextOptions {
    id?: string
    enabled?: BoolGetter
}

interface HotkeyHandlerEntry {
    cb: HotkeyCallback
    opts: HotkeyOptions
    context: string
}

interface HotkeyContextEntry {
    id: string
    enabled: () => boolean
}

const GLOBAL_CONTEXT = '__global_hotkey_context__'
const keyMap: Record<KeyCombo, HotkeyHandlerEntry[]> = {}
const contextMap = new Map<string, HotkeyContextEntry>()
const contextStack: string[] = []

const toEnabledGetter = (enabled?: BoolGetter): (() => boolean) => {
    if (typeof enabled === 'function') {
        return enabled
    }
    if (typeof enabled === 'boolean') {
        return () => enabled
    }
    return () => true
}

const normalizeCombo = (combo: string): string => {
    const tokens = combo
        .toLowerCase()
        .split('+')
        .map((token) => token.trim())
        .filter(Boolean)

    let hasCtrl = false
    let hasAlt = false
    let hasShift = false
    const primary: string[] = []

    for (const token of tokens) {
        if (token === 'ctrl' || token === 'control' || token === 'meta' || token === 'cmd' || token === 'command') {
            hasCtrl = true
            continue
        }
        if (token === 'alt' || token === 'option') {
            hasAlt = true
            continue
        }
        if (token === 'shift') {
            hasShift = true
            continue
        }
        primary.push(token)
    }

    const ordered: string[] = []
    if (hasCtrl) ordered.push('ctrl')
    if (hasAlt) ordered.push('alt')
    if (hasShift) ordered.push('shift')
    ordered.push(...primary)
    return ordered.join('+')
}

const buildComboFromEvent = (e: KeyboardEvent): string => {
    const keys: string[] = []
    if (e.ctrlKey || e.metaKey) keys.push('ctrl')
    if (e.altKey) keys.push('alt')
    if (e.shiftKey) keys.push('shift')

    if (e.key && !['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) {
        keys.push(e.key.toLowerCase())
    }

    return normalizeCombo(keys.join('+'))
}

const ensureGlobalListener = () => {
    if (isInitialized || typeof window === 'undefined') return
    window.addEventListener('keydown', handleKeyDown)
    isInitialized = true
}

const removeGlobalListenerIfIdle = () => {
    if (!isInitialized || typeof window === 'undefined') return
    const hasHandlers = Object.keys(keyMap).length > 0
    if (hasHandlers) return
    window.removeEventListener('keydown', handleKeyDown)
    isInitialized = false
}

const registerContext = (id: string, enabled: () => boolean) => {
    contextMap.set(id, { id, enabled })
    const exists = contextStack.includes(id)
    if (!exists) {
        contextStack.push(id)
    }
}

const unregisterContext = (id: string) => {
    contextMap.delete(id)
    const index = contextStack.lastIndexOf(id)
    if (index >= 0) {
        contextStack.splice(index, 1)
    }
}

const resolveActiveContext = (): string => {
    for (let i = contextStack.length - 1; i >= 0; i -= 1) {
        const id = contextStack[i]
        const entry = contextMap.get(id)
        if (entry && entry.enabled()) {
            return id
        }
    }
    return GLOBAL_CONTEXT
}

// Single global event listener to handle all bound hotkeys
function handleKeyDown(e: KeyboardEvent) {
    const combo = buildComboFromEvent(e)

    const handlers = keyMap[combo]
    if (!handlers || handlers.length === 0) return

    const activeContext = resolveActiveContext()

    // Check if target is an input
    const target = e.target as HTMLElement
    const tagName = target?.tagName || ''
    const isInput = tagName === 'INPUT' || tagName === 'TEXTAREA' || target?.isContentEditable === true

    // Iterate backwards (LIFO) so the most recently mounted handler in the active context gets priority.
    for (let i = handlers.length - 1; i >= 0; i--) {
        const { cb, opts, context } = handlers[i]
        const isEnabled = toEnabledGetter(opts.enabled)

        if (!isEnabled()) continue
        if (context !== activeContext) continue

        if (isInput && !opts.allowInInputs) {
            continue
        }

        if (opts.preventDefault) e.preventDefault()
        if (opts.stopPropagation) e.stopPropagation()

        const result = cb(e)

        // Stop processing further (older) handlers if stopPropagation is set, or if callback explicitly returns false
        if (opts.stopPropagation || result === false) break
    }
}

let isInitialized = false

export function useHotkey(combo: string, callback: HotkeyCallback, options: HotkeyOptions = {}) {
    const normalizedCombo = normalizeCombo(combo)
    const context = options.context || GLOBAL_CONTEXT

    onMounted(() => {
        ensureGlobalListener()

        if (!keyMap[normalizedCombo]) {
            keyMap[normalizedCombo] = []
        }

        keyMap[normalizedCombo].push({ cb: callback, opts: options, context })
    })

    onUnmounted(() => {
        if (keyMap[normalizedCombo]) {
            keyMap[normalizedCombo] = keyMap[normalizedCombo].filter((item) => item.cb !== callback || item.context !== context)
            if (keyMap[normalizedCombo].length === 0) {
                delete keyMap[normalizedCombo]
            }
        }

        removeGlobalListenerIfIdle()
    })
}

export function useHotkeyContext(options: HotkeyContextOptions = {}): string {
    const instance = getCurrentInstance()
    const contextId = options.id || `hotkey-context-${instance?.uid ?? Math.random().toString(36).slice(2, 10)}`
    const enabledGetter = toEnabledGetter(options.enabled)

    onMounted(() => {
        registerContext(contextId, enabledGetter)
    })

    onUnmounted(() => {
        unregisterContext(contextId)
    })

    return contextId
}
