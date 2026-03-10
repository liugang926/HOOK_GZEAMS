<template>
  <section class="page-hero">
    <div class="hero-content">
      <div class="hero-kicker">
        Navigation Control Center
      </div>
      <h2>{{ copy.title }}</h2>
      <p>{{ copy.subtitle }}</p>
      <div class="hero-stats">
        <div class="hero-stat">
          <span class="hero-stat-label">{{ copy.sections.categories }}</span>
          <strong>{{ categoryCount }}</strong>
        </div>
        <div class="hero-stat">
          <span class="hero-stat-label">{{ copy.sections.entries }}</span>
          <strong>{{ entryCount }}</strong>
        </div>
        <div class="hero-stat">
          <span class="hero-stat-label">{{ copy.fields.visible }}</span>
          <strong>{{ visibleEntryCount }}</strong>
        </div>
        <div class="hero-stat">
          <span class="hero-stat-label">{{ copy.tags.locked }}</span>
          <strong>{{ lockedEntryCount }}</strong>
        </div>
      </div>
    </div>
    <div class="hero-actions">
      <el-button @click="$emit('reload')">
        {{ copy.actions.reload }}
      </el-button>
      <el-button
        type="primary"
        :loading="saving"
        @click="$emit('save')"
      >
        {{ copy.actions.save }}
      </el-button>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  copy: any
  categoryCount: number
  entryCount: number
  visibleEntryCount: number
  lockedEntryCount: number
  saving: boolean
}>()

defineEmits<{
  (event: 'reload'): void
  (event: 'save'): void
}>()
</script>

<style scoped lang="scss">
@use '../styles/mixins' as *;

.page-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 24px 28px;
  border: 1px solid #d8e1ee;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(16, 32, 58, 0.08), transparent 30%),
    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.06);
}

.hero-content {
  min-width: 0;
}

.hero-kicker {
  margin-bottom: 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7b8ca5;
}

.page-hero h2 {
  margin: 0;
  @include title-strong(34px);
  line-height: 1.05;
}

.page-hero p {
  margin: 12px 0 0;
  max-width: 920px;
  color: #41556f;
  line-height: 1.75;
  font-size: 15px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  align-self: flex-start;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 20px;
  max-width: 760px;
}

.hero-stat {
  padding: 14px 16px;
  border: 1px solid #d8e1ee;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
}

.hero-stat strong {
  display: block;
  margin-top: 6px;
  @include title-strong(22px);
}

.hero-stat-label {
  font-size: 12px;
  color: #71839b;
}

@media (max-width: 960px) {
  .page-hero {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .page-hero {
    padding: 20px;
  }

  .page-hero h2 {
    font-size: 28px;
  }
}
</style>
