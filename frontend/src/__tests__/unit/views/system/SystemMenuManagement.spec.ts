import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import i18n from '@/locales'
import { useLocaleStore } from '@/stores/locale'
import SystemMenuManagement from '@/views/system/SystemMenuManagement.vue'

const {
  mockMenuManagement,
  mockMenuUpdateManagement,
  mockGetActiveLanguages,
  mockMessageSuccess,
  mockMessageError,
  mockMessageWarning,
  mockMessageBoxConfirm,
  mockSortableCreate,
  mockSortableDestroy,
} = vi.hoisted(() => ({
  mockMenuManagement: vi.fn(),
  mockMenuUpdateManagement: vi.fn(),
  mockGetActiveLanguages: vi.fn(),
  mockMessageSuccess: vi.fn(),
  mockMessageError: vi.fn(),
  mockMessageWarning: vi.fn(),
  mockMessageBoxConfirm: vi.fn(),
  mockSortableCreate: vi.fn(),
  mockSortableDestroy: vi.fn(),
}))

vi.mock('sortablejs', () => ({
  default: {
    create: mockSortableCreate,
  },
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: mockMessageSuccess,
    error: mockMessageError,
    warning: mockMessageWarning,
  },
  ElMessageBox: {
    confirm: mockMessageBoxConfirm,
  },
}))

vi.mock('@/api/system', () => ({
  menuApi: {
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
    code: index === 0 ? 'asset_master' : `custom_group_${index}`,
    name: index === 0 ? 'menu.categories.asset_master' : `Custom Group ${index}`,
    translationKey: index === 0 ? 'menu.categories.asset_master' : '',
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
          props: ['modelValue', 'placeholder'],
          emits: ['update:modelValue'],
          template: '<input :value="modelValue" :placeholder="placeholder" @input="$emit(\'update:modelValue\', $event.target.value)" />',
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
        'el-button': {
          props: ['disabled', 'loading', 'type'],
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
    mockMenuManagement.mockReset()
    mockMenuUpdateManagement.mockReset()
    mockGetActiveLanguages.mockReset()
    mockMessageSuccess.mockReset()
    mockMessageError.mockReset()
    mockMessageWarning.mockReset()
    mockMessageBoxConfirm.mockReset()
    mockSortableCreate.mockReset()
    mockSortableDestroy.mockReset()

    mockSortableCreate.mockReturnValue({
      destroy: mockSortableDestroy,
    })

    i18n.global.locale.value = 'zh-CN'
    mockGetActiveLanguages.mockResolvedValue([
      { id: '1', code: 'zh-CN', name: 'Chinese', nativeName: '中文', isDefault: true, isActive: true, sortOrder: 1 },
      { id: '2', code: 'en-US', name: 'English', nativeName: 'English', isDefault: false, isActive: true, sortOrder: 2 },
    ])
    mockMenuManagement.mockResolvedValue(JSON.parse(JSON.stringify(createManagementPayload())))
    mockMenuUpdateManagement.mockImplementation(async (payload) => JSON.parse(JSON.stringify(payload)))
    mockMessageBoxConfirm.mockResolvedValue(undefined)
  })

  it('shows readable default category names instead of translation keys', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).toContain('菜单管理')
    const inputValues = wrapper.findAll('input').map((input) => input.element.value)
    expect(inputValues).toContain('资产台账')
    expect(inputValues).not.toContain('menu.categories.asset_master')
  })

  it('renders paginated category and entry layouts', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.findAll('.pagination-stub')).toHaveLength(1)
    expect(wrapper.findAll('.category-item')).toHaveLength(4)
    expect(wrapper.findAll('.entry-group')).toHaveLength(1)
    expect(wrapper.findAll('.entry-item')).toHaveLength(1)
  })

  it('initializes drag sorting for categories and grouped entry lanes', async () => {
    createWrapper()
    await flushPromises()

    expect(mockSortableCreate.mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('blocks deleting a category that still has entries', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const deleteButtons = wrapper.findAll('button').filter((button) => button.text() === '删除')
    expect(deleteButtons.length).toBeGreaterThan(0)
    await deleteButtons[0].trigger('click')
    await flushPromises()

    expect(mockMessageWarning).toHaveBeenCalledWith('该分类下仍有菜单项，不能删除')
  })

  it('switches to en-US and uses localized success feedback when saving', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const localeStore = useLocaleStore()
    localeStore.setLocale('en-US')
    await flushPromises()

    expect(wrapper.text()).toContain('Menu Management')
    const saveButton = wrapper.findAll('button').find((button) => button.text() === 'Save')
    expect(saveButton).toBeTruthy()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(mockMenuUpdateManagement).toHaveBeenCalledTimes(1)
    expect(mockMessageSuccess).toHaveBeenCalledWith('Menu configuration saved')
  })

  it('regroups entries when category selection changes', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    const localeStore = useLocaleStore()
    localeStore.setLocale('en-US')
    await flushPromises()

    const selects = wrapper.findAll('select')
    expect(selects.length).toBeGreaterThan(0)
    await selects[0].setValue('custom_group_2')
    await flushPromises()

    expect(wrapper.find('.entry-group').text()).toContain('Asset Master')
    expect(wrapper.find('[data-testid="empty-group-asset_master"]').exists()).toBe(true)
  })

  it('shows empty drop zones and supports collapsing entry groups', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    await wrapper.find('[data-testid="category-item-custom_group_2"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="empty-group-custom_group_2"]').exists()).toBe(true)
    expect(wrapper.find('.entry-group-list[data-group-code="custom_group_2"]').exists()).toBe(true)

    await wrapper.find('[data-testid="toggle-group-custom_group_2"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('.entry-group-list[data-group-code="custom_group_2"]').exists()).toBe(false)
  })

  it('focuses right-side entries on the selected left category by default', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.find('[data-testid="category-item-asset_master"]').classes()).toContain('active')
    expect(wrapper.find('.entry-group').text()).toContain('资产主数据')

    await wrapper.find('[data-testid="category-item-custom_group_1"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="category-item-custom_group_1"]').classes()).toContain('active')
    expect(wrapper.find('.entry-group').text()).toContain('Custom Group 1')
  })

  it('surfaces backend migration validation messages when saving fails', async () => {
    mockMenuUpdateManagement.mockRejectedValueOnce(new Error('Move them before deleting the category.'))

    const wrapper = createWrapper()
    await flushPromises()

    const saveButton = wrapper.findAll('button').find((button) => button.text() === '保存')
    expect(saveButton).toBeTruthy()
    await saveButton!.trigger('click')
    await flushPromises()

    expect(mockMessageError).toHaveBeenCalledWith('Move them before deleting the category.')
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
        },
      ],
      items: [],
    })

    const wrapper = createWrapper()
    await flushPromises()

    const deleteButton = wrapper.findAll('button').find((button) => button.text() === '删除')
    expect(deleteButton).toBeTruthy()
    await deleteButton!.trigger('click')
    await flushPromises()

    expect(mockMessageBoxConfirm).toHaveBeenCalledTimes(1)
    expect(wrapper.findAll('.category-item')).toHaveLength(0)
  })
})
