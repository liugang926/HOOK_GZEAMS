# 布局设计器增强 PRD

## 1. 概述

### 1.1 目标
完善布局可视化设计器，实现 PRD 规范要求的所见即所得 (WYSIWYG) 布局编辑功能。

### 1.2 核心设计理念

**动态默认布局 + 差异配置**

| 概念 | 说明 |
|------|------|
| **默认布局** | 基于 `FieldDefinition` 动态生成，新增字段自动显示 |
| **自定义布局** | 仅存储与默认布局的差异配置（位置、可见性、必填等） |

```
FieldDefinition (字段定义，实时)
       ↓ 动态读取
默认布局 (自动包含所有字段)
       ↓ 合并差异配置
自定义布局配置 (仅存储调整项)
       ↓
最终渲染布局
```

### 1.3 布局层级优先级

| 优先级 | 层级 | 说明 |
|--------|------|------|
| 1 (最高) | 用户级 | 用户个人偏好 |
| 2 | 角色级 | 按角色分配 |
| 3 | 组织级 | 按组织分配 |
| 4 | 全局级 | 全系统自定义 |
| 5 (最低) | 默认布局 | 动态生成 |

---

## 2. 布局设计器功能

### 2.1 设计器核心功能

布局设计器用于**调整布局配置**，而非创建布局：

| 功能 | 说明 |
|------|------|
| 调整字段**位置** | 拖拽排序、分组到区块 |
| 调整字段**可见性** | 显示/隐藏开关 |
| 调整字段**必填属性** | 覆盖字段定义的默认值 |
| 调整字段**只读属性** | 动态控制 |
| 配置**区块分组** | Section/Tab/Column 容器 |
| 配置**操作按钮** | 自定义按钮行为 |

### 2.2 字段来源

设计器左侧面板**自动显示所有字段**：

```python
# 字段列表 = FieldDefinition 实时查询
available_fields = FieldDefinition.objects.filter(
    business_object=current_object,
    is_deleted=False
).order_by('sort_order')
```

- ✅ 新增字段自动出现
- ✅ 删除字段自动消失
- ✅ 字段属性实时同步

### 2.3 差异配置存储

自定义布局**仅存储差异**：

```json
{
  "sections": [
    {
      "id": "section_basic",
      "fields": [
        { "fieldCode": "code", "span": 24, "readonly": true },
        { "fieldCode": "status", "visible": false }
      ]
    }
  ],
  "fieldOrder": ["code", "name", "category", "status"]
}
```

**未配置的字段**按默认规则显示：
- 位置：按 `FieldDefinition.sort_order` 排序
- 可见性：默认可见
- 必填：继承 `FieldDefinition.is_required`

---

## 3. 布局容器组件

### 3.1 TabPanel 标签页

```json
{
  "type": "tab",
  "position": "top",
  "tabs": [
    { "id": "tab-1", "title": "基本信息", "fields": ["code", "name"] },
    { "id": "tab-2", "title": "详细信息", "fields": ["description"] }
  ]
}
```

### 3.2 ColumnLayout 分栏

```json
{
  "type": "column",
  "gutter": 20,
  "columns": [
    { "span": 12, "fields": ["code", "name"] },
    { "span": 12, "fields": ["status", "category"] }
  ]
}
```

### 3.3 CollapsePanel 折叠

```json
{
  "type": "collapse",
  "accordion": false,
  "items": [
    { "title": "更多信息", "expanded": false, "fields": ["description"] }
  ]
}
```

### 3.4 Divider 分隔线

```json
{
  "type": "divider",
  "content": "分隔文字",
  "contentPosition": "center"
}
```

---

## 4. 组件架构

```
components/designer/
├── LayoutDesigner.vue          # 主容器
├── ComponentPanel.vue          # 字段/组件面板
├── CanvasArea.vue              # 画布区域
├── PropertyPanel.vue           # 属性面板
├── LayoutPreview.vue           # 预览组件 (新增)
├── containers/                 # 容器组件 (新增)
│   ├── TabPanel.vue
│   ├── ColumnLayout.vue
│   └── CollapsePanel.vue
└── elements/                   # 元素组件 (新增)
    └── DividerElement.vue
```

---

## 5. 实施计划

| Phase | 任务 | 工时 |
|-------|------|------|
| Phase 1 | TabPanel + ColumnLayout + CanvasArea增强 | 3天 |
| Phase 2 | CollapsePanel + Divider | 1.5天 |
| Phase 3 | 响应式预览 | 1天 |
| Phase 4 | Schema验证 + Composable | 1天 |
| **总计** | | **6.5天** |

---

## 6. 验收标准

- [ ] 字段列表自动同步 FieldDefinition
- [ ] 区块拖拽排序正常
- [ ] Tab/Column/Collapse 容器正常
- [ ] 字段属性覆盖（visible/required/readonly）正常
- [ ] 新增字段自动显示在默认位置
- [ ] 差异配置正确保存和加载
- [ ] 响应式预览正常
