<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils/dateFormat'

interface AuditInfoLike {
  createdBy?: string
  createdAt?: string | Date
  updatedBy?: string
  updatedAt?: string | Date
}

defineProps<{
  auditInfo?: AuditInfoLike | null
}>()

const { t } = useI18n()
</script>

<template>
  <div class="audit-info">
    <div class="audit-title">
      {{ t('common.labels.auditInfo') }}
    </div>
    <el-descriptions
      :column="2"
      border
    >
      <el-descriptions-item :label="t('common.labels.createdBy')">
        {{ auditInfo?.createdBy || '-' }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('common.labels.createdAt')">
        {{ formatDate(auditInfo?.createdAt || '') }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('common.labels.updatedBy')">
        {{ auditInfo?.updatedBy || '-' }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('common.labels.updatedAt')">
        {{ formatDate(auditInfo?.updatedAt || '') }}
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.audit-info {
  margin-top: $spacing-md;
  background-color: $bg-card;
  border-radius: $radius-large;
  box-shadow: $shadow-sm;
  overflow: hidden;
  border: 1px solid $border-light;

  .audit-title {
    padding: 14px $spacing-lg;
    background-color: #f8fafc;
    border-bottom: 1px solid $border-light;
    border-left: 3px solid $text-secondary;
    font-size: 15px;
    font-weight: 600;
    color: $text-main;
  }

  :deep(.el-descriptions) {
    padding: 0;

    .el-descriptions__label {
      width: 120px;
      background-color: #fafafa;
    }
  }
}
</style>
