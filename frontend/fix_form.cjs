const fs = require('fs');
let content = fs.readFileSync('src/views/dynamic/DynamicFormPage.vue', 'utf8');

// Add i18n import and initialization
content = content.replace(/import \{ ref, computed, onMounted \} from 'vue'/, `import { ref, computed, onMounted } from 'vue'\nimport { useI18n } from 'vue-i18n'`);
content = content.replace(/const router = useRouter\(\)/, `const router = useRouter()\nconst { t } = useI18n()`);

// Fix template string
content = content.replace(/ȡ/g, `{{ t('common.actions.cancel') }}`);

// Fix script strings
content = content.replace(/([\'\"])[^\"\']*³ɹ[^\"\']*([\'\"])/g, `t('common.messages.updateSuccess') || 'Update Success'`);
content = content.replace(/([\'\"])[^\"\']*ɹ[^\"\']*([\'\"])/g, `t('common.messages.createSuccess') || 'Create Success'`);
content = content.replace(/([\'\"])[^\"\']*ʧ[^\"\']*([\'\"])/g, `t('common.messages.operationFailed') || 'Operation Failed'`);

fs.writeFileSync('src/views/dynamic/DynamicFormPage.vue', content, 'utf8');
console.log('Fixed DynamicFormPage Successfully');
