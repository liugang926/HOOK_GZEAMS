import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { DirectiveBinding } from 'vue'
import vFocusTrap from './vFocusTrap'

const createBinding = (value: boolean, autofocus = false): DirectiveBinding =>
  ({ value, modifiers: autofocus ? { autofocus: true } : {} } as DirectiveBinding)

const setFocusableSize = (el: HTMLElement) => {
  Object.defineProperty(el, 'offsetWidth', { configurable: true, get: () => 100 })
  Object.defineProperty(el, 'offsetHeight', { configurable: true, get: () => 24 })
}

const createContainer = () => {
  const container = document.createElement('div')
  container.tabIndex = 0
  setFocusableSize(container)

  const first = document.createElement('button')
  first.type = 'button'
  first.textContent = 'first'
  setFocusableSize(first)

  const second = document.createElement('button')
  second.type = 'button'
  second.textContent = 'second'
  setFocusableSize(second)

  container.append(first, second)
  document.body.appendChild(container)

  return { container, first, second }
}

describe('vFocusTrap directive', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  afterEach(() => {
    vi.useRealTimers()
    document.body.innerHTML = ''
  })

  it('activates when value toggles from false to true', () => {
    const { container } = createContainer()
    vFocusTrap.mounted?.(container as any, createBinding(false))
    expect((container as any).__focusTrapHandler).toBeUndefined()

    vFocusTrap.updated?.(container as any, createBinding(true))
    expect((container as any).__focusTrapHandler).toBeTypeOf('function')
  })

  it('deactivates when value toggles to false', () => {
    const { container } = createContainer()
    vFocusTrap.mounted?.(container as any, createBinding(true))
    expect((container as any).__focusTrapHandler).toBeTypeOf('function')

    vFocusTrap.updated?.(container as any, createBinding(false))
    expect((container as any).__focusTrapHandler).toBeUndefined()
  })

  it('traps Tab from last element to first element', () => {
    const { container, first, second } = createContainer()
    vFocusTrap.mounted?.(container as any, createBinding(true))

    second.focus()
    const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true })
    container.dispatchEvent(event)

    expect(document.activeElement).toBe(first)
    expect(event.defaultPrevented).toBe(true)
  })

  it('traps Shift+Tab from first element to last element', () => {
    const { container, first, second } = createContainer()
    vFocusTrap.mounted?.(container as any, createBinding(true))

    first.focus()
    const event = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true, cancelable: true })
    container.dispatchEvent(event)

    expect(document.activeElement).toBe(second)
    expect(event.defaultPrevented).toBe(true)
  })

  it('autofocuses first focusable element when modifier is enabled', () => {
    vi.useFakeTimers()
    const { container, first } = createContainer()
    vFocusTrap.mounted?.(container as any, createBinding(true, true))

    vi.runAllTimers()
    expect(document.activeElement).toBe(first)
  })
})

