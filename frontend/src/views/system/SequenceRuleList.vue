<template>
  <div class="sequence-rule-list">
    <div class="page-header">
      <h3>{{ $t('system.sequenceRule.title') }}</h3>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        {{ $t('system.sequenceRule.create') }}
      </el-button>
    </div>

    <!-- Filters -->
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item :label="$t('system.sequenceRule.columns.status')">
        <el-select
          v-model="filterForm.is_active"
          clearable
          :placeholder="$t('system.sequenceRule.placeholders.statusAll')"
          @change="handleSearch"
        >
          <el-option
            :label="$t('system.businessRule.messages.enabled')"
            :value="true"
          />
          <el-option
            :label="$t('system.businessRule.messages.disabled')"
            :value="false"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="handleSearch"
        >
          {{ $t('common.actions.search') }}
        </el-button>
        <el-button @click="handleFilterReset">
          {{ $t('common.actions.reset') }}
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Sequence Rules Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column
        prop="code"
        :label="$t('system.sequenceRule.columns.code')"
        width="180"
      />
      <el-table-column
        prop="name"
        :label="$t('system.sequenceRule.columns.name')"
        width="180"
      />
      <el-table-column
        :label="$t('system.sequenceRule.columns.pattern')"
        width="200"
      >
        <template #default="{ row }">
          <el-tag
            type="info"
            size="small"
          >
            {{ getPatternPreview(row) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="prefix"
        :label="$t('system.sequenceRule.columns.prefix')"
        width="120"
      />
      <el-table-column
        :label="$t('system.sequenceRule.columns.seqLength')"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          {{ row.seq_length }}
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.sequenceRule.columns.currentValue')"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          {{ row.current_value }}
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.sequenceRule.columns.resetPeriod')"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          <el-tag size="small">
            {{ getResetPeriodLabel(row.reset_period) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.sequenceRule.columns.status')"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.is_active ? 'success' : 'info'"
            size="small"
          >
            {{ row.is_active ? $t('common.status.active') : $t('common.status.inactive') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="description"
        :label="$t('system.sequenceRule.columns.description')"
        min-width="150"
        show-overflow-tooltip
      />
      <el-table-column
        :label="$t('common.labels.operation')"
        width="280"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handlePreview(row)"
          >
            {{ $t('system.sequenceRule.actions.preview') }}
          </el-button>
          <el-button
            link
            type="primary"
            @click="handleEdit(row)"
          >
            {{ $t('common.actions.edit') }}
          </el-button>
          <el-button
            link
            type="warning"
            @click="handleReset(row)"
          >
            {{ $t('system.sequenceRule.actions.reset') }}
          </el-button>
          <el-button
            link
            type="primary"
            @click="handleGenerate(row)"
          >
            {{ $t('system.sequenceRule.actions.generate') }}
          </el-button>
          <el-popconfirm
            :title="$t('system.sequenceRule.messages.confirmDelete')"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button
                link
                type="danger"
              >
                {{ $t('common.actions.delete') }}
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-footer">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>

    <!-- Sequence Rule Form Dialog -->
    <SequenceRuleForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="fetchData"
    />

    <!-- Preview Dialog -->
    <el-dialog
      v-model="previewVisible"
      :title="$t('system.sequenceRule.previewTitle')"
      width="500px"
    >
      <div
        v-if="previewData"
        class="preview-content"
      >
        <div class="preview-item">
          <span class="preview-label">{{ $t('system.sequenceRule.columns.code') }}:</span>
          <span class="preview-value">{{ previewData.code }}</span>
        </div>
        <div class="preview-item">
          <span class="preview-label">{{ $t('system.sequenceRule.columns.name') }}:</span>
          <span class="preview-value">{{ previewData.name }}</span>
        </div>
        <div class="preview-item">
          <span class="preview-label">{{ $t('system.sequenceRule.columns.pattern') }}:</span>
          <span class="preview-value">{{ previewData.pattern }}</span>
        </div>
        <div class="preview-item">
          <span class="preview-label">{{ $t('system.sequenceRule.columns.currentValue') }}:</span>
          <span class="preview-value">{{ previewData.current_value }}</span>
        </div>
        <el-divider />
        <div class="preview-samples">
          <div class="preview-label">
            Next 5 Numbers:
          </div>
          <div
            v-for="num in previewSamples"
            :key="num"
            class="sample-number"
          >
            <el-tag>{{ num }}</el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import type { SequenceRule } from '@/api/system'
import { sequenceRuleApi } from '@/api/system'
import SequenceRuleForm from './components/SequenceRuleForm.vue'

const { t } = useI18n()

const loading = ref(false)
const tableData = ref<SequenceRule[]>([])
const dialogVisible = ref(false)
const previewVisible = ref(false)
const currentRow = ref<SequenceRule | null>(null)
const previewData = ref<SequenceRule | null>(null)

const filterForm = reactive({
  is_active: undefined as unknown as boolean
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getResetPeriodLabel = (period: string) => {
  const key = `system.sequenceRule.periods.${period}`
  const label = t(key)
  return label !== key ? label : period
}

const getPatternPreview = (row: SequenceRule) => {
  const prefix = row.prefix || ''
  const seqLen = row.seq_length || 4
  return `${prefix}${'#'.repeat(seqLen)}}`
}

const previewSamples = computed(() => {
  if (!previewData.value) return []
  const samples: string[] = []
  const current = previewData.value.current_value || 0
  const prefix = previewData.value.prefix || ''
  const seqLen = previewData.value.seq_length || 4
  for (let i = 1; i <= 5; i++) {
    const num = current + i
    const padded = String(num).padStart(seqLen, '0')
    samples.push(`${prefix}${padded}`)
  }
  return samples
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await sequenceRuleApi.list({
      ...filterForm,
      page: pagination.page,
      page_size: pagination.pageSize
    }) as any

    tableData.value = res.results || []
    pagination.total = res.count || 0
  } catch (error) {
    ElMessage.error(t('common.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleFilterReset = () => {
  filterForm.is_active = undefined as unknown as boolean
  handleSearch()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: SequenceRule) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handlePreview = async (row: SequenceRule) => {
  try {
    const res = await sequenceRuleApi.preview(row.code) as any
    previewData.value = { ...row, ...res }
    previewVisible.value = true
  } catch (error) {
    ElMessage.error(t('system.sequenceRule.messages.previewFailed'))
  }
}

const handleReset = async (row: SequenceRule) => {
  try {
    await ElMessageBox.confirm(
      t('system.sequenceRule.messages.confirmReset', { name: row.name }),
      t('common.dialog.confirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('system.sequenceRule.actions.reset'),
        cancelButtonText: t('common.actions.cancel')
      }
    )

    await sequenceRuleApi.reset(row.code)
    ElMessage.success(t('system.sequenceRule.messages.resetSuccess'))
    await fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(t('system.sequenceRule.messages.resetFailed'))
    }
  }
}

const handleGenerate = async (row: SequenceRule) => {
  try {
    const res = await sequenceRuleApi.generate(row.code) as any
    ElMessage.success(t('system.sequenceRule.messages.generateSuccess', { number: res.number }))
    await fetchData()
  } catch (error) {
    ElMessage.error(t('system.sequenceRule.messages.generateFailed'))
  }
}

const handleDelete = async (row: SequenceRule) => {
  try {
    await sequenceRuleApi.delete(row.id)
    ElMessage.success(t('common.messages.deleteSuccess'))
    await fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(t('common.messages.deleteFailed'))
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.sequence-rule-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h3 {
  margin: 0;
  font-size: 18px;
}

.filter-form {
  margin-bottom: 20px;
}

.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.preview-content {
  padding: 10px 0;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.preview-label {
  font-weight: 500;
  color: #606266;
}

.preview-value {
  color: #303133;
}

.preview-samples {
  margin-top: 15px;
}

.sample-number {
  display: inline-block;
  margin-right: 8px;
  margin-top: 8px;
}
</style>
