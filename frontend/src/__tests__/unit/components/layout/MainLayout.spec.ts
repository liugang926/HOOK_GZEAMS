import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import MainLayout from '@/layouts/MainLayout.vue'

const translationMessages: Record<string, string> = {
  'common.actions.search': 'Search',
  'common.actions.collapse': 'Collapse',
  'common.actions.detail': 'Detail',
  'common.actions.create': 'Create',
  'common.actions.edit': 'Edit',
  'menu.menu.dashboard': 'Dashboard',
  'menu.menu.lifecycle': 'Lifecycle',
  'assets.lifecycle.maintenance.title': 'Maintenance',
}

const {
  routeState,
  menuStoreMock,
  featureFlagStoreMock,
  brandingStoreMock,
  prefetchRouteResourcesMock,
  scheduleIdleRoutePrefetchMock,
  cancelIdlePrefetchMock,
} = vi.hoisted(() => ({
  routeState: {
    path: '/dashboard',
    fullPath: '/dashboard',
    meta: {},
    params: {},
    query: {},
    name: 'Dashboard',
  } as {
    path: string
    fullPath: string
    meta: Record<string, unknown>
    params: Record<string, unknown>
    query: Record<string, unknown>
    name: string
  },
  menuStoreMock: {
    searchQuery: '',
    filteredMenuGroups: [
      {
        id: 'lifecycle',
        code: 'lifecycle',
        name: 'Lifecycle',
        icon: 'Menu',
        items: [
          {
            code: 'purchase-request',
            name: 'Purchase Requests',
            url: '/objects/PurchaseRequest',
            icon: 'Document',
          },
        ],
      },
    ],
    getGroupLabel: (group: { name: string }) => group.name,
    getItemLabel: (item: { name: string }) => item.name,
    getMenuGroupIdentity: (group: { id?: string; code?: string }, index: number) => group.id || group.code || `group-${index}`,
    fetchMenu: vi.fn(),
  },
  featureFlagStoreMock: {
    loadFlags: vi.fn(),
  },
  brandingStoreMock: {
    brandName: 'GZEAMS',
    brandIconText: 'GZ',
    sidebarLogoUrl: '',
    initialize: vi.fn(),
  },
  prefetchRouteResourcesMock: vi.fn(),
  scheduleIdleRoutePrefetchMock: vi.fn(),
  cancelIdlePrefetchMock: vi.fn(),
}))

scheduleIdleRoutePrefetchMock.mockImplementation(() => cancelIdlePrefetchMock)

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRoute: () => routeState,
  }
})

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()

  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => translationMessages[key] || key,
      te: (key: string) => key in translationMessages,
    }),
  }
})

vi.mock('@/stores/menu', () => ({
  useMenuStore: () => menuStoreMock,
}))

vi.mock('@/stores/featureFlag', () => ({
  useFeatureFlagStore: () => featureFlagStoreMock,
}))

vi.mock('@/stores/branding', () => ({
  useBrandingStore: () => brandingStoreMock,
}))

vi.mock('@/router/prefetch', () => ({
  prefetchRouteResources: prefetchRouteResourcesMock,
  scheduleIdleRoutePrefetch: scheduleIdleRoutePrefetchMock,
}))

vi.mock('@/utils/objectDisplay', () => ({
  resolveObjectDisplayName: (objectCode: string) => objectCode,
}))

const RouterViewStub = defineComponent({
  name: 'RouterViewStub',
  setup(_props, { slots }) {
    const RoutedPageStub = defineComponent({
      name: 'RoutedPageStub',
      template: '<div class="route-component-stub" />',
    })

    return () =>
      h('div', { class: 'router-view-stub' }, slots.default?.({ Component: RoutedPageStub }))
  }
})

const elementStubs = {
  'router-link': defineComponent({
    name: 'RouterLinkStub',
    template: '<a class="router-link-stub"><slot /></a>',
  }),
  'router-view': RouterViewStub,
  'el-container': defineComponent({
    name: 'ElContainerStub',
    template: '<div class="el-container"><slot /></div>',
  }),
  'el-aside': defineComponent({
    name: 'ElAsideStub',
    props: ['width'],
    template: '<aside class="el-aside" :data-width="width"><slot /></aside>',
  }),
  'el-header': defineComponent({
    name: 'ElHeaderStub',
    props: ['height'],
    template: '<header class="el-header" :data-height="height"><slot /></header>',
  }),
  'el-main': defineComponent({
    name: 'ElMainStub',
    template: '<main class="el-main"><slot /></main>',
  }),
  'el-scrollbar': defineComponent({
    name: 'ElScrollbarStub',
    template: '<div class="el-scrollbar"><slot /></div>',
  }),
  'el-input': defineComponent({
    name: 'ElInputStub',
    props: ['modelValue', 'placeholder'],
    emits: ['update:modelValue'],
    template: '<input class="el-input" :value="modelValue" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)">',
  }),
  'el-menu': defineComponent({
    name: 'ElMenuStub',
    props: ['defaultActive', 'router', 'collapse', 'collapseTransition'],
    template: '<nav class="el-menu" :data-active="defaultActive" :data-collapse="String(collapse)"><slot /></nav>',
  }),
  'el-menu-item': defineComponent({
    name: 'ElMenuItemStub',
    props: ['index'],
    template: '<div class="el-menu-item" :data-index="index"><slot name="title" /><slot /></div>',
  }),
  'el-sub-menu': defineComponent({
    name: 'ElSubMenuStub',
    props: ['index'],
    template: '<div class="el-sub-menu" :data-index="index"><div class="el-sub-menu__title"><slot name="title" /></div><div class="el-sub-menu__content"><slot /></div></div>',
  }),
  'el-drawer': defineComponent({
    name: 'ElDrawerStub',
    props: ['modelValue', 'direction', 'size', 'withHeader'],
    template: '<div class="el-drawer" :data-open="String(modelValue)"><slot v-if="modelValue" /></div>',
  }),
  'el-icon': defineComponent({
    name: 'ElIconStub',
    template: '<span class="el-icon"><slot /></span>',
  }),
  'el-button': defineComponent({
    name: 'ElButtonStub',
    props: ['icon', 'text'],
    emits: ['click'],
    template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>',
  }),
  'el-breadcrumb': defineComponent({
    name: 'ElBreadcrumbStub',
    props: ['separator'],
    template: '<div class="el-breadcrumb" :data-separator="separator"><slot /></div>',
  }),
  'el-breadcrumb-item': defineComponent({
    name: 'ElBreadcrumbItemStub',
    props: ['to'],
    template: '<div class="el-breadcrumb-item" :data-to="to ? JSON.stringify(to) : \'\'"><slot /></div>',
  }),
  LocaleSwitcher: defineComponent({
    name: 'LocaleSwitcherStub',
    template: '<div class="locale-switcher-stub" />',
  }),
  NotificationBell: defineComponent({
    name: 'NotificationBellStub',
    template: '<div class="notification-bell-stub" />',
  }),
}

const setViewportWidth = (width: number) => {
  Object.defineProperty(window, 'innerWidth', {
    configurable: true,
    writable: true,
    value: width,
  })
}

const createWrapper = async () => {
  const wrapper = mount(MainLayout, {
    global: {
      config: {
        globalProperties: {
          $t: (key: string) => translationMessages[key] || key,
          $te: (key: string) => key in translationMessages,
        } as any,
      },
      stubs: elementStubs,
      directives: {
        focusTrap: {},
      },
    },
  })

  await nextTick()
  return wrapper
}

describe('MainLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    scheduleIdleRoutePrefetchMock.mockImplementation(() => cancelIdlePrefetchMock)
    menuStoreMock.searchQuery = ''
    routeState.path = '/dashboard'
    routeState.fullPath = '/dashboard'
    routeState.meta = {}
    routeState.params = {}
    routeState.query = {}
    routeState.name = 'Dashboard'
    setViewportWidth(1440)
  })

  afterEach(() => {
    setViewportWidth(1440)
  })

  it('renders branding and initializes layout services on mount', async () => {
    const wrapper = await createWrapper()

    expect(wrapper.find('.main-layout').exists()).toBe(true)
    expect(wrapper.text()).toContain('GZEAMS')
    expect(brandingStoreMock.initialize).toHaveBeenCalledWith(true)
    expect(menuStoreMock.fetchMenu).toHaveBeenCalledTimes(1)
    expect(featureFlagStoreMock.loadFlags).toHaveBeenCalledTimes(1)
    expect(scheduleIdleRoutePrefetchMock).toHaveBeenCalledWith('/dashboard')
  })

  it('renders desktop navigation for large screens', async () => {
    const wrapper = await createWrapper()

    expect((wrapper.vm as any).isMobile).toBe(false)
    expect(wrapper.find('.sidebar').exists()).toBe(true)
    expect(wrapper.find('.mobile-menu-btn').exists()).toBe(false)
    expect((wrapper.vm as any).activeMenu).toBe('/dashboard')
  })

  it('switches to mobile mode and opens the drawer', async () => {
    setViewportWidth(375)
    const wrapper = await createWrapper()

    expect((wrapper.vm as any).isMobile).toBe(true)
    expect((wrapper.vm as any).drawerVisible).toBe(false)

    await wrapper.get('.mobile-menu-btn').trigger('click')

    expect((wrapper.vm as any).drawerVisible).toBe(true)
    expect(wrapper.find('.mobile-drawer').attributes('data-open')).toBe('true')
  })

  it('updates responsive state on window resize', async () => {
    const wrapper = await createWrapper()

    expect((wrapper.vm as any).isMobile).toBe(false)

    setViewportWidth(500)
    window.dispatchEvent(new Event('resize'))
    await nextTick()

    expect((wrapper.vm as any).isMobile).toBe(true)
  })

  it('maps dynamic object breadcrumbs to canonical object list routes', async () => {
    routeState.path = '/objects/Maintenance'
    routeState.fullPath = '/objects/Maintenance'
    routeState.params = { code: 'Maintenance' }
    routeState.meta = {}

    const wrapper = await createWrapper()
    const crumbs = wrapper.findAll('.el-breadcrumb-item')

    expect(crumbs).toHaveLength(2)
    expect(crumbs[1].text()).toContain('Maintenance')
    expect(crumbs[1].attributes('data-to')).toBe('{"path":"/objects/Maintenance"}')
  })

  it('cleans up resize listeners and idle prefetch callbacks on unmount', async () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
    const wrapper = await createWrapper()

    wrapper.unmount()

    expect(cancelIdlePrefetchMock).toHaveBeenCalledTimes(1)
    expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    removeEventListenerSpy.mockRestore()
  })
})
