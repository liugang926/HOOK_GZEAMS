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

    <div
      v-else
      class="dynamic-form-page__shell"
    >
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

      <div class="form-layout">
        <section class="form-panel form-panel--main">
          <header class="form-panel__header">
            <div>
              <p class="form-panel__kicker">
                {{ modeLabel }}
              </p>
              <h2 class="form-panel__title">
                {{ formPanelTitle }}
              </h2>
            </div>
            <p class="form-panel__text">
              {{ formPanelDescription }}
            </p>
          </header>

          <DynamicForm
            ref="dynamicFormRef"
            class="form-panel__renderer"
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
        </section>

        <aside class="form-panel form-panel--aside">
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
        </aside>
      </div>

      <div class="form-actions">
        <div class="form-actions__summary">
          <span class="form-actions__badge">{{ modeLabel }}</span>
          <p class="form-actions__text">
            {{ actionBarText }}
          </p>
        </div>

        <div class="form-actions__buttons">
          <el-button
            :icon="ArrowLeft"
            :disabled="submitting"
            @click="handleCancel"
          >
            {{ t('common.actions.cancel') }}
          </el-button>
          <el-button
            v-if="canEdit"
            type="primary"
            :icon="Check"
            :loading="submitting"
            @click="handleSubmit"
          >
            {{ t('common.actions.save') }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Check } from '@element-plus/icons-vue'
import DynamicForm from '@/components/engine/DynamicForm.vue'
import ObjectWorkspaceHero from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
import ObjectWorkspaceInfoCard from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'
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
} = useDynamicFormController({
  objectCode,
  recordId,
  isEdit,
  router,
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
