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

fixFileRegex('src/components/common/BaseEmptyState.vue', [
    { find: /系统出错[^')]*'\)/g, replace: `系统出错')` }
]);

fixFileRegex('src/components/designer/ActionConfigurator.vue', [
    { find: /显示的消[^|]*\r?\n/g, replace: '显示的消息\"\n' },
    { find: /显示状[^|]*?>/g, replace: '显示状态\">' },
    { find: /存储的字[^|]*\r?\n/g, replace: '存储的字段\"\n' },
    { find: /[^\{]*\?字段相加\/相减\"/g, replace: '等字段相加/相减\"' },
    { find: /\(\) 运算[^<]*/g, replace: '() 运算符\"' },
    { find: /联动的字[^|]*\r?\n/g, replace: '联动的字段\"\n' },
    { find: /设置[^<]*<\/el-radio>/g, replace: '设置值\n            </el-radio>' },
    { find: /设置的[^<]*\r?\n\s*>/g, replace: '设置的值\"\n        >' },
    { find: /触发的动[^|]*\r?\n/g, replace: '触发的动作\"\n' },
    { find: /支[^\{]*\{字段代码\}/g, replace: '支持 {字段代码}' },
    { find: /\{quantity\}.字段/g, replace: '{quantity} 等字段' }
]);

fixFileRegex('src/components/designer/ConditionBuilder.vue', [
    { find: /添加条件[^<]*/g, replace: '添加条件组' },
    { find: /不等[^']*/g, replace: '不等于' },
    { find: /包含[^']*/g, replace: '包含于' },
    { find: /不为[^']*/g, replace: '不为空' },
    { find: /结尾[^']*/g, replace: '结尾是' },
    { find: /条件表达[^']*/g, replace: '条件表达式' }
]);

fixFileRegex('src/components/designer/RuleDesigner.vue', [
    { find: /显示名[^"]*"/g, replace: '显示名称"' },
    { find: /优先[^>]*>/g, replace: '优先级">' },
    { find: /详细说[^"]*"/g, replace: '详细说明"' },
    { find: /创建[^<]*\r?\n/g, replace: '创建时\"\n' },
    { find: /更新[^<]*\r?\n/g, replace: '更新时\"\n' },
    { find: /提交[^<]*\r?\n/g, replace: '提交时\"\n' },
    { find: /审批[^<]*\r?\n/g, replace: '审批时\"\n' },
    { find: /字段变更[^<]*\r?\n/g, replace: '字段变更时\"\n' },
    { find: /条件表达[^"]*"/g, replace: '条件表达式"' },
    { find: /测试数[^"]*"/g, replace: '测试数据"' },
    { find: /条件不满[^']*/g, replace: '条件不满足' },
    { find: /规则编[^']*/g, replace: '规则编码' },
    { find: /和下划[^']*/g, replace: '和下划线' },
    { find: /规则名[^']*/g, replace: '规则名称' },
    { find: /规则已更[^']*/g, replace: '规则已更新' },
    { find: /规则已创[^']*/g, replace: '规则已创建' }
]);

fixFileRegex('src/components/designer/WysiwygLayoutDesigner.vue', [
    { find: /自定义模[^']*/g, replace: '自定义模式' }
]);
