<template>
  <div
    v-loading="loading"
    class="dynamic-form-page"
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
      v-else-if="showPermissionDenied"
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

    <BaseFormPage
      v-else
      class="dynamic-form-page__shell"
      :panel-kicker="modeLabel"
      :panel-title="formPanelTitle"
      :panel-description="formPanelDescription"
      :summary-badge="modeLabel"
      :summary-text="actionBarText"
      :cancel-icon="ArrowLeft"
      :cancel-disabled="submitting"
      :cancel-label="t('common.actions.cancel')"
      :submit-visible="canEdit"
      :submit-icon="Check"
      :submit-loading="submitting"
      :submit-label="t('common.actions.save')"
      @cancel="handleCancel"
      @submit="handleSubmit"
    >
      <template #hero>
        <ObjectWorkspaceHero
          variant="form"
          :object-code="objectCode"
          :icon="objectMetadata?.icon || ''"
          :eyebrow="moduleLabel"
          :title="pageTitle"
          :description="pageDescription"
          :chips="heroChips"
          :stats="heroStats"
          :show-back="true"
          :back-label="t('common.actions.back')"
          :back-icon="ArrowLeft"
          @back="handleCancel"
        />
      </template>

      <DynamicForm
        v-if="!usesAggregateDocument"
        ref="dynamicFormRef"
        :business-object="objectCode"
        layout-code="form"
        :model-value="formData"
        :readonly="!canEdit"
        :show-actions="false"
        :instance-id="recordId || null"
        label-position="top"
        label-width="auto"
        @update:model-value="handleModelUpdate"
        @request-save="handleFormRequestSave"
      />

      <DocumentWorkbench
        v-else
        ref="dynamicFormRef"
        :object-code="objectCode"
        :record-id="recordId || ''"
        :mode="isEdit ? 'edit' : 'create'"
        :model-value="formData"
        :document="documentPayload"
        :status-actions="aggregateStatusActions"
        :readonly="!canEdit"
        @update:model-value="handleModelUpdate"
        @request-save="handleFormRequestSave"
        @action-success="handleAggregateActionSuccess"
      />

      <template #aside>
        <ObjectWorkspaceInfoCard
          variant="form"
          :eyebrow="summaryLabel"
          :title="objectDisplayName"
          :rows="infoRows"
        />

        <ObjectWorkspaceInfoCard
          variant="form"
          :eyebrow="tipsLabel"
          :tips="tips"
          soft
        />
      </template>
    </BaseFormPage>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Check } from '@element-plus/icons-vue'
import BaseFormPage from '@/components/common/BaseFormPage.vue'
import DynamicForm from '@/components/engine/DynamicForm.vue'
import DocumentWorkbench from '@/components/common/DocumentWorkbench.vue'
import ObjectWorkspaceHero from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
import ObjectWorkspaceInfoCard from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'
import { buildAggregateDocumentStatusActions } from '@/views/dynamic/workspace/aggregateDocumentStatusActions'
import {
  useDynamicFormAccess,
  useDynamicFormController,
  useDynamicFormWorkspace,
} from '@/views/dynamic/workspace'

const route = useRoute()
const router = useRouter()
const { t, te, locale } = useI18n()

const objectCode = ref<string>((route.params.code as string) || '')
const recordId = ref<string>((route.params.id as string) || '')

const isEdit = computed(() => !!recordId.value)
const isZhLocale = computed(() => String(locale.value || '').toLowerCase().startsWith('zh'))

const {
  documentPayload,
  dynamicFormRef,
  formData,
  handleCancel,
  handleModelUpdate,
  handleSubmit,
  loadData,
  loadError,
  loading,
  metadataPermissions,
  objectMetadata,
  retryLoad,
  runtimePermissions,
  submitting,
  usesAggregateDocument,
} = useDynamicFormController({
  objectCode,
  recordId,
  isEdit,
  router,
  routeQuery: computed(() => route.query as Record<string, string | string[] | null | undefined>),
  shouldLoadRecord: () => canView.value,
  t: t as (key: string) => string,
})

const {
  canEdit,
  canView,
  showPermissionDenied,
} = useDynamicFormAccess({
  isEdit,
  loadError,
  metadataPermissions,
  runtimePermissions,
})

const handleFormRequestSave = () => {
  if (submitting.value || !canEdit.value || !!loadError.value) return
  void handleSubmit()
}

const handleAggregateActionSuccess = async () => {
  if (!isEdit.value) return
  await loadData()
}

const aggregateStatusActions = computed(() => {
  return buildAggregateDocumentStatusActions({
    objectCode: objectCode.value,
    recordId: recordId.value,
    document: documentPayload.value,
    t: t as (key: string) => string,
  })
})

const objectDisplayName = computed(() => {
  return resolveObjectDisplayName(
    objectCode.value,
    objectMetadata.value?.name || objectMetadata.value?.nameEn || '',
    t as (key: string) => string,
    te
  )
})

const {
  moduleLabel,
  modeLabel,
  pageTitle,
  pageDescription,
  formPanelTitle,
  formPanelDescription,
  summaryLabel,
  tipsLabel,
  heroChips,
  heroStats,
  infoRows,
  tips,
  actionBarText,
} = useDynamicFormWorkspace({
  isZhLocale,
  isEdit,
  canEdit,
  objectCode,
  objectMetadata,
  objectDisplayName,
})

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
@use '@/views/dynamic/styles/dynamic-form-page' as formPage;

@include formPage.dynamic-form-page-styles();
</style>
