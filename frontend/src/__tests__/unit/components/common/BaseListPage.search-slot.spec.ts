import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'

const apiMock = vi.fn()

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRoute: () => ({
      path: '/objects/Asset',
    }),
  }
})

vi.mock('@/composables/useColumnConfig', () => ({
  useColumnConfig: () => null,
}))

const stubs = {
  ColumnManager: defineComponent({
    name: 'ColumnManager',
    template: '<div class="column-manager-stub" />',
  }),
  FieldRenderer: defineComponent({
    name: 'FieldRenderer',
    template: '<div class="field-renderer-stub" />',
  }),
  ObjectAvatar: defineComponent({
    name: 'ObjectAvatar',
    template: '<div class="object-avatar-stub" />',
  }),
  'el-form': defineComponent({
    name: 'ElForm',
    template: '<form><slot /></form>',
  }),
  'el-form-item': defineComponent({
    name: 'ElFormItem',
    template: '<div><slot /></div>',
  }),
  'el-input': defineComponent({
    name: 'ElInput',
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', ($event.target as HTMLInputElement).value)" />',
  }),
  'el-select': defineComponent({
    name: 'ElSelect',
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<div class="select-stub"><slot /></div>',
  }),
  'el-option': defineComponent({
    name: 'ElOption',
    template: '<div class="option-stub" />',
  }),
  'el-date-picker': defineComponent({
    name: 'ElDatePicker',
    template: '<div class="date-picker-stub" />',
  }),
  'el-button': defineComponent({
    name: 'ElButton',
    emits: ['click'],
    template: '<button @click="$emit(\'click\')"><slot /></button>',
  }),
  'el-table': defineComponent({
    name: 'ElTable',
    template: '<div class="table-stub"><slot /><slot name="empty" /></div>',
  }),
  'el-table-column': defineComponent({
    name: 'ElTableColumn',
    template: '<div class="table-column-stub"><slot /></div>',
  }),
  'el-pagination': defineComponent({
    name: 'ElPagination',
    template: '<div class="pagination-stub" />',
  }),
  'el-empty': defineComponent({
    name: 'ElEmpty',
    template: '<div class="empty-stub" />',
  }),
  'el-skeleton': defineComponent({
    name: 'ElSkeleton',
    template: '<div class="skeleton-stub" />',
  }),
  'el-tag': defineComponent({
    name: 'ElTag',
    template: '<span><slot /></span>',
  }),
  'el-icon': defineComponent({
    name: 'ElIcon',
    template: '<i><slot /></i>',
  }),
}

describe('BaseListPage search slot binding', () => {
  it('persists custom slot search values into the request params', async () => {
    apiMock.mockResolvedValue({
      count: 0,
      results: [],
    })

    const i18n = (await import('@/locales')).default
    const BaseListPage = (await import('@/components/common/BaseListPage.vue')).default

    const wrapper = mount(BaseListPage, {
      props: {
        title: 'Assets',
        api: apiMock,
        tableColumns: [],
        searchFields: [
          {
            prop: '__unifiedKeyword',
            label: 'Search',
            type: 'slot',
          },
        ],
      },
      slots: {
        'search-__unifiedKeyword': `
          <template #default="{ setValue, search }">
            <button class="set-search-value" @click="setValue('__unifiedKeyword', '戴尔')">set</button>
            <button class="submit-search" @click="search()">search</button>
          </template>
        `,
      },
      global: {
        plugins: [i18n],
        directives: {
          loading: () => undefined,
        },
        stubs,
      },
    })

    await flushPromises()
    expect(apiMock).toHaveBeenCalledTimes(1)

    await wrapper.find('.set-search-value').trigger('click')
    await wrapper.find('.submit-search').trigger('click')
    await flushPromises()

    expect(apiMock).toHaveBeenLastCalledWith(
      expect.objectContaining({
        __unifiedKeyword: '戴尔',
      }),
    )
  })
})
