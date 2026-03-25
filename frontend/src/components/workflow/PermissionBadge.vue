<template>
  <div
    class="permission-badge"
    :class="sizeClasses"
  >
    <div
      v-if="permissionLevel"
      class="permission-badge-content"
      :class="`permission-${permissionLevel}`"
      :style="{ '--permission-color': color }"
    >
      <span class="permission-icon">
        <component :is="icon" />
      </span>
      <span class="permission-letter">{{ letter }}</span>
      <el-tooltip
        v-if="showTooltip"
        :content="tooltip"
        placement="top"
        effect="light"
        :hide-after="0"
      >
        <span class="permission-help">
          <el-icon><InfoFilled /></el-icon>
        </span>
      </el-tooltip>
    </div>
    <span
      v-else
      class="no-permission"
    >-</span>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Edit as EditIcon,
  View as ViewIcon,
  Hide as HideIcon,
  HelpFilled as HelpIcon,
  InfoFilled,
} from '@element-plus/icons-vue'

interface Props {
  permissionLevel?: 'editable' | 'read_only' | 'hidden' | null
  size?: 'small' | 'normal' | 'large'
  showTooltip?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  permissionLevel: null,
  size: 'normal',
  showTooltip: true
})

const { t } = useI18n()

// Get icon for permission level
const icon = computed(() => {
  switch (props.permissionLevel) {
    case 'editable':
      return EditIcon
    case 'read_only':
      return ViewIcon
    case 'hidden':
      return HideIcon
    default:
      return HelpIcon
  }
})

// Get letter badge for permission level
const letter = computed(() => {
  switch (props.permissionLevel) {
    case 'editable':
      return 'E'
    case 'read_only':
      return 'RO'
    case 'hidden':
      return 'H'
    default:
      return '?'
  }
})

// Get color for permission level
const color = computed(() => {
  switch (props.permissionLevel) {
    case 'editable':
      return '#27ae60'
    case 'read_only':
      return '#f39c12'
    case 'hidden':
      return '#e74c3c'
    default:
      return '#95a5a6'
  }
})

// Get tooltip text
const tooltip = computed(() => {
  switch (props.permissionLevel) {
    case 'editable':
      return t('workflow.permissions.tooltip.editable')
    case 'read_only':
      return t('workflow.permissions.tooltip.readOnly')
    case 'hidden':
      return t('workflow.permissions.tooltip.hidden')
    default:
      return t('workflow.permissions.tooltip.unconfigured')
  }
})

// Get size classes
const sizeClasses = computed(() => {
  return {
    small: 'permission-badge-small',
    normal: 'permission-badge-normal',
    large: 'permission-badge-large'
  }[props.size]
})
</script>

<style scoped lang="scss">
.permission-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;

  &-content {
    display: flex;
    align-items: center;
    gap: 3px;
    padding: 2px 6px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    color: white;
    background: var(--permission-color, #95a5a6);
    transition: all 0.2s ease;
    cursor: pointer;
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
  }

  .permission-letter {
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  }

  .permission-help {
    opacity: 0.7;
    font-size: 10px;
    
    &:hover {
      opacity: 1;
    }
  }

  .no-permission {
    color: #95a5a6;
    font-size: 11px;
  }

  // Size variants
  &.permission-badge-small &-content {
    padding: 1px 4px;
    font-size: 10px;
    
    .permission-letter {
      font-size: 9px;
    }
  }

  &.permission-badge-large &-content {
    padding: 3px 8px;
    font-size: 12px;
    
    .permission-letter {
      font-size: 10px;
    }
  }

  // Dark mode support
  @media (prefers-color-scheme: dark) {
    .permission-badge-content {
      opacity: 0.9;
      
      &:hover {
        opacity: 1;
      }
    }
  }
}

// Accessibility
.permission-badge:focus-visible {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}
</style>
