<template>
  <div class="system-menu-management page-container">
    <section class="page-hero">
      <div class="hero-content">
        <div class="hero-kicker">Navigation Control Center</div>
        <h2>{{ copy.title }}</h2>
        <p>{{ copy.subtitle }}</p>
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="hero-stat-label">{{ copy.sections.categories }}</span>
            <strong>{{ orderedCategories.length }}</strong>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-label">{{ copy.sections.entries }}</span>
            <strong>{{ orderedItems.length }}</strong>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-label">{{ copy.fields.visible }}</span>
            <strong>{{ visibleEntryCount }}</strong>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-label">{{ copy.tags.locked }}</span>
            <strong>{{ lockedEntryCount }}</strong>
          </div>
        </div>
      </div>
      <div class="hero-actions">
        <el-button @click="reload">
          {{ copy.actions.reload }}
        </el-button>
        <el-button type="primary" :loading="saving" @click="saveChanges">
          {{ copy.actions.save }}
        </el-button>
      </div>
    </section>

    <el-row :gutter="20">
      <el-col :lg="8" :md="24">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-header panel-header-stacked">
              <div class="panel-heading">
                <div class="panel-title-row">
                  <div class="panel-title">{{ copy.sections.categories }}</div>
                  <div class="panel-pills">
                    <span class="panel-pill">{{ orderedCategories.length }}</span>
                    <span class="panel-pill muted">{{ visibleCategoryCount }} {{ copy.fields.visible }}</span>
                  </div>
                </div>
                <div class="panel-subtitle">{{ copy.sections.categoriesHint }}</div>
              </div>
              <div class="panel-toolbar">
                <el-button size="small" @click="addCategory">
                  {{ copy.actions.addCategory }}
                </el-button>
              </div>
            </div>
          </template>

          <div ref="categoryListRef" class="category-list">
            <div
              v-for="category in pagedCategories"
              :key="category.originalCode"
              class="category-item"
              :class="{ active: isSelectedCategory(category) }"
              :data-row-id="category.originalCode"
              :data-testid="`category-item-${category.originalCode}`"
              @click="selectCategory(category)"
            >
              <div class="category-item-header">
                <div class="category-badges">
                  <span class="drag-handle" :title="copy.labels.dragHandle">::</span>
                  <el-tag size="small" :type="category.isDefault ? 'warning' : 'success'">
                    {{ category.isDefault ? copy.tags.default : copy.tags.custom }}
                  </el-tag>
                  <el-tag size="small" effect="plain">
                    {{ copy.labels.entries }} {{ getCategoryEntryCount(category) }}
                  </el-tag>
                </div>
                <div class="category-actions">
                  <el-button
                    link
                    :disabled="!canMoveCategory(category.originalCode, -1)"
                    @click="moveCategory(category.originalCode, -1)"
                  >
                    {{ copy.actions.moveUp }}
                  </el-button>
                  <el-button
                    link
                    :disabled="!canMoveCategory(category.originalCode, 1)"
                    @click="moveCategory(category.originalCode, 1)"
                  >
                    {{ copy.actions.moveDown }}
                  </el-button>
                  <el-button
                    link
                    type="danger"
                    @click="removeCategory(category.originalCode)"
                  >
                    {{ copy.actions.delete }}
                  </el-button>
                </div>
              </div>

              <div class="category-form-grid">
                <div class="surface-field span-2">
                  <label>{{ copy.fields.categoryName }}</label>
                  <el-input
                    v-model="category.name"
                    :placeholder="copy.placeholders.categoryName"
                  />
                </div>
                <div class="surface-field">
                  <label>{{ copy.fields.categoryCode }}</label>
                  <el-input v-model="category.code" />
                </div>
                <div class="surface-field">
                  <label>{{ copy.fields.icon }}</label>
                  <el-input v-model="category.icon" :placeholder="copy.placeholders.icon" />
                </div>
                <div class="surface-field">
                  <label>{{ copy.fields.order }}</label>
                  <el-input-number
                    v-model="category.order"
                    class="compact-order-input"
                    controls-position="right"
                    :min="1"
                    :max="9999"
                  />
                </div>
                <div class="surface-field toggle-field">
                  <label>{{ copy.fields.visible }}</label>
                  <el-switch v-model="category.isVisible" />
                </div>
              </div>
            </div>
          </div>

          <el-pagination
            class="panel-pagination"
            background
            layout="total, sizes, prev, pager, next"
            :total="orderedCategories.length"
            :current-page="categoryPage"
            :page-size="categoryPageSize"
            :page-sizes="[3, 4, 6, 8]"
            @update:current-page="categoryPage = $event"
            @update:page-size="handleCategoryPageSizeChange"
          />
        </el-card>
      </el-col>

      <el-col :lg="16" :md="24">
        <el-card shadow="never" class="panel-card panel-card-entries">
          <template #header>
            <div class="panel-header panel-header-stacked panel-header-entries sticky-panel-header">
              <div class="panel-header-top panel-header-top-entries">
                <div class="panel-title-row panel-title-row-entries">
                  <div class="panel-title">{{ copy.sections.entries }}</div>
                  <div class="panel-pills">
                    <span class="panel-pill">{{ filteredItems.length }}</span>
                    <span class="panel-pill muted">{{ visibleEntryCount }} {{ copy.fields.visible }}</span>
                    <span class="panel-pill accent">{{ lockedEntryCount }} {{ copy.tags.locked }}</span>
                  </div>
                </div>
                <div class="panel-toolbar panel-toolbar-entries">
                  <el-button size="small" :type="viewAllEntries ? 'default' : 'primary'" @click="viewAllEntries = false">
                    {{ focusModeCopy.current }}
                  </el-button>
                  <el-button size="small" :type="viewAllEntries ? 'primary' : 'default'" @click="viewAllEntries = true">
                    {{ focusModeCopy.all }}
                  </el-button>
                  <el-input
                    v-model="search"
                    class="entry-search"
                    clearable
                    :placeholder="copy.placeholders.search"
                  />
                </div>
              </div>
              <div class="panel-subtitle panel-subtitle-entries">{{ copy.sections.entriesHint }}</div>
            </div>
          </template>

            <div class="entries-workspace">
              <div ref="entryBoardRef" class="entry-board">
              <div
                v-for="group in visibleEntryGroups"
                :key="group.category.originalCode"
                class="entry-group"
                :data-group-code="group.category.code"
              >
                <div class="entry-group-header">
                  <div class="entry-group-heading">
                    <div class="entry-group-title">{{ getCategoryLabel(group.category) }}</div>
                    <div class="entry-group-code">{{ group.category.code }}</div>
                  </div>
                  <div class="entry-group-header-actions">
                    <div class="panel-pills">
                      <span class="panel-pill">{{ group.items.length }} {{ copy.labels.entries }}</span>
                      <span class="panel-pill muted">{{ copy.fields.visible }} {{ group.visibleCount }}</span>
                    </div>
                    <el-button
                      link
                      class="group-toggle"
                      :data-testid="`toggle-group-${group.category.code}`"
                      @click="toggleGroupCollapse(group.category.code)"
                    >
                      {{ getGroupToggleLabel(group.category.code) }}
                    </el-button>
                  </div>
                </div>

                <div
                  v-if="!isGroupCollapsed(group.category.code)"
                  class="entry-group-list"
                  :data-group-code="group.category.code"
                >
                  <div
                    v-if="!group.items.length"
                    class="entry-group-empty"
                    :data-testid="`empty-group-${group.category.code}`"
                  >
                    <strong>{{ emptyGroupCopy.title }}</strong>
                    <span>{{ emptyGroupCopy.hint }}</span>
                  </div>
                  <div
                    v-for="item in group.items"
                    :key="getItemIdentity(item)"
                    class="entry-item"
                    :class="{ active: isSelectedEntry(item) }"
                    :data-row-id="getItemIdentity(item)"
                    :data-testid="`entry-item-${getItemIdentity(item)}`"
                    @click="selectEntry(item)"
                  >
                    <div class="entry-item-top">
                      <div class="entry-title">
                        <span class="drag-handle" :title="copy.labels.dragHandle">::</span>
                        <div class="entry-title-text">
                          <div class="entry-mainline">
                            <strong>{{ getItemLabel(item) }}</strong>
                            <span class="entry-path">{{ item.path }}</span>
                          </div>
                          <span class="entry-code">{{ item.code }}</span>
                        </div>
                      </div>
                      <div class="entry-meta">
                        <el-tag size="small" effect="plain">
                          {{ item.sourceType === 'static' ? copy.tags.static : copy.tags.object }}
                        </el-tag>
                        <el-tag v-if="item.isLocked" size="small" type="warning">
                          {{ copy.tags.locked }}
                        </el-tag>
                      </div>
                    </div>

                    <div class="entry-item-body entry-item-body-compact">
                      <div class="entry-summary">
                        <span>{{ copy.columns.group }}: {{ getItemGroupLabel(item) }}</span>
                        <span>{{ copy.columns.order }}: {{ item.order }}</span>
                        <span>{{ copy.columns.visible }}: {{ item.isVisible ? visibilityCopy.visible : visibilityCopy.hidden }}</span>
                      </div>
                      <div class="entry-actions" @click.stop>
                        <el-button
                          link
                          :disabled="!canMoveItem(item, -1)"
                          @click="moveItem(item, -1)"
                        >
                          {{ copy.actions.moveUp }}
                        </el-button>
                        <el-button
                          link
                          :disabled="!canMoveItem(item, 1)"
                          @click="moveItem(item, 1)"
                        >
                          {{ copy.actions.moveDown }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <aside class="entry-detail" v-if="selectedEntry">
              <div class="entry-detail-card">
                <div class="entry-detail-top">
                  <div class="entry-detail-kicker">{{ detailCopy.kicker }}</div>
                  <h3>{{ getItemLabel(selectedEntry) }}</h3>
                  <p>{{ selectedEntry.path }}</p>
                </div>

                <div class="entry-detail-meta">
                  <el-tag size="small" effect="plain">
                    {{ selectedEntry.sourceType === 'static' ? copy.tags.static : copy.tags.object }}
                  </el-tag>
                  <el-tag v-if="selectedEntry.isLocked" size="small" type="warning">
                    {{ copy.tags.locked }}
                  </el-tag>
                  <el-tag size="small" type="info">
                    {{ getItemGroupLabel(selectedEntry) }}
                  </el-tag>
                </div>

                <div class="entry-detail-stack">
                  <div class="entry-field">
                    <label>{{ detailCopy.entryCode }}</label>
                    <el-input :model-value="selectedEntry.code" disabled />
                  </div>
                  <div class="entry-field">
                    <label>{{ copy.columns.group }}</label>
                    <el-select
                      :model-value="selectedEntry.groupCode"
                      @update:modelValue="handleItemGroupChange(selectedEntry, String($event))"
                    >
                      <el-option
                        v-for="category in selectableCategories"
                        :key="category.originalCode"
                        :label="getCategoryLabel(category)"
                        :value="category.code"
                      />
                    </el-select>
                  </div>
                  <div class="entry-grid entry-detail-grid">
                    <div class="entry-field">
                      <label>{{ copy.columns.order }}</label>
                      <el-input-number
                        v-model="selectedEntry.order"
                        class="compact-order-input"
                        controls-position="right"
                        :min="1"
                        :max="9999"
                      />
                    </div>
                    <div class="entry-field entry-field-toggle">
                      <label>{{ copy.columns.visible }}</label>
                      <el-switch v-model="selectedEntry.isVisible" />
                    </div>
                  </div>
                </div>

                <div class="entry-detail-actions">
                  <el-button
                    link
                    :disabled="!canMoveItem(selectedEntry, -1)"
                    @click="moveItem(selectedEntry, -1)"
                  >
                    {{ copy.actions.moveUp }}
                  </el-button>
                  <el-button
                    link
                    :disabled="!canMoveItem(selectedEntry, 1)"
                    @click="moveItem(selectedEntry, 1)"
                  >
                    {{ copy.actions.moveDown }}
                  </el-button>
                </div>
              </div>
            </aside>
          </div>

          <el-pagination
            v-if="viewAllEntries && visibleEntryGroups.length > 0"
            class="panel-pagination"
            background
            layout="total, sizes, prev, pager, next"
            :total="displayedEntryGroups.length"
            :current-page="entryPage"
            :page-size="entryPageSize"
            :page-sizes="[2, 3, 4, 6]"
            @update:current-page="entryPage = $event"
            @update:page-size="handleEntryPageSizeChange"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import Sortable from 'sortablejs'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { menuApi, type MenuManagementCategory, type MenuManagementItem } from '@/api/system'
import { useLocaleStore } from '@/stores/locale'

type LocaleKey = 'zh-CN' | 'en-US'

type EditableCategory = MenuManagementCategory & {
  originalCode: string
}

const BUILTIN_CATEGORY_LABELS: Record<LocaleKey, Record<string, string>> = {
  'zh-CN': {
    asset_master: '资产台账',
    asset_operation: '资产作业',
    lifecycle: '资产生命周期',
    consumable: '耗材管理',
    inventory: '盘点管理',
    finance: '财务管理',
    organization: '组织管理',
    workflow: '工作流',
    system: '系统管理',
    reports: '报表中心',
    other: '其他',
  },
  'en-US': {
    asset_master: 'Asset Master',
    asset_operation: 'Asset Operation',
    lifecycle: 'Lifecycle',
    consumable: 'Consumables',
    inventory: 'Inventory',
    finance: 'Finance',
    organization: 'Organization',
    workflow: 'Workflow',
    system: 'System',
    reports: 'Reports',
    other: 'Other',
  },
}

const COPY = {
  'zh-CN': {
    title: '菜单管理',
    subtitle: '统一管理菜单分类和菜单项。分类本身可以调整、删除和重排；只有默认对象菜单项保持锁定。',
    actions: {
      save: '保存',
      reload: '重新加载',
      addCategory: '新增分类',
      moveUp: '上移',
      moveDown: '下移',
      delete: '删除',
    },
    sections: {
      categories: '菜单分类',
      categoriesHint: '左侧分类支持分页和拖拽排序。默认分类也可修改、删除和重排，但删除前需要先迁移分类下菜单项。',
      entries: '菜单项',
      entriesHint: '右侧菜单项支持分页和拖拽排序。只有默认对象菜单会保持锁定；系统静态页和普通菜单项可以重新分组与排序。',
    },
    fields: {
      categoryCode: '分类编码',
      categoryName: '分类名称',
      icon: '图标',
      order: '排序',
      visible: '显示',
    },
    columns: {
      group: '所属分类',
      order: '排序',
      visible: '显示',
    },
    tags: {
      default: '默认',
      custom: '自定义',
      locked: '硬锁',
      static: '系统页',
      object: '对象',
    },
    labels: {
      entries: '条目',
      dragHandle: '拖拽排序',
    },
    placeholders: {
      categoryName: '请输入分类名称',
      icon: '例如 Setting、Grid、Files',
      search: '按名称、编码或路由搜索',
    },
    messages: {
      loadFailed: '加载菜单管理数据失败',
      saveSuccess: '菜单配置已保存',
      saveFailed: '菜单配置保存失败',
      duplicateCategory: '分类编码不能重复',
      invalidCategory: '分类编码不能为空，且只能包含字母、数字、下划线和中划线',
      categoryInUse: '该分类下仍有菜单项，不能删除',
      confirmDeleteTitle: '删除分类',
      confirmDeleteMessage: '确认删除分类“{name}”吗？删除后不会自动迁移其下菜单项。',
    },
  },
  'en-US': {
    title: 'Menu Management',
    subtitle: 'Manage menu categories and menu entries in one place. Categories can be edited, removed, and reordered; only default business-object entries remain locked.',
    actions: {
      save: 'Save',
      reload: 'Reload',
      addCategory: 'Add Category',
      moveUp: 'Up',
      moveDown: 'Down',
      delete: 'Delete',
    },
    sections: {
      categories: 'Categories',
      categoriesHint: 'The category list is paginated and supports drag sorting. Default categories can also be edited, deleted, and reordered, but entries must be migrated first.',
      entries: 'Entries',
      entriesHint: 'The entry list is paginated and supports drag sorting. Only default business-object entries remain locked.',
    },
    fields: {
      categoryCode: 'Category Code',
      categoryName: 'Category Name',
      icon: 'Icon',
      order: 'Order',
      visible: 'Visible',
    },
    columns: {
      group: 'Category',
      order: 'Order',
      visible: 'Visible',
    },
    tags: {
      default: 'Default',
      custom: 'Custom',
      locked: 'Locked',
      static: 'Static',
      object: 'Object',
    },
    labels: {
      entries: 'Entries',
      dragHandle: 'Drag to reorder',
    },
    placeholders: {
      categoryName: 'Enter category name',
      icon: 'Example: Setting, Grid, Files',
      search: 'Search by name, code, or route',
    },
    messages: {
      loadFailed: 'Failed to load menu management data',
      saveSuccess: 'Menu configuration saved',
      saveFailed: 'Failed to save menu configuration',
      duplicateCategory: 'Category code must be unique',
      invalidCategory: 'Category code is required and may only contain letters, numbers, underscores, and hyphens',
      categoryInUse: 'This category still has menu entries and cannot be deleted',
      confirmDeleteTitle: 'Delete Category',
      confirmDeleteMessage: 'Delete category "{name}"? Entries will not be migrated automatically.',
    },
  },
} as const

const localeStore = useLocaleStore()
const { t, te } = useI18n()
const loading = ref(false)
const saving = ref(false)
const search = ref('')
const categories = ref<EditableCategory[]>([])
const items = ref<MenuManagementItem[]>([])
const categoryPage = ref(1)
const categoryPageSize = ref(4)
const entryPage = ref(1)
const entryPageSize = ref(3)
const collapsedGroupCodes = ref<string[]>([])
const selectedCategoryCode = ref('')
const viewAllEntries = ref(false)
const selectedEntryId = ref('')
const categoryListRef = ref<HTMLElement | null>(null)
const entryBoardRef = ref<HTMLElement | null>(null)

let categorySortable: Sortable | null = null
const entrySortables = new Map<string, Sortable>()

const currentLocale = computed<LocaleKey>(() => localeStore.currentLocale === 'en-US' ? 'en-US' : 'zh-CN')
const copy = computed(() => COPY[currentLocale.value])
const detailCopy = computed(() => (
  currentLocale.value === 'en-US'
    ? { kicker: 'Entry Detail', entryCode: 'Entry Code' }
    : { kicker: '项详情', entryCode: '菜单编码' }
))
const focusModeCopy = computed(() => (
  currentLocale.value === 'en-US'
    ? { current: 'Current Category', all: 'View All' }
    : { current: '当前分类', all: '查看全部' }
))
const visibilityCopy = computed(() => (
  currentLocale.value === 'en-US'
    ? { visible: 'Visible', hidden: 'Hidden' }
    : { visible: '显示', hidden: '隐藏' }
))
const emptyGroupCopy = computed(() => (
  currentLocale.value === 'en-US'
    ? {
        title: 'No entries yet',
        hint: 'Drop menu items here, or move them with the category selector.',
      }
    : {
        title: '暂无菜单项',
        hint: '可以直接拖入到该分类，或通过下拉选择切换归属。',
      }
))

const sortByOrder = <T extends { order: number; code: string }>(collection: T[]) =>
  [...collection].sort((a, b) => a.order - b.order || a.code.localeCompare(b.code))

const normalizeOrder = <T extends { order: number }>(collection: T[]) => {
  collection.forEach((item, index) => {
    item.order = (index + 1) * 10
  })
}

const humanizeCode = (code: string) =>
  String(code || '').replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()).trim()

const getBuiltinCategoryLabel = (code: string) =>
  BUILTIN_CATEGORY_LABELS[currentLocale.value][code] || humanizeCode(code)

const isGroupCollapsed = (groupCode: string) => collapsedGroupCodes.value.includes(groupCode)

const getGroupToggleLabel = (groupCode: string) => {
  if (currentLocale.value === 'en-US') {
    return isGroupCollapsed(groupCode) ? 'Expand' : 'Collapse'
  }
  return isGroupCollapsed(groupCode) ? '展开' : '收起'
}

const toggleGroupCollapse = (groupCode: string) => {
  collapsedGroupCodes.value = isGroupCollapsed(groupCode)
    ? collapsedGroupCodes.value.filter((code) => code !== groupCode)
    : [...collapsedGroupCodes.value, groupCode]
}

const syncCollapsedGroups = () => {
  const validCodes = new Set(orderedCategories.value.map((category) => category.code))
  collapsedGroupCodes.value = collapsedGroupCodes.value.filter((code) => validCodes.has(code))
}

const shouldUseDefaultCategoryLabel = (category: Pick<EditableCategory, 'code' | 'name' | 'translationKey' | 'isDefault'>) => {
  const name = String(category.name || '').trim()
  const translationKey = String(category.translationKey || '').trim()
  return (
    category.isDefault &&
    (
      !name ||
      name === translationKey ||
      name.startsWith('menu.') ||
      name === humanizeCode(category.code)
    )
  )
}

const getCategoryLabel = (category: Pick<EditableCategory, 'translationKey' | 'name' | 'code' | 'isDefault'>) => {
  if (shouldUseDefaultCategoryLabel(category as EditableCategory)) {
    return getBuiltinCategoryLabel(category.code)
  }
  const translationKey = String(category.translationKey || '').trim()
  if (translationKey && te(translationKey)) {
    const translated = t(translationKey)
    if (translated && !translated.startsWith('menu.')) {
      return translated
    }
  }
  return String(category.name || category.code)
}

const hydrateCategory = (category: MenuManagementCategory): EditableCategory => ({
  ...category,
  originalCode: category.code,
  isLocked: false,
  supportsDelete: true,
  name: getCategoryLabel({
    code: category.code,
    name: category.name,
    translationKey: category.translationKey,
    isDefault: category.isDefault,
  }),
})

const orderedCategories = computed(() => sortByOrder(categories.value))
const orderedItems = computed(() => sortByOrder(items.value))

const selectableCategories = computed(() => orderedCategories.value)
const selectedCategory = computed(() =>
  orderedCategories.value.find((category) => category.originalCode === selectedCategoryCode.value || category.code === selectedCategoryCode.value) || null
)

const isItemInCategory = (
  item: Pick<MenuManagementItem, 'groupCode'>,
  category: Pick<EditableCategory, 'code' | 'originalCode'>,
) => {
  const groupCode = String(item.groupCode || '').trim()
  return groupCode === category.code.trim() || groupCode === category.originalCode
}

const getItemCategory = (item: Pick<MenuManagementItem, 'groupCode'>) =>
  orderedCategories.value.find((category) => isItemInCategory(item, category))

const getItemsForCategory = (category: Pick<EditableCategory, 'code' | 'originalCode'>) =>
  sortByOrder(items.value.filter((item) => isItemInCategory(item, category)))

const getCategoryEntryCount = (category: Pick<EditableCategory, 'code' | 'originalCode'>) =>
  items.value.filter((item) => isItemInCategory(item, category)).length

const getItemGroupLabel = (item: Pick<MenuManagementItem, 'groupCode'>) => {
  const category = getItemCategory(item)
  return category ? getCategoryLabel(category) : String(item.groupCode || '')
}

const filteredItems = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  if (!keyword) return orderedItems.value
  return orderedItems.value.filter((item) => {
    const label = getItemLabel(item).toLowerCase()
    return (
      label.includes(keyword) ||
      item.code.toLowerCase().includes(keyword) ||
      item.path.toLowerCase().includes(keyword)
    )
  })
})

const filteredEntryGroups = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  return orderedCategories.value
    .map((category) => {
      const categoryItems = getItemsForCategory(category)
      const categoryMatches = !keyword || getCategoryLabel(category).toLowerCase().includes(keyword) || category.code.toLowerCase().includes(keyword)
      const groupItems = categoryMatches
        ? categoryItems
        : categoryItems.filter((item) => {
            const label = getItemLabel(item).toLowerCase()
            return (
              label.includes(keyword) ||
              item.code.toLowerCase().includes(keyword) ||
              item.path.toLowerCase().includes(keyword)
            )
          })

      return {
        category,
        items: groupItems,
        visibleCount: groupItems.filter((item) => item.isVisible).length,
      }
    })
    .filter((group) => !keyword || group.items.length > 0)
})

const displayedEntryGroups = computed(() => {
  if (viewAllEntries.value || !selectedCategory.value) {
    return filteredEntryGroups.value
  }

  const category = selectedCategory.value
  const keyword = search.value.trim().toLowerCase()
  const categoryItems = getItemsForCategory(category)
  const categoryMatches = !keyword || getCategoryLabel(category).toLowerCase().includes(keyword) || category.code.toLowerCase().includes(keyword)
  const groupItems = categoryMatches
    ? categoryItems
    : categoryItems.filter((item) => {
        const label = getItemLabel(item).toLowerCase()
        return (
          label.includes(keyword) ||
          item.code.toLowerCase().includes(keyword) ||
          item.path.toLowerCase().includes(keyword)
        )
      })

  return [{
    category,
    items: groupItems,
    visibleCount: groupItems.filter((item) => item.isVisible).length,
  }]
})

const categoryPageCount = computed(() =>
  Math.max(1, Math.ceil(orderedCategories.value.length / categoryPageSize.value))
)

const entryPageCount = computed(() =>
  Math.max(1, Math.ceil(displayedEntryGroups.value.length / entryPageSize.value))
)

const pagedCategories = computed(() => {
  const start = (categoryPage.value - 1) * categoryPageSize.value
  return orderedCategories.value.slice(start, start + categoryPageSize.value)
})

const pagedEntryGroups = computed(() => {
  const start = (entryPage.value - 1) * entryPageSize.value
  return displayedEntryGroups.value.slice(start, start + entryPageSize.value)
})

const visibleEntryGroups = computed(() =>
  viewAllEntries.value ? pagedEntryGroups.value : displayedEntryGroups.value
)

const visibleCategoryCount = computed(() =>
  orderedCategories.value.filter((item) => item.isVisible).length
)

const visibleEntryCount = computed(() =>
  orderedItems.value.filter((item) => item.isVisible).length
)

const lockedEntryCount = computed(() =>
  orderedItems.value.filter((item) => item.isLocked).length
)

const visibleEntryItems = computed(() =>
  visibleEntryGroups.value.flatMap((group) => group.items)
)

const selectedEntry = computed<MenuManagementItem | null>(() => {
  if (!visibleEntryItems.value.length) return null
  if (selectedEntryId.value) {
    const matched = visibleEntryItems.value.find((item) => getItemIdentity(item) === selectedEntryId.value)
    if (matched) return matched
  }
  return visibleEntryItems.value[0] || null
})

const getItemLabel = (item: Pick<MenuManagementItem, 'translationKey' | 'name' | 'nameEn' | 'code'>) => {
  if (item.translationKey && te(item.translationKey)) {
    const translated = t(item.translationKey)
    if (translated && !translated.startsWith('menu.')) {
      return translated
    }
  }
  if (currentLocale.value === 'en-US' && item.nameEn) {
    return item.nameEn
  }
  return item.name || item.code
}

const getItemIdentity = (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) =>
  `${item.sourceType}:${item.sourceCode || item.code}`

const selectEntry = (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) => {
  selectedEntryId.value = getItemIdentity(item)
}

const isSelectedEntry = (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) =>
  selectedEntry.value ? getItemIdentity(item) === getItemIdentity(selectedEntry.value) : false

const syncSelectedEntry = () => {
  if (!visibleEntryItems.value.length) {
    selectedEntryId.value = ''
    return
  }
  if (!selectedEntryId.value || !visibleEntryItems.value.some((item) => getItemIdentity(item) === selectedEntryId.value)) {
    selectedEntryId.value = getItemIdentity(visibleEntryItems.value[0])
  }
}

const selectCategory = (category: Pick<EditableCategory, 'originalCode' | 'code'>) => {
  selectedCategoryCode.value = category.originalCode
  viewAllEntries.value = false
}

const isSelectedCategory = (category: Pick<EditableCategory, 'originalCode' | 'code'>) =>
  (selectedCategory.value?.originalCode || selectedCategory.value?.code) === category.originalCode

const reorderByPageMove = <T>(
  collection: T[],
  visibleItems: T[],
  oldIndex: number,
  newIndex: number,
  identity: (item: T) => string,
) => {
  if (oldIndex === newIndex) return collection
  const movedVisible = visibleItems[oldIndex]
  const targetVisible = visibleItems[newIndex]
  if (!movedVisible || !targetVisible) return collection

  const next = [...collection]
  const movedId = identity(movedVisible)
  const targetId = identity(targetVisible)
  const movedCollectionIndex = next.findIndex((item) => identity(item) === movedId)
  if (movedCollectionIndex < 0) return collection

  const [movedItem] = next.splice(movedCollectionIndex, 1)
  const targetCollectionIndex = next.findIndex((item) => identity(item) === targetId)
  if (targetCollectionIndex < 0) {
    next.push(movedItem)
    return next
  }

  const insertIndex = oldIndex < newIndex ? targetCollectionIndex + 1 : targetCollectionIndex
  next.splice(insertIndex, 0, movedItem)
  return next
}

const rebuildCategorySortable = async () => {
  await nextTick()
  categorySortable?.destroy()
  const container = categoryListRef.value
  if (!container) return
  categorySortable = Sortable.create(container, {
    animation: 180,
    handle: '.drag-handle',
    draggable: '.category-item',
    onEnd: (event) => {
      if (event.oldIndex == null || event.newIndex == null || event.oldIndex === event.newIndex) return
      const reordered = reorderByPageMove(
        orderedCategories.value,
        pagedCategories.value,
        event.oldIndex,
        event.newIndex,
        (item) => item.originalCode,
      )
      normalizeOrder(reordered)
      categories.value = reordered
    },
  })
}

const destroyEntrySortables = () => {
  for (const sortable of entrySortables.values()) {
    sortable.destroy()
  }
  entrySortables.clear()
}

const syncItemCollections = (updates: Map<string, { groupCode: string; order: number }>) => {
  items.value = items.value.map((item) => {
    const update = updates.get(getItemIdentity(item))
    return update ? { ...item, ...update } : item
  })
}

const applyGroupOrder = (
  category: Pick<EditableCategory, 'code'>,
  groupItems: MenuManagementItem[],
  updates: Map<string, { groupCode: string; order: number }>,
) => {
  groupItems.forEach((item, index) => {
    updates.set(getItemIdentity(item), {
      groupCode: category.code.trim(),
      order: (index + 1) * 10,
    })
  })
}

const handleEntryBoardDrag = (
  sourceGroupCode: string,
  targetGroupCode: string,
  oldIndex: number,
  newIndex: number,
) => {
  const sourceCategory = orderedCategories.value.find((category) => category.code === sourceGroupCode)
  const targetCategory = orderedCategories.value.find((category) => category.code === targetGroupCode)
  if (!sourceCategory || !targetCategory) return

  const sourceItems = [...getItemsForCategory(sourceCategory)]
  const targetItems = sourceCategory.originalCode === targetCategory.originalCode ? sourceItems : [...getItemsForCategory(targetCategory)]
  const [movedItem] = sourceItems.splice(oldIndex, 1)
  if (!movedItem) return

  targetItems.splice(newIndex, 0, {
    ...movedItem,
    groupCode: targetCategory.code.trim(),
  })

  const updates = new Map<string, { groupCode: string; order: number }>()
  applyGroupOrder(targetCategory, targetItems, updates)
  if (sourceCategory.originalCode !== targetCategory.originalCode) {
    applyGroupOrder(sourceCategory, sourceItems, updates)
  }
  syncItemCollections(updates)
}

const rebuildEntrySortable = async () => {
  await nextTick()
  destroyEntrySortables()
  const board = entryBoardRef.value
  if (!board) return

  const containers = Array.from(board.querySelectorAll<HTMLElement>('.entry-group-list'))
  containers.forEach((container) => {
    const groupCode = container.dataset.groupCode
    if (!groupCode) return
    const sortable = Sortable.create(container, {
      animation: 180,
      handle: '.drag-handle',
      draggable: '.entry-item',
      group: 'menu-entry-groups',
      onEnd: (event) => {
        if (event.oldIndex == null || event.newIndex == null) return
        const sourceGroupCode = (event.from as HTMLElement | null)?.dataset.groupCode
        const targetGroupCode = (event.to as HTMLElement | null)?.dataset.groupCode
        if (!sourceGroupCode || !targetGroupCode) return
        if (sourceGroupCode === targetGroupCode && event.oldIndex === event.newIndex) return
        handleEntryBoardDrag(sourceGroupCode, targetGroupCode, event.oldIndex, event.newIndex)
      },
    })
    entrySortables.set(groupCode, sortable)
  })
}

const syncPaginationBounds = () => {
  if (categoryPage.value > categoryPageCount.value) {
    categoryPage.value = categoryPageCount.value
  }
  if (entryPage.value > entryPageCount.value) {
    entryPage.value = entryPageCount.value
  }
}

const handleCategoryPageSizeChange = (value: number) => {
  categoryPageSize.value = value
  categoryPage.value = 1
}

const handleEntryPageSizeChange = (value: number) => {
  entryPageSize.value = value
  entryPage.value = 1
}

const canMoveCategory = (originalCode: string, offset: -1 | 1) => {
  const current = orderedCategories.value
  const index = current.findIndex((item) => item.originalCode === originalCode)
  const targetIndex = index + offset
  return index >= 0 && targetIndex >= 0 && targetIndex < current.length
}

const moveCategory = (originalCode: string, offset: -1 | 1) => {
  const current = [...orderedCategories.value]
  const index = current.findIndex((item) => item.originalCode === originalCode)
  const targetIndex = index + offset
  if (index < 0 || targetIndex < 0 || targetIndex >= current.length) return
  ;[current[index], current[targetIndex]] = [current[targetIndex], current[index]]
  normalizeOrder(current)
  categories.value = current
}

const canMoveItem = (item: Pick<MenuManagementItem, 'groupCode' | 'sourceType' | 'sourceCode' | 'code'>, offset: -1 | 1) => {
  const category = getItemCategory(item)
  if (!category) return false
  const current = getItemsForCategory(category)
  const index = current.findIndex((entry) => getItemIdentity(entry) === getItemIdentity(item))
  const targetIndex = index + offset
  return index >= 0 && targetIndex >= 0 && targetIndex < current.length
}

const moveItem = (item: Pick<MenuManagementItem, 'groupCode' | 'sourceType' | 'sourceCode' | 'code'>, offset: -1 | 1) => {
  const category = getItemCategory(item)
  if (!category) return
  const current = [...getItemsForCategory(category)]
  const index = current.findIndex((entry) => getItemIdentity(entry) === getItemIdentity(item))
  const targetIndex = index + offset
  if (index < 0 || targetIndex < 0 || targetIndex >= current.length) return
  ;[current[index], current[targetIndex]] = [current[targetIndex], current[index]]
  const updates = new Map<string, { groupCode: string; order: number }>()
  applyGroupOrder(category, current, updates)
  syncItemCollections(updates)
}

const buildGroupCodeMap = () => {
  const codeMap = new Map<string, string>()
  for (const category of categories.value) {
    codeMap.set(category.originalCode, category.code.trim())
  }
  return codeMap
}

const reload = async () => {
  loading.value = true
  try {
    const payload = await menuApi.management()
    categories.value = payload.categories.map(hydrateCategory)
    items.value = payload.items
    if (!selectedCategoryCode.value && payload.categories.length) {
      selectedCategoryCode.value = payload.categories[0].code
    }
    syncSelectedEntry()
    syncCollapsedGroups()
    syncPaginationBounds()
  } catch (error) {
    console.error('[menu-management] load failed', error)
    ElMessage.error(copy.value.messages.loadFailed)
  } finally {
    loading.value = false
  }
}

const addCategory = () => {
  const index = categories.value.filter((item) => !item.isDefault).length + 1
  const code = `custom_group_${index}`
  categories.value.push({
    code,
    originalCode: code,
    name: currentLocale.value === 'en-US' ? `Custom Group ${index}` : `自定义分类 ${index}`,
    translationKey: '',
    icon: 'Menu',
    order: (Math.max(0, ...categories.value.map((item) => item.order)) || 0) + 10,
    isVisible: true,
    isLocked: false,
    isDefault: false,
    entryCount: 0,
    supportsDelete: true,
  })
  categoryPage.value = categoryPageCount.value
}

const handleItemGroupChange = (
  item: Pick<MenuManagementItem, 'groupCode' | 'sourceType' | 'sourceCode' | 'code'>,
  targetGroupCode: string,
) => {
  const sourceCategory = getItemCategory(item)
  const targetCategory = orderedCategories.value.find((category) => category.code === targetGroupCode)
  if (!sourceCategory || !targetCategory || sourceCategory.originalCode === targetCategory.originalCode) {
    items.value = items.value.map((entry) =>
      getItemIdentity(entry) === getItemIdentity(item)
        ? { ...entry, groupCode: targetGroupCode }
        : entry,
    )
    return
  }

  const sourceItems = getItemsForCategory(sourceCategory).filter((entry) => getItemIdentity(entry) !== getItemIdentity(item))
  const movingItem = items.value.find((entry) => getItemIdentity(entry) === getItemIdentity(item))
  if (!movingItem) return
  const targetItems = [...getItemsForCategory(targetCategory), { ...movingItem, groupCode: targetCategory.code.trim() }]
  const updates = new Map<string, { groupCode: string; order: number }>()
  applyGroupOrder(sourceCategory, sourceItems, updates)
  applyGroupOrder(targetCategory, targetItems, updates)
  syncItemCollections(updates)
}

const removeCategory = async (originalCode: string) => {
  const category = categories.value.find((item) => item.originalCode === originalCode)
  if (!category) return

  const currentCode = category.code.trim()
  const inUse = items.value.some((item) => item.groupCode === currentCode || item.groupCode === originalCode)
  if (inUse) {
    ElMessage.warning(copy.value.messages.categoryInUse)
    return
  }

  try {
    await ElMessageBox.confirm(
      copy.value.messages.confirmDeleteMessage.replace('{name}', category.name || currentCode),
      copy.value.messages.confirmDeleteTitle,
      { type: 'warning' },
    )
  } catch {
    return
  }

  categories.value = categories.value.filter((item) => item.originalCode !== originalCode)
  syncPaginationBounds()
}

const validateCategories = () => {
  const seen = new Set<string>()
  for (const category of categories.value) {
    const code = category.code.trim()
    if (!code || !/^[A-Za-z0-9_-]+$/.test(code)) {
      ElMessage.error(copy.value.messages.invalidCategory)
      return false
    }
    if (seen.has(code)) {
      ElMessage.error(copy.value.messages.duplicateCategory)
      return false
    }
    seen.add(code)
  }
  return true
}

const saveChanges = async () => {
  if (!validateCategories()) return

  saving.value = true
  try {
    const groupCodeMap = buildGroupCodeMap()
    const payload = {
      categories: orderedCategories.value.map((category) => ({
        code: category.code.trim(),
        name: category.name.trim() || category.code.trim(),
        translationKey: category.translationKey,
        icon: category.icon,
        order: category.order,
        isVisible: category.isVisible,
        isLocked: false,
        isDefault: category.isDefault,
        entryCount: getCategoryEntryCount(category),
        supportsDelete: true,
      })),
      items: orderedItems.value.map((item) => ({
        ...item,
        groupCode: groupCodeMap.get(item.groupCode) || item.groupCode.trim(),
      })),
    }
    const saved = await menuApi.updateManagement(payload)
    categories.value = saved.categories.map(hydrateCategory)
    items.value = saved.items
    if (!selectedCategoryCode.value && saved.categories.length) {
      selectedCategoryCode.value = saved.categories[0].code
    }
    syncSelectedEntry()
    syncCollapsedGroups()
    syncPaginationBounds()
    ElMessage.success(copy.value.messages.saveSuccess)
  } catch (error) {
    console.error('[menu-management] save failed', error)
    const message = error instanceof Error && error.message
      ? error.message
      : copy.value.messages.saveFailed
    ElMessage.error(message)
  } finally {
    saving.value = false
  }
}

watch(
  () => [pagedCategories.value.map((item) => item.originalCode).join('|'), categoryPage.value, categoryPageSize.value],
  () => {
    void rebuildCategorySortable()
  },
)

watch(
  () => [visibleEntryGroups.value.map((group) => `${group.category.originalCode}:${group.items.map((item) => getItemIdentity(item)).join('|')}`).join('||'), entryPage.value, entryPageSize.value, search.value, collapsedGroupCodes.value.join('|'), viewAllEntries.value, selectedCategoryCode.value],
  () => {
    void rebuildEntrySortable()
  },
)

watch(
  () => currentLocale.value,
  () => {
    categories.value = categories.value.map((category) => ({
      ...category,
      name: shouldUseDefaultCategoryLabel(category) ? getBuiltinCategoryLabel(category.code) : category.name,
    }))
  },
)

watch(
  () => [orderedCategories.value.length, filteredEntryGroups.value.length],
  () => {
    syncPaginationBounds()
  },
)

watch(
  () => orderedItems.value.map((item) => getItemIdentity(item)).join('|'),
  () => {
    syncSelectedEntry()
  },
)

watch(
  () => orderedCategories.value.map((category) => category.code).join('|'),
  () => {
    if (!selectedCategory.value && orderedCategories.value.length) {
      selectedCategoryCode.value = orderedCategories.value[0].originalCode
    }
    syncCollapsedGroups()
  },
)

onMounted(async () => {
  await localeStore.initialize()
  await reload()
  await rebuildCategorySortable()
  await rebuildEntrySortable()
})

onBeforeUnmount(() => {
  categorySortable?.destroy()
  destroyEntrySortables()
})
</script>

<style scoped lang="scss">
.system-menu-management {
  --surface-0: #f5f7fb;
  --surface-1: #ffffff;
  --surface-2: #eef3fb;
  --line-soft: #d8e1ee;
  --line-strong: #c7d3e3;
  --ink-strong: #10203a;
  --ink-body: #41556f;
  --ink-soft: #71839b;
  --brand: #10203a;
  --brand-soft: #dbe7f7;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 12px;
}

.page-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 24px 28px;
  border: 1px solid var(--line-soft);
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(16, 32, 58, 0.08), transparent 30%),
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
}

.hero-content {
  min-width: 0;
}

.hero-kicker {
  margin-bottom: 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7b8ca5;
}

.page-hero h2 {
  margin: 0;
  font-size: 34px;
  line-height: 1.05;
  color: var(--ink-strong);
}

.page-hero p {
  margin: 12px 0 0;
  max-width: 920px;
  color: var(--ink-body);
  line-height: 1.75;
  font-size: 15px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  align-self: flex-start;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 20px;
  max-width: 760px;
}

.hero-stat {
  padding: 14px 16px;
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
}

.hero-stat strong {
  display: block;
  margin-top: 6px;
  font-size: 22px;
  color: var(--ink-strong);
}

.hero-stat-label {
  font-size: 12px;
  color: var(--ink-soft);
}

.panel-card {
  overflow: hidden;
  border-radius: 24px !important;
  border: 1px solid var(--line-soft) !important;
  background: linear-gradient(180deg, #ffffff 0%, #f9fbfe 100%);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.04);
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.panel-header-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.panel-header-stacked {
  padding-bottom: 4px;
}

.panel-heading {
  min-width: 0;
  flex: 1 1 auto;
}

.panel-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.panel-title {
  font-size: 26px;
  line-height: 1.1;
  font-weight: 800;
  color: var(--ink-strong);
}

.panel-subtitle {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-body);
  max-width: 760px;
}

.panel-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-header-entries {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
}

.panel-header-top-entries {
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 16px;
}

.panel-title-row-entries {
  flex: 1 1 320px;
  min-width: 0;
  gap: 12px;
}

.panel-toolbar-entries {
  flex: 1 1 420px;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
}

.panel-subtitle-entries {
  margin-top: 0;
  max-width: none;
}

.sticky-panel-header {
  position: sticky;
  top: 12px;
  z-index: 6;
  padding: 10px 0 14px;
  margin: -10px 0 0;
  background: linear-gradient(180deg, rgba(249, 251, 254, 0.98) 0%, rgba(249, 251, 254, 0.88) 75%, rgba(249, 251, 254, 0) 100%);
  backdrop-filter: blur(8px);
}

.panel-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.panel-pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: #edf3fb;
  color: var(--ink-strong);
  font-size: 12px;
  font-weight: 700;
}

.panel-pill.muted {
  background: #f1f5f9;
  color: var(--ink-body);
}

.panel-pill.accent {
  background: var(--brand-soft);
  color: var(--brand);
}

.entry-search {
  width: 320px;
  max-width: 100%;
}

.entries-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 0.95fr);
  gap: 18px;
  align-items: start;
}

.category-list,
.entry-board {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 180px;
}

.entry-board {
  gap: 18px;
}

.entry-group {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--line-soft);
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(16, 32, 58, 0.05), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 248, 255, 0.98) 100%);
}

.entry-group-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  flex-wrap: wrap;
}

.entry-group-heading {
  min-width: 0;
}

.entry-group-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
  margin-left: auto;
}

.entry-group-title {
  font-size: 18px;
  font-weight: 800;
  color: var(--ink-strong);
}

.entry-group-code {
  margin-top: 4px;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-soft);
}

.entry-group-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 84px;
  padding: 6px;
  border-radius: 20px;
  background: rgba(237, 243, 251, 0.72);
}

.group-toggle :deep(.el-button),
.group-toggle {
  font-weight: 700;
  color: var(--brand);
}

.entry-group-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 116px;
  padding: 18px;
  border: 1px dashed var(--line-strong);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.85);
  text-align: center;
}

.entry-group-empty strong {
  font-size: 15px;
  color: var(--ink-strong);
}

.entry-group-empty span {
  max-width: 360px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--ink-soft);
}

.entry-item.active {
  border-color: rgba(16, 32, 58, 0.24);
  box-shadow:
    0 0 0 1px rgba(16, 32, 58, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.category-item,
.entry-item {
  border: 1px solid var(--line-soft);
  border-radius: 22px;
  padding: 18px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.98) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.category-item {
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.category-item.active {
  border-color: rgba(16, 32, 58, 0.24);
  box-shadow:
    0 0 0 1px rgba(16, 32, 58, 0.08),
    0 10px 26px rgba(15, 23, 42, 0.05);
  transform: translateY(-1px);
}

.category-item-header,
.entry-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.category-badges,
.category-actions,
.entry-meta,
.entry-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.category-actions :deep(.el-button),
.entry-actions :deep(.el-button) {
  font-weight: 700;
}

.drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 10px;
  border: 1px dashed var(--line-strong);
  color: var(--ink-body);
  background: var(--surface-0);
  cursor: grab;
  user-select: none;
  font-weight: 700;
  letter-spacing: 1px;
}

.category-form-grid,
.entry-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.category-form-grid .span-2 {
  grid-column: span 2;
}

.surface-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  background: var(--surface-1);
}

.surface-field label {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink-soft);
  letter-spacing: 0.03em;
}

.toggle-field {
  justify-content: center;
}

.entry-item-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 6px;
  border-top: 1px solid rgba(216, 225, 238, 0.8);
}

.entry-item-body-compact {
  gap: 10px;
}

.entry-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  font-size: 13px;
  color: var(--ink-body);
}

.entry-detail {
  position: sticky;
  top: 96px;
}

.entry-detail-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  border: 1px solid var(--line-soft);
  border-radius: 24px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
}

.entry-detail-kicker {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-soft);
}

.entry-detail-top h3 {
  margin: 8px 0 0;
  font-size: 24px;
  color: var(--ink-strong);
}

.entry-detail-top p {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-body);
  word-break: break-all;
}

.entry-detail-meta,
.entry-detail-actions,
.entry-detail-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.entry-detail-stack {
  flex-direction: column;
}

.entry-detail-grid {
  grid-template-columns: minmax(0, 140px) minmax(0, 140px);
}

.compact-order-input {
  width: 100% !important;
  max-width: 124px;
  min-width: 0;
  flex: none;
  align-self: flex-start;
}

.compact-order-input :deep(.el-input),
.compact-order-input :deep(.el-input-number) {
  width: 100% !important;
  min-width: 0;
}

.compact-order-input :deep(.el-input-number.is-controls-right .el-input__wrapper) {
  padding-left: 12px;
}

.entry-title {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.entry-title-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.entry-mainline {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
}

.entry-mainline strong {
  font-size: 18px;
  color: var(--ink-strong);
}

.entry-path {
  color: var(--ink-soft);
  font-size: 13px;
  word-break: break-all;
}

.entry-code {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #94a3b8;
}

.entry-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  background: var(--surface-1);
}

.entry-field label {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink-soft);
  letter-spacing: 0.03em;
}

.entry-grid-tight {
  grid-template-columns: minmax(0, 2fr) minmax(160px, 0.7fr) minmax(120px, 0.55fr);
}

.entry-field-toggle {
  justify-content: center;
}

.panel-pagination {
  margin-top: 20px;
  justify-content: flex-end;
  padding-top: 14px;
  border-top: 1px solid rgba(216, 225, 238, 0.9);
}

@media (max-width: 960px) {
  .page-hero,
  .panel-header,
  .panel-header-top,
  .category-item-header,
  .entry-item-top,
  .entry-group-header {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .entry-search {
    width: 100%;
  }

  .panel-toolbar-entries {
    justify-content: flex-start;
  }

  .entries-workspace {
    grid-template-columns: 1fr;
  }

  .category-form-grid,
  .entry-grid {
    grid-template-columns: 1fr;
  }

  .category-form-grid .span-2 {
    grid-column: span 1;
  }
}

@media (max-width: 720px) {
  .page-hero {
    padding: 20px;
  }

  .page-hero h2 {
    font-size: 28px;
  }

  .hero-stats {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
