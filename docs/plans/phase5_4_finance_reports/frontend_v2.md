# Phase 5.4: Financial Reports - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement financial report generation center with template management, scheduling, and multi-format export capabilities.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/finance_reports.ts

export interface ReportTemplate {
  id: string
  code: string
  name: string
  category: ReportCategory
  description?: string
  templateConfig: ReportTemplateConfig
  outputFormats: OutputFormat[]
  isScheduled: boolean
  scheduleConfig?: ScheduleConfig
  recipients?: ReportRecipient[]
  isActive: boolean
  organizationId: string
  createdAt: string
  updatedAt: string
}

export enum ReportCategory {
  ASSET_SUMMARY = 'asset_summary',
  DEPRECIATION = 'depreciation',
  CONSUMABLE = 'consumable',
  INVENTORY = 'inventory',
  FINANCIAL = 'financial'
}

export enum OutputFormat {
  XLSX = 'xlsx',
  PDF = 'pdf',
  CSV = 'csv',
  HTML = 'html'
}

export interface ReportTemplateConfig {
  columns: ReportColumn[]
  filters?: ReportFilter[]
  groupBy?: string[]
  sortBy?: SortConfig[]
  chartConfig?: ChartConfig
}

export interface ReportColumn {
  field: string
  label: string
  width?: number
  align?: 'left' | 'center' | 'right'
  format?: 'text' | 'number' | 'currency' | 'date' | 'enum'
  formatOptions?: Record<string, any>
  aggregate?: 'sum' | 'avg' | 'count' | 'max' | 'min'
}

export interface ReportFilter {
  field: string
  label: string
  type: 'input' | 'select' | 'daterange' | 'tree'
  options?: Array<{ label: string; value: any }>
  defaultValue?: any
}

export interface SortConfig {
  field: string
  order: 'asc' | 'desc'
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'area'
  xAxis?: string
  yAxis?: string[]
  title?: string
}

export interface ScheduleConfig {
  frequency: ScheduleFrequency
  dayOfWeek?: number
  dayOfMonth?: number
  time: string
  timezone?: string
}

export enum ScheduleFrequency {
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly'
}

export interface ReportRecipient {
  userId?: string
  email?: string
  format: OutputFormat
}

export interface ReportGeneration {
  id: string
  templateId: string
  template?: ReportTemplate
  parameters: Record<string, any>
  status: GenerationStatus
  generatedAt?: string
  completedAt?: string
  error?: string
  fileUrl?: string
  createdBy: string
}

export enum GenerationStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface ReportData {
  metadata: {
    templateId: string
    templateName: string
    generatedAt: string
    generatedBy: string
    parameters: Record<string, any>
  }
  summary: Record<string, any>
  data: any[]
  chartData?: ChartDataPoint[]
}

export interface ChartDataPoint {
  name: string
  value: number
  [key: string]: any
}

export interface SavedReport {
  id: string
  templateId: string
  templateName: string
  reportName: string
  fileUrl: string
  fileSize: number
  format: OutputFormat
  generatedAt: string
  generatedBy: string
  expiresAt?: string
}
```

### API Service

```typescript
// frontend/src/api/finance_reports.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  ReportTemplate,
  ReportGeneration,
  ReportData,
  SavedReport,
  OutputFormat
} from '@/types/finance_reports'

export const reportApi = {
  // Report Templates
  listTemplates(params?: {
    category?: ReportCategory
    isActive?: boolean
  }): Promise<ReportTemplate[]> {
    return request.get('/finance/reports/templates/', { params })
  },

  getTemplate(id: string): Promise<ReportTemplate> {
    return request.get(`/finance/reports/templates/${id}/`)
  },

  createTemplate(data: Partial<ReportTemplate>): Promise<ReportTemplate> {
    return request.post('/finance/reports/templates/', data)
  },

  updateTemplate(id: string, data: Partial<ReportTemplate>): Promise<ReportTemplate> {
    return request.put(`/finance/reports/templates/${id}/`, data)
  },

  deleteTemplate(id: string): Promise<void> {
    return request.delete(`/finance/reports/templates/${id}/`)
  },

  duplicateTemplate(id: string): Promise<ReportTemplate> {
    return request.post(`/finance/reports/templates/${id}/duplicate/`)
  },

  // Report Generation
  generateReport(templateId: string, data: {
    parameters: Record<string, any>
    format: OutputFormat
  }): Promise<ReportGeneration> {
    return request.post(`/finance/reports/templates/${templateId}/generate/`, data)
  },

  getGeneration(id: string): Promise<ReportGeneration> {
    return request.get(`/finance/reports/generations/${id}/`)
  },

  downloadReport(generationId: string): Promise<Blob> {
    return request.get(`/finance/reports/generations/${generationId}/download/`, {
      responseType: 'blob'
    })
  },

  getReportData(templateId: string, params: {
    parameters: Record<string, any>
  }): Promise<ReportData> {
    return request.post(`/finance/reports/templates/${templateId}/preview/`, params)
  },

  // Saved Reports
  listSavedReports(params?: {
    templateId?: string
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<SavedReport>> {
    return request.get('/finance/reports/saved/', { params })
  },

  deleteSavedReport(id: string): Promise<void> {
    return request.delete(`/finance/reports/saved/${id}/`)
  },

  // Scheduling
  updateSchedule(templateId: string, config: {
    isScheduled: boolean
    scheduleConfig?: any
  }): Promise<void> {
    return request.put(`/finance/reports/templates/${templateId}/schedule/`, config)
  }
}
```

---

## Component: ReportCenter

```vue
<!-- frontend/src/views/finance/ReportCenter.vue -->
<template>
  <div class="report-center">
    <!-- Report Categories -->
    <el-row :gutter="16" class="category-cards">
      <el-col
        v-for="category in categories"
        :key="category.value"
        :span="6"
      >
        <el-card
          shadow="hover"
          class="category-card"
          :class="{ active: selectedCategory === category.value }"
          @click="handleCategoryClick(category.value)"
        >
          <div class="category-icon" :style="{ backgroundColor: category.color }">
            <el-icon :size="32" color="white">
              <component :is="category.icon" />
            </el-icon>
          </div>
          <div class="category-info">
            <div class="category-name">{{ category.label }}</div>
            <div class="category-count">{{ category.count }} 个报表</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Report Templates -->
    <el-card class="templates-card">
      <template #header>
        <div class="card-header">
          <span>报表模板</span>
          <el-button
            v-if="hasPermission('report.create')"
            type="primary"
            :icon="Plus"
            size="small"
            @click="handleCreateTemplate"
          >
            新建模板
          </el-button>
        </div>
      </template>

      <el-table :data="templates" border>
        <el-table-column prop="name" label="报表名称" min-width="200" />
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column label="输出格式" width="150">
          <template #default="{ row }">
            <el-space>
              <el-tag
                v-for="format in row.outputFormats"
                :key="format"
                size="small"
              >
                {{ getFormatLabel(format) }}
              </el-tag>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column label="定时任务" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.isScheduled" type="success" size="small">已启用</el-tag>
            <el-tag v-else type="info" size="small">未启用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isActive" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.isActive"
              @change="handleToggleActive(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="handleGenerate(row)"
            >
              生成
            </el-button>
            <el-button
              link
              type="primary"
              @click="handlePreview(row)"
            >
              预览
            </el-button>
            <el-button
              link
              type="primary"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-dropdown @command="(cmd) => handleCommand(cmd, row)">
              <el-button link type="primary">
                更多
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="schedule">定时配置</el-dropdown-item>
                  <el-dropdown-item command="duplicate">复制</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Recent Reports -->
    <el-card class="saved-reports-card">
      <template #header>
        <div class="card-header">
          <span>最近生成的报表</span>
          <el-button link @click="handleViewAllReports">查看全部</el-button>
        </div>
      </template>

      <el-table :data="savedReports" border>
        <el-table-column prop="reportName" label="报表名称" min-width="200" />
        <el-table-column prop="templateName" label="模板" width="150" />
        <el-table-column label="格式" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ getFormatLabel(row.format) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fileSize" label="文件大小" width="100">
          <template #default="{ row }">{{ formatFileSize(row.fileSize) }}</template>
        </el-table-column>
        <el-table-column prop="generatedAt" label="生成时间" width="160" />
        <el-table-column prop="generatedBy" label="生成人" width="100" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="handleDownload(row)"
            >
              下载
            </el-button>
            <el-button
              link
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Generate Dialog -->
    <ReportGenerateDialog
      v-model:visible="generateVisible"
      :template="currentTemplate"
      @generated="handleReportGenerated"
    />

    <!-- Preview Dialog -->
    <ReportPreviewDialog
      v-model:visible="previewVisible"
      :template="currentTemplate"
    />

    <!-- Template Form Dialog -->
    <TemplateFormDialog
      v-model:visible="templateFormVisible"
      :template="editingTemplate"
      @success="fetchTemplates"
    />

    <!-- Schedule Dialog -->
    <ScheduleConfigDialog
      v-model:visible="scheduleVisible"
      :template="currentTemplate"
      @success="fetchTemplates"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  Plus,
  DataAnalysis,
  TrendCharts,
  Goods,
  Box,
  Calendar,
  Document
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reportApi } from '@/api/finance_reports'
import ReportGenerateDialog from '../components/ReportGenerateDialog.vue'
import ReportPreviewDialog from '../components/ReportPreviewDialog.vue'
import TemplateFormDialog from '../components/TemplateFormDialog.vue'
import ScheduleConfigDialog from '../components/ScheduleConfigDialog.vue'
import type { ReportTemplate, SavedReport, OutputFormat, ReportCategory } from '@/types/finance_reports'

const selectedCategory = ref<ReportCategory | ''>('')
const templates = ref<ReportTemplate[]>([])
const savedReports = ref<SavedReport[]>([])

const generateVisible = ref(false)
const previewVisible = ref(false)
const templateFormVisible = ref(false)
const scheduleVisible = ref(false)

const currentTemplate = ref<ReportTemplate | null>(null)
const editingTemplate = ref<ReportTemplate | null>(null)

const categories = [
  {
    value: ReportCategory.ASSET_SUMMARY,
    label: '资产汇总',
    icon: DataAnalysis,
    color: '#409eff',
    count: 0
  },
  {
    value: ReportCategory.DEPRECIATION,
    label: '折旧报表',
    icon: TrendCharts,
    color: '#67c23a',
    count: 0
  },
  {
    value: ReportCategory.CONSUMABLE,
    label: '耗材报表',
    icon: Goods,
    color: '#e6a23c',
    count: 0
  },
  {
    value: ReportCategory.INVENTORY,
    label: '盘点报表',
    icon: Box,
    color: '#909399',
    count: 0
  },
  {
    value: ReportCategory.FINANCIAL,
    label: '财务报表',
    icon: Calendar,
    color: '#f56c6c',
    count: 0
  }
]

const fetchTemplates = async () => {
  const data = await reportApi.listTemplates({
    category: selectedCategory.value || undefined,
    isActive: true
  })
  templates.value = data

  // Update category counts
  const allTemplates = await reportApi.listTemplates()
  categories.forEach(cat => {
    cat.count = allTemplates.filter(t => t.category === cat.value).length
  })
}

const fetchSavedReports = async () => {
  const data = await reportApi.listSavedReports({
    pageSize: 10
  })
  savedReports.value = data.results
}

const handleCategoryClick = (category: ReportCategory) => {
  if (selectedCategory.value === category) {
    selectedCategory.value = ''
  } else {
    selectedCategory.value = category
  }
  fetchTemplates()
}

const getFormatLabel = (format: OutputFormat) => {
  const labels: Record<OutputFormat, string> = {
    xlsx: 'Excel',
    pdf: 'PDF',
    csv: 'CSV',
    html: 'HTML'
  }
  return labels[format] || format
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const handleCreateTemplate = () => {
  editingTemplate.value = null
  templateFormVisible.value = true
}

const handleGenerate = (template: ReportTemplate) => {
  currentTemplate.value = template
  generateVisible.value = true
}

const handlePreview = (template: ReportTemplate) => {
  currentTemplate.value = template
  previewVisible.value = true
}

const handleEdit = (template: ReportTemplate) => {
  editingTemplate.value = template
  templateFormVisible.value = true
}

const handleToggleActive = async (template: ReportTemplate) => {
  await reportApi.updateTemplate(template.id, { isActive: template.isActive })
  ElMessage.success(template.isActive ? '已启用' : '已禁用')
}

const handleCommand = async (command: string, template: ReportTemplate) => {
  currentTemplate.value = template

  switch (command) {
    case 'schedule':
      scheduleVisible.value = true
      break
    case 'duplicate':
      await reportApi.duplicateTemplate(template.id)
      ElMessage.success('复制成功')
      fetchTemplates()
      break
    case 'delete':
      try {
        await ElMessageBox.confirm('确认删除此报表模板？', '警告')
        await reportApi.deleteTemplate(template.id)
        ElMessage.success('删除成功')
        fetchTemplates()
      } catch {
        // User cancelled
      }
      break
  }
}

const handleReportGenerated = () => {
  fetchSavedReports()
}

const handleViewAllReports = () => {
  // Navigate to reports list
}

const handleDownload = async (report: SavedReport) => {
  try {
    const blob = await reportApi.downloadReport(report.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = report.reportName
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败')
  }
}

const handleDelete = async (report: SavedReport) => {
  try {
    await ElMessageBox.confirm('确认删除此报表？', '警告')
    await reportApi.deleteSavedReport(report.id)
    ElMessage.success('删除成功')
    fetchSavedReports()
  } catch {
    // User cancelled
  }
}

const hasPermission = (permission: string) => {
  // Implement permission check
  return true
}

onMounted(() => {
  fetchTemplates()
  fetchSavedReports()
})
</script>

<style scoped>
.report-center {
  padding: 20px;
}

.category-cards {
  margin-bottom: 20px;
}

.category-card {
  cursor: pointer;
  transition: all 0.3s;
}

.category-card:hover {
  transform: translateY(-4px);
}

.category-card.active {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.category-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  margin-bottom: 12px;
}

.category-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.category-count {
  font-size: 13px;
  color: #909399;
}

.templates-card,
.saved-reports-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/finance_reports.ts` | Finance reports type definitions |
| `frontend/src/api/finance_reports.ts` | Finance reports API service |
| `frontend/src/views/finance/ReportCenter.vue` | Report center main page |
| `frontend/src/views/finance/ReportList.vue` | Saved reports list |
| `frontend/src/components/finance/ReportGenerateDialog.vue` | Report generation dialog |
| `frontend/src/components/finance/ReportPreviewDialog.vue` | Report preview dialog |
| `frontend/src/components/finance/TemplateFormDialog.vue` | Template form dialog |
| `frontend/src/components/finance/ScheduleConfigDialog.vue` | Schedule configuration dialog |
| `frontend/src/components/finance/ReportViewer.vue` | Report viewer component |
