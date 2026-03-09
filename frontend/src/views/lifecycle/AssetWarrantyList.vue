<template>
  <div class="lifecycle-page">
    <!-- List -->
    <BaseListPage
      :title="$t('assets.lifecycle.assetWarranty.title')"
      :columns="columns"
      :data="listData"
      :loading="loading"
      :total="total"
      :page-size="pageSize"
      :current-page="currentPage"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
      @row-click="handleRowClick"
    >
      <template #header-actions>
        <el-button type="primary" @click="handleCreate">
          {{ $t('assets.lifecycle.assetWarranty.createButton') }}
        </el-button>
      </template>

      <!-- Status Column -->
      <template #column-status="{ row }">
        <el-tag :type="getStatusType(row.status)" size="small">
          {{ $t(`assets.lifecycle.assetWarranty.status.${row.status}`) }}
        </el-tag>
      </template>

      <!-- Warranty Type Column -->
      <template #column-warranty_type="{ row }">
        {{ $t(`assets.lifecycle.assetWarranty.warrantyType.${row.warranty_type}`) }}
      </template>

      <!-- Actions Column -->
      <template #column-actions="{ row }">
        <el-button
          v-if="row.status === 'draft'"
          type="success"
          size="small"
          link
          @click.stop="handleActivate(row)"
        >
          {{ $t('assets.lifecycle.assetWarranty.actions.activate') }}
        </el-button>
        <el-button
          v-if="['active', 'expiring'].includes(row.status)"
          type="warning"
          size="small"
          link
          @click.stop="handleRenew(row)"
        >
          {{ $t('assets.lifecycle.assetWarranty.actions.renew') }}
        </el-button>
        <el-button
          type="danger"
          size="small"
          link
          @click.stop="handleCancel(row)"
          v-if="!['cancelled', 'expired'].includes(row.status)"
        >
          {{ $t('assets.lifecycle.assetWarranty.actions.cancel') }}
        </el-button>
      </template>
    </BaseListPage>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { assetWarrantyApi } from '@/api/lifecycle'

const router = useRouter()
const { t } = useI18n()

// ─── State ──────────────────────────────────────────────────────────────────
const loading = ref(false)
const listData = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// ─── Columns ────────────────────────────────────────────────────────────────
const columns = computed(() => [
  { prop: 'warranty_no', label: t('assets.lifecycle.assetWarranty.columns.warrantyNo'), minWidth: 150 },
  { prop: 'asset_name', label: t('assets.lifecycle.assetWarranty.columns.assetName'), minWidth: 150 },
  { prop: 'warranty_type', label: t('assets.lifecycle.assetWarranty.columns.warrantyType'), minWidth: 120, slot: true },
  { prop: 'warranty_provider', label: t('assets.lifecycle.assetWarranty.columns.warrantyProvider'), minWidth: 150 },
  { prop: 'start_date', label: t('assets.lifecycle.assetWarranty.columns.startDate'), minWidth: 110 },
  { prop: 'end_date', label: t('assets.lifecycle.assetWarranty.columns.endDate'), minWidth: 110 },
  { prop: 'warranty_cost', label: t('assets.lifecycle.assetWarranty.columns.warrantyCost'), minWidth: 100 },
  { prop: 'status', label: t('assets.lifecycle.assetWarranty.columns.status'), minWidth: 100, slot: true },
  { prop: 'claim_count', label: t('assets.lifecycle.assetWarranty.columns.claimCount'), minWidth: 80 },
  { prop: 'actions', label: t('common.actions.actions'), minWidth: 180, slot: true, fixed: 'right' },
])

// ─── Status Helper ──────────────────────────────────────────────────────────
const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    active: 'success',
    expiring: 'warning',
    expired: 'danger',
    claimed: '',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

// ─── Data Loading ───────────────────────────────────────────────────────────
const loadData = async () => {
  loading.value = true
  try {
    const res = await assetWarrantyApi.list({
      page: currentPage.value,
      page_size: pageSize.value
    })
    listData.value = res.results
    total.value = res.count
  } catch { /* handled by interceptor */ } finally {
    loading.value = false
  }
}

// ─── Event Handlers ─────────────────────────────────────────────────────────
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadData()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadData()
}

const handleRowClick = (row: any) => {
  router.push(`/assets/lifecycle/asset-warranties/${row.id}`)
}

const handleCreate = () => {
  router.push('/assets/lifecycle/asset-warranties/create')
}

const handleActivate = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.assetWarranty.messages.activateConfirm'),
      t('common.actions.confirm'),
      { type: 'info' }
    )
    await assetWarrantyApi.activate(row.id)
    ElMessage.success(t('assets.lifecycle.assetWarranty.messages.activateSuccess'))
    loadData()
  } catch { /* cancelled */ }
}

const handleRenew = async (row: any) => {
  router.push(`/assets/lifecycle/asset-warranties/${row.id}?action=renew`)
}

const handleCancel = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('assets.lifecycle.assetWarranty.messages.cancelConfirm'),
      t('common.actions.confirm'),
      { type: 'warning' }
    )
    await assetWarrantyApi.cancel(row.id)
    ElMessage.success(t('assets.lifecycle.assetWarranty.messages.cancelSuccess'))
    loadData()
  } catch { /* cancelled */ }
}

onMounted(loadData)
</script>

<style scoped>
.lifecycle-page {
  padding: 16px;
}
</style>
