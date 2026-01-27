<!--
  AssetFormDialog Component

  Dialog for creating and editing assets with:
  - Form validation
  - Dynamic category/location selection
  - User picker for custodian
  - QR code preview (for new assets)
-->

<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑资产' : '新增资产'"
    width="700px"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:modelValue', $event)"
    @open="handleOpen"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="110px"
      class="asset-form"
    >
      <!-- Basic Information -->
      <div class="form-section">
        <div class="section-title">
          基本信息
        </div>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              label="资产编码"
              prop="code"
            >
              <el-input
                v-model="formData.code"
                placeholder="请输入资产编码"
                :disabled="isEdit && !canEditCode"
                clearable
              >
                <template
                  v-if="!isEdit"
                  #append
                >
                  <el-button
                    :icon="Refresh"
                    @click="generateCode"
                  />
                </template>
              </el-input>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item
              label="资产名称"
              prop="name"
            >
              <el-input
                v-model="formData.name"
                placeholder="请输入资产名称"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              label="资产分类"
              prop="categoryId"
            >
              <el-tree-select
                v-model="formData.categoryId"
                :data="categoryTree"
                :props="{ value: 'id', label: 'name', children: 'children' }"
                placeholder="请选择分类"
                clearable
                check-strictly
                class="full-width"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item
              label="资产状态"
              prop="status"
            >
              <el-select
                v-model="formData.status"
                placeholder="请选择状态"
                class="full-width"
              >
                <el-option
                  v-for="option in statusOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- Purchase Information -->
      <div class="form-section">
        <div class="section-title">
          采购信息
        </div>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              label="采购金额"
              prop="purchasePrice"
            >
              <el-input-number
                v-model="formData.purchasePrice"
                :min="0"
                :precision="2"
                :disabled="isEdit"
                controls-position="right"
                class="full-width"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item
              label="采购日期"
              prop="purchaseDate"
            >
              <el-date-picker
                v-model="formData.purchaseDate"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                :disabled="isEdit"
                class="full-width"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="供应商">
          <el-input
            v-model="formData.supplierName"
            placeholder="请输入供应商名称"
            clearable
          />
        </el-form-item>
      </div>

      <!-- Location & Custodian -->
      <div class="form-section">
        <div class="section-title">
          位置与使用人
        </div>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              label="存放位置"
              prop="locationId"
            >
              <el-tree-select
                v-model="formData.locationId"
                :data="locationTree"
                :props="{ value: 'id', label: 'name', children: 'children' }"
                placeholder="请选择位置"
                clearable
                check-strictly
                class="full-width"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="使用人">
              <UserPicker
                v-model="formData.custodianId"
                placeholder="请选择使用人"
                :show-dept="true"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- Additional Information -->
      <div class="form-section">
        <div class="section-title">
          其他信息
        </div>

        <el-form-item label="规格型号">
          <el-input
            v-model="formData.specification"
            placeholder="请输入规格型号"
            clearable
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </div>

      <!-- QR Code Preview (for new assets) -->
      <div
        v-if="!isEdit && formData.code"
        class="form-section"
      >
        <div class="section-title">
          二维码预览
        </div>
        <div class="qr-preview">
          <div class="qr-placeholder">
            <el-icon><QrCode /></el-icon>
            <span>二维码将在保存后生成</span>
          </div>
        </div>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * AssetFormDialog Component
 *
 * Dialog component for creating and editing assets.
 * Includes form validation and API integration.
 */

import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, QrCode } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import UserPicker from '@/components/common/UserPicker.vue'
import { assetApi } from '@/api/assets'
import { categoryApi, locationApi } from '@/api/assets'
import type { Asset, AssetStatus } from '@/types/assets'

// ============================================================================
// Props & Emits
// ============================================================================

interface Props {
  modelValue: boolean
  asset?: Asset | null
}

const props = withDefaults(defineProps<Props>(), {
  asset: null
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

// ============================================================================
// State
// ============================================================================

const formRef = ref<FormInstance>()
const submitting = ref(false)
const categoryTree = ref<any[]>([])
const locationTree = ref<any[]>([])
const canEditCode = ref(false)

const formData = reactive({
  code: '',
  name: '',
  categoryId: '',
  status: 'draft' as AssetStatus,
  purchasePrice: 0,
  purchaseDate: new Date().toISOString().split('T')[0],
  supplierName: '',
  locationId: '',
  custodianId: '',
  specification: '',
  description: ''
})

// ============================================================================
// Computed
// ============================================================================

const isEdit = computed(() => !!props.asset)

const statusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '使用中', value: 'in_use' },
  { label: '闲置', value: 'idle' },
  { label: '维修中', value: 'maintenance' },
  { label: '已报废', value: 'scrapped' }
]

// ============================================================================
// Form Rules
// ============================================================================

const rules: FormRules = {
  code: [
    { required: true, message: '请输入资产编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9-]+$/, message: '编码只能包含大写字母、数字和连字符', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入资产名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  categoryId: [
    { required: true, message: '请选择资产分类', trigger: 'change' }
  ],
  purchasePrice: [
    { required: true, message: '请输入采购金额', trigger: 'blur' },
    { type: 'number', min: 0, message: '金额不能为负数', trigger: 'blur' }
  ],
  purchaseDate: [
    { required: true, message: '请选择采购日期', trigger: 'change' }
  ]
}

// ============================================================================
// Methods
// ============================================================================

/**
 * Handle dialog open
 */
const handleOpen = async () => {
  // Load options
  await Promise.all([
    loadCategories(),
    loadLocations()
  ])

  if (props.asset) {
    // Edit mode - populate form
    Object.assign(formData, {
      code: props.asset.code,
      name: props.asset.name,
      categoryId: props.asset.categoryId || '',
      status: props.asset.status,
      purchasePrice: props.asset.purchasePrice,
      purchaseDate: props.asset.purchaseDate,
      supplierName: props.asset.supplierName || '',
      locationId: props.asset.locationId || '',
      custodianId: props.asset.custodianId || '',
      specification: props.asset.specification || '',
      description: props.asset.description || ''
    })
  } else {
    // Create mode - reset form
    resetForm()
  }
}

/**
 * Load category tree
 */
const loadCategories = async () => {
  try {
    const categories = await categoryApi.tree()
    categoryTree.value = buildTree(categories)
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

/**
 * Load location tree
 */
const loadLocations = async () => {
  try {
    const locations = await locationApi.tree()
    locationTree.value = buildTree(locations)
  } catch (error) {
    console.error('Failed to load locations:', error)
  }
}

/**
 * Build tree structure from flat list
 */
const buildTree = (items: any[], parentId: string | null = null): any[] => {
  return items
    .filter(item => item.parentId === parentId)
    .map(item => ({
      ...item,
      children: buildTree(items, item.id)
    }))
}

/**
 * Generate asset code
 */
const generateCode = async () => {
  try {
    const code = await assetApi.generateCode()
    formData.code = code
  } catch (error) {
    ElMessage.warning('自动生成编码失败，请手动输入')
  }
}

/**
 * Reset form to default values
 */
const resetForm = () => {
  Object.assign(formData, {
    code: '',
    name: '',
    categoryId: '',
    status: 'draft' as AssetStatus,
    purchasePrice: 0,
    purchaseDate: new Date().toISOString().split('T')[0],
    supplierName: '',
    locationId: '',
    custodianId: '',
    specification: '',
    description: ''
  })
  formRef.value?.clearValidate()
}

/**
 * Handle submit
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    const submitData = {
      ...formData,
      purchasePrice: Number(formData.purchasePrice)
    }

    if (isEdit.value && props.asset) {
      await assetApi.update(props.asset.id, submitData)
      ElMessage.success('更新成功')
    } else {
      await assetApi.create(submitData)
      ElMessage.success('创建成功')
    }

    emit('success')
    emit('update:modelValue', false)
  } catch (error: any) {
    if (error !== false) {
      // Validation error returns false
      console.error('Submit failed:', error)
      ElMessage.error(error?.message || '操作失败，请重试')
    }
  } finally {
    submitting.value = false
  }
}

/**
 * Handle cancel
 */
const handleCancel = () => {
  emit('update:modelValue', false)
}
</script>

<style scoped lang="scss">
.asset-form {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 10px;
}

.form-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px dashed #ebeef5;

  &:last-of-type {
    border-bottom: none;
  }
}

.section-title {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 16px;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}

.full-width {
  width: 100%;
}

.qr-preview {
  display: flex;
  justify-content: center;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.qr-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #909399;

  .el-icon {
    font-size: 48px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-form-item__label) {
  font-weight: 400;
}
</style>
