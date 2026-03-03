<template>
  <div class="language-list">
    <!-- Page Header -->
    <section-block
      :title="$t('system.languages.title')"
      class="header-section"
    >
      <template #extra>
        <el-button
          type="primary"
          @click="handleCreate"
        >
          <el-icon><Plus /></el-icon>
          {{ $t('common.actions.add') }}
        </el-button>
      </template>
    </section-block>

    <!-- Languages Table -->
    <el-table
      v-loading="loading"
      :data="languages"
      stripe
    >
      <el-table-column
        prop="flagEmoji"
        :label="$t('system.languages.flag')"
        width="80"
      >
        <template #default="{ row }">
          <span class="flag-emoji">{{ row.flagEmoji }}</span>
        </template>
      </el-table-column>
      <el-table-column
        prop="code"
        :label="$t('system.languages.code')"
        width="120"
      />
      <el-table-column
        prop="name"
        :label="$t('system.languages.name')"
      />
      <el-table-column
        prop="nativeName"
        :label="$t('system.languages.nativeName')"
      />
      <el-table-column
        prop="isDefault"
        :label="$t('system.languages.isDefault')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            v-if="row.isDefault"
            size="small"
            type="success"
          >
            {{ $t('common.yes') }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column
        prop="isActive"
        :label="$t('system.languages.isActive')"
        width="100"
      >
        <template #default="{ row }">
          <el-switch
            v-model="row.isActive"
            @change="handleToggleActive(row)"
          />
        </template>
      </el-table-column>
      <el-table-column
        prop="sortOrder"
        :label="$t('system.languages.sortOrder')"
        width="100"
      />
      <el-table-column
        :label="$t('common.actions')"
        width="200"
        fixed="right"
      >
        <template #default="{ row }">
          <el-space>
            <el-button
              v-if="!row.isDefault"
              link
              type="primary"
              size="small"
              @click="handleSetDefault(row)"
            >
              {{ $t('system.languages.setDefault') }}
            </el-button>
            <el-button
              link
              type="primary"
              size="small"
              @click="handleEdit(row)"
            >
              {{ $t('common.actions.edit') }}
            </el-button>
            <el-popconfirm
              v-if="!row.isDefault"
              :title="$t('system.languages.deleteConfirm')"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button
                  link
                  type="danger"
                  size="small"
                >
                  {{ $t('common.actions.delete') }}
                </el-button>
              </template>
            </el-popconfirm>
          </el-space>
        </template>
      </el-table-column>
    </el-table>

    <!-- Language Dialog -->
    <LanguageDialog
      v-model:visible="dialogVisible"
      :language="currentLanguage"
      @success="loadLanguages"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import SectionBlock from '@/components/common/SectionBlock.vue'
import LanguageDialog from '@/components/common/LanguageDialog.vue'
import { languageApi } from '@/api/translations'
import type { Language } from '@/api/translations'

// State
const { t } = useI18n()
const loading = ref(false)
const languages = ref<Language[]>([])
const dialogVisible = ref(false)
const currentLanguage = ref<Language | null>(null)

// Load languages
const loadLanguages = async () => {
  loading.value = true
  try {
    const response = await languageApi.list()
    const raw = response as unknown
    const payload = (
      raw && typeof raw === 'object' && 'data' in (raw as Record<string, unknown>)
        ? (raw as Record<string, unknown>).data
        : raw
    ) as unknown

    if (Array.isArray(payload)) {
      languages.value = payload as Language[]
      return
    }
    if (
      payload &&
      typeof payload === 'object' &&
      'data' in (payload as Record<string, unknown>) &&
      Array.isArray((payload as Record<string, unknown>).data)
    ) {
      languages.value = (payload as { data: Language[] }).data
      return
    }
    languages.value = []
  } finally {
    loading.value = false
  }
}

// Create language
const handleCreate = () => {
  currentLanguage.value = null
  dialogVisible.value = true
}

// Edit language
const handleEdit = (row: Language) => {
  currentLanguage.value = row
  dialogVisible.value = true
}

// Set as default
const handleSetDefault = async (row: Language) => {
  try {
    await languageApi.setDefault(row.id)
    ElMessage.success(t('system.languages.messages.setDefaultSuccess', { name: row.name }))
    loadLanguages()
  } catch (error) {
    ElMessage.error(t('system.languages.messages.setDefaultFailed'))
  }
}

// Toggle active
const handleToggleActive = async (row: Language) => {
  try {
    await languageApi.update(row.id, { isActive: row.isActive })
    ElMessage.success(
      row.isActive
        ? t('system.languages.messages.activateSuccess')
        : t('system.languages.messages.deactivateSuccess')
    )
  } catch (error) {
    // Revert on error
    row.isActive = !row.isActive
    ElMessage.error(t('system.languages.messages.updateFailed'))
  }
}

// Delete language
const handleDelete = async (id: string) => {
  try {
    await languageApi.delete(id)
    ElMessage.success(t('system.languages.messages.deleteSuccess'))
    loadLanguages()
  } catch (error) {
    ElMessage.error(t('system.languages.messages.deleteFailed'))
  }
}

// Initialize
onMounted(() => {
  loadLanguages()
})
</script>

<style scoped lang="scss">
.language-list {
  .header-section {
    margin-bottom: 16px;
  }

  .flag-emoji {
    font-size: 24px;
  }
}
</style>
