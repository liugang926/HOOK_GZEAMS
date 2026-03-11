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

    <div
      v-else
      class="dynamic-detail-page__shell"
    >
      <ObjectWorkspaceHero
        variant="detail"
        :object-code="objectCode"
        :icon="objectMetadata?.icon || ''"
        :eyebrow="moduleLabel"
        :title="heroTitle"
        :description="heroDescription"
        :chips="heroChips"
        :stats="heroStats"
        :show-back="true"
        :back-label="t('common.actions.back')"
        :back-icon="ArrowLeft"
        @back="handleBackToList"
      />

      <div class="detail-layout">
        <section class="detail-panel detail-panel--main">
          <header class="detail-panel__header">
            <div>
              <p class="detail-panel__kicker">
                {{ detailModeLabel }}
              </p>
              <h2 class="detail-panel__title">
                {{ detailPanelTitle }}
              </h2>
            </div>
            <p class="detail-panel__text">
              {{ detailPanelDescription }}
            </p>
          </header>

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
            <template
              v-if="isLifecycle"
              #action-bar
            >
              <StatusActionBar
                :actions="lifecycleRendererRef?.workflowActions || []"
                :status="lifecycleRecordData?.status || ''"
                @action-success="handleLifecycleRefresh"
              />
            </template>

            <template
              v-if="isLifecycle && lifecycleExtension?.workflowSteps"
              #header-extra
            >
              <el-card
                class="lifecycle-steps-card"
                shadow="never"
              >
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

            <template
              v-if="isLifecycle"
              #after-sections
            >
              <LifecycleDetailRenderer
                ref="lifecycleRendererRef"
                :object-code="objectCode"
                :record-id="recordId"
                :record-data="lifecycleRecordData"
                @refresh="handleLifecycleRefresh"
              />
            </template>
          </CommonDynamicDetailPage>
        </section>

        <aside class="detail-panel detail-panel--aside">
          <ObjectWorkspaceInfoCard
            variant="detail"
            :eyebrow="summaryLabel"
            :title="objectDisplayName"
            :rows="infoRows"
          />

          <ObjectWorkspaceInfoCard
            variant="detail"
            :eyebrow="tipsLabel"
            :tips="tips"
            soft
          />
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import CommonDynamicDetailPage from '@/components/common/DynamicDetailPage.vue'
import ObjectWorkspaceHero from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
import ObjectWorkspaceInfoCard from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import StatusActionBar from '@/components/common/StatusActionBar.vue'
import LifecycleDetailRenderer from '@/components/lifecycle/LifecycleDetailRenderer.vue'
import { hasLifecycleExtension, getLifecycleExtension } from '@/platform/lifecycle/lifecycleDetailExtensions'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'
import {
  useDynamicDetailController,
  useDynamicDetailWorkspace,
} from '@/views/dynamic/workspace'

const route = useRoute()
const router = useRouter()
const { t, te, locale } = useI18n()
const objectCode = ref<string>((route.params.code as string) || '')
const recordId = ref<string>((route.params.id as string) || '')
const lifecycleRendererRef = ref<InstanceType<typeof LifecycleDetailRenderer> | null>(null)
const {
  detailPageRef,
  handleBackToList,
  handleLifecycleRefresh,
  handleRecordLoaded,
  handleRelatedRecordClick,
  handleRelatedRecordEdit,
  lifecycleRecordData,
  loadError,
  loadedRecord,
  loading,
  loadMetadata,
  metadataPermissions,
  objectMetadata,
  retryLoad,
  runtimePermissions,
} = useDynamicDetailController({
  objectCode,
  recordId,
  router,
  t: t as (key: string) => string,
})

const isLifecycle = computed(() => hasLifecycleExtension(objectCode.value))
const lifecycleExtension = computed(() => getLifecycleExtension(objectCode.value))

const effectivePermissions = computed(() => {
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
const isZhLocale = computed(() => String(locale?.value || '').toLowerCase().startsWith('zh'))
const objectDisplayName = computed(() => {
  return resolveObjectDisplayName(
    objectCode.value,
    objectMetadata.value?.name || objectMetadata.value?.nameEn || '',
    t as (key: string) => string,
    (te || (() => false)) as (key: string) => boolean
  )
})
const {
  moduleLabel,
  detailModeLabel,
  detailPanelTitle,
  detailPanelDescription,
  summaryLabel,
  tipsLabel,
  heroTitle,
  heroDescription,
  heroChips,
  heroStats,
  infoRows,
  tips,
} = useDynamicDetailWorkspace({
  isZhLocale,
  objectCode,
  recordId,
  objectMetadata,
  objectDisplayName,
  canEdit,
  loadedRecord,
})

onMounted(() => {
  loadMetadata()
})
</script>

<style scoped lang="scss">
@use '@/views/dynamic/styles/dynamic-detail-page' as detailPage;

@include detailPage.dynamic-detail-page-styles();
</style>
