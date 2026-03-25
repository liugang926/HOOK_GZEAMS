import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import i18n from '@/locales'
import { useLocaleStore } from '@/stores/locale'
import SystemMenuLayoutManagement from '@/views/system/SystemMenuLayoutManagement.vue'

const {
  mockMenuGet,
  mockMenuConfig,
  mockMenuManagement,
  mockMenuUpdateManagement,
  mockBusinessObjectList,
  mockGetActiveLanguages,
  mockMessageSuccess,
  mockMessageError,
  mockRouterPush,
  mockSortableCreate,
  mockSortableDestroy,
} = vi.hoisted(() => ({
  mockMenuGet: vi.fn(),
  mockMenuConfig: vi.fn(),
  mockMenuManagement: vi.fn(),
  mockMenuUpdateManagement: vi.fn(),
  mockBusinessObjectList: vi.fn(),
  mockGetActiveLanguages: vi.fn(),
  mockMessageSuccess: vi.fn(),
  mockMessageError: vi.fn(),
  mockRouterPush: vi.fn(),
  mockSortableCreate: vi.fn(),
  mockSortableDestroy: vi.fn(),
}))

vi.mock('sortablejs', () => ({
  default: {
    create: mockSortableCreate,
  },
}))

vi.mock('element-plus', () => ({
  ElPopover: {
    props: ['visible'],
    emits: ['update:visible'],
    template: '<div class="popover-stub"><slot name="reference" /></div>',
  },
  ElMessage: {
    success: mockMessageSuccess,
    error: mockMessageError,
  },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockRouterPush,
  }),
}))

vi.mock('@/api/system', () => ({
  businessObjectApi: {
    list: mockBusinessObjectList,
  },
  menuApi: {
    get: mockMenuGet,
    config: mockMenuConfig,
    management: mockMenuManagement,
    updateManagement: mockMenuUpdateManagement,
  },
}))

vi.mock('@/api/translations', () => ({
  languageApi: {
    getActive: mockGetActiveLanguages,
  },
}))

const createCategories = () => ([
  {
    id: '1',
    code: 'asset_master',
    name: 'menu.categories.asset_master',
    translationKey: 'menu.categories.asset_master',
    localeNames: { 'zh-CN': '资产主数据', 'en-US': 'Asset Master' },
    translationTarget: {
      contentType: 'system.menugroup',
      contentTypeModel: 'menugroup',
      objectId: '1',
      fieldName: 'name',
    },
    icon: 'FolderOpened',
    order: 10,
    isVisible: true,
    isLocked: false,
    isDefault: true,
    entryCount: 2,
    supportsDelete: true,
  },
  {
    id: '2',
    code: 'asset_operation',
    name: 'menu.categories.asset_operation',
    translationKey: 'menu.categories.asset_operation',
    localeNames: { 'zh-CN': '资产业务', 'en-US': 'Asset Operations' },
    translationTarget: {
      contentType: 'system.menugroup',
      contentTypeModel: 'menugroup',
      objectId: '2',
      fieldName: 'name',
    },
    icon: 'Operation',
    order: 20,
    isVisible: true,
    isLocked: false,
    isDefault: true,
    entryCount: 1,
    supportsDelete: true,
  },
])

const createItems = () => ([
  {
    code: 'Asset',
    name: '资产卡片',
    nameEn: 'Asset Card',
    translationKey: 'menu.routes.assetList',
    sourceType: 'business_object' as const,
    sourceCode: 'Asset',
    path: '/objects/Asset',
    icon: 'Document',
    groupCode: 'asset_master',
    groupTranslationKey: 'menu.categories.asset_master',
    order: 10,
    isVisible: true,
    isLocked: true,
    isDefault: true,
    supportsDelete: false,
    supportsVisibility: true,
    supportsReorder: true,
    supportsGroupChange: true,
  },
  {
    code: 'AssetCategory',
    name: '资产分类',
    nameEn: 'Asset Category',
    translationKey: 'menu.routes.assetCategory',
    sourceType: 'business_object' as const,
    sourceCode: 'AssetCategory',
    path: '/objects/AssetCategory',
    icon: 'Folder',
    groupCode: 'asset_master',
    groupTranslationKey: 'menu.categories.asset_master',
    order: 20,
    isVisible: true,
    isLocked: true,
    isDefault: true,
    supportsDelete: false,
    supportsVisibility: true,
    supportsReorder: true,
    supportsGroupChange: true,
  },
  {
    code: 'AssetPickup',
    name: '资产领用',
    nameEn: 'Asset Pickup',
    translationKey: 'menu.routes.assetPickup',
    sourceType: 'business_object' as const,
    sourceCode: 'AssetPickup',
    path: '/objects/AssetPickup',
    icon: 'Upload',
    groupCode: 'asset_operation',
    groupTranslationKey: 'menu.categories.asset_operation',
    order: 30,
    isVisible: true,
    isLocked: true,
    isDefault: true,
    supportsDelete: false,
    supportsVisibility: true,
    supportsReorder: true,
    supportsGroupChange: true,
  },
])

const createWrapper = () => {
  const pinia = createPinia()
  setActivePinia(pinia)

  return mount(SystemMenuLayoutManagement, {
    global: {
      plugins: [pinia, i18n],
      stubs: {
        'el-row': { template: '<div><slot /></div>' },
        'el-col': { template: '<div><slot /></div>' },
        'el-card': {
          template: '<section><div><slot name="header" /></div><div><slot /></div></section>',
        },
        'el-form': { template: '<form><slot /></form>' },
        'el-form-item': {
          props: ['label'],
          template: '<label><span>{{ label }}</span><slot /></label>',
        },
        'el-input': {
          props: ['modelValue', 'placeholder', 'disabled'],
          emits: ['update:modelValue'],
          template: '<input :value="modelValue" :placeholder="placeholder" :disabled="disabled" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        'el-input-number': {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<input type="number" :value="modelValue" @input="$emit(\'update:modelValue\', Number($event.target.value))" />',
        },
        'el-switch': {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
        },
        'el-tag': { template: '<span><slot /></span>' },
        'el-icon': { template: '<span class="el-icon-stub"><slot /></span>' },
        'el-button': {
          props: ['disabled', 'loading', 'type', 'plain'],
          emits: ['click'],
          template: '<button :data-type="type" :disabled="disabled || loading" @click="$emit(\'click\')"><slot /></button>',
        },
        'el-select': {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
        },
        'el-option': {
          props: ['label', 'value'],
          template: '<option :value="value">{{ label }}</option>',
        },
        'el-pagination': {
          props: ['total', 'currentPage', 'pageSize'],
          emits: ['update:current-page', 'update:page-size'],
          template: '<div class="pagination-stub" :data-total="total" :data-page="currentPage" :data-size="pageSize"></div>',
        },
      },
    },
  })
}

describe('SystemMenuLayoutManagement', () => {
  beforeEach(() => {
    localStorage.clear()
    mockMenuGet.mockReset()
    mockMenuConfig.mockReset()
    mockMenuManagement.mockReset()
    mockMenuUpdateManagement.mockReset()
    mockBusinessObjectList.mockReset()
    mockGetActiveLanguages.mockReset()
    mockMessageSuccess.mockReset()
    mockMessageError.mockReset()
    mockRouterPush.mockReset()
    mockSortableCreate.mockReset()
    mockSortableDestroy.mockReset()

    mockSortableCreate.mockReturnValue({
      destroy: mockSortableDestroy,
    })

    i18n.global.locale.value = 'zh-CN'
    mockMenuGet.mockResolvedValue({ groups: [], items: [] })
    mockMenuConfig.mockResolvedValue({
      commonIcons: ['Menu', 'FolderOpened', 'Grid', 'Files'],
    })
    mockBusinessObjectList.mockResolvedValue([])
    mockGetActiveLanguages.mockResolvedValue([
      { id: '1', code: 'zh-CN', name: 'Chinese', nativeName: '中文', isDefault: true, isActive: true, sortOrder: 1 },
      { id: '2', code: 'en-US', name: 'English', nativeName: 'English', isDefault: false, isActive: true, sortOrder: 2 },
    ])
    mockMenuManagement.mockResolvedValue({
      categories: createCategories(),
      items: createItems(),
    })
    mockMenuUpdateManagement.mockImplementation(async (payload) => JSON.parse(JSON.stringify(payload)))
  })

  it('renders the layout workspace and grouped entries', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).toContain('菜单布局编排')
    expect(wrapper.text()).toContain('导航预览')
    expect(wrapper.text()).not.toContain('中文名称')
    expect(wrapper.findAll('.category-item')).toHaveLength(2)
    expect(wrapper.findAll('.entry-group')).toHaveLength(1)
    expect(wrapper.findAll('.entry-item')).toHaveLength(2)
    expect(wrapper.find('[data-testid="layout-preview"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="preview-item-Asset"] .preview-item-icon').exists()).toBe(true)
  })

  it('keeps the preview in sync with collapsed group state', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="toggle-group-asset_master"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="preview-group-asset_master"]').classes()).toContain('collapsed')
    expect(wrapper.find('.preview-group-collapsed').exists()).toBe(true)
  })

  it('supports compact sidebar preview mode', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="preview-mode-compact"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('.layout-preview-card').classes()).toContain('compact')
    expect(wrapper.find('[data-testid="preview-item-Asset"] .preview-item-copy').exists()).toBe(false)
  })

  it('switches back to menu resources from the view switch', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const resourceButton = wrapper.findAll('button').find((button) => button.text() === '菜单资源')
    expect(resourceButton).toBeTruthy()
    await resourceButton!.trigger('click')

    expect(mockRouterPush).toHaveBeenCalledWith({ name: 'MenuManagement' })
  })

  it('uses localized copy and save feedback in english mode', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const localeStore = useLocaleStore()
    localeStore.setLocale('en-US')
    await flushPromises()

    expect(wrapper.text()).toContain('Menu Layout')
    const saveButton = wrapper.findAll('button').find((button) => button.text() === 'Save')
    expect(saveButton).toBeTruthy()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(mockMenuUpdateManagement).toHaveBeenCalledTimes(1)
    expect(mockMessageSuccess).toHaveBeenCalledWith('Menu configuration saved')
  })
})
