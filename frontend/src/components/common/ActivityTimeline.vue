<!--
  ActivityTimeline — Salesforce-style visual vertical timeline.

  Dual-mode: timeline (default) and table view.
  - Date-grouped entries (Today / Yesterday / date)
  - Action-specific icons and colors
  - Expandable field-level change details
  - Cross-object reference links
-->

<template>
  <div class="activity-timeline-container">
    <div
      v-if="loading"
      class="timeline-loading"
    >
      <el-skeleton
        :rows="5"
        animated
      />
    </div>

    <div v-else-if="activities.length === 0">
      <BaseEmptyState
        :title="$t('common.messages.noTimelineData')"
        :description="$t('common.messages.timelineHint')"
      />
    </div>

    <template v-else>
      <!-- View switcher -->
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
            {{ activities.length }}
          </el-tag>
        </div>
        <el-segmented
          v-model="viewMode"
          :options="viewOptions"
          size="small"
        />
      </div>

      <!-- ════════ TIMELINE VIEW ════════ -->
      <div
        v-if="viewMode === 'timeline'"
        class="visual-timeline"
      >
        <div
          v-for="group in groupedByDate"
          :key="group.dateKey"
          class="timeline-date-group"
        >
          <div class="timeline-date-label">
            {{ group.dateLabel }}
          </div>

          <div
            v-for="entry in group.entries"
            :key="entry.id"
            class="timeline-entry"
          >
            <!-- Vertical line + dot -->
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

            <!-- Content card -->
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
                <span class="timeline-entry__user">{{ entry.userName || $t('common.labels.system') }}</span>
                <span class="timeline-entry__time">{{ formatTime(entry.createdAt || entry.timestamp || '') }}</span>
              </div>

              <div
                v-if="entry.description"
                class="timeline-entry__desc"
              >
                {{ entry.description }}
              </div>

              <!-- Expandable changes -->
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

      <!-- ════════ TABLE VIEW (legacy) ════════ -->
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

      <!-- Load more -->
      <div
        v-if="hasMore"
        class="load-more-container"
      >
        <el-button
          :loading="loadingMore"
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
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils/dateFormat'
import {
  Plus, EditPen, Delete, Right, Switch, InfoFilled, UserFilled,
} from '@element-plus/icons-vue'
import BaseEmptyState from '@/components/common/BaseEmptyState.vue'
import { useActivityTimeline } from '@/composables/useActivityTimeline'

interface Props {
  objectCode: string
  recordId: string
  placement?: 'top' | 'bottom'
  size?: 'normal' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  placement: 'top',
  size: 'normal',
})

const { t } = useI18n()

// ── Data via composable ──────────────────────────────────────────
const {
  activities,
  loading,
  loadingMore,
  hasMore,
  groupedByDate,
  loadMore,
} = useActivityTimeline(
  () => props.objectCode,
  () => props.recordId,
)

// ── View mode ────────────────────────────────────────────────────
const viewMode = ref<'timeline' | 'table'>('timeline')
const viewOptions = computed(() => [
  { label: t('common.labels.timeline', '时间线'), value: 'timeline' },
  { label: t('common.labels.table', '表格'), value: 'table' },
])

// ── Expandable entries ───────────────────────────────────────────
const expandedEntries = reactive(new Set<string>())
const toggleChanges = (id: string) => {
  if (expandedEntries.has(id)) {
    expandedEntries.delete(id)
  } else {
    expandedEntries.add(id)
  }
}

// ── Action helpers ───────────────────────────────────────────────
const resolveActionLabel = (action: string, actionLabel?: string) => {
  if (actionLabel && actionLabel.trim()) return actionLabel
  const key = `common.history.actions.${String(action || '').toLowerCase()}`
  const translated = t(key)
  return translated !== key ? translated : action
}

const getActivityType = (action: string) => {
  const map: Record<string, string> = {
    create: 'success', update: 'primary', delete: 'danger',
    status_change: 'warning', assign: 'warning', unassign: 'info',
    approve: 'success', reject: 'danger', comment: 'info', custom: 'info',
  }
  return map[String(action || '').toLowerCase()] || 'primary'
}

const getActionIcon = (action: string) => {
  const map: Record<string, any> = {
    create: Plus, update: EditPen, delete: Delete,
    status_change: Switch, assign: UserFilled, unassign: UserFilled,
    approve: Plus, reject: Delete, comment: InfoFilled, custom: InfoFilled,
  }
  return map[String(action || '').toLowerCase()] || EditPen
}

const formatTime = (raw: string) => {
  if (!raw) return ''
  const d = new Date(raw)
  if (isNaN(d.getTime())) return raw
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const formatValue = (value: unknown) => {
  if (value === undefined || value === null || value === '') return '-'
  if (Array.isArray(value)) return value.map(formatValue).join(', ')
  if (typeof value === 'object') {
    try { return JSON.stringify(value) } catch { return String(value) }
  }
  return String(value)
}

// ── Table view rows (legacy format) ─────────────────────────────
interface HistoryRow {
  rowKey: string; action: string; actionLabel: string
  userName?: string; timestamp?: string; fieldLabel?: string
  oldValue: any; newValue: any; description?: string
}

const historyRows = computed<HistoryRow[]>(() => {
  return activities.value.flatMap((a, ai) => {
    const base = {
      action: a.action,
      actionLabel: resolveActionLabel(a.action, a.actionLabel),
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
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.activity-timeline-container {
  padding: $spacing-md 0;
}

.timeline-loading {
  padding: $spacing-lg;
}

/* ─── Toolbar ─── */
.timeline-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;
}

.timeline-toolbar__left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.timeline-toolbar__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* ─── Visual Timeline ─── */
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

.timeline-entry__changes {
  margin-top: 8px;
}

.toggle-changes-btn {
  margin-top: 4px;
  font-size: 12px;
}

/* ─── Change rows ─── */
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
  color: var(--el-color-danger);
  text-decoration: line-through;
  padding: 1px 6px;
  border-radius: 4px;
  background: #fef2f2;
}

.change-row__arrow {
  color: var(--el-text-color-placeholder);
}

.change-row__new {
  color: var(--el-color-success);
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 4px;
  background: #f0fdf4;
}

/* ─── Legacy table ─── */
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
