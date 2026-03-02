<template>
  <div class="base-empty-state">
    <div class="empty-state-illustration">
      <slot name="illustration">
        <!-- Default Empty SVG -->
        <svg
          v-if="type === 'empty'"
          width="120"
          height="120"
          viewBox="0 0 120 120"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle cx="60" cy="60" r="50" fill="#F8FAFC" />
          <path d="M40 50H80" stroke="#CBD5E1" stroke-width="4" stroke-linecap="round" />
          <path d="M40 65H70" stroke="#CBD5E1" stroke-width="4" stroke-linecap="round" />
          <path d="M40 80H60" stroke="#CBD5E1" stroke-width="4" stroke-linecap="round" />
          <rect x="30" y="30" width="60" height="70" rx="8" stroke="#94A3B8" stroke-width="4" fill="none" />
          <circle cx="85" cy="85" r="15" fill="#FFFFFF" stroke="#3B82F6" stroke-width="4" />
          <path d="M78 85H92" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" />
          <path d="M85 78V92" stroke="#3B82F6" stroke-width="3" stroke-linecap="round" />
        </svg>

        <!-- Search Empty SVG -->
        <svg
          v-else-if="type === 'search'"
          width="120"
          height="120"
          viewBox="0 0 120 120"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle cx="60" cy="60" r="50" fill="#F1F5F9" />
          <circle cx="50" cy="50" r="20" stroke="#94A3B8" stroke-width="4" fill="none" />
          <path d="M65 65L80 80" stroke="#94A3B8" stroke-width="6" stroke-linecap="round" />
          <path d="M42 45L48 51M48 45L42 51" stroke="#CBD5E1" stroke-width="3" stroke-linecap="round" />
          <circle cx="85" cy="40" r="4" fill="#CBD5E1" />
          <circle cx="30" cy="80" r="6" fill="#E2E8F0" />
        </svg>

        <!-- Error/404 SVG -->
        <svg
          v-else-if="type === 'error'"
          width="120"
          height="120"
          viewBox="0 0 120 120"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle cx="60" cy="60" r="50" fill="#FEF2F2" />
          <path d="M60 35L90 85H30L60 35Z" stroke="#F87171" stroke-width="4" stroke-linejoin="round" fill="none" />
          <path d="M60 55V65" stroke="#F87171" stroke-width="4" stroke-linecap="round" />
          <circle cx="60" cy="76" r="3" fill="#F87171" />
        </svg>
      </slot>
    </div>
    
    <div class="empty-state-content">
      <h3 class="empty-state-title">
        {{ computedTitle }}
      </h3>
      <p
        v-if="description"
        class="empty-state-description"
      >
        {{ description }}
      </p>
    </div>

    <div
      v-if="$slots.action || actionText"
      class="empty-state-actions"
    >
      <slot name="action">
        <el-button
          type="primary"
          :icon="actionIcon"
          @click="$emit('action')"
        >
          {{ actionText }}
        </el-button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

interface Props {
  /** Primary title for the empty state */
  title?: string
  /** Secondary descriptive text providing guidance */
  description?: string
  /** Text for the primary call to action button (if using default button) */
  actionText?: string
  /** Icon for the primary call to action button */
  actionIcon?: any
  /** Empty State Type Variant */
  type?: 'empty' | 'search' | 'error'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'empty'
})
const emit = defineEmits(['action'])

const { t } = useI18n()

const computedTitle = computed(() => {
  if (props.title) return props.title
  if (props.type === 'search') return t('common.messages.noSearchResults', '未找到匹配项')
  if (props.type === 'error') return t('common.messages.systemError', '系统出错�?)
  return t('common.messages.noData', '暂无数据')
})
</script>

<style scoped lang="scss">
@import '@/styles/variables.scss';

.base-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  width: 100%;
  height: 100%;
  min-height: 240px;

  .empty-state-illustration {
    margin-bottom: 24px;
    display: flex;
    justify-content: center;
    align-items: center;

    svg {
      max-width: 100%;
      height: auto;
    }
  }

  .empty-state-content {
    max-width: 400px;
    margin-bottom: 24px;

    .empty-state-title {
      margin: 0 0 8px 0;
      font-size: 18px;
      font-weight: 600;
      color: $text-main;
    }

    .empty-state-description {
      margin: 0;
      font-size: 14px;
      color: $text-secondary;
      line-height: 1.5;
    }
  }

  .empty-state-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
  }
}
</style>
