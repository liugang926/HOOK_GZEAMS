<!--
  DesignerHistoryPanel — Collapsible right-side drawer showing the undo/redo history stack.
  Users can browse past states and jump to any point via click.
-->

<template>
  <el-drawer
    :model-value="visible"
    :title="t('system.pageLayout.designer.historyPanel.title', '操作历史')"
    direction="rtl"
    size="320px"
    :append-to-body="true"
    :destroy-on-close="false"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="history-panel">
      <div
        v-if="entries.length === 0"
        class="history-empty"
      >
        <el-empty
          :description="t('system.pageLayout.designer.historyPanel.empty', '暂无操作记录')"
          :image-size="80"
        />
      </div>

      <div
        v-else
        class="history-list"
      >
        <div
          v-for="(entry, index) in entries"
          :key="entry.id"
          class="history-item"
          :class="{
            'history-item--active': index === currentIndex,
            'history-item--future': index > currentIndex
          }"
          @click="handleGoTo(index)"
        >
          <div class="history-item__indicator">
            <div class="history-item__dot" />
            <div
              v-if="index < entries.length - 1"
              class="history-item__line"
            />
          </div>

          <div class="history-item__content">
            <div class="history-item__desc">
              {{ entry.description || t('system.pageLayout.designer.historyPanel.unknownAction', '未命名操作') }}
            </div>
            <div class="history-item__time">
              {{ formatTimestamp(entry.timestamp) }}
            </div>
          </div>

          <el-tag
            v-if="index === currentIndex"
            type="primary"
            effect="dark"
            size="small"
            class="history-item__badge"
          >
            {{ t('system.pageLayout.designer.historyPanel.current', '当前') }}
          </el-tag>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { HistoryEntry } from '@/composables/useLayoutHistory'

defineProps<{
  visible: boolean
  entries: HistoryEntry[]
  currentIndex: number
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'go-to', index: number): void
}>()

const { t } = useI18n()

const handleGoTo = (index: number) => {
  emit('go-to', index)
}

const formatTimestamp = (ts: number) => {
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffSec = Math.floor(diffMs / 1000)

  if (diffSec < 60) return t('system.pageLayout.designer.historyPanel.justNow', '刚刚')
  if (diffSec < 3600) {
    const mins = Math.floor(diffSec / 60)
    return `${mins} ${t('system.pageLayout.designer.historyPanel.minutesAgo', '分钟前')}`
  }
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}
</script>

<style scoped lang="scss">
.history-panel {
  height: 100%;
  overflow-y: auto;
}

.history-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.history-list {
  padding: 4px 0;
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;

  &:hover {
    background: var(--el-fill-color-lighter);
  }

  &--active {
    background: var(--el-color-primary-light-9);

    .history-item__dot {
      background: var(--el-color-primary);
      box-shadow: 0 0 0 3px var(--el-color-primary-light-7);
    }

    .history-item__desc {
      font-weight: 600;
      color: var(--el-color-primary);
    }
  }

  &--future {
    opacity: 0.45;

    .history-item__dot {
      background: var(--el-border-color);
    }
  }
}

.history-item__indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 14px;
  padding-top: 4px;
}

.history-item__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.history-item__line {
  width: 2px;
  flex: 1;
  min-height: 20px;
  background: var(--el-border-color-lighter);
}

.history-item__content {
  flex: 1;
  min-width: 0;
}

.history-item__desc {
  font-size: 13px;
  color: var(--el-text-color-primary);
  line-height: 1.4;
  word-break: break-word;
}

.history-item__time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 2px;
}

.history-item__badge {
  flex-shrink: 0;
  margin-top: 2px;
}
</style>
