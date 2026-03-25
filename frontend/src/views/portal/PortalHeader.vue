<template>
  <div class="portal-header">
    <div class="header-left">
      <el-avatar
        :size="48"
        class="user-avatar"
      >
        {{ userInitial }}
      </el-avatar>
      <div class="header-info">
        <h2 class="portal-title">
          {{ greeting }}
        </h2>
        <p class="portal-subtitle">
          {{ subtitle }}
        </p>
      </div>
    </div>
    <div class="header-stats">
      <div
        v-for="stat in stats"
        :key="stat.id"
        class="stat-item"
        :class="stat.tone"
      >
        <div class="stat-num">
          {{ stat.value }}
        </div>
        <div class="stat-label">
          {{ stat.label }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PortalHeaderStat } from './portalHeaderModel'

defineProps<{
  greeting: string
  stats: PortalHeaderStat[]
  subtitle: string
  userInitial: string
}>()
</script>

<style scoped>
.portal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #409eff 0%, #6366f1 100%);
  border-radius: 12px;
  padding: 24px 28px;
  margin-bottom: 20px;
  color: #fff;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.user-avatar {
  background: rgba(255,255,255,0.25);
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}
.portal-title { margin: 0 0 4px; font-size: 20px; font-weight: 700; }
.portal-subtitle { margin: 0; opacity: 0.85; font-size: 13px; }

.header-stats { display: flex; gap: 24px; }
.stat-item { text-align: center; }
.stat-item.danger .stat-num { color: #ffd666; }
.stat-num { font-size: 28px; font-weight: 700; line-height: 1; }
.stat-label { font-size: 12px; opacity: 0.8; margin-top: 4px; }
</style>
