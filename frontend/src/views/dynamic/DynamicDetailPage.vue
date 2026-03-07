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
        @loaded="handleRecordLoaded"
      >
        <!-- Lifecycle: action-bar — StatusActionBar replaces default buttons -->
        <template v-if="isLifecycle" #action-bar>
          <StatusActionBar
            :actions="lifecycleRendererRef?.workflowActions || []"
            :status="lifecycleRecordData?.status || ''"
            @action-success="handleLifecycleRefresh"
          />
        </template>

        <!-- Lifecycle: header-extra — el-steps workflow progress -->
        <template v-if="isLifecycle && lifecycleExtension?.workflowSteps" #header-extra>
          <el-card class="lifecycle-steps-card" shadow="never">
            <el-steps
              :active="lifecycleRendererRef?.getStepIndex(lifecycleRecordData?.status || '') || 0"
              finish-status="success"
            >
              <el-step
                v-for="step in lifecycleExtension.workflowSteps.steps"
                :key="step"
                :title="t(`${lifecycleExtension.workflowSteps.i18nPrefix}.${step}`)"
              />
            </el-steps>
          </el-card>
        </template>

        <!-- Lifecycle: after-sections — SubTable + cost breakdown -->
        <template v-if="isLifecycle" #after-sections>
          <LifecycleDetailRenderer
            ref="lifecycleRendererRef"
            :object-code="objectCode"
            :record-id="recordId"
            :record-data="lifecycleRecordData"
            @refresh="handleLifecycleRefresh"
          />
        </template>
      </CommonDynamicDetailPage>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import CommonDynamicDetailPage from '@/components/common/DynamicDetailPage.vue'
import StatusActionBar from '@/components/common/StatusActionBar.vue'
import LifecycleDetailRenderer from '@/components/lifecycle/LifecycleDetailRenderer.vue'
import { createObjectClient, type ObjectMetadata } from '@/api/dynamic'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import { deriveObjectCodeFromRelationCode } from '@/platform/reference/relationObjectCode'
import { hasLifecycleExtension, getLifecycleExtension } from '@/platform/lifecycle/lifecycleDetailExtensions'

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
const lifecycleRendererRef = ref<InstanceType<typeof LifecycleDetailRenderer> | null>(null)
const lifecycleRecordData = ref<Record<string, any> | null>(null)

const apiClient = computed(() => createObjectClient(objectCode.value))

// ── Lifecycle extension detection ──────────────────────────────────

const isLifecycle = computed(() => hasLifecycleExtension(objectCode.value))
const lifecycleExtension = computed(() => getLifecycleExtension(objectCode.value))

const handleRecordLoaded = (record: any) => {
  if (isLifecycle.value) {
    lifecycleRecordData.value = record
  }
}

const handleLifecycleRefresh = async () => {
  if (detailPageRef.value?.refresh) {
    await detailPageRef.value.refresh()
  }
}

// ── Permissions ────────────────────────────────────────────────────

const effectivePermissions = computed<RuntimePermissions>(() => {
  return runtimePermissions.value || metadataPermissions.value || {
    view: true,
    add: true,
    change: true,
    delete: true
  }
})

const canDelete = computed(() => effectivePermissions.value.delete)
const canEdit = computed(() => effectivePermissions.value.change)
const canView = computed(() => effectivePermissions.value.view !== false)

const buildFallbackMetadata = (): ObjectMetadata => ({
  code: objectCode.value,
  name: objectCode.value,
  isHardcoded: true,
  enableWorkflow: false,
  enableVersion: false,
  enableSoftDelete: true,
  fields: [],
  layouts: {},
  permissions: { view: true, add: true, change: true, delete: true }
} as ObjectMetadata)

const loadMetadata = async () => {
  loading.value = true
  loadError.value = null
  try {
    const [runtimeResult, metadataResult] = await Promise.allSettled([
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

const retryLoad = () => { loadMetadata() }

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

.lifecycle-steps-card {
  margin: 0 0 16px 0;

  :deep(.el-card__body) {
    padding: 20px 24px;
  }
}
</style>
