const fs = require('fs');
let content = fs.readFileSync('src/views/dynamic/DynamicListPage.vue', 'utf8');

// Create Action
content = content.replace(/<el-button\s+v-if=\"canAdd\"\s+type=\"primary\"\s+@click=\"handleCreate\"\s*>[\s\S]*?<\/el-button>/, `<el-button
          v-if="canAdd"
          type="primary"
          @click="handleCreate"
        >
          {{ t('common.actions.create') }}
        </el-button>`);

// Unified Search Bar
content = content.replace(/placeholder=".*?ֶ"/g, `:placeholder="t('common.select')"`);
content = content.replace(/label=".*?ȫֶ"/g, `:label="t('common.all')"`);
content = content.replace(/placeholder=".*?ؼ"/g, `:placeholder="t('common.selectors.searchKeyword')"`);

// List Action Buttons
content = content.replace(/@click\.stop="handleView\(row\)"\s*>[\s\S]*?<\/el-button>/, `@click.stop="handleView(row)"
        >
          {{ t('common.actions.view') }}
        </el-button>`);

content = content.replace(/@click\.stop="handleEdit\(row\)"\s*>[\s\S]*?<\/el-button>/, `@click.stop="handleEdit(row)"
        >
          {{ t('common.actions.edit') }}
        </el-button>`);

content = content.replace(/@click\.stop="handleDelete\(row\)"\s*>[\s\S]*?<\/el-button>/, `@click.stop="handleDelete(row)"
        >
          {{ t('common.actions.delete') }}
        </el-button>`);

// Error Status Action Buttons
content = content.replace(/title=".*?ʧ"/g, `:title="t('common.messages.loadFailed')"`);
content = content.replace(/@click="retryLoad"\s*>[\s\S]*?<\/el-button>/, `@click="retryLoad"
        >
          {{ t('common.actions.refresh') }}
        </el-button>`);
content = content.replace(/@click="\$router\.back\(\)"\s*>[\s\S]*?<\/el-button>/, `@click="$router.back()"
        >
          {{ t('common.actions.back') }}
        </el-button>`);

// Script Setup API messages
content = content.replace(/await ElMessageBox\.confirm\(['"].*?ɾ.*?['"],\s*['"].*?ɾ.*?['"]/g, `await ElMessageBox.confirm(
      t('common.messages.confirmDeleteMessage') || 'Confirm Delete',
      t('common.dialog.confirmTitle') || 'Confirm Delete'`);

content = content.replace(/ElMessage\.success\(['"].*?ɾ.*?['"]\)/g, `ElMessage.success(t('common.messages.deleteSuccess') || 'Success')`);
content = content.replace(/ElMessage\.error\(error\.message \|\| ['"].*?ɾ.*?['"]\)/g, `ElMessage.error(error.message || t('common.messages.deleteFailed') || 'Failed')`);

// List Health ALert
content = content.replace(/title=".*?ǰ.*?ȱ.*?.*?Ⱦ.*?ҵ.*?ֶ.*?б.*?ʾ.*?С.*?ͬ.*?ֶ.*?Ԫ.*?ݺ.*?ԡ.*?"/g, `:title="t('system.businessObject.messages.noBusinessFields') || 'Warning: No business fields defined for this object layout.'"`);

fs.writeFileSync('src/views/dynamic/DynamicListPage.vue', content, 'utf8');
console.log('Script completed Successfully!');
