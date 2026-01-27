<template>
  <div class="asset-detail-wrapper">
    <BaseDetailPage
      :title="`资产详情 - ${assetName}`"
      :sections="detailSections"
      :data="assetData"
      :loading="loading"
      :audit-info="auditInfo"
      @edit="handleEdit"
      @delete="handleDelete"
      @back="goBack"
    >
      <!-- Custom slot for QR code in Basic Info if needed, or just use image field type -->
    </BaseDetailPage>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import BaseDetailPage from '@/components/common/BaseDetailPage.vue'
import { assetApi } from '@/api/assets'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const assetData = ref<any>({})

const assetName = computed(() => assetData.value?.assetName || '未知资产')

const auditInfo = computed(() => ({
  createdBy: assetData.value.createdBy?.username || 'System',
  createdAt: assetData.value.createdAt,
  updatedBy: assetData.value.updatedBy?.username || 'System',
  updatedAt: assetData.value.updatedAt
}))

// Define sections - using camelCase after toCamelCase transformation
const detailSections = [
  {
    name: 'basic',
    title: '基本信息',
    icon: 'InfoFilled',
    fields: [
      { prop: 'assetCode', label: '资产编码', span: 8 },
      { prop: 'assetName', label: '资产名称', span: 8 },
      { prop: 'assetCategoryName', label: '资产分类', span: 8 },
      { prop: 'assetStatusDisplay', label: '状态', type: 'tag', span: 8,
        tagType: { '闲置': 'success', '在用': 'primary', '维修中': 'warning', '报废': 'danger' }
      },
      { prop: 'model', label: '规格型号', span: 8 },
      { prop: 'brand', label: '品牌', span: 8 },
      { prop: 'unit', label: '计量单位', span: 8 },
      { prop: 'serialNumber', label: '序列号', span: 8 },
    ]
  },
  {
    name: 'value',
    title: '价值信息',
    icon: 'Money',
    fields: [
      { prop: 'purchasePrice', label: '原值', type: 'currency', span: 8 },
      { prop: 'purchaseDate', label: '购置日期', type: 'date', span: 8 },
      { prop: 'supplierName', label: '供应商', span: 8 },
      { prop: 'invoiceNo', label: '发票号', span: 8 },
    ]
  },
  {
    name: 'usage',
    title: '使用信息',
    icon: 'UserFilled',
    fields: [
      { prop: 'departmentName', label: '使用部门', span: 8 },
      { prop: 'custodianName', label: '使用人', span: 8 },
      { prop: 'locationPath', label: '存放地点', span: 8 },
    ]
  },
  {
    name: 'image',
    title: '图片',
    icon: 'Picture',
    collapsible: true,
    fields: [
      { prop: 'image', label: '资产图片', type: 'image', span: 24 }
    ]
  }
]

onMounted(async () => {
    await fetchDetail()
})

const fetchDetail = async () => {
  const id = route.params.id
  if (!id) return

  loading.value = true
  try {
    const data = await assetApi.get(id)
    // Backend returns flat fields (transformed to camelCase by interceptor)
    // Add custodianName if custodian exists
    assetData.value = {
        ...data,
        custodianName: data.custodian?.username || data.user?.username || '-'
    }
  } catch (error) {
    console.error('Failed to load asset:', error)
    ElMessage.error('加载资产详情失败')
  } finally {
    loading.value = false
  }
}

const handleEdit = () => {
  router.push(`/assets/edit/${route.params.id}`)
}

const handleDelete = async () => {
  try {
    await assetApi.delete(route.params.id as string)
    ElMessage.success('删除成功')
    goBack()
  } catch (error) {
    console.error(error)
    ElMessage.error('删除失败')
  }
}

const goBack = () => {
  router.push('/assets/list')
}
</script>

<style scoped>
.asset-detail-wrapper {
  height: 100%;
}
</style>
