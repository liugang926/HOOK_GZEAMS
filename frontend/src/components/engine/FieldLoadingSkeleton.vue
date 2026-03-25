<template>
  <div class="field-loading-skeleton">
    <el-skeleton
      animated
      :rows="0"
    >
      <template #template>
        <el-skeleton-item
          variant="rect"
          class="field-loading-skeleton__bar"
        />
      </template>
    </el-skeleton>
  </div>
</template>

<style scoped>
.field-loading-skeleton {
  min-height: 32px;
  display: flex;
  align-items: center;
}

.field-loading-skeleton__bar {
  width: 100%;
  height: 32px;
  border-radius: var(--sys-radius-base, 6px);
}
</style>
