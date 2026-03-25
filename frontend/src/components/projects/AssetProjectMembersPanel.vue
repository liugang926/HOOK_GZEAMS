<template>
  <el-card
    class="asset-project-panel"
    shadow="never"
  >
    <template #header>
      <div class="asset-project-panel__header">
        <div class="asset-project-panel__heading">
          <div class="asset-project-panel__title-row">
            <span>{{ title }}</span>
            <span class="asset-project-panel__meta">{{ displayTotalCount }}</span>
          </div>
          <p class="asset-project-panel__hint">
            {{ t('projects.panels.membersHint') }}
          </p>
        </div>

        <div class="asset-project-panel__actions">
          <el-button
            size="small"
            @click="loadMembers"
          >
            {{ t('common.actions.refresh') }}
          </el-button>
          <el-button
            size="small"
            @click="handleViewAll"
          >
            {{ t('projects.actions.viewAllMembers') }}
          </el-button>
          <el-button
            size="small"
            type="primary"
            @click="handleCreate"
          >
            {{ t('projects.actions.addMember') }}
          </el-button>
        </div>
      </div>
    </template>

    <el-empty
      v-if="!loading && members.length === 0"
      :description="t('projects.messages.emptyMembers')"
    />

    <el-table
      v-else
      v-loading="loading"
      :data="members"
      border
      stripe
      @row-click="handleRowClick"
    >
      <el-table-column
        :label="t('projects.columns.member')"
        min-width="180"
      >
        <template #default="{ row }">
          {{ resolveUserName(row.userDetail) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.role')"
        width="140"
      >
        <template #default="{ row }">
          <el-tag type="info">
            {{ resolveRoleLabel(String(row.role || '')) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.primary')"
        width="110"
      >
        <template #default="{ row }">
          <el-tag :type="row.isPrimary ? 'warning' : 'info'">
            {{ row.isPrimary ? t('projects.flags.primary') : '--' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.active')"
        width="110"
      >
        <template #default="{ row }">
          <el-tag :type="row.isActive ? 'success' : 'info'">
            {{ row.isActive ? t('projects.flags.active') : t('projects.flags.inactive') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.joinDate')"
        width="130"
      >
        <template #default="{ row }">
          {{ formatDate(String(row.joinDate || '')) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="responsibilities"
        :label="t('projects.columns.responsibilities')"
        min-width="220"
        show-overflow-tooltip
      />
      <el-table-column
        :label="t('projects.columns.permissions')"
        min-width="220"
      >
        <template #default="{ row }">
          {{ resolvePermissions(row) || '--' }}
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { createObjectClient, type ListResponse } from '@/api/dynamic'
import { formatDate } from '@/utils/dateFormat'

const props = defineProps<{
  panel: Record<string, unknown>
  recordId: string
  refreshVersion?: number
  panelRefreshVersion?: number
  workspaceDashboard?: Record<string, unknown> | null
  workspaceDashboardEnabled?: boolean
}>()

const { t, te } = useI18n()
const router = useRouter()
const projectMemberApi = createObjectClient('ProjectMember')
const loading = ref(false)
const totalCount = ref(0)
const members = ref<Array<Record<string, unknown>>>([])

const title = computed(() => {
  const titleKey = String(props.panel.titleKey || props.panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(props.panel.title || t('projects.panels.members'))
})

const resolveUserName = (value: unknown) => {
  if (!value || typeof value !== 'object') return ''
  const candidate = value as Record<string, unknown>
  return String(
    candidate.fullName ||
    candidate.full_name ||
    candidate.name ||
    candidate.username ||
    ''
  ).trim()
}

const resolveRoleLabel = (value: string) => {
  const key = `projects.role.${value}`
  return value && te(key) ? t(key) : value
}

const resolvePermissions = (row: Record<string, unknown>) => {
  const labels: string[] = []
  if (row.canAllocateAsset) {
    labels.push(t('projects.flags.canAllocateAsset'))
  }
  if (row.canViewCost) {
    labels.push(t('projects.flags.canViewCost'))
  }
  return labels.join(' / ')
}

const resolveDashboardCount = (
  segmentKey: string,
  countKeys: string[],
): number | null => {
  if (!props.workspaceDashboard || typeof props.workspaceDashboard !== 'object') {
    return null
  }
  const segment = props.workspaceDashboard[segmentKey]
  if (!segment || typeof segment !== 'object') {
    return null
  }
  const candidate = segment as Record<string, unknown>
  for (const key of countKeys) {
    const value = candidate[key]
    if (value === null || value === undefined || value === '') {
      continue
    }
    const normalized = Number(value)
    if (Number.isFinite(normalized)) {
      return normalized
    }
  }
  return null
}

const sharedTotalCount = computed(() => resolveDashboardCount('members', ['totalCount', 'total_count']))
const displayTotalCount = computed(() => {
  return sharedTotalCount.value ?? totalCount.value
})

interface ListEnvelope<T> {
  count?: number
  results?: T[]
}

const resolveListEnvelope = <T extends Record<string, unknown>>(
  result: ListResponse<T> | ListEnvelope<T>
): ListEnvelope<T> => {
  if ('data' in result && result.data && typeof result.data === 'object') {
    return result.data
  }
  return {
    count: 'count' in result ? result.count : undefined,
    results: 'results' in result ? result.results : undefined,
  }
}

const loadMembers = async () => {
  if (!props.recordId) return
  loading.value = true
  try {
    const result = await projectMemberApi.list({
      project: props.recordId,
      page: 1,
      page_size: 6,
      ordering: '-is_primary,join_date',
    })
    const envelope = resolveListEnvelope(result)
    totalCount.value = Number(envelope.count || 0)
    members.value = Array.isArray(envelope.results) ? envelope.results : []
  } catch (error: unknown) {
    totalCount.value = 0
    members.value = []
    ElMessage.error(error instanceof Error ? error.message : t('projects.messages.loadMembersFailed'))
  } finally {
    loading.value = false
  }
}

const handleViewAll = () => {
  router.push({
    path: '/objects/ProjectMember',
    query: { project: props.recordId },
  })
}

const handleCreate = () => {
  router.push({
    path: '/objects/ProjectMember/create',
    query: {
      prefill_project: props.recordId,
      returnTo: `/objects/AssetProject/${props.recordId}`,
    },
  })
}

const handleRowClick = (row: Record<string, unknown>) => {
  const recordId = String(row.id || '').trim()
  if (!recordId) return
  router.push(`/objects/ProjectMember/${encodeURIComponent(recordId)}`)
}

watch(
  () => [props.recordId, props.refreshVersion, props.panelRefreshVersion],
  () => {
    void loadMembers()
  },
  { immediate: true }
)
</script>

<style scoped>
.asset-project-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.asset-project-panel__heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.asset-project-panel__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.asset-project-panel__meta {
  font-size: 12px;
  color: #606266;
}

.asset-project-panel__hint {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.asset-project-panel__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}
</style>
