<template>
  <div class="asset-detail-wrapper">
    <!--
      AssetDetail.vue - Reference implementation for metadata-driven detail pages

      This component demonstrates two approaches:
      1. DynamicDetailPage: Fully metadata-driven (recommended for new objects)
      2. BaseDetailPage: Custom sections with explicit configuration

      For Asset, we use BaseDetailPage with custom sections for backward compatibility.
      New business objects should use DynamicDetailPage instead.
    -->
    <BaseDetailPage
      :title="$t('assets.detail.title') + ' - ' + assetName"
      :sections="detailSections"
      :data="assetData"
      :loading="loading"
      :audit-info="auditInfo"
      object-code="Asset"
      :relation-group-scope-id="relationGroupScopeId"
      :show-related-objects="true"
      @edit="handleEdit"
      @delete="handleDelete"
      @back="goBack"
      @related-record-click="handleRelatedRecordClick"
      @related-record-edit="handleRelatedRecordEdit"
    >
      <!-- Custom QR Code display slot -->
      <template #field-qrCode="{ value }">
        <div class="qr-code-display">
          <el-image
            v-if="value && value !== '-'"
            :src="value"
            fit="contain"
            style="width: 80px; height: 80px"
            :preview-src-list="[value]"
          />
          <span v-else>-</span>
        </div>
      </template>

      <!-- Custom images field slot -->
      <template #field-images="{ value }">
        <div class="images-display">
          <div
            v-if="Array.isArray(value) && value.length > 0"
            class="image-gallery"
          >
            <el-image
              v-for="(img, idx) in value.slice(0, 4)"
              :key="idx"
              :src="img"
              fit="cover"
              class="gallery-image"
              :preview-src-list="value"
              :initial-index="idx"
            />
            <div
              v-if="value.length > 4"
              class="more-images"
            >
              +{{ value.length - 4 }}
            </div>
          </div>
          <span v-else>-</span>
        </div>
      </template>
    </BaseDetailPage>

    <!--
      To use DynamicDetailPage instead (metadata-driven), uncomment below:

      <DynamicDetailPage
        object-code="Asset"
        :fetch-record="fetchAssetRecord"
        edit-route="/assets/edit/:id"
        back-route="/assets/list"
        @loaded="handleAssetLoaded"
        @related-record-click="handleRelatedRecordClick"
        @related-record-edit="handleRelatedRecordEdit"
      />
    -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import BaseDetailPage from '@/components/common/BaseDetailPage.vue'
import { assetApi } from '@/api/assets'
import { deriveObjectCodeFromRelationCode } from '@/platform/reference/relationObjectCode'
import { buildRecordRelationGroupScopeId } from '@/platform/reference/relationGroupScope'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const assetData = ref<any>({})
const { t } = useI18n()

const assetName = computed(() => assetData.value?.assetName || t('assets.detail.unknownAsset'))
const relationGroupScopeId = computed(() => {
  return buildRecordRelationGroupScopeId(getRouteId(), assetData.value?.assetCode)
})

const auditInfo = computed(() => ({
  createdBy: assetData.value.createdBy?.username || assetData.value.createdBy || 'System',
  createdAt: assetData.value.createdAt || assetData.value.created_at,
  updatedBy: assetData.value.updatedBy?.username || assetData.value.updatedBy || 'System',
  updatedAt: assetData.value.updatedAt || assetData.value.updated_at
}))

// Define sections - using computed to react to language changes
const detailSections = computed(() => [
  {
    name: 'basic',
    title: t('assets.form.sections.basicInfo'),
    icon: 'InfoFilled',
    fields: [
      { prop: 'assetCode', label: t('assets.fields.assetCode'), span: 8 },
      { prop: 'assetName', label: t('assets.fields.assetName'), span: 8 },
      { prop: 'assetCategoryName', label: t('assets.fields.category'), span: 8 },
      { prop: 'assetStatus', label: t('common.labels.status'), type: 'tag', span: 8,
        // Map backend status codes to element-plus types
        // The BaseDetailPage will handle value translation if we provide a formatter or just display the value
        // Ideally we should translate the status value here or in BaseDetailPage
        tagType: { 'idle': 'success', 'in_use': 'primary', 'maintenance': 'warning', 'scrapped': 'danger', 'draft': 'info' },
        formatter: (val: string) => {
          const keyMap: Record<string, string> = {
            draft: 'assets.status.draft',
            in_use: 'assets.status.inUse',
            idle: 'assets.status.idle',
            maintenance: 'assets.status.maintenance',
            scrapped: 'assets.status.scrapped'
          }
          return keyMap[val] ? t(keyMap[val]) : val
        }
      },
      { prop: 'model', label: t('assets.fields.model'), span: 8 },
      { prop: 'brand', label: t('assets.fields.brand'), span: 8 },
      { prop: 'unit', label: t('assets.fields.unit'), span: 8 },
      { prop: 'serialNumber', label: t('assets.fields.serialNumber'), span: 8 },
    ]
  },
  {
    name: 'value',
    title: t('assets.form.sections.valueInfo'),
    icon: 'Money',
    fields: [
      { prop: 'purchasePrice', label: t('assets.fields.purchasePrice'), type: 'currency', span: 8 },
      { prop: 'purchaseDate', label: t('assets.fields.purchaseDate'), type: 'date', span: 8 },
      { prop: 'supplierName', label: t('assets.fields.supplier'), span: 8 },
      { prop: 'invoiceNo', label: t('assets.fields.invoiceNo'), span: 8 }
    ]
  },
  {
    name: 'usage',
    title: t('assets.form.sections.useInfo'),
    icon: 'UserFilled',
    fields: [
      { prop: 'departmentName', label: t('assets.fields.department'), span: 8 },
      { prop: 'custodianName', label: t('assets.fields.user'), span: 8 },
      { prop: 'locationPath', label: t('assets.fields.location'), span: 8 },
    ]
  },
  {
    name: 'image',
    title: t('assets.form.sections.image'),
    icon: 'Picture',
    collapsible: true,
    collapsed: true,
    fields: [
      { prop: 'image', label: t('assets.form.sections.image'), type: 'image', span: 24 }
    ]
  }
])

onMounted(async () => {
  await fetchDetail()
})

const getRouteId = (): string => {
  const { id } = route.params
  return Array.isArray(id) ? (id[0] || '') : (id || '')
}

const fetchDetail = async () => {
  const id = getRouteId()
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
    ElMessage.error(t('assets.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleEdit = () => {
  const id = getRouteId()
  if (!id) return
  router.push(`/assets/${id}?action=edit`)
}

const handleDelete = async () => {
  const id = getRouteId()
  if (!id) return

  try {
    await assetApi.delete(id)
    ElMessage.success(t('common.messages.deleteSuccess'))
    goBack()
  } catch (error) {
    console.error(error)
    ElMessage.error(t('common.messages.deleteFailed'))
  }
}

const goBack = () => {
  router.push('/assets/list')
}

const resolveRelationObjectCode = (relationCode: string, targetObjectCode?: string): string => {
  const explicitTarget = String(targetObjectCode || '').trim()
  if (explicitTarget) return explicitTarget
  return deriveObjectCodeFromRelationCode(relationCode)
}

const handleRelatedRecordClick = (relationCode: string, record: any, targetObjectCode?: string) => {
  const objectCode = resolveRelationObjectCode(relationCode, targetObjectCode)
  if (objectCode && record.id) {
    router.push(`/objects/${encodeURIComponent(objectCode)}/${encodeURIComponent(String(record.id))}`)
  }
}

const handleRelatedRecordEdit = (relationCode: string, record: any, targetObjectCode?: string) => {
  const objectCode = resolveRelationObjectCode(relationCode, targetObjectCode)
  if (objectCode && record.id) {
    router.push(`/objects/${encodeURIComponent(objectCode)}/${encodeURIComponent(String(record.id))}/edit`)
  }
}
</script>

<style scoped lang="scss">
.asset-detail-wrapper {
  height: 100%;
}

.qr-code-display {
  display: flex;
  align-items: center;
}

.images-display {
  .image-gallery {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;

    .gallery-image {
      width: 60px;
      height: 60px;
      border-radius: 4px;
      cursor: pointer;
    }

    .more-images {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 60px;
      height: 60px;
      background-color: #f5f7fa;
      border-radius: 4px;
      font-size: 12px;
      color: #909399;
    }
  }
}
</style>
