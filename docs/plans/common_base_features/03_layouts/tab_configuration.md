# 标签页（Tabs）配置规范

## 目录
1. [标签页概述](#1-标签页概述)
2. [标签页配置模型](#2-标签页配置模型)
3. [标签页布局配置](#3-标签页布局配置)
4. [标签页交互配置](#4-标签页交互配置)
5. [标签页内容配置](#5-标签页内容配置)
6. [标签页权限配置](#6-标签页权限配置)
7. [标签页响应式配置](#7-标签页响应式配置)
8. [标签页事件配置](#8-标签页事件配置)
9. [前端实现](#9-前端实现)
10. [使用示例](#10-使用示例)

---

## 1. 标签页概述

### 1.1 定义

**标签页（Tabs）**是一种页面内容组织方式，通过将相关内容分组到不同的标签页中，实现内容的分类展示和切换。标签页适用于字段数量较多（通常超过12个）或内容有明显业务分组的场景。

### 1.2 使用场景

| 场景 | 适用标签页 | 适用区块 |
|------|-----------|---------|
| 字段数量 8-12 个 | 可选 | 推荐 |
| 字段数量 12-20 个 | 推荐 | 不推荐（嵌套过深） |
| 字段数量 20+ 个 | 强烈推荐 | 不推荐 |
| 内容有明显业务分组 | 推荐 | 可选 |
| 需要独立保存子内容 | 推荐 | 不推荐 |

### 1.3 与区块的选择原则

**选择标签页**：
- 内容分块数量超过 4 个
- 每个分块内的字段数量较多（>8个）
- 需要在标签页之间进行独立操作
- 内容占用空间较大，需要折叠隐藏

**选择区块**：
- 内容分块数量较少（2-4个）
- 每个分块内的字段数量适中（<8个）
- 需要一次性看到所有内容概览
- 需要按顺序填写信息

**混合使用**：
- 外层使用标签页进行大分类
- 标签页内使用区块进行小分组
- 最深嵌套层级不超过 3 层

### 1.4 设计原则

1. **标签数量适中**：单个标签页组件的标签数量建议 3-7 个
2. **标签标题简洁**：标签标题不超过 6 个字
3. **内容平衡**：各标签页的字段数量尽量均衡
4. **优先级排序**：高频使用的标签放在前面
5. **关联性分组**：相关内容放在同一标签页内

---

## 2. 标签页配置模型

### 2.1 TabConfig 数据结构

**TabConfig 配置属性：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `id` | String | required | 标签页容器唯一标识 |
| `type` | String | 'tab' | 类型标识 |
| `position` | String | 'top' | 标签页位置：top/left/right/bottom |
| `type_style` | String | 'card' | 标签页样式类型 |
| `stretch` | Boolean | false | 是否拉伸标签页宽度 |
| `lazy` | Boolean | true | 是否懒加载 |
| `animated` | Boolean | true | 是否启用切换动画 |
| `closable` | Boolean | false | 标签是否可关闭 |
| `addable` | Boolean | false | 是否可动态添加标签 |
| `editable` | Boolean | false | 是否可编辑标签标题 |
| `draggable` | Boolean | false | 标签是否可拖拽排序 |
| `default_active` | String | null | 默认激活的标签 |
| `tabs` | Array | [] | 标签列表 |

**Tab 对象属性：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `id` | String | required | 标签唯一标识 |
| `title` | String | required | 标签标题 |
| `icon` | String | null | 标签图标 |
| `disabled` | Boolean | false | 是否禁用 |
| `closable` | Boolean | false | 该标签是否可关闭 |
| `lazy` | Boolean | true | 该标签是否懒加载 |
| `badge` | Object | null | 徽章配置 |
| `sections` | Array | [] | 标签内的区块 |
| `visibility_rules` | Array | [] | 标签显示规则 |
| `permission` | String | null | 标签权限要求 |
| `custom_class` | String | '' | 自定义样式类 |

### 2.2 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

### 2.3 TabConfig 表结构定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUIDField | PK | 主键（继承自BaseModel） |
| `organization` | ForeignKey | SET_NULL, to='organizations.Organization' | 所属组织（继承自BaseModel） |
| `is_deleted` | BooleanField | default=False | 软删除标记（继承自BaseModel） |
| `deleted_at` | DateTimeField | null, blank | 删除时间（继承自BaseModel） |
| `created_at` | DateTimeField | auto_now_add | 创建时间（继承自BaseModel） |
| `updated_at` | DateTimeField | auto_now | 更新时间（继承自BaseModel） |
| `created_by` | ForeignKey | SET_NULL, to='accounts.User' | 创建人（继承自BaseModel） |
| `custom_fields` | JSONField | default=dict | 自定义字段（继承自BaseModel） |
| `name` | CharField(50) | choices: form_tabs/detail_tabs | 配置名称 |
| `business_object` | ForeignKey | CASCADE, to='BusinessObject' | 关联业务对象 |
| `position` | CharField(10) | choices: top/left/right/bottom, default='top' | 标签页位置 |
| `type_style` | CharField(20) | choices: ''/card/border-card, default='' | 样式类型 |
| `stretch` | BooleanField | default=False | 拉伸标签页宽度 |
| `lazy` | BooleanField | default=True | 懒加载 |
| `animated` | BooleanField | default=True | 切换动画 |
| `tabs_config` | JSONField | default=list | 标签页配置（JSON） |
| `is_active` | BooleanField | default=True | 是否启用 |

    # 是否启用
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    class Meta:
        db_table = 'system_tab_config'
        verbose_name = '标签页配置'
        verbose_name_plural = '标签页配置'
        unique_together = [['business_object', 'name', 'organization']]

    def __str__(self):
        return f"{self.business_object.name} - {self.get_name_display()}"
```

---

## 3. 标签页布局配置

### 3.1 标签页位置（position）

| 位置值 | 说明 | 适用场景 |
|-------|------|---------|
| `top` | 顶部标签页（默认） | 大多数场景，最常见 |
| `left` | 左侧标签页 | 需要显示较多标签（5+个）时 |
| `right` | 右侧标签页 | 特殊布局需求，较少使用 |
| `bottom` | 底部标签页 | 特殊布局需求，较少使用 |

### 3.2 标签页样式类型（type_style）

| 样式值 | 说明 | Element Plus 对应 |
|-------|------|-------------------|
| ``（空字符串） | 默认样式，简洁分隔 | `type=""` |
| `card` | 卡片类型，标签有背景色 | `type="card"` |
| `border-card` | 带边框的卡片类型 | `type="border-card"` |

### 3.3 标签页尺寸

标签页支持通过 `size` 属性控制尺寸：

| 尺寸值 | 高度 | 字体大小 | 适用场景 |
|-------|------|---------|---------|
| `large` | 40px | 16px | 大屏展示、重要内容 |
| `default` | 32px | 14px | 标准场景（默认） |
| `small` | 28px | 12px | 密集布局、移动端 |

### 3.4 标签页间距

```javascript
{
  "tab_margin": "0 16px",          // 标签之间的外边距
  "tab_padding": "12px 20px",      // 标签内边距
  "pane_padding": "16px",          // 内容区内边距
  "content_gap": 16                // 内容元素间距
}
```

---

## 4. 标签页交互配置

### 4.1 默认激活标签

```javascript
{
  "default_active": "tab-basic",   // 通过标签 id 指定默认激活的标签
  "default_active_index": 0         // 或通过索引指定（0-based）
}
```

### 4.2 标签页切换动画

```javascript
{
  "animated": true,                // 是否启用切换动画
  "animation_duration": 300,       // 动画持续时间（毫秒）
  "animation_timing": "ease-in-out" // 动画缓动函数
}
```

### 4.3 标签页懒加载

懒加载指标签内容仅在首次切换到该标签时才加载。

```javascript
{
  "lazy": true,                    // 全局懒加载开关
  "lazy_load_strategy": "once",    // 懒加载策略: once(一次) / always(总是)
  "cache_loaded": true,            // 是否缓存已加载内容
  "unload_on_hide": false          // 隐藏时是否卸载内容
}
```

### 4.4 标签页可关闭配置

```javascript
{
  "closable": true,                 // 全局可关闭开关
  "close_confirm": true,           // 关闭时是否确认
  "close_confirm_text": "确定要关闭此标签吗？",
  "min_tabs": 1,                   // 最少保留的标签数量
  "hide_on_close": true            // 关闭后是否隐藏（而非移除）
}
```

### 4.5 标签页可拖拽排序

```javascript
{
  "draggable": true,               // 是否启用拖拽排序
  "draggable_animation": 150,      // 拖拽动画时长
  "sort_on_drop": true,            // 拖拽释放后是否更新配置
  "save_order_on_drop": true       // 是否保存排序结果
}
```

### 4.6 可添加标签（动态标签）

```javascript
{
  "addable": true,                 // 是否允许动态添加标签
  "add_button_text": "添加标签",
  "add_button_icon": "Plus",
  "max_tabs": 10,                  // 最大标签数量
  "new_tab_template": {            // 新标签默认配置
    "title": "新标签",
    "sections": []
  }
}
```

---

## 5. 标签页内容配置

### 5.1 标签页内字段配置

```javascript
{
  "tabs": [
    {
      "id": "tab-basic",
      "title": "基本信息",
      "fields": [                   // 直接字段列表（简化模式）
        {
          "field": "asset_code",
          "label": "资产编码",
          "span": 12,
          "required": true
        },
        {
          "field": "asset_name",
          "label": "资产名称",
          "span": 12,
          "required": true
        }
      ]
    }
  ]
}
```

### 5.2 标签页内区块配置

```javascript
{
  "tabs": [
    {
      "id": "tab-detail",
      "title": "详细信息",
      "sections": [                // 区块列表（标准模式）
        {
          "id": "section-spec",
          "title": "规格信息",
          "columns": 2,
          "collapsible": false,
          "fields": [
            {"field": "specification", "label": "规格型号", "span": 12},
            {"field": "brand", "label": "品牌", "span": 12},
            {"field": "model", "label": "型号", "span": 12}
          ]
        }
      ]
    }
  ]
}
```

### 5.3 标签页内表格配置

```javascript
{
  "tabs": [
    {
      "id": "tab-items",
      "title": "明细项",
      "table_config": {            // 表格配置
        "columns": [
          {"prop": "item_code", "label": "项目编码", "width": 150},
          {"prop": "item_name", "label": "项目名称", "width": 200},
          {"prop": "quantity", "label": "数量", "width": 100},
          {"prop": "price", "label": "单价", "width": 120}
        ],
        "row_actions": ["edit", "delete"],
        "toolbar_actions": ["add"]
      }
    }
  ]
}
```

### 5.4 标签页内嵌套表单配置

```javascript
{
  "tabs": [
    {
      "id": "tab-subform",
      "title": "子表单",
      "subform_config": {          // 嵌套表单配置
        "mode": "inline",           // inline | dialog | drawer
        "layout": "horizontal",
        "label_width": "120px",
        "sections": [
          {
            "id": "sub-section-1",
            "fields": [
              {"field": "sub_field1", "label": "子字段1", "span": 12},
              {"field": "sub_field2", "label": "子字段2", "span": 12}
            ]
          }
        ]
      }
    }
  ]
}
```

---

## 6. 标签页权限配置

### 6.1 标签页级别的显示权限

```javascript
{
  "tabs": [
    {
      "id": "tab-sensitive",
      "title": "敏感信息",
      "permission": {
        "code": "assets.view_sensitive",     // 权限代码
        "logic": "any",                      // all(所有) | any(任一)
        "permissions": [
          "assets.view_sensitive",
          "assets.admin"
        ]
      },
      "no_permission_action": "hide"     // hide(隐藏) | disable(禁用) | mask(脱敏)
    }
  ]
}
```

### 6.2 标签页级别的操作权限

```javascript
{
  "tabs": [
    {
      "id": "tab-approval",
      "title": "审批信息",
      "actions": {
        "approve": {
          "permission": "workflow.approve",
          "label": "审批",
          "type": "primary"
        },
        "reject": {
          "permission": "workflow.reject",
          "label": "驳回",
          "type": "danger"
        }
      }
    }
  ]
}
```

### 6.3 动态标签页（根据权限动态生成）

```javascript
{
  "dynamic_tabs": {               // 动态标签配置
    "source": "permission",       // 权限来源
    "mapping": [                  // 权限到标签的映射
      {
        "permission": "assets.view_financial",
        "tab": {
          "id": "tab-financial",
          "title": "财务信息",
          "sections": [...]
        }
      },
      {
        "permission": "assets.view_maintenance",
        "tab": {
          "id": "tab-maintenance",
          "title": "维护信息",
          "sections": [...]
        }
      }
    ]
  }
}
```

---

## 7. 标签页响应式配置

### 7.1 移动端标签页布局

```javascript
{
  "responsive": {
    "mobile": {                   // 移动端配置 (<768px)
      "position": "top",          // 移动端强制使用顶部标签
      "type_style": "",           // 使用简洁样式
      "size": "small",            // 小尺寸
      "stretch": true,            // 拉伸标签页宽度
      "scrollable": true,         // 允许横向滚动
      "pane_padding": "12px"      // 减小内边距
    },
    "tablet": {                   // 平板配置 (768px-1199px)
      "position": "top",
      "size": "default",
      "stretch": false,
      "pane_padding": "16px"
    },
    "desktop": {                  // 桌面配置 (≥1200px)
      "position": "top",
      "size": "default",
      "stretch": false,
      "pane_padding": "20px"
    }
  }
}
```

### 7.2 标签页横向滚动

```javascript
{
  "scrollable": true,             // 是否启用横向滚动
  "scroll_threshold": 4,          // 超过此数量的标签时启用滚动
  "scroll_button_style": {        // 滚动按钮样式
    "prev_icon": "ArrowLeft",
    "next_icon": "ArrowRight"
  }
}
```

### 7.3 响应式标签列数

```javascript
{
  "tabs": [
    {
      "id": "tab-responsive",
      "title": "响应式标签",
      "sections": [
        {
          "id": "section-responsive",
          "responsive_columns": {  // 响应式列数配置
            "mobile": 1,            // 移动端单列
            "tablet": 2,            // 平板端两列
            "desktop": 3            // 桌面端三列
          },
          "fields": [...]
        }
      ]
    }
  ]
}
```

---

## 8. 标签页事件配置

### 8.1 标签页切换前事件

```javascript
{
  "events": {
    "before_tab_change": {         // 切换前事件
      "enabled": true,
      "handler": "handleBeforeTabChange",
      "confirm_if_dirty": true,     // 如果表单有修改，是否确认
      "confirm_message": "当前标签有未保存的修改，确定要切换吗？"
    }
  }
}
```

### 8.2 标签页切换后事件

```javascript
{
  "events": {
    "after_tab_change": {          // 切换后事件
      "enabled": true,
      "handler": "handleAfterTabChange",
      "actions": [                 // 切换后执行的操作
        {
          "type": "api_call",
          "api": "/api/assets/{id}/validate",
          "method": "get"
        },
        {
          "type": "log",
          "message": "切换到标签: {tabName}"
        }
      ]
    }
  }
}
```

### 8.3 标签页关闭事件

```javascript
{
  "events": {
    "tab_close": {                 // 关闭事件
      "enabled": true,
      "handler": "handleTabClose",
      "confirm": true,
      "confirm_message": "确定要关闭此标签吗？未保存的内容将丢失。"
    }
  }
}
```

---

## 9. 前端实现

### 9.1 DynamicTabs 组件

```vue
<template>
  <div class="dynamic-tabs" :class="tabClass">
    <el-tabs
      v-model="activeTab"
      :type="config.type_style || ''"
      :position="config.position || 'top'"
      :stretch="config.stretch || false"
      :lazy="config.lazy !== false"
      :animated="config.animated !== false"
      :closable="config.closable || false"
      :addable="config.addable || false"
      :editable="config.editable || false"
      :tab-position="config.position || 'top'"
      :before-leave="handleBeforeLeave"
      @tab-change="handleTabChange"
      @tab-remove="handleTabRemove"
      @tab-add="handleTabAdd"
    >
      <el-tab-pane
        v-for="tab in visibleTabs"
        :key="tab.id"
        :label="renderTabLabel(tab)"
        :name="tab.id"
        :disabled="tab.disabled || false"
        :lazy="tab.lazy !== false"
        :closable="tab.closable || false"
      >
        <!-- 标签页内容 -->
        <tab-content
          :config="tab"
          :form-data="formData"
          :disabled="disabled"
          @field-change="handleFieldChange"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 滚动按钮 -->
    <template v-if="config.scrollable && showScrollButtons">
      <div class="tab-scroll-btn prev" @click="scrollPrev">
        <el-icon><ArrowLeft /></el-icon>
      </div>
      <div class="tab-scroll-btn next" @click="scrollNext">
        <el-icon><ArrowRight /></el-icon>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import TabContent from './TabContent.vue'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  modelValue: {
    type: String,
    default: ''
  },
  formData: {
    type: Object,
    default: () => ({})
  },
  disabled: {
    type: Boolean,
    default: false
  },
  userPermissions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'tab-change', 'tab-close', 'tab-add'])

// 状态
const activeTab = ref(props.modelValue || props.config.default_active)
const isDirty = ref(false)

// 计算属性
const tabClass = computed(() => {
  const classes = [`tabs-position-${props.config.position || 'top'}`]
  if (props.config.type_style) {
    classes.push(`tabs-type-${props.config.type_style}`)
  }
  return classes.join(' ')
})

const visibleTabs = computed(() => {
  return props.config.tabs.filter(tab => {
    // 检查显示规则
    if (tab.visibility_rules && !evaluateVisibilityRules(tab.visibility_rules)) {
      return false
    }
    // 检查权限
    if (tab.permission && !checkPermission(tab.permission)) {
      return false
    }
    return true
  })
})

const showScrollButtons = computed(() => {
  return visibleTabs.value.length > (props.config.scroll_threshold || 4)
})

// 方法
const renderTabLabel = (tab) => {
  let label = tab.title
  if (tab.icon) {
    return `${tab.icon} ${label}`
  }
  if (tab.badge) {
    return `${label} ${tab.badge}`
  }
  return label
}

const evaluateVisibilityRules = (rules) => {
  // 实现显示规则评估逻辑
  return true
}

const checkPermission = (permission) => {
  if (typeof permission === 'string') {
    return props.userPermissions.includes(permission)
  }
  if (permission.permissions) {
    const perms = permission.permissions
    return permission.logic === 'any'
      ? perms.some(p => props.userPermissions.includes(p))
      : perms.every(p => props.userPermissions.includes(p))
  }
  return true
}

const handleBeforeLeave = (activeName, oldActiveName) => {
  if (props.config.events?.before_tab_change?.enabled && isDirty.value) {
    const confirmMsg = props.config.events.before_tab_change.confirm_message ||
      '当前标签有未保存的修改，确定要切换吗？'
    return confirm(confirmMsg)
  }
  return true
}

const handleTabChange = (tabName) => {
  activeTab.value = tabName
  emit('update:modelValue', tabName)
  emit('tab-change', tabName)

  // 执行切换后事件
  if (props.config.events?.after_tab_change?.enabled) {
    executeTabActions(props.config.events.after_tab_change.actions, { tabName })
  }

  isDirty.value = false
}

const handleTabRemove = (tabName) => {
  if (props.config.events?.tab_close?.enabled) {
    const confirmMsg = props.config.events.tab_close.confirm_message ||
      '确定要关闭此标签吗？'
    if (props.config.events.tab_close.confirm && !confirm(confirmMsg)) {
      return
    }
  }
  emit('tab-close', tabName)
}

const handleTabAdd = () => {
  const newTab = {
    ...props.config.new_tab_template,
    id: `tab-${Date.now()}`
  }
  emit('tab-add', newTab)
}

const executeTabActions = (actions, context) => {
  if (!actions) return
  actions.forEach(action => {
    switch (action.type) {
      case 'api_call':
        // 执行 API 调用
        break
      case 'log':
        console.log(action.message, context)
        break
    }
  })
}

const scrollPrev = () => {
  // 实现向前滚动
}

const scrollNext = () => {
  // 实现向后滚动
}

// 监听
watch(() => props.modelValue, (newVal) => {
  activeTab.value = newVal || props.config.default_active
})
</script>

<style scoped lang="scss">
.dynamic-tabs {
  position: relative;

  &.tabs-position-left {
    :deep(.el-tabs__header) {
      flex-direction: column;
    }
  }

  &.tabs-position-right {
    :deep(.el-tabs__header) {
      flex-direction: column;
    }
  }

  .tab-scroll-btn {
    position: absolute;
    top: 0;
    z-index: 10;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fff;
    border: 1px solid #dcdfe6;
    cursor: pointer;

    &.prev {
      left: 0;
    }

    &.next {
      right: 0;
    }

    &:hover {
      background: #f5f7fa;
    }
  }
}
</style>
```

### 9.2 TabContent 组件

```vue
<template>
  <div class="tab-content">
    <!-- 直接字段模式 -->
    <template v-if="config.fields">
      <field-grid
        :fields="config.fields"
        :form-data="formData"
        :columns="config.columns || 1"
        :disabled="disabled"
        @field-change="handleFieldChange"
      />
    </template>

    <!-- 区块模式 -->
    <template v-else-if="config.sections">
      <section-block
        v-for="section in config.sections"
        :key="section.id"
        :config="section"
        :form-data="formData"
        :disabled="disabled"
        @field-change="handleFieldChange"
      />
    </template>

    <!-- 表格模式 -->
    <template v-else-if="config.table_config">
      <sub-table
        :config="config.table_config"
        :form-data="formData"
        :disabled="disabled"
        @field-change="handleFieldChange"
      />
    </template>

    <!-- 嵌套表单模式 -->
    <template v-else-if="config.subform_config">
      <sub-form
        :config="config.subform_config"
        :form-data="formData"
        :disabled="disabled"
        @field-change="handleFieldChange"
      />
    </template>
  </div>
</template>

<script setup>
import { provide, inject } from 'vue'
import FieldGrid from './FieldGrid.vue'
import SectionBlock from './SectionBlock.vue'
import SubTable from './SubTable.vue'
import SubForm from './SubForm.vue'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  formData: {
    type: Object,
    default: () => ({})
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['field-change'])

const handleFieldChange = (field, value) => {
  emit('field-change', field, value)
}
</script>
```

---

## 10. 使用示例

### 10.1 资产表单标签页配置

```json
{
  "layout_type": "form",
  "layout_mode": "tabs",
  "tabs": [
    {
      "id": "tab-basic",
      "title": "基本信息",
      "icon": "Document",
      "sections": [
        {
          "id": "section-basic",
          "title": "基本资料",
          "columns": 2,
          "fields": [
            {"field": "code", "label": "资产编码", "span": 12, "required": true},
            {"field": "name", "label": "资产名称", "span": 12, "required": true},
            {"field": "category", "label": "资产分类", "span": 12, "required": true},
            {"field": "status", "label": "资产状态", "span": 12, "required": true}
          ]
        }
      ]
    },
    {
      "id": "tab-detail",
      "title": "详细信息",
      "icon": "InfoFilled",
      "sections": [
        {
          "id": "section-spec",
          "title": "规格信息",
          "columns": 2,
          "fields": [
            {"field": "specification", "label": "规格型号", "span": 12},
            {"field": "brand", "label": "品牌", "span": 12},
            {"field": "model", "label": "型号", "span": 12},
            {"field": "serial_number", "label": "序列号", "span": 12}
          ]
        }
      ]
    },
    {
      "id": "tab-purchase",
      "title": "采购信息",
      "icon": "ShoppingCart",
      "permission": "assets.view_financial",
      "sections": [
        {
          "id": "section-purchase",
          "title": "采购详情",
          "columns": 2,
          "fields": [
            {"field": "purchase_date", "label": "采购日期", "span": 12},
            {"field": "purchase_price", "label": "采购价格", "span": 12},
            {"field": "supplier", "label": "供应商", "span": 12},
            {"field": "warranty_period", "label": "保修期（月）", "span": 12}
          ]
        }
      ]
    },
    {
      "id": "tab-lifecycle",
      "title": "生命周期",
      "icon": "Clock",
      "sections": [
        {
          "id": "section-lifecycle",
          "title": "生命周期事件",
          "type": "timeline",
          "timeline_config": {
            "field": "status_logs",
            "timestamp_field": "created_at",
            "content_field": "description"
          }
        }
      ]
    }
  ]
}
```

### 10.2 带主从表的标签页配置

```json
{
  "layout_type": "form",
  "layout_mode": "tabs",
  "tabs": [
    {
      "id": "tab-main",
      "title": "主信息",
      "sections": [
        {
          "id": "section-main",
          "title": "申请信息",
          "columns": 2,
          "fields": [
            {"field": "code", "label": "申请编号", "span": 12, "readonly": true},
            {"field": "request_date", "label": "申请日期", "span": 12, "required": true},
            {"field": "department", "label": "申请部门", "span": 12, "required": true},
            {"field": "requester", "label": "申请人", "span": 12, "required": true}
          ]
        }
      ]
    },
    {
      "id": "tab-items",
      "title": "明细项",
      "table_config": {
        "columns": [
          {"field": "asset", "label": "资产", "width": "200px", "editable": true},
          {"field": "quantity", "label": "数量", "width": "100px", "editable": true},
          {"field": "estimated_price", "label": "预估单价", "width": "120px", "editable": true},
          {"field": "subtotal", "label": "小计", "width": "120px", "formula": "quantity * estimated_price"}
        ],
        "row_actions": ["edit", "delete"],
        "toolbar_actions": ["add"],
        "summary_row": {
          "show": true,
          "fields": [
            {"field": "quantity", "label": "合计", "aggregation": "sum"},
            {"field": "subtotal", "label": "总金额", "aggregation": "sum"}
          ]
        }
      }
    }
  ]
}
```

### 10.3 响应式标签页配置

```json
{
  "layout_type": "form",
  "layout_mode": "tabs",
  "responsive": {
    "mobile": {
      "position": "top",
      "type_style": "",
      "size": "small",
      "stretch": true
    },
    "desktop": {
      "position": "top",
      "type_style": "card",
      "size": "default"
    }
  },
  "tabs": [
    {
      "id": "tab-basic",
      "title": "基本信息",
      "sections": [
        {
          "id": "section-basic",
          "responsive_columns": {
            "mobile": 1,
            "tablet": 2,
            "desktop": 2
          },
          "fields": [
            {"field": "code", "label": "编码", "span": 12},
            {"field": "name", "label": "名称", "span": 12}
          ]
        }
      ]
    }
  ]
}
```

---

## 总结

本文档详细定义了 GZEAMS 系统中标签页（Tabs）的完整配置规范，包括：

1. **标签页概述**：定义、使用场景、与区块的选择原则
2. **配置模型**：TabConfig 数据结构和后端模型定义
3. **布局配置**：位置、样式类型、尺寸、间距
4. **交互配置**：默认激活、切换动画、懒加载、关闭、拖拽、动态添加
5. **内容配置**：字段、区块、表格、嵌套表单
6. **权限配置**：显示权限、操作权限、动态标签页
7. **响应式配置**：移动端布局、横向滚动、响应式列数
8. **事件配置**：切换前/后事件、关闭事件
9. **前端实现**：DynamicTabs 和 TabContent 组件
10. **使用示例**：资产表单、主从表、响应式标签页

所有配置均遵循 GZEAMS 技术栈（Django + Vue3 + Element Plus）和项目架构规范。
