/**
 * Unit Tests for NotificationBell Component
 *
 * Tests cover:
 * - Store polling lifecycle (startPolling on mount, stopPolling on unmount)
 * - Badge visibility based on unread count
 * - Empty state and notification item rendering
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia, defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createI18n } from 'vue-i18n'
import NotificationBell from '@/components/layout/NotificationBell.vue'

// ─── Mocks ───────────────────────────────────────────────────────────────────
const mockPush = vi.fn()

vi.mock('vue-router', async (importOriginal) => {
    const actual = await importOriginal<typeof import('vue-router')>()
    return { ...actual, useRouter: () => ({ push: mockPush }) }
})

vi.mock('element-plus', async (importOriginal) => {
    const actual = await importOriginal<typeof import('element-plus')>()
    return { ...actual, ElMessage: { success: vi.fn(), error: vi.fn() } }
})

// ─── i18n fixture ──────────────────────────────────────────────────────────────
const i18n = createI18n({
    legacy: false,
    locale: 'zh-CN',
    fallbackLocale: 'zh-CN',
    messages: {
        'zh-CN': {
            notifications: {
                header: { title: '通知' },
                bell: { tooltip: '通知', noMore: '没有更多通知', viewAll: '查看全部通知' },
                actions: { markAllRead: '全部已读', preferences: '偏好设置', viewAll: '查看全部' },
                messages: { empty: '暂无通知', markAllReadSuccess: '已全部标记为已读' },
                fallback: { untitled: '未命名通知' },
                status: { read: '已读', unread: '未读' }
            },
            common: { status: { processing: '处理中...' } }
        }
    }
})

// ─── Store factory ─────────────────────────────────────────────────────────────
// Uses real async stubs so Pinia wraps them correctly.
// We spy on the store instance AFTER creation, not inside defineStore.
const buildNotificationStore = (overrides: {
    unreadCount?: number
    recentNotifications?: any[]
} = {}) => {
    const unreadCount = ref(overrides.unreadCount ?? 0)
    const recentNotifications = ref(overrides.recentNotifications ?? [])
    const hasUnread = computed(() => unreadCount.value > 0)

    return defineStore('notification', () => ({
        unreadCount,
        recentNotifications,
        hasUnread,
        loading: ref(false),
        syncing: ref(false),
        initialized: ref(true),
        startPolling: () => { },
        stopPolling: () => { },
        markAllAsRead: async () => { },
        markAsRead: async (_id: string) => { },
        refreshHeaderNotifications: async () => { },
        fetchUnreadCount: async () => 0,
        fetchRecentNotifications: async () => [],
        fetchNotificationPage: async () => ({ results: [], count: 0 })
    }))
}

// ─── Element Plus stubs ────────────────────────────────────────────────────────
const commonStubs = {
    'el-badge': {
        template: '<div class="el-badge" :data-hidden="String(hidden)"><slot /><span v-if="!hidden" class="badge-value">{{ value }}</span></div>',
        props: ['value', 'hidden', 'max']
    },
    'el-button': {
        template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>',
        props: ['title', 'circle', 'text', 'link', 'type', 'size', 'loading', 'ariaLabel']
    },
    'el-popover': {
        template: '<div class="el-popover"><slot name="reference" /><slot /></div>',
        props: ['placement', 'width', 'trigger', 'popperClass', 'teleported', 'showArrow']
    },
    'el-icon': { template: '<span class="el-icon"><slot /></span>', props: ['size'] },
    'el-divider': { template: '<hr />' },
    'el-tag': { template: '<span class="el-tag"><slot /></span>', props: ['type', 'size', 'effect'] },
    'el-empty': { template: '<div class="el-empty">{{ description }}</div>', props: ['description', 'imageSize'] },
    'el-link': { template: '<a @click="$emit(\'click\')"><slot /></a>', props: ['type', 'underline'] },
    'Bell': { template: '<svg />' }
}

// ─── Tests ─────────────────────────────────────────────────────────────────────
describe('NotificationBell — Lifecycle', () => {
    let pinia: any

    beforeEach(() => {
        pinia = createPinia()
        setActivePinia(pinia)
        mockPush.mockClear()
    })

    it('calls startPolling when mounted', () => {
        const useStore = buildNotificationStore()
        useStore(pinia)
        const store = useStore()
        const spy = vi.spyOn(store, 'startPolling')

        const wrapper = mount(NotificationBell, {
            global: { plugins: [pinia, i18n], stubs: commonStubs }
        })
        expect(spy).toHaveBeenCalledTimes(1)
        wrapper.unmount()
    })

    it('calls stopPolling when unmounted', () => {
        const useStore = buildNotificationStore()
        useStore(pinia)
        const store = useStore()
        const spy = vi.spyOn(store, 'stopPolling')

        const wrapper = mount(NotificationBell, {
            global: { plugins: [pinia, i18n], stubs: commonStubs }
        })
        wrapper.unmount()
        expect(spy).toHaveBeenCalledTimes(1)
    })
})

describe('NotificationBell — Badge visibility', () => {
    let pinia: any

    beforeEach(() => {
        pinia = createPinia()
        setActivePinia(pinia)
    })

    it('badge hidden=true when unreadCount is 0', () => {
        buildNotificationStore({ unreadCount: 0 })(pinia)
        const wrapper = mount(NotificationBell, {
            global: { plugins: [pinia, i18n], stubs: commonStubs }
        })
        const badge = wrapper.find('.el-badge')
        expect(badge.attributes('data-hidden')).toBe('true')
        wrapper.unmount()
    })

    it('badge hidden=false when unreadCount > 0', () => {
        buildNotificationStore({ unreadCount: 5 })(pinia)
        const wrapper = mount(NotificationBell, {
            global: { plugins: [pinia, i18n], stubs: commonStubs }
        })
        const badge = wrapper.find('.el-badge')
        expect(badge.attributes('data-hidden')).toBe('false')
        wrapper.unmount()
    })
})

describe('NotificationBell — Notification list', () => {
    let pinia: any

    beforeEach(() => {
        pinia = createPinia()
        setActivePinia(pinia)
    })

    it('renders empty placeholder when no notifications', () => {
        buildNotificationStore({ recentNotifications: [] })(pinia)
        const wrapper = mount(NotificationBell, {
            global: { plugins: [pinia, i18n], stubs: commonStubs }
        })
        const empty = wrapper.find('.el-empty, .empty-list, .bell-empty')
        expect(empty.exists()).toBe(true)
        wrapper.unmount()
    })

    it('renders notification title when items present', () => {
        buildNotificationStore({
            recentNotifications: [
                { id: '1', title: 'Test Alert', readAt: null, content: 'body', createdAt: new Date().toISOString() }
            ]
        })(pinia)
        const wrapper = mount(NotificationBell, {
            global: { plugins: [pinia, i18n], stubs: commonStubs }
        })
        expect(wrapper.text()).toContain('Test Alert')
        wrapper.unmount()
    })
})
