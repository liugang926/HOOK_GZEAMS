<template>
  <el-dialog
    :model-value="modelValue"
    :title="dialogTitle"
    width="840px"
    top="8vh"
    destroy-on-close
    @update:model-value="$emit('update:modelValue', $event)"
    @opened="handleOpened"
  >
    <div class="lookup-toolbar">
      <el-segmented
        v-model="viewMode"
        :options="viewModeOptions"
        class="lookup-toolbar__mode"
      />
      <el-input
        v-model="keyword"
        clearable
        class="lookup-toolbar__search"
        :placeholder="searchPlaceholder"
        @keyup.enter="handleSearch"
      />
      <div class="lookup-toolbar__scope">
        <span class="lookup-toolbar__scope-label">{{ matchInLabelText }}</span>
        <el-segmented
          v-model="searchScope"
          class="lookup-toolbar__scope-segmented"
          :options="searchScopeOptions"
          size="small"
        />
      </div>
      <el-button
        type="primary"
        :loading="loading"
        :disabled="viewMode === 'recent'"
        @click="handleSearch"
      >
        {{ searchActionText }}
      </el-button>
      <el-button @click="handleReset">
        {{ resetActionText }}
      </el-button>
      <el-button
        v-if="allowCreate"
        @click="openCreate"
      >
        {{ createActionText }}
      </el-button>
      <el-popover
        trigger="click"
        placement="bottom-end"
        :width="340"
      >
        <template #reference>
          <el-button class="lookup-toolbar__columns-trigger">
            <el-icon><Setting /></el-icon>
            <span>{{ columnsActionText }}</span>
          </el-button>
        </template>
        <div class="lookup-column-settings">
          <div class="lookup-column-settings__header">
            <div class="lookup-column-settings__title">
              {{ columnsActionText }}
            </div>
            <el-button
              link
              type="primary"
              class="lookup-column-settings__reset lookup-column-settings__reset-columns"
              @click="resetColumnsPreference"
            >
              <el-icon><Refresh /></el-icon>
              <span>{{ resetActionText }}</span>
            </el-button>
          </div>
          <el-segmented
            v-model="activeProfile"
            :options="profileOptions"
            class="lookup-column-settings__profiles"
            @change="handleProfileChange"
          />
          <div class="lookup-column-settings__profile-hint">
            {{ profileHintText }}
          </div>
          <div
            v-for="column in orderedAutoFilteredColumns"
            :key="column.key"
            class="lookup-column-settings__row"
            :class="{
              'is-locked': isColumnLocked(column.key),
              'is-dragging': draggingColumnKey === column.key,
              'is-drag-over-top': dragOverColumnKey === column.key && dragOverPosition === 'before' && draggingColumnKey !== column.key,
              'is-drag-over-bottom': dragOverColumnKey === column.key && dragOverPosition === 'after' && draggingColumnKey !== column.key
            }"
            :data-column-key="column.key"
            :draggable="!isColumnLocked(column.key)"
            @dragstart="handleColumnDragStart(column.key, $event)"
            @dragover.prevent="handleColumnDragOver(column.key, $event)"
            @drop.prevent="handleColumnDrop(column.key, $event)"
            @dragend="handleColumnDragEnd"
          >
            <span class="lookup-column-settings__drag-handle">
              <el-icon><Rank /></el-icon>
            </span>
            <el-checkbox
              :model-value="isColumnVisible(column.key)"
              :disabled="isColumnLocked(column.key)"
              class="lookup-column-settings__item"
              @change="setColumnVisible(column.key, $event)"
            >
              {{ column.label }}
            </el-checkbox>
            <el-icon
              v-if="isColumnLocked(column.key)"
              class="lookup-column-settings__lock-icon"
            >
              <Lock />
            </el-icon>
            <div class="lookup-column-settings__order">
              <el-button
                text
                circle
                class="lookup-column-settings__move-up"
                :disabled="isMoveDisabled(column.key, -1)"
                @click="moveColumn(column.key, -1)"
              >
                <el-icon><ArrowUp /></el-icon>
              </el-button>
              <el-button
                text
                circle
                class="lookup-column-settings__move-down"
                :disabled="isMoveDisabled(column.key, 1)"
                @click="moveColumn(column.key, 1)"
              >
                <el-icon><ArrowDown /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </el-popover>
    </div>

    <el-table
      ref="tableRef"
      :data="rows"
      :loading="loading"
      row-key="id"
      :highlight-current-row="!multiple"
      :row-class-name="getRowClassName"
      height="420"
      @row-click="handleRowClick"
      @row-dblclick="handleRowDblClick"
      @selection-change="handleSelectionChange"
      @header-dragend="handleHeaderDragEnd"
    >
      <el-table-column
        v-if="multiple"
        type="selection"
        width="46"
        reserve-selection
      />
      <el-table-column
        v-for="column in visibleColumns"
        :key="column.key"
        :column-key="column.key"
        :prop="column.key"
        :label="column.label"
        :min-width="column.minWidth"
        :width="column.width"
      >
        <template #default="{ row }">
          <template v-if="isPrimaryColumn(column)">
            <div
              v-if="row.__showGroupTitle"
              class="lookup-cell__group-title"
            >
              <span
                class="lookup-cell__group-dot"
                :class="row.__group === 'recent' ? 'is-recent' : 'is-search'"
              />
              {{ resolveGroupTitle(row.__group) }}
            </div>
            <div class="lookup-cell">
              <ObjectAvatar
                :object-code="objectCode || 'Ref'"
                size="xs"
              />
              <div class="lookup-cell__content">
                <span class="lookup-cell__name">
                  {{ resolvePrimaryLabel(row, column.key) }}
                  <el-tag
                    v-if="row.__recentPinned"
                    size="small"
                    effect="plain"
                    class="lookup-cell__recent-tag"
                  >
                    {{ recentTagText }}
                  </el-tag>
                </span>
                <span
                  v-if="resolveSecondary(row)"
                  class="lookup-cell__secondary"
                >
                  {{ resolveSecondary(row) }}
                </span>
              </div>
            </div>
          </template>
          <template v-else-if="column.key === 'id'">
            <span class="lookup-cell__id">{{ row.id }}</span>
          </template>
          <template v-else>
            <span class="lookup-cell__text">{{ resolveColumnValue(row, column.key) }}</span>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div class="lookup-footer">
      <div class="lookup-footer__meta">
        <span class="lookup-footer__summary">{{ selectionSummary }}</span>
        <span
          v-for="groupItem in footerGroupItems"
          :key="groupItem.key"
          class="lookup-footer__group"
          :class="groupItem.key === 'recent' ? 'is-recent' : 'is-search'"
        >
          {{ groupItem.label }} {{ groupItem.count }}
        </span>
      </div>
      <el-pagination
        v-if="viewMode === 'all'"
        background
        layout="prev, pager, next"
        :page-size="pageSize"
        :total="total"
        :current-page="page"
        @current-change="handlePageChange"
      />
    </div>
    <div
      v-if="!multiple"
      class="lookup-hotkeys"
      role="note"
      aria-live="polite"
    >
      <span class="lookup-hotkeys__title">{{ keyboardTipsTitleText }}</span>
      <span class="lookup-hotkeys__item">
        <kbd>Up</kbd><kbd>Down</kbd>
        {{ keyboardTipNavigateText }}
      </span>
      <span class="lookup-hotkeys__item">
        <kbd>Enter</kbd>
        {{ keyboardTipConfirmText }}
      </span>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="$emit('update:modelValue', false)">
          {{ cancelActionText }}
        </el-button>
        <el-button
          v-if="!multiple"
          :disabled="!activeSingleId"
          @click="handleOpenSelected"
        >
          {{ openActionText }}
        </el-button>
        <el-button
          type="primary"
          :disabled="!canConfirm"
          @click="handleConfirm"
        >
          {{ confirmActionText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown, ArrowUp, Lock, Rank, Refresh, Setting } from '@element-plus/icons-vue'
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'
import { searchReferenceData } from '@/api/system'
import { referenceResolver } from '@/platform/reference/referenceResolver'
import { resolveReferenceLabel, resolveReferenceSecondaryText } from '@/platform/reference/referenceFieldMeta'
import { loadRecentReferenceIds } from '@/platform/reference/referenceLookupRecent'
import {
  clearLookupColumnsPreference,
  hasLookupColumnsPreference,
  loadLastLookupProfile,
  loadLookupColumnsPreference,
  type LookupColumnsProfile,
  saveLastLookupProfile,
  saveLookupColumnsPreference
} from '@/platform/reference/referenceLookupColumnsPreference'

type AnyRecord = Record<string, any>
type LookupColumnConfig = {
  key: string
  label?: string
  minWidth?: number
  width?: number
}
type LookupColumn = {
  key: string
  label: string
  minWidth?: number
  width?: number
}
type LookupSearchScope = 'all' | 'primary' | 'secondary' | 'id'

const props = withDefaults(defineProps<{
  modelValue: boolean
  objectCode: string
  displayField: string
  secondaryField: string
  columns?: LookupColumnConfig[]
  preferenceKey?: string
  userScope?: string
  preferenceScope?: string
  compactKeys?: string[]
  multiple?: boolean
  selectedIds?: string[]
  allowCreate?: boolean
}>(), {
  columns: () => [],
  preferenceKey: '',
  userScope: '',
  preferenceScope: '',
  compactKeys: () => [],
  multiple: false,
  selectedIds: () => [],
  allowCreate: true
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', rows: AnyRecord[]): void
}>()

const { t } = useI18n()

const tableRef = ref<any>(null)
const loading = ref(false)
const rows = ref<AnyRecord[]>([])
const keyword = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const selectedMap = ref<Record<string, AnyRecord>>({})
const activeSingleId = ref('')
const activeSingleRow = ref<AnyRecord | null>(null)
const viewMode = ref<'all' | 'recent'>('all')
const searchScope = ref<LookupSearchScope>('all')

const tr = (key: string, fallback: string, params?: Record<string, any>) => {
  const text = t(key, params || {})
  return text === key ? fallback : text
}

const dialogTitle = computed(() =>
  `${tr('common.labels.advancedLookup', 'Advanced Lookup')} - ${props.objectCode || 'Reference'}`
)
const searchPlaceholder = computed(() =>
  tr('common.placeholders.search', 'Enter keyword')
)
const searchActionText = computed(() => tr('common.actions.search', 'Search'))
const resetActionText = computed(() => tr('common.actions.reset', 'Reset'))
const createActionText = computed(() => tr('common.actions.create', 'New'))
const openActionText = computed(() => tr('common.actions.open', 'Open'))
const cancelActionText = computed(() => tr('common.actions.cancel', 'Cancel'))
const confirmActionText = computed(() => tr('common.actions.confirm', 'Confirm'))
const nameLabel = computed(() => tr('common.columns.name', 'Name'))
const idLabel = computed(() => tr('common.relatedObject.id', 'ID'))
const recentTagText = computed(() => tr('common.recent', 'Recent'))
const codeLabel = computed(() => tr('common.columns.code', 'Code'))
const recentGroupTitleText = computed(() => tr('common.labels.recentRecords', 'Recent Records'))
const searchGroupTitleText = computed(() => tr('common.labels.searchResults', 'Search Results'))
const matchInLabelText = computed(() => tr('common.labels.lookupMatchIn', 'Match in'))
const columnsActionText = computed(() => tr('common.actions.columns', 'Columns'))
const keyboardTipsTitleText = computed(() => tr('common.hotkeys.lookup.title', 'Keyboard'))
const keyboardTipNavigateText = computed(() => tr('common.hotkeys.lookup.navigateRows', 'Move selection'))
const keyboardTipConfirmText = computed(() => tr('common.hotkeys.lookup.confirm', 'Confirm selected'))
const standardProfileText = computed(() => tr('common.labels.standard', 'Standard'))
const compactProfileText = computed(() => tr('common.labels.compact', 'Compact'))
const customProfileText = computed(() => tr('common.labels.custom', 'Custom'))
const standardProfileHintText = computed(() =>
  tr('common.messages.lookupProfileStandardHint', 'Show default columns and widths.')
)
const compactProfileHintText = computed(() =>
  tr('common.messages.lookupProfileCompactHint', 'Focus on key columns for faster scanning.')
)
const customProfileHintText = computed(() =>
  tr('common.messages.lookupProfileCustomHint', 'Uses your manual column visibility, order, and width.')
)
const profileOptions = computed(() => [
  { label: standardProfileText.value, value: 'standard' },
  { label: compactProfileText.value, value: 'compact' },
  { label: customProfileText.value, value: 'custom' }
])
const profileHintText = computed(() => {
  if (activeProfile.value === 'compact') return compactProfileHintText.value
  if (activeProfile.value === 'custom') return customProfileHintText.value
  return standardProfileHintText.value
})
const hasSecondaryField = computed(() => {
  const secondaryKey = String(props.secondaryField || '').trim()
  const displayKey = String(props.displayField || '').trim()
  return !!secondaryKey && secondaryKey !== displayKey
})
const searchScopeOptions = computed(() => {
  const options: Array<{ label: string, value: LookupSearchScope }> = [
    { label: tr('common.selectors.allFields', 'All Fields'), value: 'all' },
    { label: nameLabel.value, value: 'primary' }
  ]
  if (hasSecondaryField.value) {
    options.push({ label: codeLabel.value, value: 'secondary' })
  }
  options.push({ label: idLabel.value, value: 'id' })
  return options
})

const toColumnLabel = (key: string): string => {
  if (key === 'id') return idLabel.value
  if (key === props.displayField) return nameLabel.value
  if (key === props.secondaryField) return codeLabel.value
  return key
}

const normalizeColumn = (input: LookupColumnConfig): LookupColumn | null => {
  const key = String(input?.key || '').trim()
  if (!key) return null
  const label = String(input?.label || '').trim() || toColumnLabel(key)
  const minWidth = Number(input?.minWidth)
  const width = Number(input?.width)
  return {
    key,
    label,
    minWidth: Number.isFinite(minWidth) && minWidth > 0 ? minWidth : undefined,
    width: Number.isFinite(width) && width > 0 ? width : undefined
  }
}

const defaultColumns = computed<LookupColumn[]>(() => {
  const base: LookupColumn[] = [
    {
      key: String(props.displayField || 'name'),
      label: nameLabel.value,
      minWidth: 220
    }
  ]
  const secondaryKey = String(props.secondaryField || '').trim()
  if (secondaryKey && secondaryKey !== base[0].key) {
    base.push({
      key: secondaryKey,
      label: codeLabel.value,
      minWidth: 180
    })
  }
  if (!base.some((column) => column.key === 'id')) {
    base.push({
      key: 'id',
      label: idLabel.value,
      minWidth: 180
    })
  }
  return base
})

const hiddenColumnSet = ref<Set<string>>(new Set())
const columnOrder = ref<string[]>([])
const columnWidthMap = ref<Record<string, number>>({})
const activeProfile = ref<LookupColumnsProfile>('standard')
const applyingProfile = ref(false)
const suspendColumnPreferenceAutoSave = ref(true)
const draggingColumnKey = ref('')
const dragOverColumnKey = ref('')
const dragOverPosition = ref<'before' | 'after' | ''>('')

const baseColumns = computed<LookupColumn[]>(() => {
  const custom = (props.columns || [])
    .map((column) => normalizeColumn(column))
    .filter((column: LookupColumn | null): column is LookupColumn => !!column)
  if (custom.length === 0) return defaultColumns.value
  const deduped = new Map<string, LookupColumn>()
  for (const column of custom) deduped.set(column.key, column)
  return Array.from(deduped.values())
})

const nonEmptyRowKeySet = computed<Set<string>>(() => {
  const out = new Set<string>()
  for (const row of rows.value) {
    if (!row || typeof row !== 'object') continue
    for (const key of Object.keys(row)) {
      if (key.startsWith('__')) continue
      const value = row[key]
      if (value === undefined || value === null || value === '') continue
      out.add(key)
    }
  }
  return out
})

const primaryBaseColumnKey = computed(() => {
  const firstBase = baseColumns.value[0]?.key
  return firstBase || String(props.displayField || 'name')
})

const isColumnRequired = (key: string) => {
  return key === primaryBaseColumnKey.value || key === 'id'
}

const lockedColumnKeys = computed<string[]>(() => {
  return baseColumns.value
    .map((column) => column.key)
    .filter((key) => isColumnRequired(key))
})

const isColumnLocked = (key: string): boolean => {
  return lockedColumnKeys.value.includes(key)
}

const autoFilteredColumns = computed<LookupColumn[]>(() => {
  const available = nonEmptyRowKeySet.value
  return baseColumns.value.filter((column) => {
    if (isColumnRequired(column.key)) return true
    return available.has(column.key)
  })
})

const isColumnVisible = (key: string): boolean => {
  if (isColumnRequired(key)) return true
  return !hiddenColumnSet.value.has(key)
}

const saveColumnsPreference = (profile?: LookupColumnsProfile) => {
  const normalizedProfile = profile || activeProfile.value
  const baseOrder = baseColumns.value.map((column) => column.key)
  const isDefaultOrder = columnOrder.value.join(',') === baseOrder.join(',')
  const defaultWidthMap: Record<string, number> = {}
  for (const column of baseColumns.value) {
    const width = Number(column.width)
    if (!Number.isFinite(width) || width <= 0) continue
    defaultWidthMap[column.key] = Math.round(width)
  }
  const normalizedWidths: Record<string, number> = {}
  for (const [key, width] of Object.entries(columnWidthMap.value)) {
    const widthNum = Number(width)
    if (!Number.isFinite(widthNum) || widthNum <= 0) continue
    const rounded = Math.round(widthNum)
    if (defaultWidthMap[key] === rounded) continue
    normalizedWidths[key] = rounded
  }
  saveLookupColumnsPreference(
    props.objectCode,
    {
      hidden: Array.from(hiddenColumnSet.value),
      order: isDefaultOrder ? [] : columnOrder.value,
      widths: normalizedWidths,
      profile: normalizedProfile
    },
    { preferenceKey: props.preferenceKey, userScope: props.userScope, scope: props.preferenceScope }
  )
  saveLastLookupProfile(
    props.objectCode,
    normalizedProfile,
    { userScope: props.userScope, scope: props.preferenceScope }
  )
}

const normalizeColumnPreferences = () => {
  const baseKeys = baseColumns.value.map((column) => column.key)
  const baseKeySet = new Set(baseKeys)

  const requiredSet = new Set(
    baseKeys.filter((key) => isColumnRequired(key))
  )

  const nextHidden = new Set<string>()
  for (const key of hiddenColumnSet.value) {
    if (!baseKeySet.has(key)) continue
    if (requiredSet.has(key)) continue
    nextHidden.add(key)
  }

  const seen = new Set<string>()
  const nextOrder: string[] = []
  for (const key of columnOrder.value) {
    if (!baseKeySet.has(key)) continue
    if (seen.has(key)) continue
    nextOrder.push(key)
    seen.add(key)
  }
  for (const key of baseKeys) {
    if (seen.has(key)) continue
    nextOrder.push(key)
    seen.add(key)
  }
  const lockedSet = new Set(lockedColumnKeys.value)
  const lockedOrder = lockedColumnKeys.value.filter((key) => baseKeySet.has(key))
  const unlockedOrder = nextOrder.filter((key) => !lockedSet.has(key))
  const normalizedOrder = [...lockedOrder, ...unlockedOrder]

  const hiddenChanged = Array.from(nextHidden).sort().join(',') !== Array.from(hiddenColumnSet.value).sort().join(',')
  const orderChanged = normalizedOrder.join(',') !== columnOrder.value.join(',')
  const currentWidths = columnWidthMap.value || {}
  const nextWidths: Record<string, number> = {}
  for (const key of baseKeys) {
    const width = Number(currentWidths[key])
    if (!Number.isFinite(width) || width <= 0) continue
    nextWidths[key] = Math.round(width)
  }
  const widthsChanged = JSON.stringify(nextWidths) !== JSON.stringify(currentWidths)

  hiddenColumnSet.value = nextHidden
  columnOrder.value = normalizedOrder
  columnWidthMap.value = nextWidths

  return hiddenChanged || orderChanged || widthsChanged
}

const sortColumnsByOrder = (columns: LookupColumn[]): LookupColumn[] => {
  const orderMap = new Map<string, number>()
  for (let index = 0; index < columnOrder.value.length; index += 1) {
    orderMap.set(columnOrder.value[index], index)
  }
  const baseIndexMap = new Map<string, number>()
  for (let index = 0; index < baseColumns.value.length; index += 1) {
    baseIndexMap.set(baseColumns.value[index].key, index)
  }

  return [...columns].sort((left, right) => {
    const leftOrder = orderMap.has(left.key)
      ? Number(orderMap.get(left.key))
      : 10_000 + Number(baseIndexMap.get(left.key) ?? 0)
    const rightOrder = orderMap.has(right.key)
      ? Number(orderMap.get(right.key))
      : 10_000 + Number(baseIndexMap.get(right.key) ?? 0)
    return leftOrder - rightOrder
  })
}

const markCustomAndSave = () => {
  if (applyingProfile.value) return
  if (activeProfile.value !== 'custom') activeProfile.value = 'custom'
  saveColumnsPreference('custom')
}

const buildCompactProfileState = (): {
  hidden: Set<string>
  order: string[]
  widths: Record<string, number>
} => {
  const baseKeys = baseColumns.value.map((column) => column.key)
  const lockedSet = new Set(lockedColumnKeys.value)
  const secondaryKey = String(props.secondaryField || '').trim()

  const visibleSet = new Set<string>([...lockedSet])
  if (secondaryKey && baseKeys.includes(secondaryKey)) visibleSet.add(secondaryKey)
  for (const rawKey of props.compactKeys || []) {
    const key = String(rawKey || '').trim()
    if (!key) continue
    if (!baseKeys.includes(key)) continue
    visibleSet.add(key)
  }

  const hidden = new Set<string>()
  for (const key of baseKeys) {
    if (!visibleSet.has(key)) hidden.add(key)
  }

  const order = [...baseKeys]
  const widths: Record<string, number> = {}
  const primary = primaryBaseColumnKey.value
  if (primary) widths[primary] = 220
  if (secondaryKey && visibleSet.has(secondaryKey) && secondaryKey !== primary) widths[secondaryKey] = 160
  widths.id = 160
  return { hidden, order, widths }
}

const applyProfile = (
  profile: LookupColumnsProfile,
  options?: { persist?: boolean }
) => {
  const persist = options?.persist !== false
  applyingProfile.value = true
  if (profile === 'standard') {
    hiddenColumnSet.value = new Set()
    columnOrder.value = baseColumns.value.map((column) => column.key)
    columnWidthMap.value = {}
  } else if (profile === 'compact') {
    const compact = buildCompactProfileState()
    hiddenColumnSet.value = compact.hidden
    columnOrder.value = compact.order
    columnWidthMap.value = compact.widths
  } else {
    // custom keeps current state; explicit custom selection only updates profile flag
  }
  normalizeColumnPreferences()
  activeProfile.value = profile
  if (persist) saveColumnsPreference(profile)
  applyingProfile.value = false
}

const setColumnVisible = (key: string, value: unknown) => {
  if (isColumnRequired(key)) return
  const next = new Set(hiddenColumnSet.value)
  if (value === false) next.add(key)
  else next.delete(key)
  hiddenColumnSet.value = next
  markCustomAndSave()
}

const applyReorderedMovableKeys = (movableKeys: string[]) => {
  const locked = lockedColumnKeys.value
  columnOrder.value = [...locked, ...movableKeys]
  markCustomAndSave()
}

const moveColumn = (key: string, offset: number) => {
  if (isColumnLocked(key)) return
  const lockedSet = new Set(lockedColumnKeys.value)
  const movable = columnOrder.value.filter((item) => !lockedSet.has(item))
  const currentIndex = movable.indexOf(key)
  if (currentIndex < 0) return
  const nextIndex = Math.max(0, Math.min(movable.length - 1, currentIndex + offset))
  if (nextIndex === currentIndex) return
  const [item] = movable.splice(currentIndex, 1)
  movable.splice(nextIndex, 0, item)
  applyReorderedMovableKeys(movable)
}

const moveColumnBefore = (sourceKey: string, targetKey: string) => {
  if (isColumnLocked(sourceKey) || isColumnLocked(targetKey)) return
  const lockedSet = new Set(lockedColumnKeys.value)
  const movable = columnOrder.value.filter((item) => !lockedSet.has(item))
  const fromIndex = movable.indexOf(sourceKey)
  const targetIndex = movable.indexOf(targetKey)
  if (fromIndex < 0 || targetIndex < 0 || fromIndex === targetIndex) return
  const [item] = movable.splice(fromIndex, 1)
  const normalizedTargetIndex = movable.indexOf(targetKey)
  movable.splice(Math.max(0, normalizedTargetIndex), 0, item)
  applyReorderedMovableKeys(movable)
}

const moveColumnAfter = (sourceKey: string, targetKey: string) => {
  if (isColumnLocked(sourceKey) || isColumnLocked(targetKey)) return
  const lockedSet = new Set(lockedColumnKeys.value)
  const movable = columnOrder.value.filter((item) => !lockedSet.has(item))
  const fromIndex = movable.indexOf(sourceKey)
  const targetIndex = movable.indexOf(targetKey)
  if (fromIndex < 0 || targetIndex < 0 || fromIndex === targetIndex) return
  const [item] = movable.splice(fromIndex, 1)
  const normalizedTargetIndex = movable.indexOf(targetKey)
  movable.splice(Math.min(movable.length, normalizedTargetIndex + 1), 0, item)
  applyReorderedMovableKeys(movable)
}

const hydrateColumnPreferences = () => {
  const hasStoredPreference = hasLookupColumnsPreference(
    props.objectCode,
    { preferenceKey: props.preferenceKey, userScope: props.userScope, scope: props.preferenceScope }
  )
  const preference = loadLookupColumnsPreference(
    props.objectCode,
    { preferenceKey: props.preferenceKey, userScope: props.userScope, scope: props.preferenceScope }
  )
  hiddenColumnSet.value = new Set(preference.hidden)
  columnOrder.value = [...preference.order]
  columnWidthMap.value = { ...preference.widths }
  const fallbackProfile = loadLastLookupProfile(
    props.objectCode,
    { userScope: props.userScope, scope: props.preferenceScope }
  )
  const initialProfile = hasStoredPreference
    ? (preference.profile || 'standard')
    : fallbackProfile
  activeProfile.value = initialProfile
  if (!hasStoredPreference && initialProfile !== 'custom') {
    applyProfile(initialProfile, { persist: false })
    return
  }
  normalizeColumnPreferences()
}

const handleColumnDragStart = (key: string, event: DragEvent) => {
  if (isColumnLocked(key)) {
    event.preventDefault()
    return
  }
  draggingColumnKey.value = key
  dragOverColumnKey.value = ''
  dragOverPosition.value = ''
  if (!event.dataTransfer) return
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', key)
}

const handleColumnDragOver = (key: string, event: DragEvent) => {
  if (isColumnLocked(key)) return
  if (!draggingColumnKey.value || draggingColumnKey.value === key) return
  dragOverColumnKey.value = key
  const currentTarget = event.currentTarget
  if (currentTarget instanceof HTMLElement) {
    const rect = currentTarget.getBoundingClientRect()
    const middleY = rect.top + rect.height / 2
    dragOverPosition.value = event.clientY <= middleY ? 'before' : 'after'
  }
  if (!event.dataTransfer) return
  event.dataTransfer.dropEffect = 'move'
}

const handleColumnDrop = (targetKey: string, _event?: DragEvent) => {
  const sourceKey = draggingColumnKey.value
  if (!sourceKey || sourceKey === targetKey || isColumnLocked(sourceKey) || isColumnLocked(targetKey)) {
    draggingColumnKey.value = ''
    dragOverColumnKey.value = ''
    dragOverPosition.value = ''
    return
  }
  if (dragOverPosition.value === 'after') moveColumnAfter(sourceKey, targetKey)
  else moveColumnBefore(sourceKey, targetKey)
  draggingColumnKey.value = ''
  dragOverColumnKey.value = ''
  dragOverPosition.value = ''
}

const handleColumnDragEnd = () => {
  draggingColumnKey.value = ''
  dragOverColumnKey.value = ''
  dragOverPosition.value = ''
}

const isMoveDisabled = (key: string, offset: number): boolean => {
  if (isColumnLocked(key)) return true
  const movableKeys = orderedAutoFilteredColumns.value
    .map((column) => column.key)
    .filter((columnKey) => !isColumnLocked(columnKey))
  const index = movableKeys.indexOf(key)
  if (index < 0) return true
  if (offset < 0 && index <= 0) return true
  if (offset > 0 && index >= movableKeys.length - 1) return true
  return false
}

const handleProfileChange = (value: string | number | boolean) => {
  const normalized = String(value || '').trim().toLowerCase()
  if (normalized !== 'standard' && normalized !== 'compact' && normalized !== 'custom') return
  if (applyingProfile.value) return
  applyProfile(normalized as LookupColumnsProfile)
}

const resolveHeaderColumnKey = (column: AnyRecord): string => {
  const key = String(
    column?.columnKey ||
    column?.property ||
    column?.rawColumnKey ||
    ''
  ).trim()
  return key
}

const handleHeaderDragEnd = (newWidth: number, _oldWidth: number, column: AnyRecord) => {
  const key = resolveHeaderColumnKey(column)
  if (!key) return
  if (!baseColumns.value.some((item) => item.key === key)) return
  const width = Number(newWidth)
  if (!Number.isFinite(width) || width <= 0) return
  columnWidthMap.value = {
    ...columnWidthMap.value,
    [key]: Math.round(width)
  }
  markCustomAndSave()
}

const resetColumnsPreference = () => {
  hiddenColumnSet.value = new Set()
  columnOrder.value = baseColumns.value.map((column) => column.key)
  columnWidthMap.value = {}
  activeProfile.value = 'standard'
  clearLookupColumnsPreference(
    props.objectCode,
    { preferenceKey: props.preferenceKey, userScope: props.userScope, scope: props.preferenceScope }
  )
  saveLastLookupProfile(
    props.objectCode,
    'standard',
    { userScope: props.userScope, scope: props.preferenceScope }
  )
}

const orderedAutoFilteredColumns = computed<LookupColumn[]>(() => {
  const ordered = sortColumnsByOrder(autoFilteredColumns.value)
  return ordered.map((column) => {
    const width = Number(columnWidthMap.value[column.key])
    if (!Number.isFinite(width) || width <= 0) return column
    return {
      ...column,
      width: Math.round(width)
    }
  })
})

const visibleColumns = computed<LookupColumn[]>(() => {
  return orderedAutoFilteredColumns.value.filter((column) => isColumnVisible(column.key))
})

const primaryColumnKey = computed(() => {
  return primaryBaseColumnKey.value
})

const groupCountMap = computed<Record<string, number>>(() => {
  const out: Record<string, number> = {
    recent: 0,
    search: 0
  }
  for (const row of rows.value) {
    const group = String(row?.__group || 'search')
    out[group] = Number(out[group] || 0) + 1
  }
  return out
})
const footerGroupItems = computed<Array<{ key: 'recent' | 'search', label: string, count: number }>>(() => {
  const recentCount = Number(groupCountMap.value.recent || 0)
  const searchCount = Number(groupCountMap.value.search || 0)
  const items: Array<{ key: 'recent' | 'search', label: string, count: number }> = []
  if (recentCount > 0) {
    items.push({
      key: 'recent',
      label: tr('common.labels.recentRecords', 'Recent'),
      count: recentCount
    })
  }
  if (searchCount > 0) {
    items.push({
      key: 'search',
      label: tr('common.labels.searchResults', 'Search'),
      count: searchCount
    })
  }
  return items
})

const canConfirm = computed(() => {
  if (props.multiple) return Object.keys(selectedMap.value).length > 0
  return !!activeSingleId.value
})

const viewModeOptions = computed(() => [
  { label: tr('common.recent', 'Recent'), value: 'recent' },
  { label: tr('common.all', 'All'), value: 'all' }
])

const selectionSummary = computed(() => {
  const count = props.multiple ? Object.keys(selectedMap.value).length : (activeSingleId.value ? 1 : 0)
  return tr('common.table.selected', `Selected ${count}`, { count })
})

const normalizeRow = (input: unknown): AnyRecord | null => {
  if (!input || typeof input !== 'object') return null
  const raw = input as AnyRecord
  const id = String(raw.id || raw.pk || raw.value || '').trim()
  if (!id) return null
  return {
    ...raw,
    id
  }
}

const resolveLabel = (row: AnyRecord) => {
  return resolveReferenceLabel(row, props.displayField || 'name') || row.id
}

const resolveSecondary = (row: AnyRecord) => {
  return resolveReferenceSecondaryText(row, props.secondaryField || 'code', props.displayField || 'name')
}

const isPrimaryColumn = (column: LookupColumn) => {
  return column.key === primaryColumnKey.value
}

const resolveColumnValue = (row: AnyRecord, key: string): string => {
  if (key === 'id') return String(row?.id || '-')
  const value = row?.[key]
  if (value === undefined || value === null || value === '') return '-'
  return String(value)
}

const resolvePrimaryLabel = (row: AnyRecord, key: string): string => {
  const explicit = resolveColumnValue(row, key)
  if (explicit !== '-') return explicit
  return resolveLabel(row)
}

const resolveGroupTitle = (group: unknown): string => {
  const groupKey = group === 'recent' ? 'recent' : 'search'
  const title = groupKey === 'recent' ? recentGroupTitleText.value : searchGroupTitleText.value
  const count = Number(groupCountMap.value[groupKey] || 0)
  return `${title} (${count})`
}

const getScopedSearchCandidatePool = (row: AnyRecord): string[] => {
  const scope = searchScope.value === 'secondary' && !hasSecondaryField.value
    ? 'all'
    : searchScope.value

  if (scope === 'id') {
    return [String(row?.id || '')]
  }

  if (scope === 'primary') {
    return [
      resolveLabel(row),
      String(row?.[props.displayField || 'name'] || '')
    ]
  }

  if (scope === 'secondary') {
    return [
      resolveSecondary(row),
      String(row?.[props.secondaryField || 'code'] || '')
    ]
  }

  return [
    resolveLabel(row),
    resolveSecondary(row),
    String(row?.id || '')
  ]
}

const matchesKeyword = (row: AnyRecord, rawKeyword: string): boolean => {
  const keywordText = String(rawKeyword || '').trim().toLowerCase()
  if (!keywordText) return true
  const candidatePool = getScopedSearchCandidatePool(row)
    .map((item) => String(item || '').toLowerCase())
    .filter(Boolean)
  return candidatePool.some((text) => text.includes(keywordText))
}

const getNavigableRows = (): AnyRecord[] => {
  return rows.value.filter((row) => !!row?.id)
}

const setActiveRowByIndex = (index: number) => {
  const list = getNavigableRows()
  if (list.length === 0) return
  const bounded = Math.max(0, Math.min(index, list.length - 1))
  const row = list[bounded]
  activeSingleId.value = row.id
  activeSingleRow.value = row
  if (tableRef.value && typeof tableRef.value.setCurrentRow === 'function') {
    tableRef.value.setCurrentRow(row)
  }
}

const isToolbarInputTarget = (target: EventTarget | null): boolean => {
  if (!(target instanceof HTMLElement)) return false
  if (target.closest('.lookup-toolbar__search')) return true
  return target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
}

const handleGlobalKeydown = (event: KeyboardEvent) => {
  if (!props.modelValue) return
  if (props.multiple) return
  if (isToolbarInputTarget(event.target)) return

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    const list = getNavigableRows()
    if (list.length === 0) return
    const currentIndex = list.findIndex((row) => row.id === activeSingleId.value)
    setActiveRowByIndex(currentIndex < 0 ? 0 : currentIndex + 1)
    return
  }

  if (event.key === 'ArrowUp') {
    event.preventDefault()
    const list = getNavigableRows()
    if (list.length === 0) return
    const currentIndex = list.findIndex((row) => row.id === activeSingleId.value)
    setActiveRowByIndex(currentIndex < 0 ? 0 : currentIndex - 1)
    return
  }

  if (event.key === 'Enter' && canConfirm.value) {
    event.preventDefault()
    handleConfirm()
  }
}

const syncTableSelection = async () => {
  await nextTick()

  if (!props.multiple) {
    if (!activeSingleId.value) {
      activeSingleRow.value = null
      if (tableRef.value && typeof tableRef.value.setCurrentRow === 'function') {
        tableRef.value.setCurrentRow(null)
      }
    } else {
      const selected = rows.value.find((row) => row.id === activeSingleId.value) || null
      if (selected) {
        activeSingleRow.value = selected
      } else {
        activeSingleId.value = ''
        activeSingleRow.value = null
        if (tableRef.value && typeof tableRef.value.setCurrentRow === 'function') {
          tableRef.value.setCurrentRow(null)
        }
      }
    }
  }

  if (!props.multiple || !tableRef.value) return
  tableRef.value.clearSelection()
  for (const row of rows.value) {
    if (selectedMap.value[row.id]) {
      tableRef.value.toggleRowSelection(row, true)
    }
  }
}

const loadRecentRows = async () => {
  const recentIds = loadRecentReferenceIds(props.objectCode, {
    limit: 30,
    scope: props.preferenceScope
  })
  if (recentIds.length === 0) {
    rows.value = []
    total.value = 0
    return
  }
  const resolved = await referenceResolver.resolveMany(props.objectCode, recentIds)
  const recentRowsMaybe: Array<AnyRecord | null> = recentIds
    .map((id, index) => {
      const row = normalizeRow(resolved[id])
      if (!row) return null
      return {
        ...row,
        __recentPinned: true,
        __group: 'recent',
        __showGroupTitle: index === 0
      }
    })
  rows.value = recentRowsMaybe.filter((item: AnyRecord | null): item is AnyRecord => !!item)
  total.value = rows.value.length
}

const loadData = async () => {
  if (!props.objectCode) {
    rows.value = []
    total.value = 0
    return
  }

  loading.value = true
  try {
    if (viewMode.value === 'recent') {
      await loadRecentRows()
      return
    }

    const res: AnyRecord = await searchReferenceData({
      reference_object: props.objectCode,
      search: keyword.value.trim(),
      page: page.value,
      page_size: pageSize,
      lookup_search_scope: searchScope.value,
      lookup_display_field: props.displayField || 'name',
      lookup_secondary_field: props.secondaryField || 'code'
    })
    const rawItems: unknown[] = Array.isArray(res?.results)
      ? res.results
      : Array.isArray(res?.items)
        ? res.items
        : []
    const items: AnyRecord[] = rawItems
      .map((item: unknown) => normalizeRow(item))
      .filter((item: AnyRecord | null): item is AnyRecord => !!item)
    const recentIds = loadRecentReferenceIds(props.objectCode, {
      limit: 8,
      scope: props.preferenceScope
    })

    if (recentIds.length === 0) {
      rows.value = items.map((item: AnyRecord, index: number) => ({
        ...item,
        __recentPinned: false,
        __group: 'search',
        __showGroupTitle: index === 0
      }))
      total.value = Number(res?.count || res?.total || items.length)
      return
    }

    const recentResolved = await referenceResolver.resolveMany(props.objectCode, recentIds)
    const recentRowsMaybe: Array<AnyRecord | null> = recentIds
      .map((id, index) => {
        const fromSearch = items.find((item) => item.id === id)
        const base = fromSearch || normalizeRow(recentResolved[id])
        if (!base) return null
        return {
          ...base,
          __recentPinned: true,
          __group: 'recent',
          __showGroupTitle: index === 0
        }
      })
    const recentRows: AnyRecord[] = recentRowsMaybe.filter(
      (item: AnyRecord | null): item is AnyRecord => !!item
    )
      .filter((item: AnyRecord) => matchesKeyword(item, keyword.value))

    const recentIdSet = new Set(recentRows.map((row) => row.id))
    const searchRows = items
      .filter((item: AnyRecord) => !recentIdSet.has(item.id))
      .map((item: AnyRecord, index: number) => ({
        ...item,
        __recentPinned: false,
        __group: 'search',
        __showGroupTitle: index === 0
      }))

    const mergedRows: AnyRecord[] = [
      ...recentRows,
      ...searchRows
    ]
    rows.value = mergedRows
    total.value = Number(res?.count || res?.total || items.length)
  } catch (error) {
    console.warn('Failed to load lookup dialog data:', error)
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
    await syncTableSelection()
  }
}

const hydrateSelectedRows = async () => {
  const seedIds = (props.selectedIds || [])
    .map((id) => String(id || '').trim())
    .filter(Boolean)
  if (seedIds.length === 0) {
    selectedMap.value = {}
    activeSingleId.value = ''
    activeSingleRow.value = null
    return
  }

  if (props.multiple) {
    const next: Record<string, AnyRecord> = {}
    for (const id of seedIds) next[id] = { id }
    selectedMap.value = next
    return
  }

  activeSingleId.value = seedIds[0]
  activeSingleRow.value = { id: seedIds[0] }
}

const handleOpened = async () => {
  const recentIds = loadRecentReferenceIds(props.objectCode, {
    limit: 30,
    scope: props.preferenceScope
  })
  viewMode.value = recentIds.length > 0 ? 'recent' : 'all'
  page.value = 1
  await hydrateSelectedRows()
  await loadData()
}

const handleSearch = async () => {
  viewMode.value = 'all'
  page.value = 1
  await loadData()
}

const handleReset = async () => {
  viewMode.value = 'all'
  keyword.value = ''
  searchScope.value = 'all'
  page.value = 1
  await loadData()
}

const handlePageChange = async (nextPage: number) => {
  page.value = Number(nextPage || 1)
  await loadData()
}

const handleSelectionChange = (list: AnyRecord[]) => {
  if (!props.multiple) return
  const rowIds = new Set(rows.value.map((row) => row.id))
  const next = { ...selectedMap.value }

  for (const id of rowIds) {
    if (!list.find((row) => row.id === id)) {
      delete next[id]
    }
  }

  for (const row of list) {
    next[row.id] = row
  }
  selectedMap.value = next
}

const handleRowClick = (row: AnyRecord) => {
  if (props.multiple) return
  activeSingleId.value = row.id
  activeSingleRow.value = row
}

const handleRowDblClick = (row: AnyRecord) => {
  if (props.multiple) return
  activeSingleId.value = row.id
  activeSingleRow.value = row
  handleConfirm()
}

const getRowClassName = ({ row }: { row: AnyRecord }) => {
  const classes: string[] = []
  if (!props.multiple && row?.id === activeSingleId.value) {
    classes.push('is-active-single-row')
  }
  if (row?.__recentPinned) {
    classes.push('is-recent-pinned-row')
  }
  return classes.join(' ')
}

const handleConfirm = () => {
  if (!canConfirm.value) return
  if (props.multiple) {
    emit('confirm', Object.values(selectedMap.value))
    emit('update:modelValue', false)
    return
  }

  const single = activeSingleRow.value || rows.value.find((row) => row.id === activeSingleId.value) || { id: activeSingleId.value }
  emit('confirm', [single])
  emit('update:modelValue', false)
}

const openCreate = () => {
  if (!props.objectCode) return
  if (typeof window === 'undefined') return
  const targetUrl = `/objects/${props.objectCode}/create`
  window.open(targetUrl, '_blank', 'noopener,noreferrer')
}

const handleOpenSelected = () => {
  if (!props.objectCode) return
  const id = String(activeSingleId.value || activeSingleRow.value?.id || '').trim()
  if (!id) return
  if (typeof window === 'undefined') return
  const targetUrl = `/objects/${props.objectCode}/${encodeURIComponent(id)}`
  window.open(targetUrl, '_blank', 'noopener,noreferrer')
}

watch(
  () => props.modelValue,
  (open) => {
    if (typeof window !== 'undefined') {
      if (open) window.addEventListener('keydown', handleGlobalKeydown)
      else window.removeEventListener('keydown', handleGlobalKeydown)
    }
    if (!open) return
    // Keep keyword from last search to match common lookup behavior.
    handleOpened()
  }
)

watch(
  () => viewMode.value,
  async () => {
    page.value = 1
    await loadData()
  }
)

watch(
  () => searchScope.value,
  async () => {
    if (!props.modelValue) return
    page.value = 1
    await loadData()
  }
)

watch(
  () => baseColumns.value.map((column) => column.key).join(','),
  () => {
    if (suspendColumnPreferenceAutoSave.value) return
    normalizeColumnPreferences()
  }
)

watch(
  () => [props.displayField, props.secondaryField],
  () => {
    if (searchScope.value === 'secondary' && !hasSecondaryField.value) {
      searchScope.value = 'all'
    }
  }
)

watch(
  () => [
    props.objectCode,
    props.preferenceKey,
    props.userScope,
    props.preferenceScope,
    props.displayField,
    props.secondaryField,
    baseColumns.value.map((column) => column.key).join(',')
  ],
  async () => {
    suspendColumnPreferenceAutoSave.value = true
    hydrateColumnPreferences()
    await nextTick()
    suspendColumnPreferenceAutoSave.value = false
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (typeof window === 'undefined') return
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<style scoped lang="scss">
.lookup-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.lookup-toolbar__mode {
  flex-shrink: 0;
}

.lookup-toolbar__search {
  flex: 1;
  min-width: 220px;
}

.lookup-toolbar__scope {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.lookup-toolbar__scope-label {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.lookup-toolbar__scope-segmented {
  min-width: 220px;
}

.lookup-column-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lookup-column-settings__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.lookup-column-settings__title {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.lookup-column-settings__reset {
  font-size: 12px;
  padding: 0;
}

.lookup-column-settings__profiles {
  width: 100%;
}

.lookup-column-settings__profile-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.35;
}

.lookup-column-settings__row {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 2px 4px;
  border-radius: 6px;
}

.lookup-column-settings__row.is-locked {
  background: color-mix(in srgb, var(--el-fill-color-light) 75%, #ffffff);
}

.lookup-column-settings__row.is-dragging {
  opacity: 0.65;
}

.lookup-column-settings__row.is-drag-over-top::before,
.lookup-column-settings__row.is-drag-over-bottom::after {
  content: '';
  position: absolute;
  left: 4px;
  right: 4px;
  height: 2px;
  border-radius: 2px;
  background: var(--el-color-primary);
}

.lookup-column-settings__row.is-drag-over-top::before {
  top: -1px;
}

.lookup-column-settings__row.is-drag-over-bottom::after {
  bottom: -1px;
}

.lookup-column-settings__drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  cursor: grab;
}

.lookup-column-settings__row.is-locked .lookup-column-settings__drag-handle {
  cursor: default;
  opacity: 0.55;
}

.lookup-column-settings__lock-icon {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.lookup-column-settings__order {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.lookup-column-settings__item {
  margin: 0;
  flex: 1;
  min-width: 0;
}

.lookup-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lookup-cell__group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 11px;
  letter-spacing: 0.2px;
  text-transform: uppercase;
  margin: 2px 0 6px;
}

.lookup-cell__group-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  flex-shrink: 0;
}

.lookup-cell__group-dot.is-recent {
  background: color-mix(in srgb, var(--el-color-warning) 88%, #ffffff);
}

.lookup-cell__group-dot.is-search {
  background: color-mix(in srgb, var(--el-color-primary) 88%, #ffffff);
}

.lookup-cell__group-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--el-border-color-light), transparent);
}

.lookup-cell__content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.lookup-cell__name {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.lookup-cell__recent-tag {
  flex-shrink: 0;
}

.lookup-cell__secondary {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.lookup-cell__id {
  font-family: 'Consolas', 'Monaco', monospace;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.lookup-cell__text {
  color: var(--el-text-color-regular);
  font-size: 13px;
  word-break: break-word;
}

.lookup-footer {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.lookup-footer__meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.lookup-footer__summary {
  white-space: nowrap;
}

.lookup-footer__group {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding-left: 10px;
  white-space: nowrap;
}

.lookup-footer__group::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 999px;
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
}

.lookup-footer__group.is-recent::before {
  background: color-mix(in srgb, var(--el-color-warning) 88%, #ffffff);
}

.lookup-footer__group.is-search::before {
  background: color-mix(in srgb, var(--el-color-primary) 88%, #ffffff);
}

.lookup-hotkeys {
  margin-top: 8px;
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.lookup-hotkeys__title {
  font-weight: 600;
}

.lookup-hotkeys__item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.lookup-hotkeys kbd {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
  line-height: 1;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 3px 5px;
  color: var(--el-text-color-regular);
  background: color-mix(in srgb, var(--el-fill-color-light) 70%, #ffffff);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 980px) {
  .lookup-toolbar__scope {
    width: 100%;
  }

  .lookup-toolbar__scope-segmented {
    flex: 1;
    min-width: 0;
  }
}

:deep(.el-table .is-active-single-row > td) {
  background: color-mix(in srgb, var(--el-color-primary-light-9) 78%, #ffffff);
}

:deep(.el-table .is-recent-pinned-row > td) {
  border-top: 1px dashed var(--el-border-color-light);
}
</style>
