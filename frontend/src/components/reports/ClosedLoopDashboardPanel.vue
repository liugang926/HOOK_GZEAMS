<template>
  <section class="closed-loop-panel">
    <div class="closed-loop-panel__toolbar">
      <div>
        <h3 class="closed-loop-panel__title">
          {{ t('reports.closedLoop.title') }}
        </h3>
        <p class="closed-loop-panel__description">
          {{ t('reports.closedLoop.description') }}
        </p>
      </div>
      <div class="closed-loop-panel__toolbar-actions">
        <div
          v-if="scopeOptions.length"
          class="closed-loop-panel__scope-picker"
        >
          <label
            class="closed-loop-panel__scope-label"
            for="closed-loop-organization-selector"
          >
            {{ t('reports.closedLoop.scope.organization') }}
          </label>
          <select
            id="closed-loop-organization-selector"
            v-model="selectedOrganizationId"
            class="closed-loop-panel__scope-select"
            :disabled="organizationsLoading"
            @change="handleOrganizationChange"
          >
            <option
              v-for="option in scopeOptions"
              :key="option.id"
              :value="option.id"
            >
              {{ formatOrganizationLabel(option) }}
            </option>
          </select>
        </div>

        <div class="closed-loop-panel__window-picker">
          <button
            v-for="option in windowOptions"
            :key="option.value"
            class="closed-loop-panel__window-button"
            :class="{ 'is-active': selectedWindow === option.value }"
            type="button"
            @click="handleWindowChange(option.value)"
          >
            {{ option.label }}
          </button>
        </div>

        <div class="closed-loop-panel__action-group">
          <button
            type="button"
            class="closed-loop-panel__retry"
            :disabled="!overview || exportLoading"
            @click="handleExportWorkbook"
          >
            {{ t('reports.closedLoop.actions.exportExcel') }}
          </button>
          <button
            type="button"
            class="closed-loop-panel__retry"
            :disabled="!overview || Boolean(activeSnapshot)"
            @click="handleSaveSnapshot"
          >
            {{ t('reports.closedLoop.snapshot.save') }}
          </button>
        </div>
      </div>
    </div>

    <section
      v-if="snapshotEntries.length || activeSnapshot"
      class="closed-loop-panel__snapshot-strip"
    >
      <div
        v-if="activeSnapshot"
        class="closed-loop-panel__snapshot-banner"
      >
        <div>
          <p class="closed-loop-panel__snapshot-eyebrow">
            {{ t('reports.closedLoop.snapshot.viewTitle') }}
          </p>
          <strong class="closed-loop-panel__snapshot-title">
            {{ activeSnapshot.label }}
          </strong>
          <p class="closed-loop-panel__snapshot-hint">
            {{ t('reports.closedLoop.snapshot.savedAt', { time: formatSnapshotTime(activeSnapshot.createdAt) }) }}
          </p>
        </div>
        <div class="closed-loop-panel__action-group">
          <button
            type="button"
            class="closed-loop-panel__retry"
            :disabled="snapshotComparisonLoading"
            @click="compareSnapshotToLive"
          >
            {{ t('reports.closedLoop.snapshot.compare') }}
          </button>
          <button
            type="button"
            class="closed-loop-panel__retry"
            @click="exitSnapshotView"
          >
            {{ t('reports.closedLoop.snapshot.backToLive') }}
          </button>
        </div>
      </div>

      <div
        v-if="activeSnapshot && snapshotComparisonLoading"
        class="closed-loop-panel__loading"
      >
        {{ t('reports.closedLoop.snapshot.comparing') }}
      </div>

      <section
        v-if="activeSnapshot && snapshotComparisonCards.length"
        class="closed-loop-panel__snapshot-compare"
      >
        <div class="closed-loop-panel__section-header closed-loop-panel__section-header--snapshot">
          <h4>{{ t('reports.closedLoop.snapshot.compareTitle') }}</h4>
        </div>
        <div class="closed-loop-panel__snapshot-compare-grid">
          <article
            v-for="card in snapshotComparisonCards"
            :key="card.code"
            class="closed-loop-panel__snapshot-compare-card"
          >
            <span class="closed-loop-panel__summary-label">{{ card.label }}</span>
            <strong class="closed-loop-panel__snapshot-compare-delta">
              {{ card.deltaLabel }}
            </strong>
            <span class="closed-loop-panel__snapshot-compare-meta">
              {{ t('reports.closedLoop.snapshot.snapshotValue') }}: {{ card.snapshotValue }}
            </span>
            <span class="closed-loop-panel__snapshot-compare-meta">
              {{ t('reports.closedLoop.snapshot.liveValue') }}: {{ card.liveValue }}
            </span>
          </article>
        </div>

        <div class="closed-loop-panel__section-header closed-loop-panel__section-header--snapshot">
          <h4>{{ t('reports.closedLoop.snapshot.compareByObjectTitle') }}</h4>
        </div>
        <table
          v-if="snapshotComparisonObjectRows.length"
          class="closed-loop-panel__table closed-loop-panel__snapshot-compare-table"
        >
          <thead>
            <tr>
              <th>{{ t('reports.closedLoop.table.object') }}</th>
              <th>{{ t('reports.closedLoop.snapshot.snapshotBacklog') }}</th>
              <th>{{ t('reports.closedLoop.snapshot.liveBacklog') }}</th>
              <th>{{ t('reports.closedLoop.snapshot.backlogDelta') }}</th>
              <th>{{ t('reports.closedLoop.snapshot.snapshotOverdue') }}</th>
              <th>{{ t('reports.closedLoop.snapshot.liveOverdue') }}</th>
              <th>{{ t('reports.closedLoop.snapshot.overdueDelta') }}</th>
              <th>{{ t('reports.closedLoop.snapshot.snapshotClosed') }}</th>
              <th>{{ t('reports.closedLoop.snapshot.liveClosed') }}</th>
              <th>{{ t('reports.closedLoop.snapshot.closedDelta') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in snapshotComparisonObjectRows"
              :key="item.objectCode"
            >
              <td>{{ item.objectName }}</td>
              <td>{{ item.snapshotBacklog }}</td>
              <td>{{ item.liveBacklog }}</td>
              <td>{{ item.backlogDeltaLabel }}</td>
              <td>{{ item.snapshotOverdue }}</td>
              <td>{{ item.liveOverdue }}</td>
              <td>{{ item.overdueDeltaLabel }}</td>
              <td>{{ item.snapshotClosed }}</td>
              <td>{{ item.liveClosed }}</td>
              <td>{{ item.closedDeltaLabel }}</td>
            </tr>
          </tbody>
        </table>
        <div
          v-else
          class="closed-loop-panel__empty"
        >
          {{ t('reports.closedLoop.snapshot.noChangedObjects') }}
        </div>
      </section>

      <div class="closed-loop-panel__section-header closed-loop-panel__section-header--snapshot">
        <h4>{{ t('reports.closedLoop.snapshot.title') }}</h4>
      </div>

      <div
        v-if="snapshotEntries.length"
        class="closed-loop-panel__snapshot-list"
      >
        <article
          v-for="snapshot in snapshotEntries"
          :key="snapshot.id"
          class="closed-loop-panel__snapshot-card"
          :class="{ 'is-active': activeSnapshot?.id === snapshot.id }"
        >
          <div class="closed-loop-panel__snapshot-card-content">
            <strong>{{ snapshot.label }}</strong>
            <span>{{ t('reports.closedLoop.snapshot.savedAt', { time: formatSnapshotTime(snapshot.createdAt) }) }}</span>
          </div>
          <div class="closed-loop-panel__snapshot-card-actions">
            <button
              type="button"
              class="closed-loop-panel__table-link"
              @click="openSnapshot(snapshot.id)"
            >
              {{ t('reports.closedLoop.snapshot.open') }}
            </button>
            <button
              type="button"
              class="closed-loop-panel__table-link"
              @click="handleDeleteSnapshot(snapshot.id)"
            >
              {{ t('reports.closedLoop.snapshot.delete') }}
            </button>
          </div>
        </article>
      </div>
      <div
        v-else
        class="closed-loop-panel__empty"
      >
        {{ t('reports.closedLoop.snapshot.empty') }}
      </div>
    </section>

    <div
      v-if="loadError"
      class="closed-loop-panel__error"
    >
      <span>{{ t('reports.closedLoop.messages.loadFailed') }}</span>
      <button
        type="button"
        class="closed-loop-panel__retry"
        @click="loadDashboard"
      >
        {{ t('reports.closedLoop.retry') }}
      </button>
    </div>

    <div
      v-if="loading"
      class="closed-loop-panel__loading"
    >
      {{ t('reports.closedLoop.loading') }}
    </div>

    <template v-else>
      <div class="closed-loop-panel__summary-grid">
        <article
          v-for="card in summaryCards"
          :key="card.code"
          class="closed-loop-panel__summary-card"
        >
          <span class="closed-loop-panel__summary-label">{{ card.label }}</span>
          <strong class="closed-loop-panel__summary-value">{{ card.value }}</strong>
        </article>
      </div>

      <div class="closed-loop-panel__summary-grid closed-loop-panel__summary-grid--workflow">
        <article
          v-for="card in workflowCards"
          :key="card.code"
          class="closed-loop-panel__summary-card closed-loop-panel__summary-card--workflow"
        >
          <span class="closed-loop-panel__summary-label">{{ card.label }}</span>
          <strong class="closed-loop-panel__summary-value">{{ card.value }}</strong>
        </article>
      </div>

      <section class="closed-loop-panel__section">
        <div class="closed-loop-panel__section-header">
          <h4>{{ t('reports.closedLoop.sections.coverage') }}</h4>
          <span class="closed-loop-panel__window-meta">
            {{ selectedOrganizationName }}
            <span class="closed-loop-panel__window-meta-separator">·</span>
            {{ windowMeta }}
          </span>
        </div>
        <div class="closed-loop-panel__object-filter-list">
          <button
            type="button"
            class="closed-loop-panel__object-filter-chip"
            :class="{ 'is-active': !selectedObjectCodes.length }"
            @click="clearObjectFilters"
          >
            {{ t('reports.closedLoop.filters.allObjects') }}
          </button>
          <button
            v-for="object in availableCoverageObjects"
            :key="object.objectCode"
            type="button"
            class="closed-loop-panel__object-filter-chip"
            :class="{ 'is-active': selectedObjectCodes.includes(object.objectCode) }"
            @click="toggleObjectFilter(object.objectCode)"
          >
            {{ object.objectName }}
          </button>
        </div>
        <div class="closed-loop-panel__coverage-list">
          <button
            v-for="object in objectsCovered"
            :key="object.objectCode"
            type="button"
            class="closed-loop-panel__coverage-chip"
            @click="openRoute(object.primaryRoute)"
          >
            {{ object.objectName }}
          </button>
        </div>
      </section>

      <section class="closed-loop-panel__section">
        <div class="closed-loop-panel__section-header">
          <h4>{{ t('reports.closedLoop.sections.trend') }}</h4>
        </div>
        <div
          v-if="recentTrendPoints.length"
          class="closed-loop-panel__trend-chart"
        >
          <div class="closed-loop-panel__trend-legend">
            <span class="closed-loop-panel__trend-legend-item">
              <span class="closed-loop-panel__trend-swatch closed-loop-panel__trend-swatch--opened" />
              {{ t('reports.closedLoop.trend.opened') }}
            </span>
            <span class="closed-loop-panel__trend-legend-item">
              <span class="closed-loop-panel__trend-swatch closed-loop-panel__trend-swatch--closed" />
              {{ t('reports.closedLoop.trend.closed') }}
            </span>
          </div>
          <div class="closed-loop-panel__trend-bars">
            <div
              v-for="point in recentTrendPoints"
              :key="point.date"
              class="closed-loop-panel__trend-day"
            >
              <div class="closed-loop-panel__trend-columns">
                <span
                  class="closed-loop-panel__trend-bar closed-loop-panel__trend-bar--opened"
                  :style="{ height: getTrendBarHeight(point.opened) }"
                />
                <span
                  class="closed-loop-panel__trend-bar closed-loop-panel__trend-bar--closed"
                  :style="{ height: getTrendBarHeight(point.closed) }"
                />
              </div>
              <span class="closed-loop-panel__trend-day-label">
                {{ formatTrendLabel(point.date) }}
              </span>
            </div>
          </div>
        </div>
        <table class="closed-loop-panel__table">
          <thead>
            <tr>
              <th>{{ t('reports.closedLoop.trend.date') }}</th>
              <th>{{ t('reports.closedLoop.trend.opened') }}</th>
              <th>{{ t('reports.closedLoop.trend.closed') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="point in recentTrendPoints"
              :key="point.date"
            >
              <td>{{ point.date }}</td>
              <td>{{ point.opened }}</td>
              <td>{{ point.closed }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="closed-loop-panel__section">
        <div class="closed-loop-panel__section-header">
          <h4>{{ t('reports.closedLoop.sections.byObject') }}</h4>
        </div>
        <table class="closed-loop-panel__table">
          <thead>
            <tr>
              <th>{{ t('reports.closedLoop.table.object') }}</th>
              <th>{{ t('reports.closedLoop.summary.openedCount') }}</th>
              <th>{{ t('reports.closedLoop.summary.closedCount') }}</th>
              <th>{{ t('reports.closedLoop.summary.backlogCount') }}</th>
              <th>{{ t('reports.closedLoop.summary.overdueCount') }}</th>
              <th>{{ t('reports.closedLoop.table.action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in byObjectItems"
              :key="item.objectCode"
            >
              <td>{{ item.objectName }}</td>
              <td>{{ item.summary.openedCount }}</td>
              <td>{{ item.summary.closedCount }}</td>
              <td>{{ item.summary.backlogCount }}</td>
              <td>{{ item.summary.overdueCount }}</td>
              <td>
                <button
                  type="button"
                  class="closed-loop-panel__table-link"
                  @click="openRoute(item.primaryRoute)"
                >
                  {{ t('reports.closedLoop.actions.open') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="closed-loop-panel__section">
        <div class="closed-loop-panel__section-header">
          <h4>{{ t('reports.closedLoop.sections.owners') }}</h4>
        </div>
        <table
          v-if="ownerRankings.length"
          class="closed-loop-panel__table"
        >
          <thead>
            <tr>
              <th>{{ t('reports.closedLoop.owners.person') }}</th>
              <th>{{ t('reports.closedLoop.owners.openCount') }}</th>
              <th>{{ t('reports.closedLoop.owners.overdueCount') }}</th>
              <th>{{ t('reports.closedLoop.owners.topSource') }}</th>
              <th>{{ t('reports.closedLoop.owners.sourceBreakdown') }}</th>
              <th>{{ t('reports.closedLoop.table.action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in ownerRankings"
              :key="item.userId"
            >
              <td>{{ item.displayName || item.username }}</td>
              <td>{{ item.openCount }}</td>
              <td>{{ item.overdueCount }}</td>
              <td>{{ formatSource(item.topSource) }}</td>
              <td>{{ formatSourceBreakdown(item.sourceCounts) }}</td>
              <td>
                <button
                  type="button"
                  class="closed-loop-panel__table-link closed-loop-panel__drilldown-trigger"
                  @click="openOwnerDrilldown(item)"
                >
                  {{ t('reports.closedLoop.actions.drillDown') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div
          v-else
          class="closed-loop-panel__empty"
        >
          {{ t('reports.closedLoop.empty.owners') }}
        </div>
      </section>

      <section class="closed-loop-panel__section">
        <div class="closed-loop-panel__section-header">
          <h4>{{ t('reports.closedLoop.sections.departments') }}</h4>
        </div>
        <table
          v-if="departmentRankings.length"
          class="closed-loop-panel__table"
        >
          <thead>
            <tr>
              <th>{{ t('reports.closedLoop.departments.name') }}</th>
              <th>{{ t('reports.closedLoop.departments.openCount') }}</th>
              <th>{{ t('reports.closedLoop.departments.overdueCount') }}</th>
              <th>{{ t('reports.closedLoop.departments.topSource') }}</th>
              <th>{{ t('reports.closedLoop.departments.sourceBreakdown') }}</th>
              <th>{{ t('reports.closedLoop.table.action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in departmentRankings"
              :key="item.departmentId"
            >
              <td>{{ item.departmentName }}</td>
              <td>{{ item.openCount }}</td>
              <td>{{ item.overdueCount }}</td>
              <td>{{ formatSource(item.topSource) }}</td>
              <td>{{ formatSourceBreakdown(item.sourceCounts) }}</td>
              <td>
                <button
                  type="button"
                  class="closed-loop-panel__table-link closed-loop-panel__drilldown-trigger"
                  @click="openDepartmentDrilldown(item)"
                >
                  {{ t('reports.closedLoop.actions.drillDown') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div
          v-else
          class="closed-loop-panel__empty"
        >
          {{ t('reports.closedLoop.empty.departments') }}
        </div>
      </section>

      <section
        v-if="selectedDrilldown"
        class="closed-loop-panel__section"
      >
        <div class="closed-loop-panel__section-header">
          <h4>{{ selectedDrilldown.title }}</h4>
          <button
            type="button"
            class="closed-loop-panel__table-link"
            @click="selectedDrilldown = null"
          >
            {{ t('common.actions.close') }}
          </button>
        </div>
        <table class="closed-loop-panel__table">
          <thead>
            <tr>
              <th>{{ t('reports.closedLoop.drilldown.source') }}</th>
              <th>{{ t('reports.closedLoop.drilldown.count') }}</th>
              <th>{{ t('reports.closedLoop.table.action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in selectedDrilldown.items"
              :key="item.key"
            >
              <td>{{ item.label }}</td>
              <td>{{ item.count }}</td>
              <td>
                <button
                  v-if="item.route"
                  type="button"
                  class="closed-loop-panel__table-link closed-loop-panel__drilldown-open"
                  @click="openRoute(item.route)"
                >
                  {{ t('reports.closedLoop.actions.openQueue') }}
                </button>
                <button
                  v-if="item.overdueRoute"
                  type="button"
                  class="closed-loop-panel__table-link closed-loop-panel__drilldown-overdue"
                  @click="openRoute(item.overdueRoute)"
                >
                  {{ t('reports.closedLoop.actions.openOverdue') }}
                </button>
                <span
                  v-if="!item.route && !item.overdueRoute"
                  class="closed-loop-panel__inline-note"
                >
                  {{ t('reports.closedLoop.actions.notAvailable') }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <div class="closed-loop-panel__table-grid">
        <section class="closed-loop-panel__section">
          <div class="closed-loop-panel__section-header">
            <h4>{{ t('reports.closedLoop.sections.queues') }}</h4>
          </div>
          <table
            v-if="queues.length"
            class="closed-loop-panel__table"
          >
            <thead>
              <tr>
                <th>{{ t('reports.closedLoop.table.label') }}</th>
                <th>{{ t('reports.closedLoop.table.object') }}</th>
                <th>{{ t('reports.closedLoop.table.count') }}</th>
                <th>{{ t('reports.closedLoop.table.action') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in queues"
                :key="item.objectCode + item.code"
              >
                <td>{{ item.label }}</td>
                <td>{{ item.objectName }}</td>
                <td>{{ item.count }}</td>
                <td>
                  <button
                    type="button"
                    class="closed-loop-panel__table-link"
                    @click="openRoute(item.route)"
                  >
                    {{ t('reports.closedLoop.actions.open') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div
            v-else
            class="closed-loop-panel__empty"
          >
            {{ t('reports.closedLoop.empty.queues') }}
          </div>
        </section>

        <section class="closed-loop-panel__section">
          <div class="closed-loop-panel__section-header">
            <h4>{{ t('reports.closedLoop.sections.bottlenecks') }}</h4>
          </div>
          <table
            v-if="bottlenecks.length"
            class="closed-loop-panel__table"
          >
            <thead>
              <tr>
                <th>{{ t('reports.closedLoop.table.label') }}</th>
                <th>{{ t('reports.closedLoop.table.object') }}</th>
                <th>{{ t('reports.closedLoop.table.count') }}</th>
                <th>{{ t('reports.closedLoop.table.severity') }}</th>
                <th>{{ t('reports.closedLoop.table.action') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in bottlenecks"
                :key="item.objectCode + item.code"
              >
                <td>{{ item.label }}</td>
                <td>{{ item.objectName }}</td>
                <td>{{ item.count }}</td>
                <td>{{ t(`reports.closedLoop.severity.${item.severity}`) }}</td>
                <td>
                  <button
                    type="button"
                    class="closed-loop-panel__table-link"
                    @click="openRoute(item.route)"
                  >
                    {{ t('reports.closedLoop.actions.open') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div
            v-else
            class="closed-loop-panel__empty"
          >
            {{ t('reports.closedLoop.empty.bottlenecks') }}
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  closedLoopMetricsApi,
  type ClosedLoopBottleneckItem,
  type ClosedLoopByObjectItem,
  type ClosedLoopDashboardSnapshotDetail,
  type ClosedLoopDashboardSnapshotPayload,
  type ClosedLoopDashboardSnapshotSummary,
  type ClosedLoopOverview,
  type ClosedLoopQueueItem,
  type ClosedLoopWindowKey,
} from '@/api/closedLoopMetrics'
import { userApi } from '@/api/users'
import { getStoredCurrentOrgId, setStoredCurrentOrgId } from '@/platform/auth/sessionPreference'
import { exportClosedLoopDashboardWorkbook } from '@/platform/reports/closedLoopDashboardExport'

const { t } = useI18n()
const router = useRouter()

type OrganizationScopeOption = {
  id: string
  name: string
  code?: string
}

type DashboardUserPayload = {
  id?: string
  primaryOrganization?: OrganizationScopeOption | null
  accessibleOrganizations?: OrganizationScopeOption[]
}

type RankingSourceCode = keyof NonNullable<ClosedLoopOverview['ownerRankings'][number]>['sourceCounts'] | string

type RankingDrilldownItem = {
  key: string
  label: string
  count: number
  route: string
  overdueRoute: string
}

type RankingDrilldownPayload = {
  title: string
  items: RankingDrilldownItem[]
}

const selectedWindow = ref<ClosedLoopWindowKey>('30d')
const selectedOrganizationId = ref('')
const selectedObjectCodes = ref<string[]>([])
const loading = ref(false)
const loadError = ref(false)
const organizationsLoading = ref(false)
const overview = ref<ClosedLoopOverview | null>(null)
const byObjectItems = ref<ClosedLoopByObjectItem[]>([])
const queues = ref<ClosedLoopQueueItem[]>([])
const bottlenecks = ref<ClosedLoopBottleneckItem[]>([])
const organizationOptions = ref<OrganizationScopeOption[]>([])
const availableCoverageObjects = ref<ClosedLoopOverview['objectsCovered']>([])
const selectedDrilldown = ref<RankingDrilldownPayload | null>(null)
const currentUserId = ref('')
const snapshotEntries = ref<ClosedLoopDashboardSnapshotSummary[]>([])
const activeSnapshot = ref<ClosedLoopDashboardSnapshotDetail | null>(null)
const snapshotComparisonOverview = ref<ClosedLoopOverview | null>(null)
const snapshotComparisonByObjectItems = ref<ClosedLoopByObjectItem[]>([])
const snapshotComparisonLoading = ref(false)
const exportLoading = ref(false)

const windowOptions = computed(() => [
  { value: '7d' as ClosedLoopWindowKey, label: t('reports.closedLoop.windows.7d') },
  { value: '30d' as ClosedLoopWindowKey, label: t('reports.closedLoop.windows.30d') },
  { value: '90d' as ClosedLoopWindowKey, label: t('reports.closedLoop.windows.90d') },
])

const scopeOptions = computed(() => organizationOptions.value)

const summaryCards = computed(() => {
  const summary = overview.value?.summary
  if (!summary) return []
  return [
    { code: 'opened', label: t('reports.closedLoop.summary.openedCount'), value: summary.openedCount },
    { code: 'closed', label: t('reports.closedLoop.summary.closedCount'), value: summary.closedCount },
    { code: 'backlog', label: t('reports.closedLoop.summary.backlogCount'), value: summary.backlogCount },
    { code: 'overdue', label: t('reports.closedLoop.summary.overdueCount'), value: summary.overdueCount },
    { code: 'autoClosed', label: t('reports.closedLoop.summary.autoClosedCount'), value: summary.autoClosedCount },
    { code: 'avgCycle', label: t('reports.closedLoop.summary.avgCycleHours'), value: summary.avgCycleHours.toFixed(2) },
  ]
})

const workflowCards = computed(() => {
  const summary = overview.value?.workflowSla
  if (!summary) return []
  return [
    { code: 'active', label: t('reports.closedLoop.workflow.activeTaskCount'), value: summary.activeTaskCount },
    { code: 'overdue', label: t('reports.closedLoop.workflow.overdueTaskCount'), value: summary.overdueTaskCount },
    { code: 'escalated', label: t('reports.closedLoop.workflow.escalatedTaskCount'), value: summary.escalatedTaskCount },
    { code: 'bottlenecks', label: t('reports.closedLoop.workflow.bottleneckCount'), value: summary.bottleneckCount },
  ]
})

const objectsCovered = computed(() => overview.value?.objectsCovered ?? [])
const ownerRankings = computed(() => overview.value?.ownerRankings ?? [])
const departmentRankings = computed(() => overview.value?.departmentRankings ?? [])

const recentTrendPoints = computed(() => {
  const points = overview.value?.trend.points ?? []
  return points.slice(-7)
})

const trendMaxValue = computed(() => {
  const values = recentTrendPoints.value.flatMap((point) => [Number(point.opened) || 0, Number(point.closed) || 0])
  return Math.max(1, ...values)
})

const windowMeta = computed(() => {
  const window = overview.value?.window
  if (!window) return ''
  return `${window.startDate} - ${window.endDate}`
})

const selectedOrganizationName = computed(() => {
  if (activeSnapshot.value?.organization?.name) {
    return activeSnapshot.value.organization.name
  }
  const selectedOption = scopeOptions.value.find((option) => option.id === selectedOrganizationId.value)
  if (selectedOption?.name) {
    return selectedOption.name
  }
  return t('reports.closedLoop.scope.currentOrganization')
})

const buildRoute = (path: string, query?: Record<string, string | number | boolean | undefined>) => {
  const searchParams = new URLSearchParams()
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    searchParams.set(key, String(value))
  })
  const queryString = searchParams.toString()
  return queryString ? `${path}?${queryString}` : path
}

const buildMetricsParams = () => {
  const params: {
    window: ClosedLoopWindowKey
    organizationId?: string
    objectCodes?: string[]
  } = {
    window: selectedWindow.value,
  }
  if (selectedOrganizationId.value) {
    params.organizationId = selectedOrganizationId.value
  }
  if (selectedObjectCodes.value.length) {
    params.objectCodes = [...selectedObjectCodes.value]
  }
  return params
}

const mergeOrganizationOptions = (...collections: Array<OrganizationScopeOption[] | undefined>) => {
  const seen = new Set<string>()
  const merged: OrganizationScopeOption[] = []

  collections.forEach((collection) => {
    collection?.forEach((option) => {
      if (!option?.id || seen.has(option.id)) {
        return
      }
      seen.add(option.id)
      merged.push({
        id: option.id,
        name: option.name,
        code: option.code,
      })
    })
  })

  return merged
}

const refreshSnapshotEntries = async (organizationId = selectedOrganizationId.value) => {
  if (!organizationId) {
    snapshotEntries.value = []
    return
  }

  const response = await closedLoopMetricsApi.listSnapshots({
    organizationId,
  })
  snapshotEntries.value = response.results
}

const applyDashboardSnapshotPayload = (payload: ClosedLoopDashboardSnapshotPayload) => {
  overview.value = payload.overview
  byObjectItems.value = payload.byObjectItems
  queues.value = payload.queues.slice(0, 8)
  bottlenecks.value = payload.bottlenecks.slice(0, 8)
  availableCoverageObjects.value = payload.overview.objectsCovered
  loadError.value = false
  loading.value = false
}

const buildCurrentSnapshotPayload = (): ClosedLoopDashboardSnapshotPayload | null => {
  if (!overview.value) return null

  return {
    overview: overview.value,
    byObjectItems: byObjectItems.value,
    queues: queues.value,
    bottlenecks: bottlenecks.value,
  }
}

const applyDashboardBundle = (payload: ClosedLoopDashboardSnapshotPayload) => {
  applyDashboardSnapshotPayload(payload)
}

const buildSnapshotLabel = () => {
  return `${selectedOrganizationName.value} · ${selectedWindow.value.toUpperCase()} · ${windowMeta.value || t('reports.closedLoop.scope.currentOrganization')}`
}

const formatSnapshotTime = (value: string) => {
  const normalized = String(value || '').trim()
  if (!normalized) return ''
  return normalized.replace('T', ' ').slice(0, 16)
}

const buildSnapshotMetricsParams = (snapshot: ClosedLoopDashboardSnapshotDetail) => {
  return {
    window: snapshot.windowKey,
    organizationId: snapshot.organization?.id || selectedOrganizationId.value || undefined,
    objectCodes: [...(snapshot.objectCodes || [])],
  }
}

const formatComparisonDelta = (delta: number, digits = 0) => {
  const normalized = Number(delta || 0)
  const formatted = digits > 0 ? normalized.toFixed(digits) : String(Math.round(normalized))
  if (normalized > 0) return `+${formatted}`
  return formatted
}

const snapshotComparisonCards = computed(() => {
  if (!activeSnapshot.value || !snapshotComparisonOverview.value) return []

  const snapshotSummary = activeSnapshot.value.payload.overview.summary
  const liveSummary = snapshotComparisonOverview.value.summary

  return [
    {
      code: 'opened',
      label: t('reports.closedLoop.summary.openedCount'),
      snapshotValue: snapshotSummary.openedCount,
      liveValue: liveSummary.openedCount,
      deltaLabel: formatComparisonDelta(liveSummary.openedCount - snapshotSummary.openedCount),
    },
    {
      code: 'closed',
      label: t('reports.closedLoop.summary.closedCount'),
      snapshotValue: snapshotSummary.closedCount,
      liveValue: liveSummary.closedCount,
      deltaLabel: formatComparisonDelta(liveSummary.closedCount - snapshotSummary.closedCount),
    },
    {
      code: 'backlog',
      label: t('reports.closedLoop.summary.backlogCount'),
      snapshotValue: snapshotSummary.backlogCount,
      liveValue: liveSummary.backlogCount,
      deltaLabel: formatComparisonDelta(liveSummary.backlogCount - snapshotSummary.backlogCount),
    },
    {
      code: 'overdue',
      label: t('reports.closedLoop.summary.overdueCount'),
      snapshotValue: snapshotSummary.overdueCount,
      liveValue: liveSummary.overdueCount,
      deltaLabel: formatComparisonDelta(liveSummary.overdueCount - snapshotSummary.overdueCount),
    },
    {
      code: 'avgCycle',
      label: t('reports.closedLoop.summary.avgCycleHours'),
      snapshotValue: snapshotSummary.avgCycleHours.toFixed(2),
      liveValue: liveSummary.avgCycleHours.toFixed(2),
      deltaLabel: formatComparisonDelta(liveSummary.avgCycleHours - snapshotSummary.avgCycleHours, 2),
    },
  ]
})

const snapshotComparisonObjectRows = computed(() => {
  if (!activeSnapshot.value || !snapshotComparisonOverview.value) {
    return []
  }

  const snapshotItems = activeSnapshot.value.payload.byObjectItems || []
  const liveItems = snapshotComparisonByObjectItems.value
  const snapshotMap = new Map(snapshotItems.map((item) => [item.objectCode, item]))
  const liveMap = new Map(liveItems.map((item) => [item.objectCode, item]))
  const objectCodes = new Set<string>([
    ...snapshotMap.keys(),
    ...liveMap.keys(),
  ])

  return [...objectCodes]
    .map((objectCode) => {
      const snapshotItem = snapshotMap.get(objectCode)
      const liveItem = liveMap.get(objectCode)
      const snapshotSummary = snapshotItem?.summary
      const liveSummary = liveItem?.summary
      const backlogDelta = (liveSummary?.backlogCount || 0) - (snapshotSummary?.backlogCount || 0)
      const overdueDelta = (liveSummary?.overdueCount || 0) - (snapshotSummary?.overdueCount || 0)
      const closedDelta = (liveSummary?.closedCount || 0) - (snapshotSummary?.closedCount || 0)

      return {
        objectCode,
        objectName: snapshotItem?.objectName || liveItem?.objectName || objectCode,
        snapshotBacklog: snapshotSummary?.backlogCount || 0,
        liveBacklog: liveSummary?.backlogCount || 0,
        backlogDelta,
        backlogDeltaLabel: formatComparisonDelta(backlogDelta),
        snapshotOverdue: snapshotSummary?.overdueCount || 0,
        liveOverdue: liveSummary?.overdueCount || 0,
        overdueDelta,
        overdueDeltaLabel: formatComparisonDelta(overdueDelta),
        snapshotClosed: snapshotSummary?.closedCount || 0,
        liveClosed: liveSummary?.closedCount || 0,
        closedDelta,
        closedDeltaLabel: formatComparisonDelta(closedDelta),
      }
    })
    .filter((item) => item.backlogDelta || item.overdueDelta || item.closedDelta)
    .sort((left, right) => {
      const rightScore = Math.abs(right.backlogDelta) + Math.abs(right.overdueDelta) + Math.abs(right.closedDelta)
      const leftScore = Math.abs(left.backlogDelta) + Math.abs(left.overdueDelta) + Math.abs(left.closedDelta)
      return rightScore - leftScore
    })
})

const loadOrganizationOptions = async () => {
  organizationsLoading.value = true
  const storedOrganizationId = getStoredCurrentOrgId()

  try {
    const currentUser = await userApi.getMe() as DashboardUserPayload
    currentUserId.value = currentUser.id || ''
    const availableOptions = mergeOrganizationOptions(
      currentUser.accessibleOrganizations,
      currentUser.primaryOrganization ? [currentUser.primaryOrganization] : [],
    )

    if (!availableOptions.length && storedOrganizationId) {
      availableOptions.push({
        id: storedOrganizationId,
        name: t('reports.closedLoop.scope.currentOrganization'),
      })
    }

    organizationOptions.value = availableOptions

    if (!selectedOrganizationId.value) {
      selectedOrganizationId.value = (
        availableOptions.find((option) => option.id === storedOrganizationId)?.id
        || currentUser.primaryOrganization?.id
        || availableOptions[0]?.id
        || storedOrganizationId
        || ''
      )
    }
  } catch {
    if (storedOrganizationId) {
      organizationOptions.value = [
        {
          id: storedOrganizationId,
          name: t('reports.closedLoop.scope.currentOrganization'),
        },
      ]
      selectedOrganizationId.value = storedOrganizationId
    }
  } finally {
    organizationsLoading.value = false
  }
}

const ensureNavigationOrganizationContext = async () => {
  const storedOrganizationId = getStoredCurrentOrgId()
  if (!selectedOrganizationId.value || selectedOrganizationId.value === storedOrganizationId || !currentUserId.value) {
    return true
  }

  try {
    await userApi.switchOrganization(currentUserId.value, selectedOrganizationId.value)
    setStoredCurrentOrgId(selectedOrganizationId.value)
    return true
  } catch (error) {
    console.error('Failed to switch organization before navigation.', error)
    return false
  }
}

const loadDashboardBundle = async (params = buildMetricsParams()) => {
  const [overviewPayload, byObjectPayload, queuePayload, bottleneckPayload] = await Promise.all([
    closedLoopMetricsApi.getOverview(params),
    closedLoopMetricsApi.getByObject(params),
    closedLoopMetricsApi.getQueues(params),
    closedLoopMetricsApi.getBottlenecks(params),
  ])

  return {
    overview: overviewPayload,
    byObjectItems: byObjectPayload.results,
    queues: queuePayload.results.slice(0, 8),
    bottlenecks: bottleneckPayload.results.slice(0, 8),
  }
}

const loadDashboard = async () => {
  activeSnapshot.value = null
  snapshotComparisonOverview.value = null
  snapshotComparisonByObjectItems.value = []
  loading.value = true
  loadError.value = false
  try {
    applyDashboardBundle(await loadDashboardBundle(buildMetricsParams()))
    try {
      await refreshSnapshotEntries(selectedOrganizationId.value)
    } catch {
      snapshotEntries.value = []
    }
  } catch (error) {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

const handleSaveSnapshot = async () => {
  if (!overview.value || activeSnapshot.value) return

  await closedLoopMetricsApi.createSnapshot({
    label: buildSnapshotLabel(),
    window: selectedWindow.value,
    organizationId: selectedOrganizationId.value || undefined,
    objectCodes: [...selectedObjectCodes.value],
  })
  await refreshSnapshotEntries(selectedOrganizationId.value)
}

const handleDeleteSnapshot = async (snapshotId: string) => {
  await closedLoopMetricsApi.deleteSnapshot(snapshotId, {
    organizationId: selectedOrganizationId.value || undefined,
  })
  await refreshSnapshotEntries(selectedOrganizationId.value)

  if (activeSnapshot.value?.id === snapshotId) {
    activeSnapshot.value = null
    snapshotComparisonOverview.value = null
    snapshotComparisonByObjectItems.value = []
    await loadDashboard()
  }
}

const openSnapshot = async (snapshotId: string) => {
  const snapshot = await closedLoopMetricsApi.getSnapshot(snapshotId, {
    organizationId: selectedOrganizationId.value || undefined,
  })

  activeSnapshot.value = snapshot
  snapshotComparisonOverview.value = null
  snapshotComparisonByObjectItems.value = []
  selectedWindow.value = snapshot.windowKey
  selectedOrganizationId.value = snapshot.organization?.id || selectedOrganizationId.value
  selectedObjectCodes.value = [...(snapshot.objectCodes || [])]
  selectedDrilldown.value = null
  applyDashboardSnapshotPayload(snapshot.payload)
}

const exitSnapshotView = async () => {
  if (!activeSnapshot.value) return
  activeSnapshot.value = null
  snapshotComparisonOverview.value = null
  snapshotComparisonByObjectItems.value = []
  selectedDrilldown.value = null
  await loadDashboard()
}

const compareSnapshotToLive = async () => {
  if (!activeSnapshot.value || snapshotComparisonLoading.value) return

  snapshotComparisonLoading.value = true
  try {
    const params = buildSnapshotMetricsParams(activeSnapshot.value)
    const [liveOverview, liveByObject] = await Promise.all([
      closedLoopMetricsApi.getOverview(params),
      closedLoopMetricsApi.getByObject(params),
    ])
    snapshotComparisonOverview.value = liveOverview
    snapshotComparisonByObjectItems.value = liveByObject.results
  } finally {
    snapshotComparisonLoading.value = false
  }
}

const handleExportWorkbook = async () => {
  const payload = buildCurrentSnapshotPayload()
  if (!payload || exportLoading.value) return

  exportLoading.value = true
  try {
    await exportClosedLoopDashboardWorkbook({
      filename: buildSnapshotLabel(),
      ...payload,
    })
  } finally {
    exportLoading.value = false
  }
}

const handleWindowChange = async (windowKey: ClosedLoopWindowKey) => {
  if (selectedWindow.value === windowKey) return
  selectedWindow.value = windowKey
  selectedDrilldown.value = null
  await loadDashboard()
}

const handleOrganizationChange = async () => {
  selectedObjectCodes.value = []
  selectedDrilldown.value = null
  await loadDashboard()
}

const openRoute = async (route: string) => {
  if (!route) return
  const canNavigate = await ensureNavigationOrganizationContext()
  if (!canNavigate) {
    return
  }
  await router.push(route)
}

const formatSource = (source: string) => {
  if (!source) return t('reports.closedLoop.owners.unknownSource')
  return t(`reports.closedLoop.sources.${source}`)
}

const formatSourceBreakdown = (sourceCounts: Record<string, number>) => {
  const segments = Object.entries(sourceCounts)
    .filter(([, count]) => Number(count) > 0)
    .sort((left, right) => Number(right[1]) - Number(left[1]))
    .map(([source, count]) => `${formatSource(source)} ${count}`)
  return segments.join(' / ')
}

const buildOwnerRoute = (source: RankingSourceCode, userId: string, ownerLabel: string) => {
  switch (source) {
    case 'inventory_differences':
      return buildRoute('/objects/InventoryItem', {
        owner: userId,
        unresolved_only: true,
        source_label: formatSource(source),
        owner_label: ownerLabel,
      })
    case 'workflow_tasks':
      return buildRoute('/workflow/tasks', {
        assignee: userId,
        assignee_label: ownerLabel,
        source_label: formatSource(source),
        status: 'pending',
      })
    case 'projects':
      return buildRoute('/objects/AssetProject', {
        project_manager: userId,
        source_label: formatSource(source),
        owner_label: ownerLabel,
      })
    case 'finance_vouchers':
      return buildRoute('/objects/FinanceVoucher', {
        created_by: userId,
        source_label: formatSource(source),
        owner_label: ownerLabel,
      })
    case 'insurance_policies':
      return buildRoute('/objects/InsurancePolicy', {
        created_by: userId,
        source_label: formatSource(source),
        owner_label: ownerLabel,
      })
    case 'claim_records':
      return buildRoute('/objects/ClaimRecord', {
        created_by: userId,
        source_label: formatSource(source),
        owner_label: ownerLabel,
      })
    case 'leasing_contracts':
      return buildRoute('/objects/LeasingContract', {
        created_by: userId,
        source_label: formatSource(source),
        owner_label: ownerLabel,
      })
    default:
      return ''
  }
}

const buildOwnerOverdueRoute = (source: RankingSourceCode, userId: string, ownerLabel: string) => {
  switch (source) {
    case 'workflow_tasks':
      return buildRoute('/workflow/tasks', {
        assignee: userId,
        assignee_label: ownerLabel,
        source_label: formatSource(source),
        status: 'pending',
        overdue_only: true,
      })
    default:
      return ''
  }
}

const buildDepartmentRoute = (source: RankingSourceCode, departmentId: string, departmentLabel: string) => {
  switch (source) {
    case 'inventory_differences':
      return buildRoute('/objects/InventoryItem', {
        department: departmentId,
        unresolved_only: true,
        source_label: formatSource(source),
        department_label: departmentLabel,
      })
    case 'workflow_tasks':
      return buildRoute('/workflow/tasks', {
        department: departmentId,
        department_label: departmentLabel,
        source_label: formatSource(source),
        status: 'pending',
      })
    case 'projects':
      return buildRoute('/objects/AssetProject', {
        department: departmentId,
        source_label: formatSource(source),
        department_label: departmentLabel,
      })
    case 'finance_vouchers':
      return buildRoute('/objects/FinanceVoucher', {
        department: departmentId,
        source_label: formatSource(source),
        department_label: departmentLabel,
      })
    case 'insurance_policies':
      return buildRoute('/objects/InsurancePolicy', {
        department: departmentId,
        source_label: formatSource(source),
        department_label: departmentLabel,
      })
    case 'claim_records':
      return buildRoute('/objects/ClaimRecord', {
        department: departmentId,
        source_label: formatSource(source),
        department_label: departmentLabel,
      })
    case 'leasing_contracts':
      return buildRoute('/objects/LeasingContract', {
        department: departmentId,
        source_label: formatSource(source),
        department_label: departmentLabel,
      })
    default:
      return ''
  }
}

const buildDepartmentOverdueRoute = (source: RankingSourceCode, departmentId: string, departmentLabel: string) => {
  switch (source) {
    case 'workflow_tasks':
      return buildRoute('/workflow/tasks', {
        department: departmentId,
        department_label: departmentLabel,
        source_label: formatSource(source),
        status: 'pending',
        overdue_only: true,
      })
    default:
      return ''
  }
}

const buildDrilldownItems = (
  sourceCounts: Record<string, number>,
  routeBuilder: (source: RankingSourceCode) => string,
  overdueRouteBuilder: (source: RankingSourceCode) => string,
) => {
  return Object.entries(sourceCounts)
    .filter(([, count]) => Number(count) > 0)
    .sort((left, right) => Number(right[1]) - Number(left[1]))
    .map(([source, count]) => ({
      key: source,
      label: formatSource(source),
      count: Number(count) || 0,
      route: routeBuilder(source),
      overdueRoute: overdueRouteBuilder(source),
    }))
}

const openOwnerDrilldown = (item: ClosedLoopOverview['ownerRankings'][number]) => {
  const ownerLabel = item.displayName || item.username
  selectedDrilldown.value = {
    title: t('reports.closedLoop.drilldown.ownerTitle', {
      name: ownerLabel,
    }),
    items: buildDrilldownItems(
      item.sourceCounts,
      (source) => buildOwnerRoute(source, item.userId, ownerLabel),
      (source) => buildOwnerOverdueRoute(source, item.userId, ownerLabel),
    ),
  }
}

const openDepartmentDrilldown = (item: ClosedLoopOverview['departmentRankings'][number]) => {
  selectedDrilldown.value = {
    title: t('reports.closedLoop.drilldown.departmentTitle', {
      name: item.departmentName,
    }),
    items: buildDrilldownItems(
      item.sourceCounts,
      (source) => buildDepartmentRoute(source, item.departmentId, item.departmentName),
      (source) => buildDepartmentOverdueRoute(source, item.departmentId, item.departmentName),
    ),
  }
}

const formatOrganizationLabel = (option: OrganizationScopeOption) => {
  if (!option.code) {
    return option.name
  }
  return `${option.name} (${option.code})`
}

const formatTrendLabel = (date: string) => {
  return date.slice(5)
}

const getTrendBarHeight = (value: number) => {
  if (value <= 0) {
    return '0%'
  }
  return `${Math.max(12, Math.round((value / trendMaxValue.value) * 100))}%`
}

const clearObjectFilters = async () => {
  if (!selectedObjectCodes.value.length) {
    return
  }
  selectedObjectCodes.value = []
  selectedDrilldown.value = null
  await loadDashboard()
}

const toggleObjectFilter = async (objectCode: string) => {
  const nextCodes = selectedObjectCodes.value.includes(objectCode)
    ? selectedObjectCodes.value.filter((code) => code !== objectCode)
    : [...selectedObjectCodes.value, objectCode]

  selectedObjectCodes.value = nextCodes
  selectedDrilldown.value = null
  await loadDashboard()
}

onMounted(() => {
  void (async () => {
    await loadOrganizationOptions()
    await loadDashboard()
  })()
})
</script>

<style scoped>
.closed-loop-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.closed-loop-panel__toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.closed-loop-panel__toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
  align-items: flex-start;
}

.closed-loop-panel__action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.closed-loop-panel__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.closed-loop-panel__description {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}

.closed-loop-panel__window-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.closed-loop-panel__scope-picker {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 220px;
}

.closed-loop-panel__scope-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
}

.closed-loop-panel__scope-select {
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  background: #fff;
  color: #111827;
  font-size: 13px;
  font-weight: 600;
}

.closed-loop-panel__window-button,
.closed-loop-panel__retry,
.closed-loop-panel__coverage-chip,
.closed-loop-panel__table-link {
  border: 1px solid #d1d5db;
  background: #fff;
  color: #111827;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.closed-loop-panel__window-button,
.closed-loop-panel__retry,
.closed-loop-panel__coverage-chip {
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
}

.closed-loop-panel__window-button.is-active {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.closed-loop-panel__summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
}

.closed-loop-panel__summary-card {
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%);
  border: 1px solid #fed7aa;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.closed-loop-panel__summary-card--workflow {
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
  border-color: #bfdbfe;
}

.closed-loop-panel__summary-label {
  font-size: 12px;
  color: #6b7280;
}

.closed-loop-panel__summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.closed-loop-panel__section {
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  padding: 18px;
  background: #fff;
}

.closed-loop-panel__snapshot-strip {
  display: flex;
  flex-direction: column;
  gap: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  padding: 18px;
  background: linear-gradient(180deg, #fafaf9 0%, #ffffff 100%);
}

.closed-loop-panel__snapshot-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid #fde68a;
  background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
}

.closed-loop-panel__snapshot-eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #b45309;
}

.closed-loop-panel__snapshot-title {
  display: block;
  margin-top: 6px;
  color: #111827;
}

.closed-loop-panel__snapshot-hint {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.closed-loop-panel__section-header--snapshot {
  margin-bottom: 0;
}

.closed-loop-panel__snapshot-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.closed-loop-panel__snapshot-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}

.closed-loop-panel__snapshot-card.is-active {
  border-color: #111827;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.closed-loop-panel__snapshot-card-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.closed-loop-panel__snapshot-card-content strong {
  color: #111827;
  font-size: 14px;
}

.closed-loop-panel__snapshot-card-content span {
  color: #6b7280;
  font-size: 12px;
}

.closed-loop-panel__snapshot-card-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.closed-loop-panel__snapshot-compare {
  border: 1px solid #dbeafe;
  border-radius: 18px;
  padding: 16px;
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.closed-loop-panel__snapshot-compare-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.closed-loop-panel__snapshot-compare-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #bfdbfe;
}

.closed-loop-panel__snapshot-compare-delta {
  font-size: 24px;
  font-weight: 700;
  color: #1d4ed8;
}

.closed-loop-panel__snapshot-compare-meta {
  font-size: 12px;
  color: #64748b;
}

.closed-loop-panel__section-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
}

.closed-loop-panel__section-header h4 {
  margin: 0;
  font-size: 15px;
  color: #111827;
}

.closed-loop-panel__window-meta {
  font-size: 12px;
  color: #6b7280;
}

.closed-loop-panel__window-meta-separator {
  margin: 0 6px;
}

.closed-loop-panel__coverage-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.closed-loop-panel__inline-note {
  color: #6b7280;
  font-size: 12px;
}

.closed-loop-panel__drilldown-open,
.closed-loop-panel__drilldown-overdue {
  margin-right: 8px;
}

.closed-loop-panel__object-filter-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.closed-loop-panel__object-filter-chip {
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid #d1d5db;
  background: #f9fafb;
  color: #374151;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.closed-loop-panel__object-filter-chip.is-active {
  border-color: #111827;
  background: #111827;
  color: #ffffff;
}

.closed-loop-panel__trend-chart {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px 16px;
  margin-bottom: 14px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid #e5e7eb;
}

.closed-loop-panel__trend-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.closed-loop-panel__trend-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6b7280;
}

.closed-loop-panel__trend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.closed-loop-panel__trend-swatch--opened,
.closed-loop-panel__trend-bar--opened {
  background: #f97316;
}

.closed-loop-panel__trend-swatch--closed,
.closed-loop-panel__trend-bar--closed {
  background: #2563eb;
}

.closed-loop-panel__trend-bars {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(48px, 1fr));
  gap: 12px;
  align-items: end;
}

.closed-loop-panel__trend-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.closed-loop-panel__trend-columns {
  height: 124px;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 6px;
  padding: 0 4px;
}

.closed-loop-panel__trend-bar {
  width: 14px;
  border-radius: 999px 999px 4px 4px;
  transition: height 0.2s ease;
}

.closed-loop-panel__trend-day-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
}

.closed-loop-panel__drilldown-trigger,
.closed-loop-panel__drilldown-open {
  white-space: nowrap;
}

.closed-loop-panel__coverage-chip:hover,
.closed-loop-panel__table-link:hover,
.closed-loop-panel__retry:hover {
  border-color: #111827;
  color: #111827;
}

.closed-loop-panel__table-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.closed-loop-panel__table {
  width: 100%;
  border-collapse: collapse;
}

.closed-loop-panel__table th,
.closed-loop-panel__table td {
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
  text-align: left;
  font-size: 13px;
  color: #374151;
}

.closed-loop-panel__table th {
  font-weight: 700;
  color: #111827;
}

.closed-loop-panel__table-link {
  padding: 6px 12px;
  font-size: 12px;
}

.closed-loop-panel__loading,
.closed-loop-panel__empty,
.closed-loop-panel__error {
  padding: 18px;
  border-radius: 16px;
  background: #f9fafb;
  color: #6b7280;
  font-size: 13px;
}

.closed-loop-panel__error {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  border: 1px solid #fecaca;
  background: #fff1f2;
  color: #991b1b;
}

@media (max-width: 768px) {
  .closed-loop-panel__toolbar {
    flex-direction: column;
  }

  .closed-loop-panel__toolbar-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .closed-loop-panel__scope-picker {
    width: 100%;
  }

  .closed-loop-panel__section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .closed-loop-panel__snapshot-banner,
  .closed-loop-panel__snapshot-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .closed-loop-panel__snapshot-card-actions {
    align-items: flex-start;
  }
}
</style>
