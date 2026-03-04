<template>
  <div
    class="object-avatar"
    :class="[`size-${size}`, { 'is-rounded': rounded }]"
    :style="{ backgroundColor: avatarColor }"
  >
    <el-icon
      v-if="icon"
      class="avatar-icon"
    >
      <component :is="icon" />
    </el-icon>
    <span
      v-else
      class="avatar-text"
    >{{ fallbackText }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  /** The unique object code, used to generate a consistent color */
  objectCode: {
    type: String,
    required: true
  },
  /** Element Plus Icon name */
  icon: {
    type: String,
    default: ''
  },
  /** Force a specific color (hex or rgb), overrides automatic generation */
  color: {
    type: String,
    default: ''
  },
  /** The size of the avatar */
  size: {
    type: String as () => 'xs' | 'sm' | 'md' | 'lg' | 'xl',
    default: 'md'
  },
  /** Whether the avatar should be fully rounded (circle) instead of soft square */
  rounded: {
    type: Boolean,
    default: false
  }
})

// Curated luxurious/professional colors for B-end objects
// Similar to Salesforce/Jira predefined color palettes
const COLOR_PALETTE = [
  '#4f46e5', // Indigo 600
  '#0ea5e9', // Light Blue 500
  '#0d9488', // Teal 600
  '#059669', // Emerald 600
  '#65a30d', // Lime 600
  '#d97706', // Amber 600
  '#ea580c', // Orange 600
  '#dc2626', // Red 600
  '#be185d', // Pink 700
  '#9333ea', // Purple 600
  '#475569', // Slate 600
  '#57534e'  // Stone 600
]

/**
 * Generate a consistent color based on string hash
 */
const avatarColor = computed(() => {
  if (props.color) return props.color
  if (!props.objectCode) return COLOR_PALETTE[0]

  // Simple string hashing
  let hash = 0
  for (let i = 0; i < props.objectCode.length; i++) {
    hash = props.objectCode.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  // Map hash to palette length
  const index = Math.abs(hash) % COLOR_PALETTE.length
  return COLOR_PALETTE[index]
})

/**
 * Fallback text: e.g., "AST" for "asset_list"
 */
const fallbackText = computed(() => {
  if (!props.objectCode) return '?'
  const parts = props.objectCode.split(/_|-/)
  if (parts.length > 1) {
    return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase()
  }
  return props.objectCode.substring(0, 2).toUpperCase()
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.object-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-base; // Use global soft edge
  color: #ffffff;
  overflow: hidden;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.1); // Inner border to pop out
  transition: all 0.2s ease;

  // Fully rounded option
  &.is-rounded {
    border-radius: 50%;
  }

  // --- Sizes ---
  &.size-xs {
    width: 20px;
    height: 20px;
    font-size: 10px;
    border-radius: 4px;
    .avatar-icon { font-size: 12px; }
  }

  &.size-sm {
    width: 28px;
    height: 28px;
    font-size: 12px;
    border-radius: 6px;
    .avatar-icon { font-size: 16px; }
  }

  &.size-md {
    width: 36px;
    height: 36px;
    font-size: 14px;
    border-radius: 8px;
    .avatar-icon { font-size: 20px; }
  }

  &.size-lg {
    width: 48px;
    height: 48px;
    font-size: 16px;
    border-radius: 12px;
    .avatar-icon { font-size: 28px; }
  }

  &.size-xl {
    width: 64px;
    height: 64px;
    font-size: 20px;
    border-radius: 16px;
    .avatar-icon { font-size: 36px; }
  }

  .avatar-text {
    font-weight: 600;
    letter-spacing: 0.5px;
  }
}
</style>
