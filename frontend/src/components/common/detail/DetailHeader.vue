<template>
  <div class="page-header record-profile-header">
    <div class="header-left">
      <el-button
        v-if="showBack"
        :icon="ArrowLeft"
        link
        class="back-btn"
        @click="$emit('back')"
      >
        {{ backText || $t('common.actions.back') }}
      </el-button>

      <div class="profile-identity">
        <ObjectAvatar
          v-if="objectCode || title"
          :object-code="objectCode || title || ''"
          :icon="objectIcon"
          size="lg"
          class="profile-avatar"
        />
        <div class="profile-text">
          <span class="object-type-name">{{ objectName || $t('common.labels.record') }}</span>
          <h1 class="page-title">
            {{ title || '...' }}
          </h1>
        </div>
      </div>
    </div>

    <div class="header-right">
      <div
        v-if="hasAuditInfo"
        class="header-audit-info"
      >
        <template v-if="auditInfo?.updatedBy">
          <div class="audit-item">
            {{ $t('common.labels.updatedAt') }}: <span class="val">{{ formatDate(auditInfo?.updatedAt || '') }}</span>
          </div>
          <div class="audit-item">
            {{ $t('common.labels.updatedBy') }}: <span class="val">{{ auditInfo?.updatedBy }}</span>
          </div>
        </template>
        <template v-else-if="auditInfo?.createdBy">
          <div class="audit-item">
            {{ $t('common.labels.createdBy') }}: <span class="val">{{ auditInfo?.createdBy }}</span>
          </div>
        </template>
      </div>

      <div class="header-actions">
        <slot name="toolbar" />
        <el-button
          v-for="action in availableActions"
          :key="action.label"
          :type="action.type as any"
          :icon="action.icon as any"
          :disabled="action.disabled"
          @click="action.action"
        >
          {{ action.label }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
import ObjectAvatar from '../ObjectAvatar.vue'
import { formatDate } from '@/utils/dateFormat'
import type { AuditInfo } from '../BaseDetailPage.vue'

interface DetailAction {
  label: string
  type?: string
  icon?: string
  action: () => void | Promise<void>
  disabled?: boolean
}

defineProps<{
  title?: string
  objectCode?: string
  objectIcon?: string
  objectName?: string
  showBack?: boolean
  backText?: string
  hasAuditInfo?: boolean
  auditInfo?: AuditInfo | null
  availableActions?: DetailAction[]
}>()

defineEmits<{
  (e: 'back'): void
}>()
</script>

