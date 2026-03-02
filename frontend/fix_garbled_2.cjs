const fs = require('fs');

const fixFileRegex = (path, rules) => {
    let content = fs.readFileSync(path, 'utf8');
    const original = content;
    for (const rule of rules) {
        content = content.replace(rule.find, rule.replace);
    }
    if (content !== original) {
        fs.writeFileSync(path, content, 'utf8');
        console.log('Fixed ' + path);
    }
};

fixFileRegex('src/components/designer/ConditionBuilder.vue', [
    { find: /'不等于'all'\] \},/g, replace: `'不等于', types: ['all'] },` },
    { find: /'包含于'all'\] \},/g, replace: `'包含于', types: ['all'] },` },
    { find: /'不为空'all'\] \},/g, replace: `'不为空', types: ['all'] },` },
    { find: /'结尾是'string'\] \},/g, replace: `'结尾是', types: ['string'] },` }
]);

fixFileRegex('src/components/designer/RuleDesigner.vue', [
    { find: /编码'blur' \},/g, replace: `编码', trigger: 'blur' },` },
    { find: /下划线'blur' \}/g, replace: `下划线', trigger: 'blur' }` },
    { find: /名称'blur' \}/g, replace: `名称', trigger: 'blur' }` },
    { find: /'规则已更新'规则已创建'saved'/g, replace: `'规则已更新' : '规则已创建')\n    emit('saved'` }
]);

fixFileRegex('src/components/designer/WysiwygLayoutDesigner.vue', [
    { find: /自定义模式'active'"/g, replace: `自定义模式' }}\n        </el-tag>\n        <el-button\n          :disabled="previewMode === 'active'"` },
    { find: /搜索字段名称或编\?\.\./g, replace: `搜索字段名称或编码...` },
    { find: /已切换到自定义模式\?\)/g, replace: `已切换到自定义模式')` }
]);
