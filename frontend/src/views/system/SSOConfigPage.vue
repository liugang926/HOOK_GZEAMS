<!--
  SSOConfigPage.vue

  Single-Sign-On configuration management.
  Three tabs:
    1. SSO Providers 鈥?list/create/edit WeWork, DingTalk, Feishu configs
    2. User Mappings 鈥?map local users 鈫?third-party platform users
    3. Sync Logs    鈥?view sync history, trigger manual sync

  Uses ssoConfigApi / userMappingApi / ssoSyncApi from @/api/sso.ts
-->
<template>
  <div class="sso-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          {{ $t('sso.title') }}
        </h2>
        <el-tag
          type="info"
          class="ml-8"
        >
          {{ $t('sso.subtitle') }}
        </el-tag>
      </div>
    </div>

    <el-tabs
      v-model="activeTab"
      type="border-card"
    >
      <!-- 鈹€鈹€ Tab 1: SSO Providers 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
      <el-tab-pane
        :label="$t('sso.tabs.providers')"
        name="providers"
      >
        <div class="tab-toolbar">
          <el-button
            type="primary"
            :icon="Plus"
            @click="openProviderDialog()"
          >
            {{ $t('sso.providers.add') }}
          </el-button>
        </div>

        <el-table
          v-loading="loadingProviders"
          :data="providers"
          border
          stripe
        >
          <el-table-column
            :label="$t('sso.providers.cols.platform')"
            prop="platform"
            width="120"
          >
            <template #default="{ row }">
              <el-tag :type="platformTagType(row.platform)">
                {{ row.platform }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('sso.providers.cols.name')"
            prop="name"
          />
          <el-table-column
            :label="$t('sso.providers.cols.appId')"
            prop="appId"
          />
          <el-table-column
            :label="$t('sso.providers.cols.enabled')"
            prop="isEnabled"
            width="90"
          >
            <template #default="{ row }">
              <el-switch
                :model-value="row.isEnabled"
                @change="toggleProvider(row)"
              />
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('sso.providers.cols.actions')"
            width="160"
          >
            <template #default="{ row }">
              <el-button
                size="small"
                @click="openProviderDialog(row)"
              >
                {{ $t('common.actions.edit') }}
              </el-button>
              <el-button
                size="small"
                type="success"
                @click="testConnection(row)"
              >
                {{ $t('sso.providers.test') }}
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteProvider(row)"
              >
                {{ $t('common.actions.delete') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 鈹€鈹€ Tab 2: User Mappings 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
      <el-tab-pane
        :label="$t('sso.tabs.mappings')"
        name="mappings"
      >
        <div class="tab-toolbar">
          <el-input
            v-model="mappingSearch"
            :placeholder="$t('sso.mappings.searchPlaceholder')"
            clearable
            style="width:260px"
            @input="loadMappings"
          />
          <el-button
            type="primary"
            :icon="Refresh"
            @click="triggerSync"
          >
            {{ $t('sso.mappings.triggerSync') }}
          </el-button>
        </div>

        <el-table
          v-loading="loadingMappings"
          :data="mappings"
          border
          stripe
        >
          <el-table-column
            :label="$t('sso.mappings.cols.localUser')"
            prop="localUserDisplay"
          />
          <el-table-column
            :label="$t('sso.mappings.cols.platform')"
            prop="platform"
            width="100"
          >
            <template #default="{ row }">
              <el-tag
                size="small"
                :type="platformTagType(row.platform)"
              >
                {{ row.platform }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('sso.mappings.cols.externalId')"
            prop="externalId"
          />
          <el-table-column
            :label="$t('sso.mappings.cols.externalName')"
            prop="externalName"
          />
          <el-table-column
            :label="$t('sso.mappings.cols.syncStatus')"
            prop="syncStatus"
            width="100"
          >
            <template #default="{ row }">
              <el-tag
                :type="row.syncStatus === 'synced' ? 'success' : 'warning'"
                size="small"
              >
                {{ row.syncStatus }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('sso.mappings.cols.lastSyncAt')"
            prop="lastSyncAt"
            width="160"
          />
          <el-table-column
            :label="$t('sso.mappings.cols.actions')"
            width="100"
          >
            <template #default="{ row }">
              <el-button
                size="small"
                type="danger"
                @click="deleteMapping(row)"
              >
                {{ $t('common.actions.delete') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="mappingPage"
          v-model:page-size="mappingPageSize"
          :total="mappingTotal"
          layout="total, prev, pager, next"
          class="mt-16"
          @current-change="loadMappings"
        />
      </el-tab-pane>

      <!-- 鈹€鈹€ Tab 3: Sync Logs 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
      <el-tab-pane
        :label="$t('sso.tabs.syncLogs')"
        name="syncLogs"
      >
        <div class="tab-toolbar">
          <el-select
            v-model="syncLogPlatform"
            :placeholder="$t('sso.syncLogs.allPlatforms')"
            clearable
            style="width:160px"
            @change="loadSyncLogs"
          >
            <el-option
              value="wework"
              :label="$t('sso.platforms.wework')"
            />
            <el-option
              value="dingtalk"
              :label="$t('sso.platforms.dingtalk')"
            />
            <el-option
              value="feishu"
              :label="$t('sso.platforms.feishu')"
            />
          </el-select>
          <el-button
            :icon="Refresh"
            @click="loadSyncLogs"
          >
            {{ $t('common.actions.refresh') }}
          </el-button>
        </div>

        <el-table
          v-loading="loadingSyncLogs"
          :data="syncLogs"
          border
          stripe
        >
          <el-table-column
            :label="$t('sso.syncLogs.cols.platform')"
            prop="platform"
            width="100"
          >
            <template #default="{ row }">
              <el-tag
                size="small"
                :type="platformTagType(row.platform)"
              >
                {{ row.platform }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('sso.syncLogs.cols.syncType')"
            prop="syncType"
            width="100"
          />
          <el-table-column
            :label="$t('sso.syncLogs.cols.status')"
            prop="status"
            width="100"
          >
            <template #default="{ row }">
              <el-tag
                :type="row.status === 'success' ? 'success' : row.status === 'running' ? 'warning' : 'danger'"
                size="small"
              >
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('sso.syncLogs.cols.totalCount')"
            prop="totalCount"
            width="90"
          />
          <el-table-column
            :label="$t('sso.syncLogs.cols.successCount')"
            prop="successCount"
            width="90"
          />
          <el-table-column
            :label="$t('sso.syncLogs.cols.failedCount')"
            prop="failedCount"
            width="90"
          />
          <el-table-column
            :label="$t('sso.syncLogs.cols.startTime')"
            prop="startTime"
            width="160"
          />
          <el-table-column
            :label="$t('sso.syncLogs.cols.errorMsg')"
            prop="errorMessage"
            show-overflow-tooltip
          />
        </el-table>
        <el-pagination
          v-model:current-page="syncLogPage"
          v-model:page-size="syncLogPageSize"
          :total="syncLogTotal"
          layout="total, prev, pager, next"
          class="mt-16"
          @current-change="loadSyncLogs"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 鈹€鈹€ Provider Create/Edit Dialog 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
    <el-dialog
      v-model="providerDialog"
      :title="editingProvider ? $t('sso.providers.editTitle') : $t('sso.providers.createTitle')"
      width="520px"
      destroy-on-close
    >
      <el-form
        ref="providerFormRef"
        :model="providerForm"
        :rules="providerRules"
        label-width="120px"
      >
        <el-form-item
          :label="$t('sso.providers.form.platform')"
          prop="platform"
        >
          <el-select
            v-model="providerForm.platform"
            :disabled="!!editingProvider"
          >
            <el-option
              value="wework"
              :label="$t('sso.platforms.wework')"
            />
            <el-option
              value="dingtalk"
              :label="$t('sso.platforms.dingtalk')"
            />
            <el-option
              value="feishu"
              :label="$t('sso.platforms.feishu')"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          :label="$t('sso.providers.form.name')"
          prop="name"
        >
          <el-input v-model="providerForm.name" />
        </el-form-item>
        <el-form-item
          :label="$t('sso.providers.form.appId')"
          prop="appId"
        >
          <el-input v-model="providerForm.appId" />
        </el-form-item>
        <el-form-item
          :label="$t('sso.providers.form.appSecret')"
          prop="appSecret"
        >
          <el-input
            v-model="providerForm.appSecret"
            type="password"
            show-password
          />
        </el-form-item>
        <el-form-item :label="$t('sso.providers.form.redirectUri')">
          <el-input v-model="providerForm.redirectUri" />
        </el-form-item>
        <el-form-item :label="$t('sso.providers.form.enabled')">
          <el-switch v-model="providerForm.isEnabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="providerDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="savingProvider"
          @click="saveProvider"
        >
          {{ $t('common.actions.save') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { ssoConfigApi, userMappingApi, ssoSyncApi } from '@/api/sso'

const { t } = useI18n()
const activeTab = ref('providers')

// 鈹€鈹€ Providers 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const loadingProviders = ref(false)
const providers = ref<any[]>([])

const providerDialog = ref(false)
const savingProvider = ref(false)
const editingProvider = ref<any>(null)
const providerFormRef = ref()
const providerForm = reactive({
  platform: 'wework',
  name: '',
  appId: '',
  appSecret: '',
  redirectUri: '',
  isEnabled: true
})
const providerRules = {
  platform: [{ required: true }],
  name:     [{ required: true }],
  appId:    [{ required: true }],
  appSecret:[{ required: true }]
}

const loadProviders = async () => {
  loadingProviders.value = true
  try {
    const res: any = await ssoConfigApi.list()
    providers.value = res?.results ?? (Array.isArray(res) ? res : [])
  } finally {
    loadingProviders.value = false
  }
}

const platformTagType = (p: string) => {
  const map: any = { wework: 'success', dingtalk: 'primary', feishu: 'warning' }
  return map[p] || 'info'
}

const openProviderDialog = (row?: any) => {
  editingProvider.value = row || null
  if (row) {
    Object.assign(providerForm, row)
  } else {
    Object.assign(providerForm, { platform: 'wework', name: '', appId: '', appSecret: '', redirectUri: '', isEnabled: true })
  }
  providerDialog.value = true
}

const saveProvider = async () => {
  await providerFormRef.value?.validate()
  savingProvider.value = true
  try {
    if (editingProvider.value) {
      await ssoConfigApi.update(editingProvider.value.id, providerForm)
    } else {
      await ssoConfigApi.create(providerForm)
    }
    ElMessage.success(t('common.messages.saveSuccess'))
    providerDialog.value = false
    loadProviders()
  } finally {
    savingProvider.value = false
  }
}

const toggleProvider = async (row: any) => {
  await ssoConfigApi.update(row.id, { isEnabled: !row.isEnabled })
  loadProviders()
}

const testConnection = async (row: any) => {
  try {
    await ssoConfigApi.test(row.id)
    ElMessage.success(t('sso.providers.testSuccess'))
  } catch {
    ElMessage.error(t('sso.providers.testFailed'))
  }
}

const deleteProvider = async (row: any) => {
  await ElMessageBox.confirm(t('common.messages.deleteConfirm'), t('common.messages.warning'), { type: 'warning' })
  await ssoConfigApi.delete(row.id)
  ElMessage.success(t('common.messages.deleteSuccess'))
  loadProviders()
}

// 鈹€鈹€ User Mappings 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const loadingMappings = ref(false)
const mappings = ref<any[]>([])
const mappingSearch = ref('')
const mappingPage = ref(1)
const mappingPageSize = ref(20)
const mappingTotal = ref(0)

const loadMappings = async () => {
  loadingMappings.value = true
  try {
    const res: any = await userMappingApi.list({ search: mappingSearch.value, page: mappingPage.value, page_size: mappingPageSize.value })
    mappings.value = res?.results ?? []
    mappingTotal.value = res?.count ?? 0
  } finally {
    loadingMappings.value = false
  }
}

const triggerSync = async () => {
  try {
    await ssoSyncApi.execute('all')
    ElMessage.success(t('sso.mappings.syncTriggered'))
    setTimeout(loadSyncLogs, 1500)
  } catch {
    ElMessage.error(t('sso.mappings.syncFailed'))
  }
}

const deleteMapping = async (row: any) => {
  await ElMessageBox.confirm(t('common.messages.deleteConfirm'), t('common.messages.warning'), { type: 'warning' })
  await userMappingApi.delete(row.id)
  loadMappings()
}

// 鈹€鈹€ Sync Logs 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const loadingSyncLogs = ref(false)
const syncLogs = ref<any[]>([])
const syncLogPlatform = ref('')
const syncLogPage = ref(1)
const syncLogPageSize = ref(20)
const syncLogTotal = ref(0)

const loadSyncLogs = async () => {
  loadingSyncLogs.value = true
  try {
    const res: any = await ssoSyncApi.getLogs({ platform: syncLogPlatform.value || undefined, page: syncLogPage.value, page_size: syncLogPageSize.value })
    syncLogs.value = res?.results ?? []
    syncLogTotal.value = res?.count ?? 0
  } finally {
    loadingSyncLogs.value = false
  }
}

onMounted(() => {
  loadProviders()
  loadMappings()
  loadSyncLogs()
})
</script>

<style scoped>
.sso-page { padding: 20px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.ml-8 { margin-left: 8px; }
.tab-toolbar { display: flex; gap: 10px; margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
</style>

