<template>
  <el-row
    :gutter="20"
    class="stats-row"
  >
    <el-col :span="6">
      <el-card>
        <div class="stat-item">
          <div class="stat-value">
            {{ stats.total }}
          </div>
          <div class="stat-label">
            {{ t('integration.stats.total') }}
          </div>
        </div>
      </el-card>
    </el-col>
    <el-col :span="6">
      <el-card>
        <div class="stat-item">
          <div class="stat-value healthy">
            {{ stats.healthy }}
          </div>
          <div class="stat-label">
            {{ t('integration.stats.healthy') }}
          </div>
        </div>
      </el-card>
    </el-col>
    <el-col :span="6">
      <el-card>
        <div class="stat-item">
          <div class="stat-value degraded">
            {{ stats.degraded }}
          </div>
          <div class="stat-label">
            {{ t('integration.stats.degraded') }}
          </div>
        </div>
      </el-card>
    </el-col>
    <el-col :span="6">
      <el-card>
        <div class="stat-item">
          <div class="stat-value unhealthy">
            {{ stats.unhealthy }}
          </div>
          <div class="stat-label">
            {{ t('integration.stats.unhealthy') }}
          </div>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { IntegrationStats } from '@/types/integration'

defineProps<{
  stats: IntegrationStats
}>()

const { t } = useI18n()
</script>

<style scoped>
.stats-row {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}

.stat-value.healthy {
  color: #67c23a;
}

.stat-value.degraded {
  color: #e6a23c;
}

.stat-value.unhealthy {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}
</style>
