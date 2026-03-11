<template>
  <div class="page-layout-designer">
    <div class="page-header">
      <el-button
        link
        @click="goBack"
      >
        <el-icon><ArrowLeft /></el-icon>
        {{ $t('common.actions.back') }}
      </el-button>
      <div class="header-title">
        <span class="title">{{ $t('system.pageLayout.designer.title') }}</span>
        <span
          v-if="layoutName"
          class="subtitle"
        >- {{ layoutName }}</span>
      </div>
      <div class="header-meta">
        <el-tag
          v-if="objectDisplayName"
          size="small"
          type="info"
        >
          {{ objectDisplayName }}
        </el-tag>
        <el-tag
          size="small"
          type="success"
        >
          {{ layoutTypeLabel }}
        </el-tag>
      </div>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="designer-hint"
    >
      {{ $t('system.pageLayout.designer.hints.singleLayoutModel') }}
    </el-alert>

    <div class="designer-stage">
      <WysiwygLayoutDesigner
        v-if="objectCode"
        :layout-id="layoutId"
        :mode="mode"
        :layout-name="layoutName || $t('system.pageLayout.designer.title')"
        :object-code="objectCode"
        :business-object-id="businessObjectId"
        :initial-preview-mode="initialPreviewMode"
        @cancel="goBack"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import WysiwygLayoutDesigner from '@/components/designer/WysiwygLayoutDesigner.vue'
import type { LayoutMode } from '@/types/layout'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'

const { t, te } = useI18n()
const route = useRoute()
const router = useRouter()

const layoutId = computed(() => (route.query.layoutId as string) || '')
const objectCode = computed(() => (route.query.objectCode as string) || '')
const layoutName = computed(() => (route.query.layoutName as string) || '')
const layoutType = computed(() => String(route.query.layoutType || '').toLowerCase())
const initialPreviewMode = computed<'current' | 'active'>(() => {
  return (route.query.previewMode as string) === 'active' ? 'active' : 'current'
})

const mode = computed<LayoutMode>(() => {
  if (layoutType.value === 'readonly' || layoutType.value === 'detail') {
    return 'readonly'
  }
  if (layoutType.value === 'search') {
    return 'search'
  }
  return 'edit'
})
const objectName = computed(() => (route.query.objectName as string) || '')
const objectDisplayName = computed(() => {
  return resolveObjectDisplayName(
    objectCode.value,
    objectName.value,
    t as (key: string) => string,
    te
  )
})
const layoutTypeLabel = computed(() => {
  if (layoutType.value === 'readonly' || layoutType.value === 'detail') {
    return t('system.pageLayout.types.readonly')
  }
  if (layoutType.value === 'search') {
    return t('system.pageLayout.types.search')
  }
  return t('system.pageLayout.types.edit')
})
const businessObjectId = computed(() => (route.query.businessObjectId as string) || '')

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push({
    name: 'PageLayoutList',
    query: {
      objectCode: objectCode.value,
      objectName: objectDisplayName.value || objectName.value
    }
  })
}
</script>

<style scoped>
.page-layout-designer {
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 12px;
  overflow: hidden;
  background: #f0f2f5;
}

.designer-hint {
  margin: 0 16px;
  flex-shrink: 0;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
  flex-shrink: 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-meta {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.subtitle {
  font-size: 14px;
  color: #909399;
}

.designer-stage {
  flex: 1;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}
</style>
