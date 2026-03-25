<template>
  <div
    v-if="renderMode === 'design'"
    class="field-panel"
    data-testid="layout-field-panel"
  >
    <div class="panel-header">
      <el-input
        ref="searchInputRef"
        :model-value="searchQuery"
        :placeholder="t('system.pageLayout.designer.placeholders.searchField')"
        :prefix-icon="Search"
        size="small"
        clearable
        @update:model-value="emit('update:searchQuery', String($event || ''))"
      />
      <div class="assignment-summary">
        <div class="assignment-summary__meta">
          <span class="assignment-summary__label">{{ t('system.pageLayout.designer.stats.assigned', 'Assigned') }}</span>
          <span class="assignment-summary__value">{{ assignedFieldCount }}/{{ totalFieldCount }}</span>
        </div>
        <el-progress
          :percentage="assignmentPercentage"
          :stroke-width="6"
          :show-text="false"
        />
      </div>
    </div>
    <div class="panel-content">
      <div
        v-if="resolvedSectionTemplateOptions.length > 0"
        class="field-group"
      >
        <div
          class="group-header"
          @click="emit('toggleGroup', 'section-template')"
        >
          <span class="group-title">{{ t('system.pageLayout.designer.panel.sectionTemplates') }}</span>
          <el-icon
            class="expand-icon"
            :class="{ expanded: isGroupExpanded('section-template') }"
          >
            <ArrowRight />
          </el-icon>
        </div>
        <div
          v-show="isGroupExpanded('section-template')"
          class="group-fields-grid"
        >
          <div
            v-for="template in resolvedSectionTemplateOptions"
            :key="template.templateCode"
            class="field-tile section-template-tile"
            :data-testid="`layout-palette-section-template-${template.templateCode}`"
            draggable="true"
            :title="template.title"
            @dragstart="emit('sectionTemplateDragStart', $event, template)"
            @dragend="emit('dragEnd')"
            @click="emit('sectionTemplateClick', template)"
          >
            <el-icon
              class="tile-icon"
              :style="{ color: resolveSectionTemplateColor(template) }"
            >
              <component :is="resolveSectionTemplateIcon(template)" />
            </el-icon>
            <span
              class="tile-label"
              :title="template.title"
            >{{ template.title }}</span>
            <span
              v-if="template.description"
              class="tile-meta"
              :title="template.description"
            >{{ template.description }}</span>
          </div>
        </div>
      </div>
      <div
        v-if="resolvedDetailRegionOptions.length > 0"
        class="field-group"
      >
        <div
          class="group-header"
          @click="emit('toggleGroup', 'detail-region')"
        >
          <span class="group-title">{{ t('system.pageLayout.designer.defaults.detailRegion') }}</span>
          <el-icon
            class="expand-icon"
            :class="{ expanded: isGroupExpanded('detail-region') }"
          >
            <ArrowRight />
          </el-icon>
        </div>
        <div
          v-show="isGroupExpanded('detail-region')"
          class="detail-region-group-list"
        >
          <div
            v-for="group in resolvedDetailRegionGroups"
            :key="group.key"
            class="detail-region-subgroup"
            :data-testid="`layout-palette-detail-region-group-${group.key}`"
          >
            <button
              type="button"
              class="detail-region-subgroup__header"
              :data-testid="`layout-palette-detail-region-group-toggle-${group.key}`"
              :title="isDetailRegionGroupExpanded(group.key) ? t('common.actions.collapse') : t('common.actions.expand')"
              @click="toggleDetailRegionGroup(group.key)"
            >
              <div class="detail-region-subgroup__header-main">
                <span
                  class="detail-region-subgroup__title"
                  :title="group.title"
                >{{ group.title }}</span>
                <span
                  v-if="group.meta"
                  class="detail-region-subgroup__meta"
                  :title="group.meta"
                >{{ group.meta }}</span>
              </div>
              <div class="detail-region-subgroup__header-side">
                <span class="detail-region-subgroup__count">{{ group.options.length }}</span>
                <el-icon
                  class="detail-region-subgroup__expand"
                  :class="{ expanded: isDetailRegionGroupExpanded(group.key) }"
                >
                  <ArrowRight />
                </el-icon>
              </div>
            </button>
            <div
              v-if="!isDetailRegionGroupExpanded(group.key)"
              class="detail-region-subgroup__summary"
              :title="group.previewText"
            >
              {{ group.previewText }}
            </div>
            <div
              v-if="isDetailRegionGroupExpanded(group.key)"
              class="detail-region-subgroup__body"
              :data-testid="`layout-palette-detail-region-group-grid-${group.key}`"
            >
              <div
                v-if="group.primaryOption"
                class="detail-region-primary"
              >
                <div class="detail-region-primary__badge">
                  {{ t('system.pageLayout.designer.stats.default', 'Default') }}
                </div>
                <div
                  class="field-tile detail-region-tile detail-region-tile--primary"
                  :data-testid="`layout-palette-detail-region-${group.primaryOption.templateCode || group.primaryOption.relationCode}`"
                  draggable="true"
                  :title="`${group.primaryOption.title} (${group.primaryOption.relationCode}${group.primaryOption.targetObjectLabel ? ` / ${group.primaryOption.targetObjectLabel}` : ''})`"
                  :class="{
                    'is-added': resolveDetailRegionAdded(group.primaryOption.relationCode, group.primaryOption.fieldCode),
                    'is-unassigned': !resolveDetailRegionAdded(group.primaryOption.relationCode, group.primaryOption.fieldCode),
                  }"
                  @dragstart="emit('detailRegionDragStart', $event, group.primaryOption)"
                  @dragend="emit('dragEnd')"
                  @click="emit('detailRegionClick', group.primaryOption)"
                >
                  <el-icon
                    class="tile-icon"
                    :style="{ color: '#2563eb' }"
                  >
                    <Grid />
                  </el-icon>
                  <span
                    class="tile-label"
                    :title="group.primaryOption.title"
                  >
                    {{ group.primaryOption.variantTitle || group.primaryOption.title }}
                  </span>
                  <span
                    class="tile-meta"
                    :title="group.primaryOption.description || group.primaryOption.groupMeta || group.primaryOption.targetObjectLabel"
                  >
                    {{ group.primaryOption.description || group.primaryOption.groupMeta || group.primaryOption.targetObjectLabel }}
                  </span>
                </div>
              </div>
              <div
                v-if="group.secondaryOptions.length > 0"
                class="detail-region-secondary"
              >
                <template v-if="isDetailRegionSearchActive">
                  <div
                    class="detail-region-subgroup__grid"
                    :data-testid="`layout-palette-detail-region-secondary-grid-${group.key}`"
                  >
                    <div
                      v-for="region in group.secondaryOptions"
                      :key="region.templateCode || region.relationCode"
                      class="field-tile detail-region-tile"
                      :data-testid="`layout-palette-detail-region-${region.templateCode || region.relationCode}`"
                      draggable="true"
                      :title="`${region.title} (${region.relationCode}${region.targetObjectLabel ? ` / ${region.targetObjectLabel}` : ''})`"
                      :class="{
                        'is-added': resolveDetailRegionAdded(region.relationCode, region.fieldCode),
                        'is-unassigned': !resolveDetailRegionAdded(region.relationCode, region.fieldCode),
                      }"
                      @dragstart="emit('detailRegionDragStart', $event, region)"
                      @dragend="emit('dragEnd')"
                      @click="emit('detailRegionClick', region)"
                    >
                      <el-icon
                        class="tile-icon"
                        :style="{ color: '#2563eb' }"
                      >
                        <Grid />
                      </el-icon>
                      <span
                        class="tile-label"
                        :title="region.title"
                      >{{ region.variantTitle || region.title }}</span>
                      <span
                        class="tile-meta"
                        :title="region.description || region.groupMeta || region.targetObjectLabel"
                      >
                        {{ region.description || region.groupMeta || region.targetObjectLabel }}
                      </span>
                    </div>
                  </div>
                </template>
                <template v-else>
                  <button
                    :ref="(el) => setDetailRegionSecondaryToggleRef(group.key, el)"
                    type="button"
                    class="detail-region-secondary__toggle"
                    :data-testid="`layout-palette-detail-region-secondary-toggle-${group.key}`"
                    :aria-expanded="isDetailRegionSecondaryExpanded(group.key)"
                    aria-haspopup="menu"
                    :aria-controls="`layout-palette-detail-region-secondary-menu-${group.key}`"
                    @click="toggleDetailRegionSecondary(group.key)"
                    @keydown.down.prevent="openDetailRegionSecondaryFromKey(group.key, 0)"
                    @keydown.up.prevent="openDetailRegionSecondaryFromKey(group.key, group.secondaryOptions.length - 1)"
                  >
                    <span class="detail-region-secondary__toggle-main">
                      <span class="detail-region-secondary__toggle-label">
                        {{ t('common.actions.loadMore') }}
                      </span>
                      <span
                        class="detail-region-secondary__summary"
                        :title="group.secondaryPreviewText"
                      >
                        {{ group.secondaryPreviewText }}
                      </span>
                    </span>
                    <span class="detail-region-secondary__toggle-side">
                      <span class="detail-region-secondary__toggle-count">{{ group.secondaryOptions.length }}</span>
                      <el-icon
                        class="detail-region-secondary__toggle-icon"
                        :class="{ expanded: isDetailRegionSecondaryExpanded(group.key) }"
                      >
                        <ArrowRight />
                      </el-icon>
                    </span>
                  </button>
                  <div
                    v-if="isDetailRegionSecondaryExpanded(group.key)"
                    :id="`layout-palette-detail-region-secondary-menu-${group.key}`"
                    class="detail-region-secondary__menu"
                    :data-testid="`layout-palette-detail-region-secondary-menu-${group.key}`"
                    role="menu"
                    @mouseleave="emit('detailRegionPreview', null)"
                  >
                    <button
                      v-for="(region, index) in group.secondaryOptions"
                      :key="region.templateCode || region.relationCode"
                      :ref="(el) => setDetailRegionSecondaryItemRef(group.key, index, el)"
                      type="button"
                      class="detail-region-secondary__menu-item"
                      :data-testid="`layout-palette-detail-region-secondary-item-${region.templateCode || region.relationCode}`"
                      :title="`${region.title} (${region.relationCode}${region.targetObjectLabel ? ` / ${region.targetObjectLabel}` : ''})`"
                      role="menuitem"
                      @click="handleDetailRegionSecondaryClick(group.key, region)"
                      @mouseenter="emit('detailRegionPreview', region)"
                      @focus="emit('detailRegionPreview', region)"
                      @keydown="handleDetailRegionSecondaryItemKeydown($event, group.key, index, region)"
                    >
                      <span class="detail-region-secondary__menu-item-title">
                        {{ region.variantTitle || region.title }}
                      </span>
                      <span
                        class="detail-region-secondary__menu-item-meta"
                        :title="region.description || region.groupMeta || region.targetObjectLabel"
                      >
                        {{ region.description || region.groupMeta || region.targetObjectLabel }}
                      </span>
                    </button>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div
        v-for="group in filteredFieldGroups"
        :key="group.type"
        class="field-group"
      >
        <div
          class="group-header"
          @click="emit('toggleGroup', group.type)"
        >
          <span class="group-title">{{ group.label }}</span>
          <el-icon
            class="expand-icon"
            :class="{ expanded: isGroupExpanded(group.type) }"
          >
            <ArrowRight />
          </el-icon>
        </div>
        <div
          v-show="isGroupExpanded(group.type)"
          class="group-fields-grid"
        >
          <div
            v-for="field in group.fields"
            :key="field.code"
            class="field-tile"
            :data-testid="`layout-palette-field-${field.code}`"
            :draggable="canAddField(field)"
            :title="getDisabledReason(field) || field.name"
            :class="{
              'is-added': isFieldAdded(field.code),
              'is-unassigned': !isFieldAdded(field.code) && canAddField(field),
              'is-disabled': !canAddField(field)
            }"
            @dragstart="emit('fieldDragStart', $event, field)"
            @dragend="emit('dragEnd')"
            @click="emit('fieldClick', field)"
          >
            <el-icon
              class="tile-icon"
              :style="{ color: resolveFieldColor(field) }"
            >
              <component :is="resolveFieldIcon(field)" />
            </el-icon>
            <span
              class="tile-label"
              :title="field.name"
            >{{ field.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, type Component, type ComponentPublicInstance } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowRight, Check, Search,
  Edit, EditPen, Document, Histogram, Calendar, Timer,
  Message, Link, Connection, User, OfficeBuilding,
  Folder, Grid, Picture, Select, CircleCheck, Ticket, FolderOpened
} from '@element-plus/icons-vue'
import { normalizeFieldType } from '@/utils/fieldType'
import type {
  DesignerDetailRegionOption,
  DesignerFieldDefinition,
  DesignerSectionTemplateOption,
  FieldGroup
} from '@/components/designer/designerTypes'

const props = defineProps<{
  renderMode: 'design' | 'preview'
  searchQuery: string
  filteredFieldGroups: FieldGroup[]
  sectionTemplateOptions?: DesignerSectionTemplateOption[]
  detailRegionOptions?: DesignerDetailRegionOption[]
  assignedFieldCount: number
  totalFieldCount: number
  isGroupExpanded: (type: string) => boolean
  canAddField: (field: DesignerFieldDefinition) => boolean
  getDisabledReason: (field: DesignerFieldDefinition) => string | null
  isFieldAdded: (code: string) => boolean
  isDetailRegionAdded?: (relationCode: string, fieldCode?: string) => boolean
}>()

const emit = defineEmits<{
  (e: 'update:searchQuery', value: string): void
  (e: 'toggleGroup', type: string): void
  (e: 'fieldClick', field: DesignerFieldDefinition): void
  (e: 'sectionTemplateClick', template: DesignerSectionTemplateOption): void
  (e: 'detailRegionClick', region: DesignerDetailRegionOption): void
  (e: 'detailRegionPreview', region: DesignerDetailRegionOption | null): void
  (e: 'fieldDragStart', event: DragEvent, field: DesignerFieldDefinition): void
  (e: 'sectionTemplateDragStart', event: DragEvent, template: DesignerSectionTemplateOption): void
  (e: 'detailRegionDragStart', event: DragEvent, region: DesignerDetailRegionOption): void
  (e: 'dragEnd'): void
}>()

const { t } = useI18n()
const searchInputRef = ref<{ focus: () => void } | null>(null)
const resolvedSectionTemplateOptions = computed(() => props.sectionTemplateOptions || [])
const resolvedDetailRegionOptions = computed(() => props.detailRegionOptions || [])
const resolvedDetailRegionGroups = computed(() => {
  const groups = new Map<string, {
    key: string
    title: string
    meta: string
    options: DesignerDetailRegionOption[]
    previewText: string
    primaryOption: DesignerDetailRegionOption | null
    secondaryOptions: DesignerDetailRegionOption[]
    secondaryPreviewText: string
  }>()

  for (const option of resolvedDetailRegionOptions.value) {
    const key = String(option.relationCode || option.templateCode || option.title).trim()

    if (!groups.has(key)) {
      groups.set(key, {
        key,
        title: String(option.groupTitle || option.title).trim(),
        meta: String(option.groupMeta || option.targetObjectLabel || '').trim(),
        options: [],
        previewText: '',
        primaryOption: null,
        secondaryOptions: [],
        secondaryPreviewText: ''
      })
    }

    groups.get(key)?.options.push(option)
  }

  return [...groups.values()].map((group) => {
    const orderedOptions = [...group.options].sort(compareDetailRegionPaletteOptions)
    const [primaryOption, ...secondaryOptions] = orderedOptions

    return {
      ...group,
      options: orderedOptions,
      primaryOption: primaryOption || null,
      secondaryOptions,
      previewText: orderedOptions
        .map((option) => String(option.variantTitle || option.title || '').trim())
        .filter(Boolean)
        .slice(0, 3)
        .join(' / '),
      secondaryPreviewText: secondaryOptions
        .map((option) => String(option.variantTitle || option.title || '').trim())
        .filter(Boolean)
        .slice(0, 3)
        .join(' / ')
    }
  })
})
const collapsedDetailRegionGroups = ref<Set<string>>(new Set())
const expandedDetailRegionSecondaryGroups = ref<Set<string>>(new Set())
const detailRegionSecondaryToggleRefs = new Map<string, HTMLButtonElement>()
const detailRegionSecondaryItemRefs = new Map<string, Array<HTMLButtonElement | undefined>>()
const isDetailRegionSearchActive = computed(() => props.searchQuery.trim().length > 0)
const assignmentPercentage = computed(() => {
  if (props.totalFieldCount <= 0) return 0
  return Math.max(0, Math.min(100, Math.round((props.assignedFieldCount / props.totalFieldCount) * 100)))
})

function resolveDetailRegionAdded(relationCode: string, fieldCode?: string): boolean {
  if (!props.isDetailRegionAdded) return false
  return props.isDetailRegionAdded(relationCode, fieldCode)
}

function isDetailRegionGroupExpanded(key: string): boolean {
  if (isDetailRegionSearchActive.value) return true
  return !collapsedDetailRegionGroups.value.has(key)
}

function toggleDetailRegionGroup(key: string) {
  if (isDetailRegionSearchActive.value) return

  const next = new Set(collapsedDetailRegionGroups.value)
  const nextSecondary = new Set(expandedDetailRegionSecondaryGroups.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
    nextSecondary.delete(key)
  }
  collapsedDetailRegionGroups.value = next
  expandedDetailRegionSecondaryGroups.value = nextSecondary
}

function isDetailRegionSecondaryExpanded(key: string): boolean {
  if (isDetailRegionSearchActive.value) return true
  return expandedDetailRegionSecondaryGroups.value.has(key)
}

function setDetailRegionSecondaryExpanded(key: string, expanded: boolean) {
  if (isDetailRegionSearchActive.value) return

  const next = new Set<string>()
  if (expanded) {
    next.add(key)
  }
  expandedDetailRegionSecondaryGroups.value = next
}

function toggleDetailRegionSecondary(key: string) {
  const nextExpanded = !expandedDetailRegionSecondaryGroups.value.has(key)
  setDetailRegionSecondaryExpanded(key, nextExpanded)
  if (!nextExpanded) {
    emit('detailRegionPreview', null)
  }
}

function handleDetailRegionSecondaryClick(key: string, region: DesignerDetailRegionOption) {
  setDetailRegionSecondaryExpanded(key, false)
  emit('detailRegionPreview', null)
  emit('detailRegionClick', region)
}

function resolveTemplateRefElement(
  el: Element | ComponentPublicInstance | null
): Element | null {
  if (el instanceof Element) return el
  if (el && '$el' in el && el.$el instanceof Element) return el.$el
  return null
}

function setDetailRegionSecondaryToggleRef(key: string, el: Element | ComponentPublicInstance | null) {
  const element = resolveTemplateRefElement(el)
  if (element instanceof HTMLButtonElement) {
    detailRegionSecondaryToggleRefs.set(key, element)
    return
  }
  detailRegionSecondaryToggleRefs.delete(key)
}

function setDetailRegionSecondaryItemRef(
  key: string,
  index: number,
  el: Element | ComponentPublicInstance | null
) {
  const items = detailRegionSecondaryItemRefs.get(key) || []
  const element = resolveTemplateRefElement(el)

  if (element instanceof HTMLButtonElement) {
    items[index] = element
  } else {
    items[index] = undefined
  }

  detailRegionSecondaryItemRefs.set(key, items)
}

function getDetailRegionSecondaryItems(key: string): HTMLButtonElement[] {
  return (detailRegionSecondaryItemRefs.get(key) || []).filter(
    (item): item is HTMLButtonElement => item instanceof HTMLButtonElement
  )
}

function focusDetailRegionSecondaryToggle(key: string) {
  nextTick(() => {
    detailRegionSecondaryToggleRefs.get(key)?.focus()
  })
}

function focusDetailRegionSecondaryItem(key: string, index: number) {
  nextTick(() => {
    const items = getDetailRegionSecondaryItems(key)
    if (items.length === 0) return

    const safeIndex = Math.max(0, Math.min(index, items.length - 1))
    items[safeIndex]?.focus()
  })
}

function openDetailRegionSecondaryFromKey(key: string, index: number) {
  if (isDetailRegionSearchActive.value) return
  setDetailRegionSecondaryExpanded(key, true)
  focusDetailRegionSecondaryItem(key, index)
}

function handleDetailRegionSecondaryItemKeydown(
  event: KeyboardEvent,
  key: string,
  index: number,
  region: DesignerDetailRegionOption
) {
  const items = getDetailRegionSecondaryItems(key)
  if (items.length === 0) return

  switch (event.key) {
    case 'ArrowDown':
    case 'ArrowRight': {
      event.preventDefault()
      focusDetailRegionSecondaryItem(key, (index + 1) % items.length)
      break
    }
    case 'ArrowUp':
    case 'ArrowLeft': {
      event.preventDefault()
      focusDetailRegionSecondaryItem(key, (index - 1 + items.length) % items.length)
      break
    }
    case 'Home': {
      event.preventDefault()
      focusDetailRegionSecondaryItem(key, 0)
      break
    }
    case 'End': {
      event.preventDefault()
      focusDetailRegionSecondaryItem(key, items.length - 1)
      break
    }
    case 'Escape': {
      event.preventDefault()
      setDetailRegionSecondaryExpanded(key, false)
      emit('detailRegionPreview', null)
      focusDetailRegionSecondaryToggle(key)
      break
    }
    case 'Enter':
    case ' ': {
      event.preventDefault()
      handleDetailRegionSecondaryClick(key, region)
      break
    }
    default:
      break
  }
}

function compareDetailRegionPaletteOptions(a: DesignerDetailRegionOption, b: DesignerDetailRegionOption): number {
  const weightA = resolveDetailRegionPalettePriority(a.presetCode)
  const weightB = resolveDetailRegionPalettePriority(b.presetCode)

  if (weightA !== weightB) return weightA - weightB

  return String(a.variantTitle || a.title || '')
    .localeCompare(String(b.variantTitle || b.title || ''), undefined, { sensitivity: 'base' })
}

function resolveDetailRegionPalettePriority(presetCode?: string): number {
  if (presetCode === 'editableDetail') return 0
  if (presetCode === 'reviewTable') return 1
  if (presetCode === 'sidebarSummary') return 2
  return 99
}

const sectionTemplateVisuals: Record<DesignerSectionTemplateOption['icon'], { icon: Component; color: string }> = {
  section: { icon: Document, color: '#0f766e' },
  tab: { icon: Ticket, color: '#9333ea' },
  collapse: { icon: FolderOpened, color: '#b45309' }
}

function resolveSectionTemplateIcon(template: DesignerSectionTemplateOption): Component {
  return sectionTemplateVisuals[template.icon].icon
}

function resolveSectionTemplateColor(template: DesignerSectionTemplateOption): string {
  return sectionTemplateVisuals[template.icon].color
}



// ── Per-field-type icon / color resolution ──
const fieldTypeVisuals: Record<string, { icon: Component; color: string }> = {
  text: { icon: EditPen, color: '#606266' },
  textarea: { icon: Document, color: '#409eff' },
  rich_text: { icon: Document, color: '#409eff' },
  number: { icon: Histogram, color: '#e6a23c' },
  currency: { icon: Histogram, color: '#e6a23c' },
  percent: { icon: Histogram, color: '#e6a23c' },
  boolean: { icon: CircleCheck, color: '#67c23a' },
  date: { icon: Calendar, color: '#409eff' },
  datetime: { icon: Timer, color: '#409eff' },
  email: { icon: Message, color: '#409eff' },
  url: { icon: Link, color: '#3498db' },
  reference: { icon: Connection, color: '#9b59b6' },
  user: { icon: User, color: '#f56c6c' },
  department: { icon: OfficeBuilding, color: '#f56c6c' },
  file: { icon: Folder, color: '#e6a23c' },
  image: { icon: Picture, color: '#e91e63' },
  select: { icon: Select, color: '#67c23a' },
  multi_select: { icon: Select, color: '#67c23a' },
  radio: { icon: CircleCheck, color: '#67c23a' },
  checkbox: { icon: Check, color: '#67c23a' },
  sub_table: { icon: FolderOpened, color: '#909399' },
  formula: { icon: Ticket, color: '#9c27b0' },
  empty: { icon: Edit, color: '#c0c4cc' }
}

const defaultVisual = { icon: EditPen, color: '#909399' }

function resolveFieldIcon(field: DesignerFieldDefinition): Component {
  const ft = normalizeFieldType(field.fieldType || field.type || 'text')
  return (fieldTypeVisuals[ft] || defaultVisual).icon
}

function resolveFieldColor(field: DesignerFieldDefinition): string {
  const ft = normalizeFieldType(field.fieldType || field.type || 'text')
  return (fieldTypeVisuals[ft] || defaultVisual).color
}

defineExpose({
  focusSearch: () => searchInputRef.value?.focus()
})
</script>

<style scoped>
.field-panel {
  width: 100%;
  height: 100%;
  min-width: 0;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.panel-header {
  padding: 16px 16px 14px;
  border-bottom: 1px solid #e4e7ed;
  background: rgba(255, 255, 255, 0.92);
}

.assignment-summary {
  margin-top: 12px;
}

.assignment-summary__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 12px;
}

.assignment-summary__label {
  color: #606266;
}

.assignment-summary__value {
  color: #303133;
  font-weight: 600;
}

.panel-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 0 28px;
  overscroll-behavior: contain;
}

.panel-content::-webkit-scrollbar {
  width: 5px;
}
.panel-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 4px;
}

.field-group {
  margin-bottom: 2px;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}
.group-header:hover {
  background: #f5f7fa;
}
.group-title {
  flex: 1;
}
.expand-icon {
  transition: transform 0.25s ease;
  font-size: 12px;
  color: #909399;
}
.expand-icon.expanded {
  transform: rotate(90deg);
}

.group-fields-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 6px 12px 16px;
}

.detail-region-group-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 6px 12px 16px;
}

.detail-region-subgroup {
  border: 1px solid #eef2f7;
  border-radius: 10px;
  padding: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
}

.detail-region-subgroup__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  margin-bottom: 10px;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.detail-region-subgroup__header-main {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
  flex-wrap: wrap;
}

.detail-region-subgroup__title {
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
  min-width: 0;
}

.detail-region-subgroup__meta {
  font-size: 11px;
  color: #64748b;
  flex-shrink: 0;
}

.detail-region-subgroup__header-side {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.detail-region-subgroup__count {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  line-height: 20px;
  text-align: center;
}

.detail-region-subgroup__expand {
  font-size: 12px;
  color: #64748b;
  transition: transform 0.2s ease;
}

.detail-region-subgroup__expand.expanded {
  transform: rotate(90deg);
}

.detail-region-subgroup__summary {
  margin-bottom: 10px;
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
}

.detail-region-subgroup__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-region-primary {
  position: relative;
}

.detail-region-primary__badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
  padding: 2px 8px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 10px;
  font-weight: 700;
}

.detail-region-tile--primary {
  border-color: #bfdbfe;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}

.detail-region-secondary {
  border-top: 1px dashed #dbe3ef;
  padding-top: 10px;
}

.detail-region-secondary__toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.detail-region-secondary__toggle:hover {
  border-color: #bfdbfe;
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
}

.detail-region-secondary__toggle:focus-visible,
.detail-region-secondary__menu-item:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.detail-region-secondary__toggle-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.detail-region-secondary__toggle-label {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}

.detail-region-secondary__toggle-side {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.detail-region-secondary__toggle-count {
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
  font-size: 10px;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
}

.detail-region-secondary__summary {
  font-size: 11px;
  color: #64748b;
  line-height: 1.4;
}

.detail-region-secondary__toggle-icon {
  font-size: 12px;
  color: #64748b;
  transition: transform 0.2s ease;
}

.detail-region-secondary__toggle-icon.expanded {
  transform: rotate(90deg);
}

.detail-region-secondary__menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
  padding: 8px;
  border: 1px solid #dbe3ef;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.detail-region-secondary__menu-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: #ffffff;
  cursor: pointer;
  text-align: left;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.detail-region-secondary__menu-item:hover {
  background: #f8fbff;
  border-color: #bfdbfe;
}

.detail-region-secondary__menu-item-title {
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
}

.detail-region-secondary__menu-item-meta {
  font-size: 11px;
  color: #64748b;
  line-height: 1.35;
}

.detail-region-subgroup__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.field-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 8px;
  border-radius: 4px;
  cursor: grab;
  transition: all 0.2s ease;
  border: 1px solid #f1f2f3;
  position: relative;
  background: #fdfdfe;
  min-height: 78px;
}
.tile-icon {
  font-size: 20px;
  transition: all 0.2s ease;
  color: #555555 !important;
}
.tile-label {
  font-size: 12px;
  color: #333333;
  text-align: center;
  line-height: 1.2;
  width: 100%;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
}

.tile-meta {
  display: inline-block;
  max-width: 100%;
  font-size: 11px;
  color: #64748b;
  text-align: center;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-tile:hover {
  background: #ffffff;
  border-color: #409EFF;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.15);
}
.field-tile:hover .tile-icon {
  color: #409EFF !important;
}
.field-tile:hover .tile-label {
  color: #409EFF;
}

.field-tile:active {
  cursor: grabbing;
  transform: scale(0.96);
  background: var(--el-color-primary-light-9, #ecf5ff);
}

.field-tile.is-added {
  /* FormCreate uses a subtle blue border for added/selected items, no green background */
  border-color: #409EFF;
  background: #ffffff;
}
.field-tile.is-added .tile-icon {
  color: #409EFF !important;
}
.field-tile.is-added .tile-label {
  color: #409EFF;
}

.field-tile.is-unassigned:not(.is-added) {
  border-color: #d9ecff;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}

.field-tile.is-disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
  background: #f5f7fa;
  border-color: #e4e7ed;
}
</style>
