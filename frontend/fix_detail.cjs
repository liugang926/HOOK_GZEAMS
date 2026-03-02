const fs = require('fs');
let content = fs.readFileSync('src/views/dynamic/DynamicDetailPage.vue', 'utf8');

// Add i18n
content = content.replace(/import \{ ref, computed, onMounted \} from 'vue'/, `import { ref, computed, onMounted } from 'vue'\nimport { useI18n } from 'vue-i18n'`);
content = content.replace(/const route = useRoute\(\)/, `const route = useRoute()\nconst { t } = useI18n()`);

// Fix loadError result strings
content = content.replace(/title=".*?ʧ.*?"/, `:title="t('common.messages.loadFailed')"`);
content = content.replace(/@click="retryLoad"\s*>[\s\S]*?<\/el-button>/, `@click="retryLoad"\n          >\n            {{ t('common.actions.refresh') }}\n          </el-button>`);
content = content.replace(/@click="\$router\.back\(\)"\s*>[\s\S]*?<\/el-button>/, `@click="$router.back()"\n          >\n            {{ t('common.actions.back') }}\n          </el-button>`);

// Fix Drawer UI strings
content = content.replace(/v-model="editDrawerVisible"\s*title=".*?༭.*?"/, `v-model="editDrawerVisible"\n        :title="t('common.actions.edit')"`);
content = content.replace(/@click="handleEditCancel"\s*>[\s\S]*?<\/el-button>/, `@click="handleEditCancel"\n            >\n              {{ t('common.actions.cancel') }}\n            </el-button>`);
content = content.replace(/@click="handleEditSubmit"\s*>[\s\S]*?<\/el-button>/, `@click="handleEditSubmit"\n            >\n              {{ t('common.actions.save') || 'Save' }}\n            </el-button>`);

// Fix API Messages
content = content.replace(/ElMessage\.success\(['"]+.*?ɹ.*?['"]+\)/, `ElMessage.success(t('common.messages.saveSuccess') || 'Save Success')`);
content = content.replace(/ElMessage\.error\(error\.message \|\| ['"]+.*?ʧ.*?['"]+\)/, `ElMessage.error(error.message || t('common.messages.operationFailed') || 'Operation Failed')`);

fs.writeFileSync('src/views/dynamic/DynamicDetailPage.vue', content, 'utf8');
console.log('Fixed DynamicDetailPage successfully');
