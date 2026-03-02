const fs = require('fs');
let content = fs.readFileSync('src/views/dynamic/DynamicListPage.vue', 'utf8');

// Fix unifiedSearchFields label
content = content.replace(/prop:\s*'__unifiedKeyword',\s*label:\s*'.*?',\s*type:\s*'slot'/, `prop: '__unifiedKeyword',\n      label: t('common.actions.search'),\n      type: 'slot'`);

// Fix batchActions label and confirm
content = content.replace(/label:\s*'.*?ɾ.*?',\s*type:\s*'danger'/, `label: t('common.actions.batchDelete') || 'Batch Delete',\n      type: 'danger'`);
content = content.replace(/await ElMessageBox\.confirm\(\`.*?ɾ.*?/, `await ElMessageBox.confirm(\n            t('common.messages.confirmDelete') || 'Confirm Delete',\n            t('common.dialog.confirmTitle') || 'Confirm',\n            {`);
content = content.replace(/ElMessage\.success\('.*?ɹ.*?'\)/, `ElMessage.success(t('common.messages.deleteSuccess') || 'Success')`);
content = content.replace(/ElMessage\.error\(error\.message \|\| '.*?ʧ.*?'\)/, `ElMessage.error(error.message || t('common.messages.deleteFailed') || 'Failed')`);

fs.writeFileSync('src/views/dynamic/DynamicListPage.vue', content, 'utf8');
console.log('Fixed search label and batch actions');
