# GZEAMS 前端多语言适配完成度 PRD

## 文档信息
| 项目 | 说明 |
|------|------|
| PRD版本 | v1.0 |
| 创建日期 | 2026-02-07 |
| 涉及模块 | 前端所有模块 |
| 作者/Agent | Claude Code |

---

## 一、功能概述与业务场景

### 1.1 背景
GZEAMS 系统已完成 Vue I18n 基础设施搭建和部分模块的多语言适配。为了实现真正的国际化支持，需要完成所有前端组件和视图的中英文翻译。

### 1.2 业务场景
1. **国际用户支持** - 支持中英文双语切换
2. **一致性体验** - 所有界面元素统一使用多语言
3. **扩展性** - 预留未来支持更多语言的能力

### 1.3 当前状态
- ✅ Vue I18n 配置完成
- ✅ 语言切换组件实现
- ✅ 部分模块翻译完成 (system, assets, workflow)
- ❌ 大量硬编码中文未处理
- ❌ 基础组件未完全适配

---

## 二、用户角色与权限

| 角色 | 描述 | 权限 |
|------|------|------|
| 系统用户 | 使用系统的所有用户 | 可切换语言，系统自动保存偏好 |

---

## 三、公共模型引用声明

| 组件类型 | 基类/库 | 引用路径 | 说明 |
|---------|--------|---------|------|
| i18n框架 | Vue I18n | `vue-i18n@9` | Composition API 模式 |
| 语言存储 | LocalStorage | `localStorage.getItem('locale')` | 持久化用户偏好 |
| 状态管理 | Pinia Store | `@/stores/locale.ts` | 语言切换状态 |

---

## 四、翻译文件结构设计

### 4.1 文件组织

```
frontend/src/locales/
├── index.ts                  # 主配置文件
├── zh-CN/                   # 中文翻译
│   ├── index.ts            # 模块聚合
│   ├── common.json         # 通用UI元素
│   ├── form.json           # 表单相关
│   ├── table.json          # 表格相关
│   ├── message.json        # 消息提示
│   ├── validation.json     # 验证消息
│   ├── assets.json         # 资产模块
│   ├── inventory.json      # 盘点模块
│   ├── workflow.json       # 工作流模块
│   ├── finance.json        # 财务模块
│   ├── itAssets.json       # IT资产模块
│   └── mobile.json         # 移动端组件
└── en-US/                   # 英文翻译 (镜像结构)
    ├── index.ts
    ├── common.json
    ├── form.json
    └── ...
```

### 4.2 翻译键命名规范

```
{namespace}.{category}.{item}
```

**命名空间列表**:
- `common` - 通用UI元素 (按钮、操作、状态)
- `form` - 表单相关 (字段标签、占位符、验证)
- `table` - 表格相关 (列头、操作列)
- `message` - 消息提示 (成功、错误、警告)
- `validation` - 验证消息
- `asset` - 资产模块专用
- `inventory` - 盘点模块专用
- `workflow` - 工作流模块专用
- `mobile` - 移动端专用

---

## 五、API接口设计

无需后端接口，所有翻译在前端完成。

---

## 六、翻译内容清单

### 6.1 Common (common.json) - 通用UI元素

```json
{
  "actions": {
    "confirm": "确认",
    "cancel": "取消",
    "save": "保存",
    "delete": "删除",
    "edit": "编辑",
    "create": "新建",
    "add": "添加",
    "remove": "移除",
    "search": "搜索",
    "query": "查询",
    "reset": "重置",
    "submit": "提交",
    "close": "关闭",
    "back": "返回",
    "refresh": "刷新",
    "export": "导出",
    "import": "导入",
    "download": "下载",
    "upload": "上传",
    "view": "查看",
    "detail": "详情",
    "selectAll": "全选",
    "deselectAll": "取消全选",
    "batchDelete": "批量删除",
    "batchEdit": "批量编辑"
  },
  "status": {
    "loading": "加载中...",
    "success": "操作成功",
    "error": "操作失败",
    "warning": "警告",
    "info": "提示",
    "confirm": "确认操作",
    "processing": "处理中..."
  },
  "table": {
    "operations": "操作",
    "noData": "暂无数据",
    "total": "共 {total} 条",
    "selected": "已选择 {count} 项"
  },
  "pagination": {
    "total": "共 {total} 条",
    "page": "第 {current} / {total} 页",
    "goto": "前往",
    "pageSize": "每页显示"
  },
  "dialog": {
    "confirmDelete": "确认删除",
    "confirmDeleteMessage": "确定要删除选中的 {count} 条记录吗？",
    "confirmTitle": "确认操作",
    "confirmMessage": "确定要执行此操作吗？"
  },
  "time": {
    "justNow": "刚刚",
    "minutesAgo": "{minutes} 分钟前",
    "hoursAgo": "{hours} 小时前",
    "daysAgo": "{days} 天前",
    "yesterday": "昨天",
    "today": "今天"
  }
}
```

### 6.2 Form (form.json) - 表单相关

```json
{
  "fields": {
    "name": "名称",
    "code": "编码",
    "status": "状态",
    "type": "类型",
    "category": "类别",
    "description": "描述",
    "remark": "备注",
    "createTime": "创建时间",
    "updateTime": "更新时间",
    "createdBy": "创建人",
    "updatedBy": "更新人",
    "org": "所属组织",
    "dept": "所属部门",
    "user": "用户",
    "date": "日期",
    "time": "时间",
    "quantity": "数量",
    "amount": "金额",
    "price": "价格",
    "location": "位置",
    "address": "地址",
    "phone": "电话",
    "email": "邮箱",
    "attachment": "附件",
    "image": "图片"
  },
  "placeholders": {
    "input": "请输入{field}",
    "select": "请选择{field}",
    "search": "搜索{field}"
  },
  "validation": {
    "required": "该字段不能为空",
    "invalidFormat": "格式不正确",
    "invalidEmail": "邮箱格式不正确",
    "invalidPhone": "电话格式不正确",
    "minLength": "最少输入 {min} 个字符",
    "maxLength": "最多输入 {max} 个字符",
    "range": "请输入 {min} 到 {max} 之间的数值"
  },
  "actions": {
    "addRow": "添加行",
    "deleteRow": "删除行",
    "resetForm": "重置表单"
  }
}
```

### 6.3 Asset (assets.json) - 资产模块

```json
{
  "title": "固定资产管理",
  "list": "资产列表",
  "detail": "资产详情",
  "create": "新建资产",
  "edit": "编辑资产",
  "fields": {
    "assetCode": "资产编码",
    "assetName": "资产名称",
    "assetCategory": "资产分类",
    "specification": "规格型号",
    "unit": "计量单位",
    "quantity": "数量",
    "unitPrice": "单价",
    "totalValue": "总价值",
    "purchaseDate": "购置日期",
    "supplier": "供应商",
    "custodian": "保管人",
    "location": "存放位置",
    "department": "使用部门",
    "status": "资产状态"
  },
  "status": {
    "idle": "闲置",
    "inUse": "使用中",
    "maintenance": "维修中",
    "scrapped": "已报废",
    "disposed": "已处置",
    "borrowed": "借用中"
  },
  "operations": {
    "pickup": "领用",
    "return": "归还",
    "transfer": "调拨",
    "loan": "借用",
    "maintenance": "维修",
    "scrap": "报废",
    "dispose": "处置",
    "inventory": "盘点"
  }
}
```

### 6.4 Inventory (inventory.json) - 盘点模块

```json
{
  "title": "资产盘点",
  "taskList": "盘点任务",
  "taskDetail": "任务详情",
  "execute": "执行盘点",
  "fields": {
    "taskCode": "任务编号",
    "taskName": "任务名称",
    "taskType": "盘点类型",
    "planDate": "计划日期",
    "executor": "执行人",
    "status": "任务状态",
    "assetCount": "资产数量",
    "scannedCount": "已扫描数量",
    "differenceCount": "差异数量"
  },
  "status": {
    "pending": "待开始",
    "inProgress": "进行中",
    "completed": "已完成",
    "cancelled": "已取消"
  },
  "operations": {
    "scan": "扫码盘点",
    "manualInput": "手动输入",
    "confirmInventory": "确认盘点",
    "viewDifference": "查看差异",
    "submitReview": "提交审核"
  },
  "scanner": {
    "title": "扫码盘点",
    "scanResult": "扫描结果",
    "assetFound": "找到资产",
    "assetNotFound": "未找到资产",
    "scanSuccess": "扫描成功",
    "scanFailed": "扫描失败",
    "cameraError": "摄像头初始化失败",
    "selectCamera": "选择摄像头",
    "manualInput": "手动输入",
    "inputPlaceholder": "请输入资产编码或扫描二维码"
  }
}
```

### 6.5 Workflow (workflow.json) - 工作流模块

```json
{
  "title": "工作流管理",
  "designer": "流程设计器",
  "taskCenter": "任务中心",
  "myApprovals": "我的审批",
  "fields": {
    "processName": "流程名称",
    "processCode": "流程编码",
    "version": "版本",
    "status": "状态",
    "approvalType": "审批方式",
    "approver": "审批人",
    "timeout": "超时时间",
    "timeoutAction": "超时操作"
  },
  "approvalType": {
    "or": "或签",
    "and": "会签",
    "sequence": "依次审批"
  },
  "timeoutAction": {
    "pass": "自动通过",
    "reject": "自动拒绝",
    "transfer": "转交上级"
  },
  "status": {
    "pending": "待审批",
    "approved": "已通过",
    "rejected": "已拒绝",
    "cancelled": "已撤销"
  },
  "actions": {
    "approve": "通过",
    "reject": "拒绝",
    "transfer": "转交",
    "comment": "评论",
    "viewHistory": "查看历史"
  }
}
```

### 6.6 Mobile (mobile.json) - 移动端组件

```json
{
  "scanner": {
    "title": "扫码",
    "startScan": "开始扫描",
    "stopScan": "停止扫描",
    "scanResult": "扫描结果",
    "noResult": "未扫描到内容",
    "permissionDenied": "相机权限被拒绝",
    "cameraUnavailable": "相机不可用"
  },
  "assetDetail": {
    "title": "资产详情",
    "basicInfo": "基本信息",
    "usageInfo": "使用信息",
    "maintenanceInfo": "维护信息",
    "operations": "操作"
  }
}
```

---

## 七、实施计划

### 7.1 阶段划分

| 阶段 | 内容 | 文件数 | 预估工作量 |
|------|------|--------|-----------|
| Phase 1 | 基础组件适配 | 6 | 4小时 |
| Phase 2 | 通用翻译完善 | 6个JSON | 2小时 |
| Phase 3 | 资产模块适配 | ~10 | 3小时 |
| Phase 4 | 盘点模块适配 | ~5 | 2小时 |
| Phase 5 | 工作流模块适配 | ~5 | 2小时 |
| Phase 6 | 移动端组件适配 | ~5 | 2小时 |
| Phase 7 | 测试与修复 | - | 2小时 |

**总计**: ~36个文件，17小时

### 7.2 详细任务清单

#### Phase 1: 基础组件适配 (P0)

1. **BaseListPage.vue**
   - 替换表格操作按钮
   - 替换分页文案
   - 替换搜索占位符
   - 替换空状态文案

2. **BaseFormPage.vue**
   - 替换表单按钮
   - 替换验证消息
   - 替换提交成功/失败提示

3. **BaseDetailPage.vue**
   - 替换基本信息标题
   - 替换审计信息标题

4. **BaseFileUpload.vue**
   - 替换上传按钮
   - 替换文件类型提示
   - 替换大小限制提示

5. **SectionBlock.vue**
   - 替换展开/折叠提示

6. **ColumnManager.vue**
   - 替换列设置标题
   - 替换保存/取消按钮

#### Phase 2: 通用翻译完善

创建/完善以下翻译文件：
- `common.json` - 通用UI元素
- `form.json` - 表单相关
- `table.json` - 表格相关
- `message.json` - 消息提示
- `validation.json` - 验证消息
- `mobile.json` - 移动端组件

#### Phase 3: 资产模块适配

1. `views/assets/AssetList.vue`
2. `views/assets/AssetForm.vue`
3. `views/assets/AssetDetail.vue`
4. `views/assets/operations/LoanList.vue`
5. `views/assets/operations/LoanForm.vue`
6. `views/assets/operations/PickupList.vue`
7. `views/assets/operations/PickupForm.vue`
8. `views/assets/operations/ReturnList.vue`
9. `views/assets/operations/ReturnForm.vue`
10. `views/assets/operations/TransferList.vue`
11. `views/assets/operations/TransferForm.vue`

#### Phase 4: 盘点模块适配

1. `views/inventory/TaskList.vue`
2. `views/inventory/TaskExecute.vue`
3. `components/mobile/MobileQRScanner.vue`

#### Phase 5: 工作流模块适配

1. `views/workflow/TaskCenter.vue`
2. `views/workflow/MyApprovals.vue`
3. `components/workflow/WorkflowDesigner.vue`

#### Phase 6: 移动端组件适配

1. `views/mobile/assets/AssetDetail.vue`
2. 其他移动端视图

#### Phase 7: 测试与修复

1. 逐模块测试语言切换
2. 检查遗漏的硬编码文本
3. 验证翻译准确性
4. 性能测试

---

## 八、测试用例

### 8.1 功能测试

| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| 语言切换 | 点击语言切换器，选择英文 | 所有文案切换为英文 |
| 持久化 | 切换语言后刷新页面 | 语言保持为选择的语言 |
| 基础组件 | 测试列表/表单/详情页 | 所有文案使用翻译 |
| 移动端 | 测试移动端扫码页面 | 移动端文案正确翻译 |

### 8.2 回归测试

1. 确保所有功能不受语言切换影响
2. 确保表单验证消息正确显示
3. 确保API错误消息正确处理

---

## 九、验收标准

1. ✅ 所有Vue组件中无硬编码中文字符
2. ✅ 所有翻译键在zh-CN和en-US中都有对应值
3. ✅ 语言切换流畅，无页面闪烁
4. ✅ 移动端所有文案正确翻译
5. ✅ 通过所有E2E测试

---

## 十、注意事项

1. **翻译键命名一致性** - 遵循 `{namespace}.{category}.{item}` 格式
2. **参数插值** - 使用 `{parameter}` 格式，如 `{field}`, `{count}`
3. **上下文相关** - 同一词在不同上下文可能需要不同翻译
4. **性能考虑** - 翻译文件在首次加载时引入，使用懒加载
5. **回退机制** - 缺失翻译时回退到中文

---

## 附录A: 快速参考

### 常用翻译模式

```vue
<!-- 按钮文本 -->
<el-button>{{ $t('common.actions.save') }}</el-button>

<!-- 带参数的翻译 -->
<el-input :placeholder="$t('form.placeholders.input', { field: $t('form.fields.name') })" />

<!-- 脚本中使用 -->
const { t } = useI18n()
ElMessage.success(t('message.success'))

<!-- 复数形式 -->
<span>{{ $t('table.selected', { count: selectedRows.length }) }}</span>
```

### 检查命令

```bash
# 查找未翻译的中文
grep -r "[\u4e00-\u9fa5]" frontend/src/components/
grep -r "[\u4e00-\u9fa5]" frontend/src/views/

# 检查翻译文件完整性
npm run i18n:check  # 如果有配置的话
```
