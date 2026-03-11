import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import i18n from '@/locales'
import { useLocaleStore } from '@/stores/locale'
import SystemMenuManagement from '@/views/system/SystemMenuManagement.vue'

const {
  mockMenuGet,
  mockMenuConfig,
  mockMenuManagement,
  mockMenuUpdateManagement,
  mockBusinessObjectList,
  mockGetActiveLanguages,
  mockMessageSuccess,
  mockMessageError,
  mockMessageWarning,
  mockMessageBoxConfirm,
  mockRouterPush,
  mockSortableCreate,
  mockSortableDestroy,
  mockConsoleError,
} = vi.hoisted(() => ({
  mockMenuGet: vi.fn(),
  mockMenuConfig: vi.fn(),
  mockMenuManagement: vi.fn(),
  mockMenuUpdateManagement: vi.fn(),
  mockBusinessObjectList: vi.fn(),
  mockGetActiveLanguages: vi.fn(),
  mockMessageSuccess: vi.fn(),
  mockMessageError: vi.fn(),
  mockMessageWarning: vi.fn(),
  mockMessageBoxConfirm: vi.fn(),
  mockRouterPush: vi.fn(),
  mockSortableCreate: vi.fn(),
  mockSortableDestroy: vi.fn(),
  mockConsoleError: vi.fn(),
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
    warning: mockMessageWarning,
  },
  ElMessageBox: {
    confirm: mockMessageBoxConfirm,
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

const createCategories = (count = 6) =>
  Array.from({ length: count }, (_, index) => ({
    id: `${index + 1}`,
    code: index === 0 ? 'asset_master' : `custom_group_${index}`,
    name: index === 0 ? 'menu.categories.asset_master' : `Custom Group ${index}`,
    translationKey: index === 0 ? 'menu.categories.asset_master' : '',
    localeNames: index === 0
      ? { 'zh-CN': '资产主数据', 'en-US': 'Asset Master' }
      : { 'zh-CN': `自定义分类${index}`, 'en-US': `Custom Group ${index}` },
    translationTarget: {
      contentType: 'system.menugroup',
      contentTypeModel: 'menugroup',
      objectId: `${index + 1}`,
      fieldName: 'name',
    },
    icon: 'Menu',
    order: (index + 1) * 10,
    isVisible: true,
    isLocked: false,
    isDefault: index === 0,
    entryCount: index === 0 ? 1 : 0,
    supportsDelete: true,
  }))

const createItems = (count = 10) =>
  Array.from({ length: count }, (_, index) => ({
    code: index === 0 ? 'Asset' : `Entry${index}`,
    name: index === 0 ? '资产' : `Entry ${index}`,
    nameEn: index === 0 ? 'Asset' : `Entry ${index}`,
    translationKey: index === 0 ? 'menu.routes.assetList' : '',
    sourceType: (index === 0 ? 'business_object' : 'static') as 'business_object' | 'static',
    sourceCode: index === 0 ? 'Asset' : `Entry${index}`,
    path: index === 0 ? '/objects/Asset' : `/system/entry-${index}`,
    icon: 'Document',
    groupCode: index === 0 ? 'asset_master' : 'custom_group_1',
    groupTranslationKey: index === 0 ? 'menu.categories.asset_master' : '',
    order: (index + 1) * 10,
    isVisible: true,
    isLocked: index === 0,
    isDefault: index === 0,
    supportsDelete: !index,
    supportsVisibility: true,
    supportsReorder: true,
    supportsGroupChange: true,
  }))

const createManagementPayload = () => ({
  categories: createCategories(),
  items: createItems(),
})

const createWrapper = () => {
  const pinia = createPinia()
  setActivePinia(pinia)

  return mount(SystemMenuManagement, {
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

describe('SystemMenuManagement', () => {
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
    mockMessageWarning.mockReset()
    mockMessageBoxConfirm.mockReset()
    mockRouterPush.mockReset()
    mockSortableCreate.mockReset()
    mockSortableDestroy.mockReset()
    mockConsoleError.mockReset()
    vi.spyOn(console, 'error').mockImplementation(mockConsoleError)

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
    mockMenuManagement.mockResolvedValue(JSON.parse(JSON.stringify(createManagementPayload())))
    mockMenuUpdateManagement.mockImplementation(async (payload) => JSON.parse(JSON.stringify(payload)))
    mockMessageBoxConfirm.mockResolvedValue(undefined)
  })

  it('shows the new resource-management title and readable localized category names', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).toContain('菜单资源管理')
    const inputValues = wrapper.findAll('input').map((input) => input.element.value)
    expect(inputValues).toContain('资产主数据')
    expect(inputValues).not.toContain('menu.categories.asset_master')
  })

  it('locks category code editing and renders icon-library selection', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const codeDisplay = wrapper.findAll('.readonly-code').find((node) => node.text() === 'asset_master')
    expect(codeDisplay).toBeDefined()
    expect(wrapper.findAll('.icon-picker-trigger').length).toBeGreaterThan(0)
    expect(wrapper.find('.entry-detail-card .icon-picker-trigger').exists()).toBe(true)
  })

  it('opens the translation module for a saved menu category', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const translationButton = wrapper.findAll('button').find((button) => button.text().includes('语'))
    expect(translationButton).toBeDefined()
    await translationButton!.trigger('click')

    expect(mockRouterPush).toHaveBeenCalledWith({
      name: 'TranslationList',
      query: {
        type: 'object_field',
        content_type_model: 'menugroup',
        object_id: '1',
        field_name: 'name',
        show_all_languages: '1',
        focus_label: 'Asset Master',
        focus_code: 'asset_master',
      },
    })
  })

  it('renders paginated categories and a focused resource catalog', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.findAll('.pagination-stub')).toHaveLength(1)
    expect(wrapper.findAll('.category-item')).toHaveLength(4)
    expect(wrapper.findAll('.entry-card')).toHaveLength(1)
  })

  it('navigates to the layout workspace from the view switch', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const layoutButton = wrapper.findAll('button').find((button) => button.text() === '菜单布局')
    expect(layoutButton).toBeTruthy()
    await layoutButton!.trigger('click')

    expect(mockRouterPush).toHaveBeenCalledWith({ name: 'MenuLayoutManagement' })
  })

  it('blocks deleting a category that still has entries', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const deleteButtons = wrapper.findAll('button').filter((button) => button.text().includes('删'))
    expect(deleteButtons.length).toBeGreaterThan(0)
    await deleteButtons[0].trigger('click')
    await flushPromises()

    expect(mockMessageWarning).toHaveBeenCalled()
  })

  it('switches to en-US and uses localized success feedback when saving', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const localeStore = useLocaleStore()
    localeStore.setLocale('en-US')
    await flushPromises()

    expect(wrapper.text()).toContain('Menu Resources')
    const saveButton = wrapper.findAll('button').find((button) => button.text() === 'Save')
    expect(saveButton).toBeTruthy()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(mockMenuUpdateManagement).toHaveBeenCalledTimes(1)
    expect(mockMessageSuccess).toHaveBeenCalledWith('Menu configuration saved')
  })

  it('updates item ownership when category selection changes in the resource detail panel', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const localeStore = useLocaleStore()
    localeStore.setLocale('en-US')
    await flushPromises()

    const selects = wrapper.findAll('select')
    expect(selects.length).toBeGreaterThan(0)
    await selects[selects.length - 1].setValue('custom_group_2')
    await flushPromises()

    expect(wrapper.find('.entry-detail-card').text()).toContain('Custom Group 2')
  })

  it('shows an empty resource state when the selected category has no entries', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="category-item-custom_group_2"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('.entry-empty').exists()).toBe(true)
  })

  it('focuses right-side resources on the selected left category by default', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.find('[data-testid="category-item-asset_master"]').classes()).toContain('active')
    expect(wrapper.find('.entry-card').text()).toContain('资产')

    await wrapper.find('[data-testid="category-item-custom_group_1"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="category-item-custom_group_1"]').classes()).toContain('active')
    expect(wrapper.find('.entry-card').text()).toContain('Entry 1')
  })

  it('surfaces backend migration validation messages when saving fails', async () => {
    mockMenuUpdateManagement.mockRejectedValueOnce(new Error('Move them before deleting the category.'))

    const wrapper = createWrapper()
    await flushPromises()

    const saveButton = wrapper.findAll('button').find((button) => button.text().includes('保存'))
    expect(saveButton).toBeTruthy()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(mockMessageError).toHaveBeenCalledWith('Move them before deleting the category.')
    expect(mockConsoleError).not.toHaveBeenCalled()
  })

  it('asks for confirmation before deleting an empty category', async () => {
    mockMenuManagement.mockResolvedValueOnce({
      categories: [
        {
          code: 'custom_empty',
          name: 'Custom Empty',
          translationKey: '',
          icon: 'Menu',
          order: 120,
          isVisible: true,
          isLocked: false,
          isDefault: false,
          entryCount: 0,
          supportsDelete: true,
          localeNames: { 'zh-CN': '空分类', 'en-US': 'Empty Category' },
        },
      ],
      items: [],
    })

    const wrapper = createWrapper()
    await flushPromises()

    const deleteButton = wrapper.findAll('button').find((button) => button.text().includes('删'))
    expect(deleteButton).toBeTruthy()
    await deleteButton!.trigger('click')
    await flushPromises()

    expect(mockMessageBoxConfirm).toHaveBeenCalledTimes(1)
    expect(wrapper.findAll('.category-item')).toHaveLength(0)
  })
})
