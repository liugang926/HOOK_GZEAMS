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
    >
      <el-table-column
        v-if="multiple"
        type="selection"
        width="46"
        reserve-selection
      />
      <el-table-column
        :label="nameLabel"
        min-width="220"
      >
        <template #default="{ row }">
          <div class="lookup-cell">
            <ObjectAvatar
              :object-code="objectCode || 'Ref'"
              size="xs"
            />
            <div class="lookup-cell__content">
              <span class="lookup-cell__name">
                {{ resolveLabel(row) }}
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
      </el-table-column>
      <el-table-column
        :label="idLabel"
        min-width="180"
      >
        <template #default="{ row }">
          <span class="lookup-cell__id">{{ row.id }}</span>
        </template>
      </el-table-column>
    </el-table>

    <div class="lookup-footer">
      <div class="lookup-footer__meta">
        {{ selectionSummary }}
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

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="$emit('update:modelValue', false)">
          {{ cancelActionText }}
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
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'
import { searchReferenceData } from '@/api/system'
import { referenceResolver } from '@/platform/reference/referenceResolver'
import { resolveReferenceLabel, resolveReferenceSecondaryText } from '@/platform/reference/referenceFieldMeta'
import { loadRecentReferenceIds } from '@/platform/reference/referenceLookupRecent'

type AnyRecord = Record<string, any>

const props = withDefaults(defineProps<{
  modelValue: boolean
  objectCode: string
  displayField: string
  secondaryField: string
  multiple?: boolean
  selectedIds?: string[]
  allowCreate?: boolean
}>(), {
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

const tr = (key: string, fallback: string, params?: Record<string, any>) => {
  const text = t(key, params || {})
  return text === key ? fallback : text
}

const dialogTitle = computed(() =>
  `${tr('common.actions.search', 'Advanced Lookup')} - ${props.objectCode || 'Reference'}`
)
const searchPlaceholder = computed(() =>
  tr('common.placeholders.search', 'Enter keyword')
)
const searchActionText = computed(() => tr('common.actions.search', 'Search'))
const resetActionText = computed(() => tr('common.actions.reset', 'Reset'))
const createActionText = computed(() => tr('common.actions.create', 'New'))
const cancelActionText = computed(() => tr('common.actions.cancel', 'Cancel'))
const confirmActionText = computed(() => tr('common.actions.confirm', 'Confirm'))
const nameLabel = computed(() => tr('common.columns.name', 'Name'))
const idLabel = 'ID'
const recentTagText = computed(() => tr('common.recent', 'Recent'))

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

const matchesKeyword = (row: AnyRecord, rawKeyword: string): boolean => {
  const keywordText = String(rawKeyword || '').trim().toLowerCase()
  if (!keywordText) return true
  const candidatePool = [
    resolveLabel(row),
    resolveSecondary(row),
    row?.id
  ]
    .map((item) => String(item || '').toLowerCase())
    .filter(Boolean)
  return candidatePool.some((text) => text.includes(keywordText))
}

const syncTableSelection = async () => {
  await nextTick()

  if (!props.multiple && activeSingleId.value) {
    const selected = rows.value.find((row) => row.id === activeSingleId.value) || null
    if (selected) activeSingleRow.value = selected
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
  const recentIds = loadRecentReferenceIds(props.objectCode, { limit: 30 })
  if (recentIds.length === 0) {
    rows.value = []
    total.value = 0
    return
  }
  const resolved = await referenceResolver.resolveMany(props.objectCode, recentIds)
  const recentRowsMaybe: Array<AnyRecord | null> = recentIds
    .map((id) => {
      const row = normalizeRow(resolved[id])
      if (!row) return null
      return {
        ...row,
        __recentPinned: true
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
      page_size: pageSize
    })
    const rawItems: unknown[] = Array.isArray(res?.results)
      ? res.results
      : Array.isArray(res?.items)
        ? res.items
        : []
    const items: AnyRecord[] = rawItems
      .map((item: unknown) => normalizeRow(item))
      .filter((item: AnyRecord | null): item is AnyRecord => !!item)
    const recentIds = loadRecentReferenceIds(props.objectCode, { limit: 8 })

    if (recentIds.length === 0) {
      rows.value = items
      total.value = Number(res?.count || res?.total || items.length)
      return
    }

    const recentResolved = await referenceResolver.resolveMany(props.objectCode, recentIds)
    const recentRowsMaybe: Array<AnyRecord | null> = recentIds
      .map((id) => {
        const fromSearch = items.find((item) => item.id === id)
        const base = fromSearch || normalizeRow(recentResolved[id])
        if (!base) return null
        return {
          ...base,
          __recentPinned: true
        }
      })
    const recentRows: AnyRecord[] = recentRowsMaybe.filter(
      (item: AnyRecord | null): item is AnyRecord => !!item
    )
      .filter((item: AnyRecord) => matchesKeyword(item, keyword.value))

    const recentIdSet = new Set(recentRows.map((row) => row.id))
    const mergedRows: AnyRecord[] = [
      ...recentRows,
      ...items
        .filter((item: AnyRecord) => !recentIdSet.has(item.id))
        .map((item: AnyRecord) => ({
          ...item,
          __recentPinned: false
        }))
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
  const recentIds = loadRecentReferenceIds(props.objectCode, { limit: 30 })
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

watch(
  () => props.modelValue,
  (open) => {
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
</script>

<style scoped lang="scss">
.lookup-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.lookup-toolbar__mode {
  flex-shrink: 0;
}

.lookup-toolbar__search {
  flex: 1;
}

.lookup-cell {
  display: flex;
  align-items: center;
  gap: 8px;
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

.lookup-footer {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.lookup-footer__meta {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

:deep(.el-table .is-active-single-row > td) {
  background: color-mix(in srgb, var(--el-color-primary-light-9) 78%, #ffffff);
}

:deep(.el-table .is-recent-pinned-row > td) {
  border-top: 1px dashed var(--el-border-color-light);
}
</style>
