<template>
  <div
    v-loading="loading"
    class="dynamic-detail-page"
  >
    <div
      v-if="loadError"
      class="load-error"
    >
      <el-result
        icon="error"
        :title="t('common.messages.loadFailed')"
        :sub-title="loadError"
      >
        <template #extra>
          <el-button
            type="primary"
            @click="retryLoad"
          >
            {{ t('common.actions.refresh') }}
          </el-button>
          <el-button @click="$router.back()">
            {{ t('common.actions.back') }}
          </el-button>
        </template>
      </el-result>
    </div>

    <div
      v-else-if="!canView"
      class="load-error"
    >
      <el-result
        icon="warning"
        :title="t('common.messages.permissionDenied')"
        :sub-title="t('common.messages.permissionDeniedHint')"
      >
        <template #extra>
          <el-button @click="$router.back()">
            {{ t('common.actions.back') }}
          </el-button>
        </template>
      </el-result>
    </div>

    <div v-else>
      <CommonDynamicDetailPage
        ref="detailPageRef"
        :object-code="objectCode"
        :record-id="recordId"
        :show-edit="canEdit"
        :show-delete="canDelete"
        :object-name="objectMetadata?.name || objectMetadata?.nameEn"
        :object-icon="objectMetadata?.icon"
        @related-record-click="handleRelatedRecordClick"
        @related-record-edit="handleRelatedRecordEdit"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import CommonDynamicDetailPage from '@/components/common/DynamicDetailPage.vue'
import { createObjectClient, type ObjectMetadata } from '@/api/dynamic'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import { deriveObjectCodeFromRelationCode } from '@/platform/reference/relationObjectCode'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const objectCode = ref<string>((route.params.code as string) || '')
const recordId = ref<string>((route.params.id as string) || '')
const metadataPermissions = ref<ObjectMetadata['permissions'] | null>(null)
const objectMetadata = ref<ObjectMetadata | null>(null)
const runtimePermissions = ref<RuntimePermissions | null>(null)
const loading = ref(false)
const loadError = ref<string | null>(null)
const detailPageRef = ref<any>(null)

const apiClient = computed(() => createObjectClient(objectCode.value))

const effectivePermissions = computed<RuntimePermissions>(() => {
  return runtimePermissions.value || metadataPermissions.value || {
    view: true,
    add: true,
    change: true,
    delete: true
  }
})

const canDelete = computed(() => {
  return effectivePermissions.value.delete
})

const canEdit = computed(() => {
  return effectivePermissions.value.change
})

const canView = computed(() => {
  return effectivePermissions.value.view !== false
})

const buildFallbackMetadata = (): ObjectMetadata => ({
  code: objectCode.value,
  name: objectCode.value,
  isHardcoded: true,
  enableWorkflow: false,
  enableVersion: false,
  enableSoftDelete: true,
  fields: [],
  layouts: {},
  permissions: {
    view: true,
    add: true,
    change: true,
    delete: true
  }
} as ObjectMetadata)

const loadMetadata = async () => {
  loading.value = true
  loadError.value = null
  try {
    const [runtimeResult, metadataResult] = await Promise.allSettled([
      // Detail/edit now share one layout model. Use edit runtime contract as source of truth.
      resolveRuntimeLayout(objectCode.value, 'edit', { includeRelations: false }),
      apiClient.value.getMetadata()
    ])

    runtimePermissions.value = runtimeResult.status === 'fulfilled'
      ? (runtimeResult.value.permissions || null)
      : null

    if (metadataResult.status === 'fulfilled') {
      const metadata = (metadataResult.value as ObjectMetadata) || buildFallbackMetadata()
      metadataPermissions.value = metadata.permissions || null
      objectMetadata.value = metadata
    } else {
      metadataPermissions.value = buildFallbackMetadata().permissions
      console.warn('[DynamicDetailPage] Metadata load failed, runtime permissions remain active')
    }

    if (runtimeResult.status === 'rejected' && metadataResult.status === 'rejected') {
      const runtimeError = runtimeResult.reason instanceof Error ? runtimeResult.reason.message : ''
      const metadataError = metadataResult.reason instanceof Error ? metadataResult.reason.message : ''
      loadError.value = metadataError || runtimeError || t('system.businessObject.messages.loadMetadataFailed')
    }
  } finally {
    loading.value = false
  }
}

const retryLoad = () => {
  loadMetadata()
}

const resolveRelationObjectCode = (relationCode: string, targetObjectCode?: string): string => {
  const explicitTarget = String(targetObjectCode || '').trim()
  if (explicitTarget) return explicitTarget
  return deriveObjectCodeFromRelationCode(relationCode)
}

const handleRelatedRecordClick = (relationCode: string, record: any, targetObjectCode?: string): void => {
  const relatedCode = resolveRelationObjectCode(relationCode, targetObjectCode)
  if (!relatedCode || !record?.id) return
  router.push(`/objects/${encodeURIComponent(relatedCode)}/${encodeURIComponent(String(record.id))}`)
}

const handleRelatedRecordEdit = (relationCode: string, record: any, targetObjectCode?: string): void => {
  const relatedCode = resolveRelationObjectCode(relationCode, targetObjectCode)
  if (!relatedCode || !record?.id) return
  router.push(`/objects/${encodeURIComponent(relatedCode)}/${encodeURIComponent(String(record.id))}/edit`)
}

onMounted(() => {
  loadMetadata()
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.dynamic-detail-page {
  height: 100%;
  background-color: $bg-body;
}
</style>
