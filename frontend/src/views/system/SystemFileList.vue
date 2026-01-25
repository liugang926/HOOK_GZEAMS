<template>
  <div class="system-file-list">
    <div class="page-header">
      <h3>System File Management</h3>
      <el-upload
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :show-file-list="false"
        :before-upload="beforeUpload"
      >
        <el-button type="primary">Upload File</el-button>
      </el-upload>
    </div>

    <!-- Filters -->
    <el-form :model="filterForm" inline class="filter-form">
      <el-form-item label="Search">
        <el-input
          v-model="filterForm.search"
          placeholder="File name"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item label="File Type">
        <el-select v-model="filterForm.file_type" clearable placeholder="All Types" @change="handleSearch">
          <el-option label="Images" value="image" />
          <el-option label="Documents" value="document" />
          <el-option label="Videos" value="video" />
          <el-option label="Archives" value="archive" />
        </el-select>
      </el-form-item>
      <el-form-item label="Business Type">
        <el-select v-model="filterForm.biz_type" clearable placeholder="All" @change="handleSearch">
          <el-option label="Asset Image" value="asset_image" />
          <el-option label="Contract" value="contract" />
          <el-option label="Invoice" value="invoice" />
          <el-option label="Attachment" value="attachment" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">Search</el-button>
        <el-button @click="handleFilterReset">Reset</el-button>
      </el-form-item>
    </el-form>

    <!-- Statistics Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.total_files }}</div>
            <div class="stat-label">Total Files</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ formatFileSize(stats.total_size) }}</div>
            <div class="stat-label">Total Size</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.today_uploads }}</div>
            <div class="stat-label">Today Uploads</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.image_count }}</div>
            <div class="stat-label">Images</div>
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
      <el-table-column type="selection" width="55" />
      <el-table-column label="Preview" width="80">
        <template #default="{ row }">
          <div v-if="isImage(row)" class="file-preview">
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
          <el-icon v-else class="file-icon"><Document /></el-icon>
        </template>
      </el-table-column>
      <el-table-column prop="file_name" label="File Name" min-width="200" />
      <el-table-column label="Type" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="getFileTagType(row)">
            {{ getFileTypeLabel(row) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="file_size" label="Size" width="100">
        <template #default="{ row }">
          {{ formatFileSize(row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column prop="biz_type" label="Business Type" width="130" />
      <el-table-column prop="description" label="Description" min-width="150" show-overflow-tooltip />
      <el-table-column prop="created_at" label="Upload Date" width="170" />
      <el-table-column label="Actions" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleDownload(row)">Download</el-button>
          <el-button link type="primary" @click="handleEdit(row)">Edit</el-button>
          <el-popconfirm
            title="Are you sure to delete this file?"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button link type="danger">Delete</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Batch Actions -->
    <div v-if="selectedFiles.length > 0" class="batch-actions">
      <span class="selected-count">{{ selectedFiles.length }} files selected</span>
      <el-button type="danger" @click="handleBatchDelete">Batch Delete</el-button>
      <el-button @click="clearSelection">Clear Selection</el-button>
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
      title="Edit File"
      width="500px"
    >
      <el-form :model="editForm" label-width="120px">
        <el-form-item label="File Name">
          <el-input v-model="editForm.file_name" disabled />
        </el-form-item>
        <el-form-item label="Business Type">
          <el-select v-model="editForm.biz_type" style="width: 100%">
            <el-option label="Asset Image" value="asset_image" />
            <el-option label="Contract" value="contract" />
            <el-option label="Invoice" value="invoice" />
            <el-option label="Attachment" value="attachment" />
            <el-option label="Other" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="handleSaveEdit">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, Document } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

interface SystemFile {
  id: string
  file_name: string
  file_path: string
  file_size: number
  file_type: string
  file_extension: string
  biz_type?: string
  biz_id?: string
  description?: string
  url?: string
  created_at: string
}

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
  return '/api/system/files/upload/'
})

const uploadHeaders = computed(() => {
  return {
    'Authorization': `Bearer ${userStore.token}`
  }
})

const isImage = (file: SystemFile) => {
  return file.file_type?.startsWith('image/') ||
    ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(file.file_extension?.toLowerCase() || '')
}

const getFileTagType = (file: SystemFile) => {
  if (file.file_type?.startsWith('image/')) return 'success'
  if (file.file_type?.startsWith('video/')) return 'warning'
  if (file.file_type?.includes('pdf')) return 'danger'
  return ''
}

const getFileTypeLabel = (file: SystemFile) => {
  if (file.file_type?.startsWith('image/')) return 'Image'
  if (file.file_type?.startsWith('video/')) return 'Video'
  if (file.file_type?.includes('pdf')) return 'PDF'
  if (file.file_extension) return file.file_extension.toUpperCase()
  return 'File'
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
      params.file_name__icontains = filterForm.search
    }
    if (filterForm.file_type) {
      params.file_type__startswith = filterForm.file_type
    }
    if (filterForm.biz_type) {
      params.biz_type = filterForm.biz_type
    }

    const res = await fetch('/api/system/files/', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    }).then(r => r.json())
    tableData.value = res.results || []
    pagination.total = res.count || 0
  } catch (error) {
    ElMessage.error('Failed to load files')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await fetch('/api/system/files/stats/', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    }).then(r => r.json())
    stats.value = res.data || stats.value
  } catch (error) {
    // Ignore stats error
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
    ElMessage.error('File size cannot exceed 100MB')
    return false
  }
  return true
}

const handleUploadSuccess = (response: any) => {
  ElMessage.success('File uploaded successfully')
  fetchData()
  fetchStats()
}

const handleUploadError = () => {
  ElMessage.error('Upload failed')
}

const handleDownload = (file: SystemFile) => {
  window.open(file.url || `/media/${file.file_path}`, '_blank')
}

const handleEdit = (file: SystemFile) => {
  editForm.value = {
    id: file.id,
    file_name: file.file_name,
    biz_type: file.biz_type || '',
    description: file.description || ''
  }
  editDialogVisible.value = true
}

const handleSaveEdit = async () => {
  try {
    await fetch(`/api/system/files/${editForm.value.id}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        biz_type: editForm.value.biz_type,
        description: editForm.value.description
      })
    })
    ElMessage.success('Updated successfully')
    editDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('Update failed')
  }
}

const handleDelete = async (file: SystemFile) => {
  try {
    await fetch(`/api/system/files/${file.id}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    ElMessage.success('Deleted successfully')
    fetchData()
    fetchStats()
  } catch (error) {
    ElMessage.error('Delete failed')
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
    await fetch('/api/system/files/batch-delete/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ids })
    })
    ElMessage.success(`Deleted ${ids.length} files`)
    clearSelection()
    fetchData()
    fetchStats()
  } catch (error) {
    ElMessage.error('Batch delete failed')
  }
}

onMounted(() => {
  fetchData()
  fetchStats()
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
