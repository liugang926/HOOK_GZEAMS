<template>
  <div class="asset-form-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? $t('assets.form.edit') : $t('assets.form.create') }}</span>
          <el-button @click="goBack">
            {{ $t('common.actions.back') }}
          </el-button>
        </div>
      </template>

      <BaseForm
        ref="baseFormRef"
        v-model="form"
        v-loading="loading"
        :fields="fields"
        :rules="rules"
      />

      <template #footer>
        <div class="form-footer">
          <el-button @click="goBack">
            {{ $t('common.actions.cancel') }}
          </el-button>
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            {{ isEdit ? $t('common.actions.save') : $t('common.actions.create') }}
          </el-button>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
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
const { t } = useI18n()

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

const rules = computed<FormRules>(() => ({
  assetCode: [{ required: true, message: t('common.validation.required', { field: t('assets.fields.assetCode') }), trigger: 'blur' }],
  assetName: [{ required: true, message: t('common.validation.required', { field: t('assets.fields.assetName') }), trigger: 'blur' }],
  assetCategory: [{ required: true, message: t('common.validation.required', { field: t('assets.fields.category') }), trigger: 'change' }]
}))

// Option data
const categories = ref<any[]>([])
const suppliers = ref<any[]>([])
const departments = ref<any[]>([])
const users = ref<any[]>([])
const locationTree = ref<any[]>([])

const isEdit = computed(() => !!route.params.id)

// Fields Definition
const fields = computed<FormField[]>(() => [
  { type: 'divider', prop: 'basic_info', label: t('assets.form.sections.basicInfo'), span: 24 },
  { prop: 'assetCode', label: t('assets.fields.assetCode'), type: 'input', placeholder: t('common.placeholders.input', { field: t('assets.fields.assetCode') }) },
  { prop: 'assetName', label: t('assets.fields.assetName'), type: 'input', placeholder: t('common.placeholders.input', { field: t('assets.fields.assetName') }) },
  { 
    prop: 'assetCategory', 
    label: t('assets.fields.category'), 
    type: 'select', 
    placeholder: t('common.placeholders.select', { field: t('assets.fields.category') }),
    options: categories.value.map(c => ({ label: c.name, value: c.id }))
  },
  { 
    prop: 'assetStatus', 
    label: t('common.labels.status'), 
    type: 'select', 
    placeholder: t('common.placeholders.select', { field: t('common.labels.status') }),
    options: [
      { label: t('assets.status.idle'), value: 'idle' },
      { label: t('assets.status.inUse'), value: 'in_use' },
      { label: t('assets.status.maintenance'), value: 'maintenance' },
      { label: t('assets.status.scrapped'), value: 'scrapped' }
    ]
  },
  { prop: 'brand', label: t('assets.fields.brand'), type: 'input', placeholder: t('common.placeholders.input', { field: t('assets.fields.brand') }) },
  { prop: 'model', label: t('assets.fields.model'), type: 'input', placeholder: t('common.placeholders.input', { field: t('assets.fields.model') }) },
  { prop: 'unit', label: t('assets.fields.unit'), type: 'input', placeholder: t('common.placeholders.input', { field: t('assets.fields.unit') }) },
  { prop: 'serialNumber', label: t('assets.fields.serialNumber'), type: 'input', placeholder: t('common.placeholders.input', { field: t('assets.fields.serialNumber') }) },
  
  { type: 'divider', prop: 'value_info', label: t('assets.form.sections.valueInfo'), span: 24 },
  { 
    prop: 'purchasePrice', 
    label: t('assets.fields.purchasePrice'), 
    type: 'number', 
    placeholder: t('common.placeholders.input', { field: t('assets.fields.purchasePrice') }),
    props: { min: 0, precision: 2 }
  },
  { prop: 'purchaseDate', label: t('assets.fields.purchaseDate'), type: 'date', placeholder: t('common.placeholders.select', { field: t('assets.fields.purchaseDate') }) },
  { 
    prop: 'supplier', 
    label: t('assets.fields.supplier'), 
    type: 'select', 
    placeholder: t('common.placeholders.select', { field: t('assets.fields.supplier') }), 
    options: suppliers.value,
    props: { filterable: true, clearable: true }
  },
  { prop: 'invoiceNo', label: t('assets.fields.invoiceNo'), type: 'input', placeholder: t('common.placeholders.input', { field: t('assets.fields.invoiceNo') }) },

  { type: 'divider', prop: 'use_info', label: t('assets.form.sections.useInfo'), span: 24 },
  { 
    prop: 'department', 
    label: t('assets.fields.department'), 
    type: 'select', 
    placeholder: t('common.placeholders.select', { field: t('assets.fields.department') }),
    options: departments.value,
    props: { filterable: true, clearable: true }
  },
  { 
    prop: 'custodian', 
    label: t('assets.fields.user'), 
    type: 'select', 
    placeholder: t('common.placeholders.select', { field: t('assets.fields.user') }),
    options: users.value,
    props: { filterable: true, clearable: true }
  },
  { 
    prop: 'location', 
    label: t('assets.fields.location'), 
    type: 'tree-select', 
    placeholder: t('common.placeholders.select', { field: t('assets.fields.location') }),
    options: locationTree.value,
    props: { clearable: true, checkStrictly: true, props: { label: 'name', value: 'id', children: 'children' } }
  },

  { prop: 'remarks', label: t('common.labels.remark'), type: 'textarea', placeholder: t('common.placeholders.input', { field: t('common.labels.remark') }), span: 24 }
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
    ElMessage.error(t('assets.messages.loadFailed'))
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
      ElMessage.success(t('common.messages.updateSuccess'))
    } else {
      await assetApi.create(form.value)
      ElMessage.success(t('common.messages.createSuccess'))
    }
    goBack()
  } catch (error) {
    console.error('Submit failed:', error)
    ElMessage.error(isEdit.value ? t('common.messages.updateFailed') : t('common.messages.createFailed'))
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
