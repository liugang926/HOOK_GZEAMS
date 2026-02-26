<template>
  <div class="system-file-list">
    <div class="page-header">
      <h3>{{ $t('system.file.title') }}</h3>
      <el-upload
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">
          {{ $t('system.file.actions.upload') }}
        </el-button>
      </el-upload>
    </div>

    <!-- Filters -->
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item :label="$t('system.file.filter.search')">
        <el-input
          v-model="filterForm.search"
          :placeholder="$t('system.file.filter.searchPlaceholder')"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item :label="$t('system.file.filter.fileType')">
        <el-select
          v-model="filterForm.file_type"
          clearable
          :placeholder="$t('system.file.filter.allTypes')"
          @change="handleSearch"
        >
          <el-option
            :label="$t('system.file.types.image')"
            value="image"
          />
          <el-option
            :label="$t('system.file.types.document')"
            value="document"
          />
          <el-option
            :label="$t('system.file.types.video')"
            value="video"
          />
          <el-option
            :label="$t('system.file.types.archive')"
            value="archive"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('system.file.filter.bizType')">
        <el-select
          v-model="filterForm.biz_type"
          clearable
          :placeholder="$t('system.file.filter.allBizTypes')"
          @change="handleSearch"
        >
          <el-option
            :label="$t('system.file.types.asset_image')"
            value="asset_image"
          />
          <el-option
            :label="$t('system.file.types.contract')"
            value="contract"
          />
          <el-option
            :label="$t('system.file.types.invoice')"
            value="invoice"
          />
          <el-option
            :label="$t('system.file.types.attachment')"
            value="attachment"
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

    <!-- Statistics Cards -->
    <el-row
      :gutter="20"
      class="stats-row"
    >
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">
              {{ stats.total_files }}
            </div>
            <div class="stat-label">
              {{ $t('system.file.stats.totalFiles') }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">
              {{ formatFileSize(stats.total_size) }}
            </div>
            <div class="stat-label">
              {{ $t('system.file.stats.totalSize') }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">
              {{ stats.today_uploads }}
            </div>
            <div class="stat-label">
              {{ $t('system.file.stats.todayUploads') }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">
              {{ stats.image_count }}
            </div>
            <div class="stat-label">
              {{ $t('system.file.stats.images') }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Files Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        type="selection"
        width="55"
      />
      <el-table-column
        :label="$t('system.file.columns.preview')"
        width="80"
      >
        <template #default="{ row }">
          <div
            v-if="isImage(row)"
            class="file-preview"
          >
            <el-image
              :src="row.url"
              :preview-src-list="[row.url]"
              fit="cover"
              style="width: 50px; height: 50px; border-radius: 4px"
            >
              <template #error>
                <div class="image-error">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </div>
          <el-icon
            v-else
            class="file-icon"
          >
            <Document />
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column
        prop="fileName"
        :label="$t('system.file.columns.fileName')"
        min-width="200"
      />
      <el-table-column
        :label="$t('system.file.columns.type')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            size="small"
            :type="getFileTagType(row)"
          >
            {{ getFileTypeLabel(row) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="fileSize"
        :label="$t('system.file.columns.size')"
        width="100"
      >
        <template #default="{ row }">
          {{ formatFileSize(row.fileSize) }}
        </template>
      </el-table-column>
      <el-table-column
        prop="bizType"
        :label="$t('system.file.columns.bizType')"
        width="130"
      >
        <template #default="{ row }">
          {{ row.bizType ? $t(`system.file.types.${row.bizType}`) : row.bizType }}
        </template>
      </el-table-column>
      <el-table-column
        prop="description"
        :label="$t('system.file.columns.description')"
        min-width="150"
        show-overflow-tooltip
      />
      <el-table-column
        prop="createdAt"
        :label="$t('system.file.columns.uploadDate')"
        width="170"
      />
      <el-table-column
        :label="$t('common.actions.detail')"
        width="180"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleDownload(row)"
          >
            {{ $t('system.file.actions.download') }}
          </el-button>
          <el-button
            link
            type="primary"
            @click="handleEdit(row)"
          >
            {{ $t('common.actions.edit') }}
          </el-button>
          <el-popconfirm
            :title="$t('system.file.messages.confirmDelete')"
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

    <!-- Batch Actions -->
    <div
      v-if="selectedFiles.length > 0"
      class="batch-actions"
    >
      <span class="selected-count">{{ $t('system.file.actions.selection', { count: selectedFiles.length }) }}</span>
      <el-button
        type="danger"
        @click="handleBatchDelete"
      >
        {{ $t('system.file.actions.batchDelete') }}
      </el-button>
      <el-button @click="clearSelection">
        {{ $t('system.file.actions.clearSelection') }}
      </el-button>
    </div>

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

    <!-- Edit File Dialog -->
    <el-dialog
      v-model="editDialogVisible"
      :title="$t('system.file.dialog.editTitle')"
      width="500px"
    >
      <el-form
        :model="editForm"
        label-width="120px"
      >
        <el-form-item :label="$t('system.file.dialog.fileName')">
          <el-input
            v-model="editForm.file_name"
            disabled
          />
        </el-form-item>
        <el-form-item :label="$t('system.file.dialog.bizType')">
          <el-select
            v-model="editForm.biz_type"
            style="width: 100%"
          >
            <el-option
              :label="$t('system.file.types.asset_image')"
              value="asset_image"
            />
            <el-option
              :label="$t('system.file.types.contract')"
              value="contract"
            />
            <el-option
              :label="$t('system.file.types.invoice')"
              value="invoice"
            />
            <el-option
              :label="$t('system.file.types.attachment')"
              value="attachment"
            />
            <el-option
              :label="$t('system.file.types.other')"
              value="other"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('system.file.dialog.description')">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          @click="handleSaveEdit"
        >
          {{ $t('common.actions.save') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, Document } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'
import type { SystemFile } from '@/api/systemFile'

const { t } = useI18n()
const userStore = useUserStore()
const loading = ref(false)
const tableData = ref<SystemFile[]>([])
const selectedFiles = ref<SystemFile[]>([])
const editDialogVisible = ref(false)

const filterForm = reactive({
  search: '',
  file_type: undefined as unknown as string,
  biz_type: undefined as unknown as string
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const stats = ref({
  total_files: 0,
  total_size: 0,
  today_uploads: 0,
  image_count: 0
})

const editForm = ref({
  id: '',
  file_name: '',
  biz_type: '',
  description: ''
})

const uploadUrl = computed(() => {
  return '/api/system/system-files/upload/'
})

const uploadHeaders = computed(() => {
  return {
    'Authorization': `Bearer ${userStore.token}`
  }
})

const isImage = (file: SystemFile) => {
  return file.fileType?.startsWith('image/') ||
    ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(file.fileExtension?.toLowerCase() || '')
}

const getFileTagType = (file: SystemFile) => {
  if (file.fileType?.startsWith('image/')) return 'success'
  if (file.fileType?.startsWith('video/')) return 'warning'
  if (file.fileType?.includes('pdf')) return 'danger'
  return ''
}

const getFileTypeLabel = (file: SystemFile) => {
  if (file.fileType?.startsWith('image/')) return t('system.file.types.image')
  if (file.fileType?.startsWith('video/')) return t('system.file.types.video')
  if (file.fileType?.includes('pdf')) return t('system.file.types.pdf')
  if (file.fileExtension) return file.fileExtension.toUpperCase()
  return t('system.file.types.file')
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filterForm.search) {
      params.search = filterForm.search
    }
    if (filterForm.file_type) {
      params.file_type__startswith = filterForm.file_type
    }
    if (filterForm.biz_type) {
      params.biz_type = filterForm.biz_type
    }

    const res = await request.get('/system/system-files/', { params })
    tableData.value = res?.results || []
    pagination.total = res?.count || 0
    stats.value.total_files = pagination.total
  } catch (error) {
    ElMessage.error(t('system.file.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleFilterReset = () => {
  filterForm.search = ''
  filterForm.file_type = undefined as unknown as string
  filterForm.biz_type = undefined as unknown as string
  handleSearch()
}

const beforeUpload = (file: File) => {
  const maxSize = 100 * 1024 * 1024 // 100MB
  if (file.size > maxSize) {
    ElMessage.error(t('system.file.messages.sizeLimit', { size: '100MB' }))
    return false
  }
  return true
}

const handleUploadSuccess = (response: any) => {
  ElMessage.success(t('system.file.messages.uploadSuccess'))
  fetchData()
}

const handleUploadError = () => {
  ElMessage.error(t('system.file.messages.uploadFailed'))
}

const handleDownload = (file: SystemFile) => {
  window.open(file.url || `/media/${file.filePath}`, '_blank')
}

const handleEdit = (file: SystemFile) => {
  editForm.value = {
    id: file.id,
    file_name: file.fileName,
    biz_type: file.bizType || '',
    description: file.description || ''
  }
  editDialogVisible.value = true
}

const handleSaveEdit = async () => {
  try {
    await request.patch(`/system/system-files/${editForm.value.id}/`, {
      bizType: editForm.value.biz_type,
      description: editForm.value.description
    })
    ElMessage.success(t('system.file.messages.updateSuccess'))
    editDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error(t('system.file.messages.updateFailed'))
  }
}

const handleDelete = async (file: SystemFile) => {
  try {
    await request.delete(`/system/system-files/${file.id}/`)
    ElMessage.success(t('system.file.messages.deleteSuccess'))
    fetchData()
  } catch (error) {
    ElMessage.error(t('system.file.messages.deleteFailed'))
  }
}

const handleSelectionChange = (selection: SystemFile[]) => {
  selectedFiles.value = selection
}

const clearSelection = () => {
  selectedFiles.value = []
}

const handleBatchDelete = async () => {
  try {
    const ids = selectedFiles.value.map(f => f.id)
    await request.post('/system/system-files/batch_delete/', { ids })
    ElMessage.success(t('system.file.messages.batchDeleteSuccess', { count: ids.length }))
    clearSelection()
    fetchData()
  } catch (error) {
    ElMessage.error(t('system.file.messages.batchDeleteFailed'))
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.system-file-list {
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

.stats-row {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.file-preview {
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-icon {
  font-size: 32px;
  color: #909399;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  background: #f5f7fa;
  border-radius: 4px;
  color: #909399;
}

.batch-actions {
  padding: 10px 20px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.selected-count {
  margin-right: auto;
  font-weight: 500;
}

.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
