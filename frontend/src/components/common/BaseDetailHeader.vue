<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils/dateFormat'
import ObjectAvatar from './ObjectAvatar.vue'

interface AuditInfoLike {
  createdBy?: string
  createdAt?: string | Date
  updatedBy?: string
  updatedAt?: string | Date
}

interface HeaderActionLike {
  label: string
  type?: string
  icon?: string
  action: () => void | Promise<void>
}

interface Props {
  title?: string
  objectCode?: string
  objectIcon?: string
  objectName?: string
  showBack?: boolean
  backText?: string
  hasAuditInfo: boolean
  auditInfo?: AuditInfoLike | null
  data: Record<string, any>
  availableActions: HeaderActionLike[]
  onBack: () => void
}

withDefaults(defineProps<Props>(), {
  title: '',
  objectCode: '',
  objectIcon: '',
  objectName: '',
  showBack: true,
  backText: '',
  auditInfo: null
})

const { t } = useI18n()
</script>

<template>
  <div class="page-header record-profile-header">
    <div class="header-left">
      <el-button
        v-if="showBack"
        :icon="ArrowLeft"
        link
        class="back-btn"
        @click="onBack"
      >
        {{ backText || t('common.actions.back') }}
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
          <span class="object-type-name">{{ objectName || t('common.labels.record') }}</span>
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
            {{ t('common.labels.updatedAt') }}: <span class="val">{{ formatDate(auditInfo?.updatedAt || '') }}</span>
          </div>
          <div class="audit-item">
            {{ t('common.labels.updatedBy') }}: <span class="val">{{ auditInfo?.updatedBy }}</span>
          </div>
        </template>
        <template v-else-if="auditInfo?.createdBy">
          <div class="audit-item">
            {{ t('common.labels.createdBy') }}: <span class="val">{{ auditInfo?.createdBy }}</span>
          </div>
        </template>
      </div>

      <div class="header-actions">
        <slot
          name="action-bar"
          :data="data"
          :actions="availableActions"
        >
          <el-button
            v-for="action in availableActions"
            :key="action.label"
            :type="action.type as any"
            :icon="action.icon"
            @click="action.action"
          >
            {{ action.label }}
          </el-button>
        </slot>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: $spacing-md $spacing-lg;
  background-color: $bg-card;
  border-radius: $radius-large;
  box-shadow: $shadow-md;

  .header-left {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    .back-btn {
      font-size: 14px;
      margin-right: 8px;
      color: $text-secondary;
    }

    .profile-identity {
      display: flex;
      align-items: center;
      gap: $spacing-md;
    }

    .profile-text {
      display: flex;
      flex-direction: column;
      justify-content: center;

      .object-type-name {
        font-size: 12px;
        color: $text-secondary;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
      }

      .page-title {
        margin: 0;
        font-size: 20px;
        font-weight: 700;
        color: $text-main;
      }
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: $spacing-lg;

    .header-audit-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
      text-align: right;
      padding-right: $spacing-md;
      border-right: 1px solid $border-color;

      .audit-item {
        font-size: 12px;
        color: $text-secondary;

        .val {
          color: $text-regular;
          font-weight: 500;
        }
      }
    }

    .header-actions {
      display: flex;
      gap: $spacing-sm;
    }
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;

    .header-actions {
      width: 100%;
      justify-content: flex-start;
    }
  }
}
</style>
