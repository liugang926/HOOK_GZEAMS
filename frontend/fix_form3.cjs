const fs = require('fs');
let content = fs.readFileSync('src/views/dynamic/DynamicFormPage.vue', 'utf8');

// Fix the bad title replacement
content = content.replace(/title=t\('common\.messages\.operationFailed'\) \|\| 'Operation Failed'/, `:title="t('common.messages.loadFailed') || 'Load Failed'"`);

// Fix loadError extra buttons
content = content.replace(/@click="retryLoad"\s*>[\s\S]*?<\/el-button>/, `@click="retryLoad"\n          >\n            {{ t('common.actions.refresh') }}\n          </el-button>`);
content = content.replace(/@click="\$router\.back\(\)"\s*>[\s\S]*?<\/el-button>/, `@click="$router.back()"\n          >\n            {{ t('common.actions.back') }}\n          </el-button>`);

// Fix save/cancel buttons in drawer footer
content = content.replace(/@click="handleCancel"\s*>[\s\S]*?<\/el-button>/, `@click="handleCancel"\n        >\n          {{ t('common.actions.cancel') }}\n        </el-button>`);
content = content.replace(/@click="handleSubmit"\s*>[\s\S]*?<\/el-button>/, `@click="handleSubmit"\n        >\n          {{ t('common.actions.save') }}\n        </el-button>`);

fs.writeFileSync('src/views/dynamic/DynamicFormPage.vue', content, 'utf8');
console.log('Fixed DynamicFormPage syntaxes successfully');
