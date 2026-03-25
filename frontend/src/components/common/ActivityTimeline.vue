<template>
  <div class="activity-timeline-container">
    <div
      v-if="effectiveLoading"
      class="timeline-loading"
    >
      <el-skeleton
        :rows="5"
        animated
      />
    </div>

    <div v-else-if="effectiveActivities.length === 0">
      <BaseEmptyState
        :title="$t('common.messages.noTimelineData')"
        :description="$t('common.messages.timelineHint')"
      />
    </div>

    <template v-else>
      <div class="timeline-toolbar">
        <div class="timeline-toolbar__left">
          <h3 class="timeline-toolbar__title">
            {{ $t('common.history.title') }}
          </h3>
          <el-tag
            type="info"
            effect="plain"
            size="small"
          >
            {{ filteredActivities.length }}
          </el-tag>
        </div>

        <div class="timeline-toolbar__right">
          <el-select
            v-if="sourceOptions.length > 1"
            v-model="sourceFilter"
            size="small"
            class="timeline-filter"
          >
            <el-option
              v-for="option in sourceOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>

          <el-segmented
            v-model="viewMode"
            :options="viewOptions"
            size="small"
          />
        </div>
      </div>

      <BaseEmptyState
        v-if="filteredActivities.length === 0"
        :title="translateOrFallback('common.messages.noTimelineData', 'No timeline data')"
        :description="translateOrFallback('common.messages.timelineHint', 'Try a different filter to view lifecycle activity.')"
      />

      <div
        v-else-if="viewMode === 'timeline'"
        class="visual-timeline"
      >
        <div
          v-for="group in filteredGroups"
          :key="group.dateKey"
          class="timeline-date-group"
        >
          <div class="timeline-date-label">
            {{ formatDateLabel(group.dateKey, group.dateLabel) }}
          </div>

          <div
            v-for="entry in group.entries"
            :key="entry.id"
            class="timeline-entry"
          >
            <div class="timeline-entry__rail">
              <div
                class="timeline-entry__dot"
                :class="`dot--${entry.action}`"
              >
                <el-icon :size="14">
                  <component :is="getActionIcon(entry.action)" />
                </el-icon>
              </div>
              <div class="timeline-entry__line" />
            </div>

            <div class="timeline-entry__body">
              <div class="timeline-entry__header">
                <el-tag
                  :type="getActivityType(entry.action) as any"
                  effect="light"
                  size="small"
                  class="action-badge"
                >
                  {{ resolveActionLabel(entry.action, entry.actionLabel) }}
                </el-tag>
                <el-tag
                  v-if="entry.sourceLabel"
                  size="small"
                  effect="plain"
                  class="source-badge"
                >
                  {{ entry.sourceLabel }}
                </el-tag>
                <span class="timeline-entry__user">{{ entry.userName || $t('common.labels.system') }}</span>
                <span class="timeline-entry__time">{{ formatTime(entry.createdAt || entry.timestamp || '') }}</span>
              </div>

              <div
                v-if="entry.description"
                class="timeline-entry__desc"
              >
                {{ entry.description }}
              </div>

              <div
                v-if="canNavigate(entry)"
                class="timeline-entry__link-row"
              >
                <span class="timeline-entry__record">{{ entry.recordLabel || entry.objectId }}</span>
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="navigateToEntry(entry)"
                >
                  {{ translateOrFallback('common.actions.view', 'View') }}
                </el-button>
              </div>

              <div
                v-if="entry.changes && entry.changes.length > 0"
                class="timeline-entry__changes"
              >
                <el-collapse-transition>
                  <div v-if="expandedEntries.has(entry.id)">
                    <div
                      v-for="(change, ci) in entry.changes"
                      :key="ci"
                      class="change-row"
                    >
                      <span class="change-row__field">{{ change.fieldLabel || change.fieldCode }}</span>
                      <span class="change-row__old">{{ formatValue(change.oldValue) }}</span>
                      <el-icon
                        :size="12"
                        class="change-row__arrow"
                      >
                        <Right />
                      </el-icon>
                      <span class="change-row__new">{{ formatValue(change.newValue) }}</span>
                    </div>
                  </div>
                </el-collapse-transition>
                <el-button
                  type="primary"
                  link
                  size="small"
                  class="toggle-changes-btn"
                  @click="toggleChanges(entry.id)"
                >
                  {{ expandedEntries.has(entry.id)
                    ? $t('common.actions.collapse')
                    : $t('common.actions.viewChanges', { count: entry.changes.length })
                  }}
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="history-table-shell"
      >
        <el-table
          :data="historyRows"
          row-key="rowKey"
          stripe
          border
          class="history-table"
        >
          <el-table-column
            prop="timestamp"
            :label="$t('common.history.columns.changedAt')"
            min-width="168"
          >
            <template #default="{ row }">
              {{ formatDate(row.timestamp || '') }}
            </template>
          </el-table-column>
          <el-table-column
            prop="sourceLabel"
            :label="translateOrFallback('common.labels.object', 'Object')"
            min-width="140"
          />
          <el-table-column
            prop="recordLabel"
            :label="translateOrFallback('common.labels.record', 'Record')"
            min-width="160"
          >
            <template #default="{ row }">
              <el-button
                v-if="row.objectCode && row.objectId"
                type="primary"
                link
                size="small"
                @click="navigateToEntry(row)"
              >
                {{ row.recordLabel || row.objectId }}
              </el-button>
              <span v-else>{{ row.recordLabel || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="userName"
            :label="$t('common.history.columns.changedBy')"
            min-width="140"
          >
            <template #default="{ row }">
              {{ row.userName || $t('common.labels.system') }}
            </template>
          </el-table-column>
          <el-table-column
            prop="actionLabel"
            :label="$t('common.history.columns.action')"
            min-width="132"
          >
            <template #default="{ row }">
              <el-tag
                :type="getActivityType(row.action) as any"
                effect="light"
                class="action-badge"
              >
                {{ row.actionLabel }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="fieldLabel"
            :label="$t('common.history.columns.field')"
            min-width="160"
          >
            <template #default="{ row }">
              {{ row.fieldLabel || $t('common.history.labels.recordLevel') }}
            </template>
          </el-table-column>
          <el-table-column
            prop="oldValue"
            :label="$t('common.history.columns.oldValue')"
            min-width="180"
          >
            <template #default="{ row }">
              <span class="value-chip old-value">{{ formatValue(row.oldValue) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="newValue"
            :label="$t('common.history.columns.newValue')"
            min-width="180"
          >
            <template #default="{ row }">
              <span class="value-chip new-value">{{ formatValue(row.newValue) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="description"
            :label="$t('common.history.columns.description')"
            min-width="220"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              {{ row.description || '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div
        v-if="effectiveHasMore"
        class="load-more-container"
      >
        <el-button
          :loading="effectiveLoadingMore"
          type="primary"
          link
          @click="loadMore"
        >
          {{ $t('common.actions.loadMore') }}
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils/dateFormat'
import {
  Plus, EditPen, Delete, Right, Switch, InfoFilled, UserFilled,
} from '@element-plus/icons-vue'
import BaseEmptyState from '@/components/common/BaseEmptyState.vue'
import { useActivityTimeline, type ActivityLogEntry, type DateGroup } from '@/composables/useActivityTimeline'

interface Props {
  objectCode: string
  recordId: string
  fetchUrl?: string
  entries?: ActivityLogEntry[]
  placement?: 'top' | 'bottom'
  size?: 'normal' | 'large'
}

interface TimelineRow extends ActivityLogEntry {
  rowKey: string
  fieldLabel?: string
  oldValue: any
  newValue: any
}

const props = withDefaults(defineProps<Props>(), {
  placement: 'top',
  size: 'normal',
  fetchUrl: '',
  entries: () => [],
})

const router = useRouter()
const { t } = useI18n()
const externalEntriesMode = computed(() => Array.isArray(props.entries) && props.entries.length > 0)

const {
  activities,
  loading,
  loadingMore,
  hasMore,
  loadMore,
} = useActivityTimeline(
  () => (externalEntriesMode.value ? '' : props.objectCode),
  () => (externalEntriesMode.value ? '' : props.recordId),
  () => (externalEntriesMode.value ? '' : props.fetchUrl),
)
const effectiveActivities = computed(() => (externalEntriesMode.value ? props.entries : activities.value))
const effectiveLoading = computed(() => (externalEntriesMode.value ? false : loading.value))
const effectiveLoadingMore = computed(() => (externalEntriesMode.value ? false : loadingMore.value))
const effectiveHasMore = computed(() => (externalEntriesMode.value ? false : hasMore.value))

const viewMode = ref<'timeline' | 'table'>('timeline')
const sourceFilter = ref('all')
const expandedEntries = reactive(new Set<string>())

const viewOptions = computed(() => [
  { label: translateOrFallback('common.labels.timeline', 'Timeline'), value: 'timeline' },
  { label: translateOrFallback('common.labels.table', 'Table'), value: 'table' },
])

const sourceOptions = computed(() => {
  const seen = new Map<string, string>()
  effectiveActivities.value.forEach((entry) => {
    const value = entry.sourceCode || entry.objectCode || ''
    const label = entry.sourceLabel || entry.objectCode || ''
    if (value && label && !seen.has(value)) {
      seen.set(value, label)
    }
  })

  return [
    { value: 'all', label: translateOrFallback('common.filters.allObjects', 'All Objects') },
    ...Array.from(seen.entries()).map(([value, label]) => ({ value, label })),
  ]
})

const filteredActivities = computed(() => {
  if (sourceFilter.value === 'all') return effectiveActivities.value
  return effectiveActivities.value.filter((entry) => (entry.sourceCode || entry.objectCode) === sourceFilter.value)
})

const filteredGroups = computed<DateGroup[]>(() => groupByDate(filteredActivities.value))

const toggleChanges = (id: string) => {
  if (expandedEntries.has(id)) {
    expandedEntries.delete(id)
  } else {
    expandedEntries.add(id)
  }
}

const resolveActionLabel = (action: string, actionLabel?: string) => {
  if (actionLabel && actionLabel.trim()) return actionLabel
  const key = `common.history.actions.${String(action || '').toLowerCase()}`
  const translated = t(key)
  return translated !== key ? translated : action
}

const translateOrFallback = (key: string, fallback: string) => {
  const translated = t(key)
  return translated !== key ? translated : fallback
}

const getActivityType = (action: string) => {
  const map: Record<string, string> = {
    create: 'success',
    update: 'primary',
    delete: 'danger',
    status_change: 'warning',
    assign: 'warning',
    unassign: 'info',
    approve: 'success',
    reject: 'danger',
    comment: 'info',
    custom: 'info',
  }
  return map[String(action || '').toLowerCase()] || 'primary'
}

const getActionIcon = (action: string) => {
  const map: Record<string, any> = {
    create: Plus,
    update: EditPen,
    delete: Delete,
    status_change: Switch,
    assign: UserFilled,
    unassign: UserFilled,
    approve: Plus,
    reject: Delete,
    comment: InfoFilled,
    custom: InfoFilled,
  }
  return map[String(action || '').toLowerCase()] || EditPen
}

const canNavigate = (entry: Pick<ActivityLogEntry, 'objectCode' | 'objectId'>) => {
  return Boolean(entry.objectCode && entry.objectId)
}

const navigateToEntry = (entry: Pick<ActivityLogEntry, 'objectCode' | 'objectId'>) => {
  if (!entry.objectCode || !entry.objectId) return
  router.push(`/objects/${encodeURIComponent(entry.objectCode)}/${encodeURIComponent(entry.objectId)}`)
}

const formatDateLabel = (dateKey: string, dateLabel: string) => {
  if (dateKey === 'today') return translateOrFallback('common.labels.today', 'Today')
  if (dateKey === 'yesterday') return translateOrFallback('common.labels.yesterday', 'Yesterday')
  return dateLabel
}

const formatTime = (raw: string) => {
  if (!raw) return ''
  const d = new Date(raw)
  if (isNaN(d.getTime())) return raw
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const formatValue = (value: unknown): string => {
  if (value === undefined || value === null || value === '') return '-'
  if (Array.isArray(value)) return value.map(formatValue).join(', ')
  if (typeof value === 'object') {
    try { return JSON.stringify(value) } catch { return String(value) }
  }
  return String(value)
}

const historyRows = computed<TimelineRow[]>(() => {
  return filteredActivities.value.flatMap((a, ai) => {
    const base = {
      id: String(a.id || ai),
      action: a.action,
      actionLabel: resolveActionLabel(a.action, a.actionLabel),
      sourceCode: a.sourceCode,
      sourceLabel: a.sourceLabel,
      objectCode: a.objectCode,
      objectId: a.objectId,
      recordLabel: a.recordLabel,
      userName: a.userName,
      timestamp: a.createdAt || a.timestamp,
      description: a.description,
    }
    if (!a.changes?.length) {
      return [{ rowKey: `${a.id || ai}-summary`, ...base, fieldLabel: '', oldValue: '', newValue: '' }]
    }
    return a.changes.map((c, ci) => ({
      rowKey: `${a.id || ai}-${c.fieldCode || ci}`,
      ...base,
      fieldLabel: c.fieldLabel || c.fieldCode,
      oldValue: c.oldValue,
      newValue: c.newValue,
    }))
  })
})

const groupByDate = (entries: ActivityLogEntry[]): DateGroup[] => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  const groups = new Map<string, { label: string; entries: ActivityLogEntry[] }>()
  for (const entry of entries) {
    const raw = entry.createdAt || entry.timestamp || ''
    const d = raw ? new Date(raw) : null
    let dateKey = 'unknown'
    let dateLabel = '-'

    if (d && !isNaN(d.getTime())) {
      const day = new Date(d)
      day.setHours(0, 0, 0, 0)
      if (day.getTime() === today.getTime()) {
        dateKey = 'today'
        dateLabel = 'Today'
      } else if (day.getTime() === yesterday.getTime()) {
        dateKey = 'yesterday'
        dateLabel = 'Yesterday'
      } else {
        dateKey = day.toISOString().slice(0, 10)
        dateLabel = dateKey
      }
    }

    if (!groups.has(dateKey)) {
      groups.set(dateKey, { label: dateLabel, entries: [] })
    }
    groups.get(dateKey)!.entries.push(entry)
  }

  return Array.from(groups.entries()).map(([key, val]) => ({
    dateKey: key,
    dateLabel: val.label,
    entries: val.entries,
  }))
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.activity-timeline-container {
  padding: $spacing-md 0;
}

.timeline-loading {
  padding: $spacing-lg;
}

.timeline-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: $spacing-md;
  flex-wrap: wrap;
}

.timeline-toolbar__left,
.timeline-toolbar__right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.timeline-toolbar__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.timeline-filter {
  min-width: 160px;
}

.visual-timeline {
  padding-left: 4px;
}

.timeline-date-group {
  margin-bottom: 20px;
}

.timeline-date-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
  padding-left: 40px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.timeline-entry {
  display: flex;
  gap: 12px;
  position: relative;

  &:last-child .timeline-entry__line {
    display: none;
  }
}

.timeline-entry__rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 28px;
}

.timeline-entry__dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  z-index: 1;

  &.dot--create { background: var(--el-color-success); }
  &.dot--update { background: var(--el-color-primary); }
  &.dot--delete { background: var(--el-color-danger); }
  &.dot--status_change { background: var(--el-color-warning); }
  &.dot--assign { background: #8b5cf6; }
  &.dot--unassign { background: var(--el-color-info); }
  &.dot--approve { background: var(--el-color-success); }
  &.dot--reject { background: var(--el-color-danger); }
  &.dot--comment { background: var(--el-color-info); }
  &.dot--custom { background: var(--el-color-info); }
}

.timeline-entry__line {
  width: 2px;
  flex: 1;
  background: var(--el-border-color-light);
  min-height: 16px;
}

.timeline-entry__body {
  flex: 1;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-extra-light);
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 10px;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: var(--el-box-shadow-lighter);
  }
}

.timeline-entry__header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.timeline-entry__user {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.timeline-entry__time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-left: auto;
}

.timeline-entry__desc {
  margin-top: 6px;
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
}

.timeline-entry__link-row {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.timeline-entry__record {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.timeline-entry__changes {
  margin-top: 8px;
}

.toggle-changes-btn {
  margin-top: 4px;
  font-size: 12px;
}

.change-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  font-size: 12px;
  flex-wrap: wrap;

  &:not(:last-child) {
    border-bottom: 1px dashed var(--el-border-color-extra-light);
  }
}

.change-row__field {
  font-weight: 500;
  color: var(--el-text-color-primary);
  min-width: 80px;
}

.change-row__old {
  color: $danger-color;
  text-decoration: line-through;
  padding: 1px 6px;
  border-radius: 4px;
  background: #fef2f2;
}

.change-row__arrow {
  color: var(--el-text-color-placeholder);
}

.change-row__new {
  color: $success-color;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 4px;
  background: #f0fdf4;
}

.history-table-shell {
  .history-table :deep(.el-table__cell) {
    vertical-align: top;
  }

  .history-table :deep(.cell) {
    line-height: 1.6;
  }
}

.action-badge {
  font-weight: 500;
  border-radius: 999px;
}

.source-badge {
  border-radius: 999px;
}

.value-chip {
  display: inline-flex;
  max-width: 100%;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  word-break: break-word;
  white-space: normal;
}

.old-value {
  color: $danger-color;
  background-color: #fef2f2;
  text-decoration: line-through;
}

.new-value {
  color: $success-color;
  background-color: #f0fdf4;
  font-weight: 500;
}

.load-more-container {
  display: flex;
  justify-content: center;
  padding: $spacing-md 0 0;
  margin-top: $spacing-sm;
  border-top: 1px dashed $border-light;
}
</style>
