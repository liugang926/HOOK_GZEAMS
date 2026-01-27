<template>
  <div class="asset-form-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑资产' : '新增资产' }}</span>
          <el-button @click="goBack">返回</el-button>
        </div>
      </template>

      <BaseForm
        ref="baseFormRef"
        v-model="form"
        :fields="fields"
        :rules="rules"
        v-loading="loading"
      />

      <template #footer>
        <div class="form-footer">
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormRules } from 'element-plus'
import { assetApi, categoryApi, locationApi } from '@/api/assets'
// import { userApi, deptApi } from '@/api/system' // Assuming these exist or mock them
import BaseForm from '@/components/common/BaseForm.vue'
import type { FormField } from '@/types/models'

const route = useRoute()
const router = useRouter()
const baseFormRef = ref()
const loading = ref(false)
const submitting = ref(false)

const form = ref({
  assetCode: '',
  assetName: '',
  assetCategory: '',
  assetStatus: 'idle',
  brand: '',
  model: '',
  unit: '',
  serialNumber: '',
  purchasePrice: 0,
  purchaseDate: '',
  supplier: '',
  invoiceNo: '',
  department: '',
  custodian: '',
  location: '',
  remarks: ''
})

const rules: FormRules = {
  assetCode: [{ required: true, message: '请输入资产编码', trigger: 'blur' }],
  assetName: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  assetCategory: [{ required: true, message: '请选择资产分类', trigger: 'change' }]
}

// Option data
const categories = ref<any[]>([])
const suppliers = ref<any[]>([])
const departments = ref<any[]>([])
const users = ref<any[]>([])
const locationTree = ref<any[]>([])

const isEdit = computed(() => !!route.params.id)

// Fields Definition
const fields = computed<FormField[]>(() => [
  { type: 'divider', prop: 'basic_info', label: '基本信息', span: 24 },
  { prop: 'assetCode', label: '资产编码', type: 'input', placeholder: '请输入资产编码' },
  { prop: 'assetName', label: '资产名称', type: 'input', placeholder: '请输入资产名称' },
  { 
    prop: 'assetCategory', 
    label: '资产分类', 
    type: 'select', 
    placeholder: '请选择资产分类',
    options: categories.value.map(c => ({ label: c.name, value: c.id }))
  },
  { 
    prop: 'assetStatus', 
    label: '资产状态', 
    type: 'select', 
    placeholder: '请选择状态',
    options: [
      { label: '闲置', value: 'idle' },
      { label: '在用', value: 'in_use' },
      { label: '维修中', value: 'maintenance' },
      { label: '报废', value: 'scrapped' }
    ]
  },
  { prop: 'brand', label: '品牌', type: 'input', placeholder: '请输入品牌' },
  { prop: 'model', label: '规格型号', type: 'input', placeholder: '请输入规格型号' },
  { prop: 'unit', label: '计量单位', type: 'input', placeholder: '请输入计量单位' },
  { prop: 'serialNumber', label: '序列号', type: 'input', placeholder: '请输入序列号' },
  
  { type: 'divider', prop: 'value_info', label: '价值信息', span: 24 },
  { 
    prop: 'purchasePrice', 
    label: '原值', 
    type: 'number', 
    placeholder: '请输入原值',
    props: { min: 0, precision: 2 }
  },
  { prop: 'purchaseDate', label: '购置日期', type: 'date', placeholder: '请选择购置日期' },
  { 
    prop: 'supplier', 
    label: '供应商', 
    type: 'select', 
    placeholder: '请选择供应商', 
    options: suppliers.value,
    props: { filterable: true, clearable: true }
  },
  { prop: 'invoiceNo', label: '发票号', type: 'input', placeholder: '请输入发票号' },

  { type: 'divider', prop: 'use_info', label: '使用信息', span: 24 },
  { 
    prop: 'department', 
    label: '使用部门', 
    type: 'select', 
    placeholder: '请选择部门',
    options: departments.value,
    props: { filterable: true, clearable: true }
  },
  { 
    prop: 'custodian', 
    label: '使用人', 
    type: 'select', 
    placeholder: '请选择使用人',
    options: users.value,
    props: { filterable: true, clearable: true }
  },
  { 
    prop: 'location', 
    label: '存放位置', 
    type: 'tree-select', 
    placeholder: '请选择存放位置',
    options: locationTree.value,
    props: { clearable: true, checkStrictly: true, props: { label: 'name', value: 'id', children: 'children' } }
  },

  { prop: 'remarks', label: '备注', type: 'textarea', placeholder: '请输入备注', span: 24 }
])

onMounted(async () => {
  await fetchOptions()
  if (isEdit.value) {
    await fetchAssetDetail()
  }
})

const fetchOptions = async () => {
  try {
    const catData = await categoryApi.list()
    categories.value = Array.isArray(catData) ? catData : (catData.results || [])

    const locData = await locationApi.tree()
    locationTree.value = buildTree(locData || [])

    // TODO: Load others from API
    // suppliers.value = ...
    // departments.value = ...
    // users.value = ...
  } catch (error) {
    console.error('Failed to fetch options:', error)
  }
}

const buildTree = (flatData: any[]) => {
  const map = new Map()
  const tree: any[] = []

  flatData.forEach(item => {
    map.set(item.id, { ...item, children: [] })
  })

  flatData.forEach(item => {
    const node = map.get(item.id)
    if (item.parentId) {
      const parent = map.get(item.parentId)
      if (parent) {
        parent.children.push(node)
      } else {
        tree.push(node)
      }
    } else {
      tree.push(node)
    }
  })

  return tree
}

const fetchAssetDetail = async () => {
  const id = route.params.id
  loading.value = true
  try {
    const data = await assetApi.get(id)
    // Merge data into form, ensuring all keys exist
    Object.keys(form.value).forEach(key => {
      if (data[key] !== undefined) {
        form.value[key] = data[key]
      }
    })
  } catch (error) {
    console.error('Failed to load asset:', error)
    ElMessage.error('加载资产详情失败')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!baseFormRef.value) return

  const valid = await baseFormRef.value.validate()
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      await assetApi.update(route.params.id as string, form.value)
      ElMessage.success('更新成功')
    } else {
      await assetApi.create(form.value)
      ElMessage.success('创建成功')
    }
    goBack()
  } catch (error) {
    console.error('Submit failed:', error)
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  router.push('/assets')
}
</script>

<style scoped>
.asset-form-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 10px;
}
</style>
