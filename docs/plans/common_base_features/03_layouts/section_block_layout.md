# Section/Block 区块布局配置完整规范

## 概述

区块（Section/Block）是 GZEAMS 低代码平台中页面布局的核心组织单元，用于将相关字段进行逻辑分组和视觉组织。通过区块配置，可以实现清晰的信息层级、优化的空间利用和良好的用户体验。

---

## 1. 区块概述

### 1.1 区块定义

**区块（Section/Block）** 是页面布局中用于组织和管理字段的容器组件，具有以下特征：

- **逻辑分组**: 将业务相关的字段聚合在一起，形成清晰的信息模块
- **视觉独立**: 通过边框、背景、间距等样式与周围内容区分
- **可折叠性**: 支持展开/收起交互，优化长表单的浏览体验
- **灵活布局**: 支持单列、多列等多种列数配置
- **嵌套支持**: 支持区块内嵌套子区块，实现复杂布局结构

### 1.2 区块与字段的关系

```
PageLayout (页面布局)
    └── Tabs (标签页)
        └── Section (区块)
            └── Fields (字段) / Sub-Sections (子区块)
```

| 关系类型 | 说明 | 示例 |
|---------|------|------|
| **包含关系** | 区块包含字段列表 | "基本信息" 区块包含：资产编码、资产名称、分类 |
| **排序关系** | 区块内字段按配置顺序排列 | 字段排列顺序决定表单中的显示顺序 |
| **布局关系** | 区块列数配置决定字段排列方式 | 2列区块内字段呈左右并排布局 |
| **样式继承** | 字段可继承区块级样式配置 | 区块背景色可影响内部字段视觉呈现 |

### 1.3 区块与标签页的区别

| 维度 | 区块 (Section) | 标签页 (Tab) |
|------|---------------|-------------|
| **交互方式** | 垂直堆叠，可折叠展开 | 水平切换，点击切换 |
| **信息展示** | 可同时浏览多个区块内容 | 一次只能查看一个标签页内容 |
| **适用场景** | 相关信息分组、表单分段 | 独立业务模块、不同类型信息 |
| **空间利用** | 纵向展开，适合信息密度适中 | 横向扩展，适合信息量大且独立的场景 |
| **嵌套支持** | 区块可嵌套子区块 | 标签页内可嵌套区块 |
| **移动端表现** | 默认折叠，节省空间 | 底部 Tab 切换或顶部滑动切换 |

---

## 2. 区块配置模型

### 2.1 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

**注意**: 区块（Section）是 PageLayout JSON 配置的一部分，不是独立的数据库表。区块配置存储在 PageLayout.layout_config JSON 字段中。

### 2.2 SectionConfig 数据结构

```json
{
  "sections": [
    {
      "id": "section_basic_info",
      "type": "section",
      "name": "基本信息",
      "icon": "InfoFilled",
      "description": "资产的基本信息",
      "fields": ["code", "name", "category", "status"],
      "layout": {
        "columns": 2,
        "columnSpacing": 16,
        "padding": "16px",
        "border": true,
        "borderStyle": "solid",
        "borderColor": "#DCDFE6",
        "borderRadius": "4px",
        "backgroundColor": "#FFFFFF",
        "margin": "0 0 16px 0"
      },
      "interaction": {
        "collapsible": true,
        "defaultCollapsed": false,
        "draggable": true,
        "animation": {
          "duration": 300,
          "easing": "ease-in-out"
        }
      },
      "style": {
        "titleAlign": "left",
        "titleBold": true,
        "titleColor": "#303133",
        "customClass": "custom-section-basic",
        "conditionalStyles": [
          {
            "condition": "status === 'draft'",
            "styles": {
              "backgroundColor": "#F5F7FA"
            }
          }
        ]
      },
      "responsive": {
        "desktop": { "columns": 2 },
        "tablet": { "columns": 1 },
        "mobile": { "columns": 1, "defaultCollapsed": true }
      },
      "display": {
        "visible": true,
        "condition": "category !== 'disposed'",
        "permissions": ["view_basic_info"],
        "dynamic": {
          "enabled": false,
          "dataSource": "",
          "dataField": ""
        }
      },
      "content": {
        "divider": true,
        "emptyState": {
          "enabled": true,
          "icon": "Box",
          "text": "暂无基本信息",
          "action": {
            "label": "添加信息",
            "handler": "addBasicInfo"
          }
        },
        "subSections": []
      }
    }
  ]
}
```

### 2.2 区块属性定义

| 属性路径 | 类型 | 必填 | 默认值 | 说明 |
|---------|------|------|--------|------|
| `sections[]` | Array | 是 | - | 区块配置数组 |
| `sections[].id` | String | 是 | - | 区块唯一标识（建议：section_{功能名}） |
| `sections[].type` | String | 是 | "section" | 固定值，标识为区块类型 |
| `sections[].name` | String | 是 | - | 区块显示名称 |
| `sections[].icon` | String | 否 | - | 区块标题图标（Element Plus Icon 名称） |
| `sections[].description` | String | 否 | - | 区块描述文本 |
| `sections[].fields` | Array | 是 | [] | 区块内字段 ID 列表 |
| `sections[].layout` | Object | 是 | - | 区块布局配置 |
| `sections[].layout.columns` | Integer | 是 | 1 | 区块列数（1-4） |
| `sections[].layout.columnSpacing` | Integer | 否 | 16 | 列间距（px） |
| `sections[].layout.padding` | String | 否 | "16px" | 区块内边距 |
| `sections[].layout.border` | Boolean | 否 | true | 是否显示边框 |
| `sections[].layout.borderStyle` | String | 否 | "solid" | 边框样式（solid/dashed/dotted） |
| `sections[].layout.borderColor` | String | 否 | "#DCDFE6" | 边框颜色 |
| `sections[].layout.borderRadius` | String | 否 | "4px" | 边框圆角 |
| `sections[].layout.backgroundColor` | String | 否 | "#FFFFFF" | 背景色 |
| `sections[].layout.margin` | String | 否 | "0 0 16px 0" | 外边距 |
| `sections[].interaction` | Object | 否 | - | 交互配置 |
| `sections[].interaction.collapsible` | Boolean | 否 | true | 是否可折叠 |
| `sections[].interaction.defaultCollapsed` | Boolean | 否 | false | 是否默认折叠 |
| `sections[].interaction.draggable` | Boolean | 否 | true | 是否可拖拽排序 |
| `sections[].interaction.animation` | Object | 否 | - | 动画配置 |
| `sections[].style` | Object | 否 | - | 样式配置 |
| `sections[].responsive` | Object | 否 | - | 响应式配置 |
| `sections[].display` | Object | 否 | - | 显示规则配置 |
| `sections[].content` | Object | 否 | - | 内容配置 |

### 2.3 区块嵌套规则

```json
{
  "sections": [
    {
      "id": "section_main",
      "name": "主区块",
      "fields": ["field1", "field2"],
      "content": {
        "subSections": [
          {
            "id": "subsection_level1",
            "name": "一级子区块",
            "fields": ["field3", "field4"],
            "content": {
              "subSections": [
                {
                  "id": "subsection_level2",
                  "name": "二级子区块",
                  "fields": ["field5"],
                  "content": {
                    "subSections": []
                  }
                }
              ]
            }
          }
        ]
      }
    }
  ]
}
```

**嵌套规则约束**:

| 约束类型 | 规则 | 说明 |
|---------|------|------|
| **最大嵌套层级** | 3 层 | 主区块 > 一级子区块 > 二级子区块 |
| **字段归属** | 字段只能在最内层区块 | 子区块不能包含字段，只能包含更深层子区块 |
| **布局继承** | 子区块继承父区块列数配置 | 子区块可覆盖父区块布局配置 |
| **折叠联动** | 父区块折叠时子区块自动隐藏 | 子区块折叠状态不影响父区块 |
| **样式隔离** | 子区块样式独立于父区块 | 子区块可独立配置边框、背景等样式 |

---

## 3. 区块布局配置

### 3.1 区块列数配置

#### 支持的列数

| 列数 | 代码值 | 适用场景 | 字段排列方式 |
|------|--------|---------|-------------|
| **1列** | `1` | 长文本字段、复杂表单项 | 垂直单列排列 |
| **2列** | `2` | 大多数表单字段（推荐） | 左右并排两列 |
| **3列** | `3` | 短字段、选项类字段 | 三列并排 |
| **4列** | `4` | 简单选项、开关类字段 | 四列并排 |

#### 列数配置示例

```json
{
  "sections": [
    {
      "id": "section_1column",
      "name": "单列布局",
      "layout": {
        "columns": 1
      },
      "fields": ["description", "remarks"]
    },
    {
      "id": "section_2column",
      "name": "双列布局",
      "layout": {
        "columns": 2,
        "columnSpacing": 16
      },
      "fields": ["code", "name", "category", "status"]
    },
    {
      "id": "section_3column",
      "name": "三列布局",
      "layout": {
        "columns": 3,
        "columnSpacing": 12
      },
      "fields": ["brand", "model", "supplier"]
    },
    {
      "id": "section_4column",
      "name": "四列布局",
      "layout": {
        "columns": 4,
        "columnSpacing": 8
      },
      "fields": ["is_active", "is_deleted", "is_locked", "is_verified"]
    }
  ]
}
```

#### 字段跨列配置

```json
{
  "sections": [
    {
      "id": "section_span",
      "name": "字段跨列示例",
      "layout": {
        "columns": 2
      },
      "fields": [
        {
          "field": "code",
          "span": 1
        },
        {
          "field": "name",
          "span": 1
        },
        {
          "field": "description",
          "span": 2
        }
      ]
    }
  ]
}
```

**跨列规则**:
- `span` 值必须 <= 总列数
- `span` 默认值为 1（不跨列）
- `span` = 总列数时，字段占满整行

### 3.2 区块间距配置

#### 列间距 (columnSpacing)

```json
{
  "layout": {
    "columns": 2,
    "columnSpacing": 16
  }
}
```

**推荐值**:

| 间距值 | 适用场景 | 视觉效果 |
|--------|---------|---------|
| `8px` | 信息密集型布局 | 紧凑排列 |
| `12px` | 常规表单 | 适中间距 |
| `16px` | 标准表单（推荐） | 舒适间距 |
| `20px` | 宽松布局 | 较大间距 |
| `24px` | 特殊场景 | 宽松排列 |

#### 区块外边距 (margin)

```json
{
  "layout": {
    "margin": "0 0 16px 0"
  }
}
```

**格式**: `上 右 下 左`

**推荐配置**:
- 垂直间距: `16px`（区块之间的垂直距离）
- 水平边距: `0`（由容器统一控制）

#### 区块内边距 (padding)

```json
{
  "layout": {
    "padding": "16px"
  }
}
```

**推荐值**:

| 布局类型 | 推荐内边距 | 说明 |
|---------|-----------|------|
| 紧凑型 | `12px` | 移动端或信息密集场景 |
| 标准型 | `16px`（推荐） | 适用于大多数场景 |
| 宽松型 | `20px` | 需要留白的特殊场景 |

### 3.3 区块边框样式

#### 边框配置

```json
{
  "layout": {
    "border": true,
    "borderStyle": "solid",
    "borderColor": "#DCDFE6",
    "borderWidth": "1px",
    "borderRadius": "4px"
  }
}
```

#### 边框样式选项

| borderStyle | 效果 | 适用场景 |
|------------|------|---------|
| `solid` | 实线边框 | 标准区块（推荐） |
| `dashed` | 虚线边框 | 可选信息分组、次要区块 |
| `dotted` | 点线边框 | 辅助信息分组 |
| `none` | 无边框 | 需要无边框的场景（配合背景色区分） |

#### 边框颜色建议

| 场景 | 推荐颜色 | 色值 |
|------|---------|------|
| 标准区块 | 灰色边框 | `#DCDFE6` |
| 强调区块 | 主题色边框 | `#409EFF` |
| 警告区块 | 警告色边框 | `#E6A23C` |
| 成功区块 | 成功色边框 | `#67C23A` |
| 危险区块 | 危险色边框 | `#F56C6C` |

#### 边框圆角建议

| 圆角值 | 视觉效果 | 适用场景 |
|--------|---------|---------|
| `0px` | 直角 | 严谨风格、传统系统 |
| `2px` | 微圆角 | 标准 UI（推荐） |
| `4px` | 小圆角 | 现代化 UI（推荐） |
| `8px` | 中圆角 | 卡片式布局 |
| `12px` | 大圆角 | 特殊设计风格 |

### 3.4 区块背景色

#### 背景色配置

```json
{
  "layout": {
    "backgroundColor": "#FFFFFF"
  }
}
```

#### 推荐背景色

| 场景 | 背景色 | 色值 | 适用区块类型 |
|------|--------|------|-------------|
| 标准区块 | 白色 | `#FFFFFF` | 大多数区块 |
| 次要区块 | 浅灰 | `#F5F7FA` | 辅助信息、可折叠区块 |
| 强调区块 | 浅蓝 | `#ECF5FF` | 重要信息区块 |
| 警告区块 | 浅橙 | `#FDF6EC` | 警告提示区块 |
| 成功区块 | 浅绿 | `#F0F9FF` | 成功状态区块 |
| 禁用区块 | 浅灰 | `#FAFAFA` | 只读或禁用区块 |

#### 渐变背景配置（可选）

```json
{
  "layout": {
    "backgroundGradient": {
      "enabled": true,
      "direction": "to right",
      "startColor": "#ECF5FF",
      "endColor": "#FFFFFF"
    }
  }
}
```

---

## 4. 区块交互配置

### 4.1 区块可折叠

#### 折叠配置

```json
{
  "interaction": {
    "collapsible": true,
    "defaultCollapsed": false,
    "collapseIcon": "ArrowDown",
    "expandIcon": "ArrowRight",
    "animation": {
      "duration": 300,
      "easing": "ease-in-out"
    }
  }
}
```

#### 折叠行为

| 配置项 | 说明 | 推荐值 |
|--------|------|--------|
| `collapsible` | 是否启用折叠功能 | `true`（内容较多时）<br>`false`（内容必填或重要时） |
| `defaultCollapsed` | 默认折叠状态 | `false`（重要信息）<br>`true`（次要信息） |
| `collapseIcon` | 折叠状态图标 | `ArrowRight` |
| `expandIcon` | 展开状态图标 | `ArrowDown` |
| `persistState` | 是否持久化折叠状态 | `true`（记住用户选择）<br>`false`（每次重置） |

#### 折叠状态联动

```json
{
  "interaction": {
    "collapsible": true,
    "collapseBehavior": {
      "mode": "independent",
      "linkWith": ["section_related_info"],
      "autoCollapseOthers": false
    }
  }
}
```

**折叠模式**:

| 模式 | 代码值 | 说明 |
|------|--------|------|
| 独立模式 | `independent` | 各区块独立折叠，互不影响 |
| 手风琴模式 | `accordion` | 一个区块展开时，其他区块自动折叠 |
| 联动模式 | `linked` | 与指定区块同步折叠状态 |

### 4.2 区块展开/收起动画

#### 动画配置

```json
{
  "interaction": {
    "collapsible": true,
    "animation": {
      "enabled": true,
      "duration": 300,
      "easing": "ease-in-out",
      "delay": 0
    }
  }
}
```

#### 动画参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `enabled` | `true` | 是否启用动画（移动端建议关闭以提升性能） |
| `duration` | `300` | 动画时长（ms），推荐 200-400ms |
| `easing` | `ease-in-out` | 缓动函数 |
| `delay` | `0` | 动画延迟（ms） |

#### 缓动函数选项

| easing 值 | 效果 | 适用场景 |
|-----------|------|---------|
| `linear` | 线性匀速 | 不推荐（缺乏自然感） |
| `ease` | 开始和结束慢，中间快 | 标准 UI（推荐） |
| `ease-in` | 开始慢，之后快 | 进入动画 |
| `ease-out` | 开始快，结束慢 | 退出动画（推荐） |
| `ease-in-out` | 开始和结束慢，中间快 | 折叠动画（推荐） |
| `cubic-bezier(...)` | 自定义贝塞尔曲线 | 特殊设计需求 |

### 4.3 区块拖拽排序

#### 拖拽配置

```json
{
  "interaction": {
    "draggable": true,
    "dragHandle": ".section-header",
    "dragPlaceholder": {
      "enabled": true,
      "className": "section-drag-placeholder",
      "showGhost": true
    },
    "dropZones": ["#form-canvas"],
    "onDragStart": "handleSectionDragStart",
    "onDragEnd": "handleSectionDragEnd",
    "confirmOnDrop": false
  }
}
```

#### 拖拽行为配置

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `draggable` | Boolean | 是否启用拖拽 |
| `dragHandle` | String | 拖拽手柄选择器（为空时整个区块可拖拽） |
| `dragPlaceholder.enabled` | Boolean | 是否显示拖拽占位符 |
| `dragPlaceholder.showGhost` | Boolean | 是否显示拖拽时的幽灵元素 |
| `dropZones` | Array | 允许放置的 DOM 区域选择器 |
| `confirmOnDrop` | Boolean | 放置前是否确认（防止误操作） |

#### 拖拽手柄样式

```html
<!-- 推荐的区块头部结构 -->
<div class="section-header">
  <div class="section-drag-handle">
    <el-icon><Rank /></el-icon>
  </div>
  <div class="section-title">区块标题</div>
  <div class="section-actions">
    <el-icon class="collapse-icon"><ArrowDown /></el-icon>
  </div>
</div>
```

```css
.section-drag-handle {
  cursor: move;
  padding: 4px;
  color: #909399;
  transition: color 0.3s;
}

.section-drag-handle:hover {
  color: #409EFF;
}
```

#### 拖拽权限控制

```json
{
  "interaction": {
    "draggable": true,
    "dragPermissions": {
      "enabled": true,
      "permissions": ["layout:edit"],
      "roleBased": {
        "admin": true,
        "editor": true,
        "viewer": false
      }
    }
  }
}
```

---

## 5. 区块样式配置

### 5.1 区块标题样式

#### 标题配置

```json
{
  "style": {
    "title": {
      "align": "left",
      "bold": true,
      "color": "#303133",
      "fontSize": "16px",
      "lineHeight": "24px",
      "icon": {
        "enabled": true,
        "name": "InfoFilled",
        "size": "18px",
        "color": "#409EFF",
        "position": "before"
      }
    }
  }
}
```

#### 标题对齐方式

| align 值 | 效果 | 适用场景 |
|---------|------|---------|
| `left` | 左对齐（推荐） | 标准表单布局 |
| `center` | 居中对齐 | 特殊设计需求 |
| `right` | 右对齐 | RTL 语言或特殊布局 |

#### 标题字体建议

| 场景 | fontSize | fontWeight | color |
|------|----------|------------|-------|
| 标准区块 | `16px` | `500`（medium） | `#303133` |
| 重要区块 | `18px` | `600`（semibold） | `#000000` |
| 次要区块 | `14px` | `400`（regular） | `#606266` |

### 5.2 区块图标配置

#### 图标配置结构

```json
{
  "style": {
    "title": {
      "icon": {
        "enabled": true,
        "name": "InfoFilled",
        "size": "18px",
        "color": "#409EFF",
        "position": "before",
        "spacing": "8px",
        "clickable": false
      }
    }
  }
}
```

#### 图标位置选项

| position | 效果 | 适用场景 |
|---------|------|---------|
| `before` | 标题左侧（推荐） | 标准 UI 模式 |
| `after` | 标题右侧 | 状态图标、操作图标 |
| `above` | 标题上方 | 特殊布局需求 |
| `background` | 背景图标 | 装饰性图标（不推荐） |

#### 常用区块图标

| 区块类型 | 推荐图标 | 图标名称 |
|---------|---------|---------|
| 基本信息 | 信息图标 | `InfoFilled` |
| 详细信息 | 文档图标 | `Document` |
| 联系信息 | 用户图标 | `User` |
| 位置信息 | 定位图标 | `Location` |
| 时间信息 | 时钟图标 | `Clock` |
| 财务信息 | 金钱图标 | `Money` |
| 状态信息 | 标签图标 | `PriceTag` |
| 附件信息 | 文件夹图标 | `Folder` |
| 设置信息 | 设置图标 | `Setting` |
| 警告信息 | 警告图标 | `Warning` |

### 5.3 区块自定义样式类

#### CSS 类配置

```json
{
  "style": {
    "customClass": "custom-section-basic section-highlight",
    "customStyles": {
      "section": "box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);",
      "header": "background: linear-gradient(to right, #ECF5FF, #FFFFFF);",
      "body": "padding: 20px;"
    }
  }
}
```

#### 样式类命名规范

| 类型 | 命名规范 | 示例 |
|------|---------|------|
| 页面级 | `page-{页面名}-{区块名}` | `page-asset-form-basic` |
| 模块级 | `{模块名}-section-{功能名}` | `asset-section-basic-info` |
| 功能级 | `section-{状态/功能}` | `section-highlight`, `section-disabled` |
| 临时样式 | `temp-{用途}` | `temp-testing-style` |

#### 预定义样式类库

```css
/* Element Plus 扩展样式类 */
.section-no-border { border: none; }
.section-no-padding { padding: 0; }
.section-highlight { box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2); }
.section-dashed { border-style: dashed; }
.section-transparent { background-color: transparent; }
.section-dark { background-color: #303133; color: #FFFFFF; }
.section-card { box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1); }
.section-compact { padding: 12px; }
.section-loose { padding: 24px; }
```

### 5.4 区块条件样式

#### 条件样式配置

```json
{
  "style": {
    "conditionalStyles": [
      {
        "id": "style_draft_status",
        "condition": "status === 'draft'",
        "operator": "===",
        "styles": {
          "backgroundColor": "#F5F7FA",
          "borderColor": "#909399",
          "borderStyle": "dashed"
        }
      },
      {
        "id": "style_urgent_status",
        "condition": "priority === 'urgent'",
        "operator": "===",
        "styles": {
          "backgroundColor": "#FEF0F0",
          "borderColor": "#F56C6C",
          "titleColor": "#F56C6C"
        }
      },
      {
        "id": "style_readonly_mode",
        "condition": "isReadonly === true",
        "operator": "===",
        "styles": {
          "backgroundColor": "#FAFAFA",
          "opacity": 0.8,
          "customClass": "section-readonly"
        }
      }
    ]
  }
}
```

#### 条件操作符

| operator | 说明 | 示例 |
|---------|------|------|
| `===` | 严格相等 | `status === 'draft'` |
| `!==` | 严格不等 | `status !== 'deleted'` |
| `>` | 大于 | `amount > 1000` |
| `<` | 小于 | `quantity < 10` |
| `>=` | 大于等于 | `score >= 60` |
| `<=` | 小于等于 | `discount <= 0.5` |
| `contains` | 包含 | `tags.contains('important')` |
| `in` | 在数组中 | `status in ['pending', 'processing']` |
| `&&` | 逻辑与 | `status === 'urgent' && priority === 'high'` |
| `\|\|` | 逻辑或 | `status === 'draft' \|\| status === 'pending'` |
| `!` | 逻辑非 | `!isDeleted` |

#### 复杂条件表达式

```json
{
  "style": {
    "conditionalStyles": [
      {
        "id": "style_complex_condition",
        "condition": {
          "operator": "&&",
          "conditions": [
            {
              "field": "status",
              "operator": "===",
              "value": "urgent"
            },
            {
              "field": "priority",
              "operator": "in",
              "value": ["high", "critical"]
            },
            {
              "operator": "!",
              "field": "isDeleted"
            }
          ]
        },
        "styles": {
          "backgroundColor": "#FEF0F0",
          "borderColor": "#F56C6C",
          "boxShadow": "0 0 12px rgba(245, 108, 108, 0.3)"
        }
      }
    ]
  }
}
```

---

## 6. 区块内容配置

### 6.1 区块内字段排列

#### 字段排序配置

```json
{
  "fields": [
    {
      "id": "code",
      "order": 1,
      "span": 1,
      "visible": true,
      "readonly": false
    },
    {
      "id": "name",
      "order": 2,
      "span": 1,
      "visible": true,
      "readonly": false
    },
    {
      "id": "description",
      "order": 3,
      "span": 2,
      "visible": true,
      "readonly": false
    }
  ]
}
```

#### 字段属性说明

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | String | 是 | - | 字段 ID（对应 FieldDefinition.code） |
| `order` | Integer | 否 | 自动递增 | 字段排序序号（从小到大排列） |
| `span` | Integer | 否 | 1 | 字段跨列数（1 <= span <= 区块总列数） |
| `visible` | Boolean | 否 | true | 字段是否可见 |
| `readonly` | Boolean | 否 | false | 字段是否只读 |
| `required` | Boolean | 否 | false | 字段是否必填（覆盖 FieldDefinition 配置） |
| `labelWidth` | String | 否 | 继承 | 字段标签宽度（如 "120px"） |
| `placeholder` | String | 否 | 继承 | 字段占位符文本 |
| `defaultValue` | Any | 否 | 继承 | 字段默认值 |

#### 字段排列规则

| 规则类型 | 说明 | 示例 |
|---------|------|------|
| **顺序排列** | 按 `order` 值从小到大排列 | order: 1 在 order: 2 之前 |
| **自动换行** | 当一行字段 span 总和 > 区块列数时自动换行 | 2列布局，字段1（span=2）独占一行 |
| **跨列优先** | 大 span 字段优先占用整行 | span=2 的字段在 span=1 的字段之前 |
| **隐藏字段** | visible=false 的字段不占用空间 | 仅在编辑模式下显示 |

### 6.2 区块内子区块

#### 子区块配置

```json
{
  "id": "section_main",
  "name": "主区块",
  "fields": ["field1", "field2"],
  "content": {
    "subSections": [
      {
        "id": "subsection_detail",
        "name": "详细信息",
        "layout": {
          "columns": 2,
          "backgroundColor": "#F5F7FA"
        },
        "fields": ["field3", "field4", "field5"],
        "content": {
          "subSections": [
            {
              "id": "subsection_sub_detail",
              "name": "子详细信息",
              "fields": ["field6"]
            }
          ]
        }
      }
    ]
  }
}
```

#### 子区块样式隔离

```json
{
  "id": "subsection_detail",
  "name": "详细信息",
  "layout": {
    "columns": 2,
    "border": true,
    "borderStyle": "dashed",
    "borderColor": "#E4E7ED",
    "backgroundColor": "#F5F7FA",
    "margin": "12px 0"
  },
  "style": {
    "title": {
      "fontSize": "14px",
      "color": "#606266",
      "bold": false
    }
  }
}
```

#### 子区块布局建议

| 嵌套层级 | 推荐列数 | 背景色建议 | 边框样式 |
|---------|---------|-----------|---------|
| 一级子区块 | 与父区块相同或减 1 | `#F5F7FA`（浅灰） | 虚线边框 |
| 二级子区块 | 1 或 2 | `#FAFAFA`（更浅灰） | 细实线边框 |
| 三级子区块 | 1（推荐） | 透明或 `#FFFFFF` | 无边框或点线边框 |

### 6.3 区块内分隔线

#### 分隔线配置

```json
{
  "content": {
    "divider": {
      "enabled": true,
      "position": "after_field",
      "targetField": "description",
      "style": {
        "type": "solid",
        "color": "#DCDFE6",
        "thickness": "1px",
        "margin": "16px 0"
      },
      "text": {
        "enabled": true,
        "content": "以下为扩展信息",
        "backgroundColor": "#FFFFFF"
      }
    }
  }
}
```

#### 分隔线位置

| position | 说明 | 示例 |
|---------|------|------|
| `before_field` | 在指定字段之前插入分隔线 | 在"备注"字段前显示分隔线 |
| `after_field` | 在指定字段之后插入分隔线 | 在"描述"字段后显示分隔线 |
| `before_subsection` | 在子区块之前插入分隔线 | 主区块字段与子区块之间 |
| `after_subsection` | 在子区块之后插入分隔线 | 子区块与后续内容之间 |

#### 分隔线样式

| type | 效果 | 适用场景 |
|------|------|---------|
| `solid` | 实线（推荐） | 标准分隔 |
| `dashed` | 虚线 | 次级分隔 |
| `dotted` | 点线 | 辅助分隔 |
| `double` | 双线 | 强调分隔 |

### 6.4 区块内空状态

#### 空状态配置

```json
{
  "content": {
    "emptyState": {
      "enabled": true,
      "trigger": "no_fields_visible",
      "display": {
        "icon": "Box",
        "iconSize": "64px",
        "iconColor": "#C0C4CC",
        "text": "暂无信息",
        "description": "该区块暂无可显示的内容",
        "action": {
          "enabled": true,
          "type": "button",
          "label": "添加信息",
          "icon": "Plus",
          "buttonType": "primary",
          "handler": "handleAddInfo"
        }
      }
    }
  }
}
```

#### 触发条件

| trigger | 说明 |
|---------|------|
| `no_fields_visible` | 所有字段都不可见时触发 |
| `all_fields_empty` | 所有字段值都为空时触发 |
| `no_data` | 数据源返回空数据时触发（动态区块） |
| `custom_condition` | 自定义条件表达式 |

#### 空状态预设样式

```json
{
  "presets": {
    "no_data": {
      "icon": "Box",
      "text": "暂无数据"
    },
    "no_permission": {
      "icon": "Lock",
      "text": "无权限查看"
    },
    "loading": {
      "icon": "Loading",
      "text": "加载中..."
    },
    "error": {
      "icon": "Warning",
      "text": "加载失败"
    },
    "search_empty": {
      "icon": "Search",
      "text": "未找到匹配结果"
    }
  }
}
```

---

## 7. 区块响应式配置

### 7.1 不同设备下的列数适配

#### 响应式断点

```json
{
  "responsive": {
    "breakpoints": {
      "mobile": 768,
      "tablet": 992,
      "desktop": 1200,
      "large": 1920
    }
  }
}
```

#### 响应式列数配置

```json
{
  "id": "section_responsive",
  "layout": {
    "columns": 2
  },
  "responsive": {
    "mobile": {
      "columns": 1,
      "columnSpacing": 12,
      "padding": "12px",
      "defaultCollapsed": true
    },
    "tablet": {
      "columns": 1,
      "columnSpacing": 14,
      "padding": "14px"
    },
    "desktop": {
      "columns": 2,
      "columnSpacing": 16,
      "padding": "16px"
    },
    "large": {
      "columns": 3,
      "columnSpacing": 20,
      "padding": "20px"
    }
  }
}
```

#### 列数适配规则

| 设备类型 | 屏幕宽度 | 推荐列数 | 说明 |
|---------|---------|---------|------|
| **移动端** | < 768px | 1 | 单列布局，确保可用性 |
| **平板竖屏** | 768px - 991px | 1 或 2 | 根据内容复杂度选择 |
| **平板横屏** | 992px - 1199px | 2 | 双列布局 |
| **桌面端** | 1200px - 1919px | 2 或 3 | 根据字段数量选择 |
| **大屏** | >= 1920px | 3 或 4 | 充分利用屏幕空间 |

### 7.2 移动端区块布局规则

#### 移动端专用配置

```json
{
  "responsive": {
    "mobile": {
      "columns": 1,
      "defaultCollapsed": true,
      "collapsible": true,
      "compactMode": true,
      "fontScale": 0.9,
      "touchOptimized": true,
      "floatingLabels": false,
      "hideDescription": true,
      "actionButton": {
        "position": "bottom",
        "fixed": true,
        "labels": {
          "collapse": "收起",
          "expand": "展开"
        }
      }
    }
  }
}
```

#### 移动端优化策略

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| `columns` | `1` | 强制单列布局 |
| `defaultCollapsed` | `true` | 非活跃区块默认折叠 |
| `compactMode` | `true` | 启用紧凑模式，减少间距 |
| `fontScale` | `0.9` | 字体缩放（0.85-0.95） |
| `touchOptimized` | `true` | 增大点击区域（>=44px） |
| `hideDescription` | `true` | 隐藏字段描述，节省空间 |
| `floatingLabels` | `false` | 不使用浮动标签（移动端易混淆） |

#### 移动端区块间距调整

```json
{
  "responsive": {
    "mobile": {
      "layout": {
        "margin": "0 0 12px 0",
        "padding": "12px",
        "columnSpacing": 12
      }
    }
  }
}
```

**移动端间距建议**:
- 外边距: `12px`（比桌面端减少 25%）
- 内边距: `12px`（比桌面端减少 25%）
- 字段间距: `12px`（比桌面端减少 25%）

### 7.3 平板端区块布局规则

#### 平板端配置

```json
{
  "responsive": {
    "tablet": {
      "columns": 2,
      "columnSpacing": 14,
      "padding": "14px",
      "landscape": {
        "columns": 2,
        "columnSpacing": 16
      },
      "portrait": {
        "columns": 1,
        "columnSpacing": 14
      }
    }
  }
}
```

#### 平板端布局建议

| 方向 | 推荐列数 | 列间距 | 说明 |
|------|---------|--------|------|
| **竖屏** | 1 | `14px` | 与移动端类似，但间距稍大 |
| **横屏** | 2 | `16px` | 接近桌面端体验 |

#### 平板端特殊配置

```json
{
  "responsive": {
    "tablet": {
      "touchOptimized": true,
      "swipeToCollapse": true,
      "floatingActionButtons": false,
      "splitView": {
        "enabled": false,
        "minWidth": 768
      }
    }
  }
}
```

---

## 8. 区块显示规则

### 8.1 区块级显示条件

#### 条件显示配置

```json
{
  "display": {
    "visible": true,
    "condition": {
      "operator": "&&",
      "rules": [
        {
          "field": "category",
          "operator": "!==",
          "value": "disposed"
        },
        {
          "field": "status",
          "operator": "in",
          "value": ["draft", "pending", "active"]
        }
      ]
    },
    "logic": "show_when_match"
  }
}
```

#### 显示逻辑类型

| logic 值 | 说明 | 示例 |
|---------|------|------|
| `show_when_match` | 条件匹配时显示（推荐） | 仅当资产状态为"使用中"时显示区块 |
| `hide_when_match` | 条件匹配时隐藏 | 资产状态为"已报废"时隐藏区块 |
| `always_show` | 始终显示 | 忽略条件，强制显示 |
| `always_hide` | 始终隐藏 | 忽略条件，强制隐藏 |

#### 常见条件表达式

| 场景 | 条件表达式 |
|------|-----------|
| 仅显示草稿状态的区块 | `status === 'draft'` |
| 隐藏已删除资产的区块 | `status !== 'deleted'` |
| 显示金额大于1000时的区块 | `amount > 1000` |
| 显示包含特定标签的区块 | `tags.contains('important')` |
| 显示多种状态之一的区块 | `status in ['draft', 'pending', 'active']` |
| 显示未归档资产的区块 | `!archived` |
| 组合条件 | `status === 'urgent' && priority === 'high'` |

### 8.2 区块权限控制

#### 权限配置

```json
{
  "display": {
    "permissions": {
      "view": ["asset:view", "asset:view_basic_info"],
      "edit": ["asset:edit", "asset:edit_basic_info"],
      "requiredAction": "view",
      "hideOnNoPermission": true,
      "disabledOnNoPermission": false
    }
  }
}
```

#### 权限控制模式

| 模式 | 配置 | 效果 |
|------|------|------|
| **完全隐藏** | `hideOnNoPermission: true` | 无权限时不显示区块（推荐） |
| **禁用模式** | `disabledOnNoPermission: true` | 无权限时显示但禁用（带视觉提示） |
| **只读模式** | `readonlyOnNoPermission: true` | 无权限时显示但只读 |
| **提示模式** | `showPermissionTip: true` | 无权限时显示权限不足提示 |

#### 权限不足提示

```json
{
  "display": {
    "permissions": {
      "view": ["asset:edit_sensitive_info"],
      "hideOnNoPermission": false,
      "disabledOnNoPermission": true,
      "noPermissionTip": {
        "enabled": true,
        "icon": "Lock",
        "text": "您无权限查看此信息",
        "type": "warning",
        "showContact": true
      }
    }
  }
}
```

#### 基于角色的区块可见性

```json
{
  "display": {
    "roleBasedVisibility": {
      "enabled": true,
      "rules": [
        {
          "roles": ["admin", "super_admin"],
          "visible": true
        },
        {
          "roles": ["editor", "viewer"],
          "visible": true,
          "readonly": true
        },
        {
          "roles": ["guest"],
          "visible": false
        }
      ],
      "defaultVisible": false
    }
  }
}
```

### 8.3 动态区块（根据条件动态显示）

#### 动态区块配置

```json
{
  "id": "section_dynamic_attachments",
  "name": "相关附件",
  "type": "dynamic_section",
  "display": {
    "dynamic": {
      "enabled": true,
      "dataSource": "api",
      "endpoint": "/api/assets/{id}/attachments/",
      "method": "GET",
      "trigger": "on_load",
      "autoRefresh": false,
      "refreshInterval": 0,
      "cache": {
        "enabled": true,
        "ttl": 300
      }
    }
  },
  "content": {
    "template": "attachments_list",
    "loadingState": {
      "enabled": true,
      "skeleton": true,
      "skeletonRows": 3
    },
    "errorState": {
      "enabled": true,
      "retry": true
    }
  }
}
```

#### 动态区块触发时机

| trigger | 说明 | 适用场景 |
|---------|------|---------|
| `on_load` | 页面加载时触发 | 初始数据加载 |
| `on_click` | 用户点击时触发 | 按需加载（优化性能） |
| `on_field_change` | 字段值变化时触发 | 联动显示区块 |
| `on_manual` | 手动触发（如刷新按钮） | 用户主动刷新 |
| `on_schedule` | 定时触发 | 需要实时更新的数据 |

#### 字段变化联动示例

```json
{
  "id": "section_dynamic_loan_info",
  "name": "借阅信息",
  "display": {
    "dynamic": {
      "enabled": true,
      "trigger": "on_field_change",
      "watchFields": ["status", "loan_status"],
      "condition": "status === 'on_loan' && loan_status === 'active'",
      "dataSource": "api",
      "endpoint": "/api/assets/{id}/loan-info/",
      "method": "GET"
    }
  }
}
```

#### 动态区块数据源类型

| 类型 | 配置值 | 说明 | 示例 |
|------|--------|------|------|
| **API 接口** | `api` | 从后端 API 获取数据 | 关联资产列表 |
| **静态数据** | `static` | 从配置的静态数据获取 | 固定选项列表 |
| **计算字段** | `computed` | 基于其他字段计算得出 | 总金额、数量统计 |
| **外部系统** | `external` | 从第三方系统获取 | ERP 系统数据 |

#### 动态区块缓存策略

```json
{
  "display": {
    "dynamic": {
      "cache": {
        "enabled": true,
        "ttl": 300,
        "strategy": "memory",
        "key": "section_dynamic_{asset_id}",
        "invalidateOn": [
          "asset_update",
          "attachment_change"
        ]
      }
    }
  }
}
```

**缓存策略**:

| strategy | 说明 | 适用场景 |
|---------|------|---------|
| `memory` | 内存缓存（会话级别） | 临时数据、用户会话数据 |
| `localStorage` | 本地存储缓存（持久化） | 用户偏好设置 |
| `sessionStorage` | 会话存储缓存（标签页级别） | 临时状态数据 |
| `none` | 不缓存 | 实时性要求高的数据 |

---

## 9. 后端实现

### 9.1 Section 配置模型

```python
from django.db import models
from apps.common.models import BaseModel

class SectionConfig(BaseModel):
    """
    区块配置模型

    用于定义页面布局中的区块结构和属性
    """
    # 关联页面布局
    page_layout = models.ForeignKey(
        'system.PageLayout',
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='页面布局'
    )

    # 区块基本信息
    section_id = models.CharField(
        max_length=100,
        verbose_name='区块ID',
        help_text='区块的唯一标识'
    )

    name = models.CharField(
        max_length=100,
        verbose_name='区块名称'
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='图标',
        help_text='Element Plus Icon 名称'
    )

    description = models.TextField(
        blank=True,
        verbose_name='区块描述'
    )

    # 区块顺序
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='排序序号'
    )

    # 区块配置（JSON）
    config = models.JSONField(
        default=dict,
        verbose_name='区块配置',
        help_text='包含布局、交互、样式等配置'
    )

    # 关联字段（多对多）
    fields = models.ManyToManyField(
        'system.FieldDefinition',
        through='SectionField',
        related_name='sections',
        verbose_name='字段列表'
    )

    # 父区块（支持嵌套）
    parent_section = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_sections',
        verbose_name='父区块'
    )

    # 区块状态
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    is_visible = models.BooleanField(
        default=True,
        verbose_name='是否可见'
    )

    class Meta:
        db_table = 'section_config'
        verbose_name = '区块配置'
        verbose_name_plural = '区块配置'
        ordering = ['page_layout', 'order', 'id']
        unique_together = [['page_layout', 'section_id']]

    def __str__(self):
        return f"{self.page_layout.name} - {self.name}"
```

### 9.2 SectionField 关联模型

```python
class SectionField(BaseModel):
    """
    区块字段关联模型

    定义区块与字段的关联关系及字段在区块内的配置
    """
    # 区块关联
    section = models.ForeignKey(
        SectionConfig,
        on_delete=models.CASCADE,
        related_name='section_fields',
        verbose_name='区块'
    )

    # 字段关联
    field = models.ForeignKey(
        'system.FieldDefinition',
        on_delete=models.CASCADE,
        related_name='section_fields',
        verbose_name='字段'
    )

    # 字段排序
    field_order = models.PositiveIntegerField(
        default=0,
        verbose_name='字段排序'
    )

    # 字段配置（JSON）
    field_config = models.JSONField(
        default=dict,
        verbose_name='字段配置',
        help_text='包含 span, visible, readonly 等配置'
    )

    class Meta:
        db_table = 'section_field'
        verbose_name = '区块字段关联'
        verbose_name_plural = '区块字段关联'
        ordering = ['section', 'field_order', 'id']
        unique_together = [['section', 'field']]

    def __str__(self):
        return f"{self.section.name} - {self.field.name}"
```

### 9.3 Section 序列化器

```python
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer

class SectionFieldSerializer(BaseModelSerializer):
    """区块字段关联序列化器"""

    field_id = serializers.CharField(source='field.code', read_only=True)
    field_name = serializers.CharField(source='field.name', read_only=True)
    field_type = serializers.CharField(source='field.field_type', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SectionField
        fields = BaseModelSerializer.Meta.fields + [
            'field', 'field_id', 'field_name', 'field_type',
            'field_order', 'field_config'
        ]

class SectionConfigSerializer(BaseModelSerializer):
    """区块配置序列化器"""

    section_fields = SectionFieldSerializer(
        many=True,
        read_only=True,
        source='section_fields'
    )

    field_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = SectionConfig
        fields = BaseModelSerializer.Meta.fields + [
            'page_layout', 'section_id', 'name', 'icon', 'description',
            'order', 'config', 'section_fields', 'parent_section',
            'is_active', 'is_visible', 'field_count'
        ]

    def get_field_count(self, obj):
        """获取区块内字段数量"""
        return obj.section_fields.count()
```

### 9.4 Section Service

```python
from apps.common.services.base_crud import BaseCRUDService

class SectionConfigService(BaseCRUDService):
    """区块配置服务"""

    def __init__(self):
        super().__init__(SectionConfig)

    def get_sections_by_layout(self, layout_id: str, include_inactive: bool = False):
        """获取指定布局的所有区块"""
        queryset = self.model_class.objects.filter(
            page_layout_id=layout_id
        ).select_related(
            'parent_section'
        ).prefetch_related(
            'section_fields__field'
        ).order_by('order', 'id')

        if not include_inactive:
            queryset = queryset.filter(is_active=True)

        return queryset.all()

    def get_section_tree(self, layout_id: str):
        """获取区块树形结构"""
        sections = self.get_sections_by_layout(layout_id)

        # 构建树形结构
        root_sections = []
        section_map = {s.id: s for s in sections}

        for section in sections:
            if section.parent_section_id is None:
                root_sections.append(section)
            else:
                parent = section_map.get(section.parent_section_id)
                if parent:
                    if not hasattr(parent, '_children'):
                        parent._children = []
                    parent._children.append(section)

        return root_sections

    def update_section_order(self, layout_id: str, section_orders: list):
        """批量更新区块排序"""
        updated_count = 0
        for item in section_orders:
            section_id = item.get('section_id')
            order = item.get('order', 0)

            updated = self.model_class.objects.filter(
                id=section_id,
                page_layout_id=layout_id
            ).update(order=order)

            updated_count += updated

        return updated_count

    def toggle_section_visibility(self, section_id: str, visible: bool):
        """切换区块可见性"""
        section = self.get_by_id(section_id)
        if section:
            section.is_visible = visible
            section.save()
            return section
        return None
```

---

## 10. 前端实现

### 10.1 SectionBlock 组件

```vue
<template>
  <div
    v-if="isVisible"
    :class="sectionClasses"
    :style="sectionStyles"
    class="section-block"
  >
    <!-- 区块头部 -->
    <div
      v-if="showHeader"
      class="section-header"
      @click="handleHeaderClick"
    >
      <!-- 拖拽手柄 -->
      <div
        v-if="draggable"
        class="section-drag-handle"
        @mousedown="handleDragStart"
      >
        <el-icon><Rank /></el-icon>
      </div>

      <!-- 区块图标 -->
      <div
        v-if="iconConfig.enabled"
        class="section-icon"
      >
        <el-icon :size="iconConfig.size">
          <component :is="iconConfig.name" />
        </el-icon>
      </div>

      <!-- 区块标题 -->
      <div class="section-title">
        {{ section.name }}
      </div>

      <!-- 区块描述 -->
      <div
        v-if="section.description && showDescription"
        class="section-description"
      >
        {{ section.description }}
      </div>

      <!-- 折叠图标 -->
      <div
        v-if="collapsible"
        class="section-collapse-icon"
      >
        <el-icon>
          <component :is="isCollapsed ? ArrowRight : ArrowDown" />
        </el-icon>
      </div>
    </div>

    <!-- 区块内容 -->
    <transition
      :name="transitionName"
      @before-enter="handleBeforeEnter"
      @after-leave="handleAfterLeave"
    >
      <div
        v-show="!isCollapsed"
        class="section-body"
        :style="bodyStyles"
      >
        <!-- 字段渲染 -->
        <div
          :class="bodyClasses"
          class="section-fields"
        >
          <template
            v-for="fieldItem in visibleFields"
            :key="fieldItem.id"
          >
            <div
              :class="getFieldClasses(fieldItem)"
              :style="getFieldStyles(fieldItem)"
            >
              <FieldRenderer
                :field="fieldItem"
                :readonly="isReadonly || fieldItem.readonly"
                :label-width="fieldItem.labelWidth"
                @change="handleFieldChange"
              />
            </div>
          </template>
        </div>

        <!-- 子区块渲染 -->
        <div
          v-if="hasSubSections"
          class="sub-sections"
        >
          <SectionBlock
            v-for="subSection in subSections"
            :key="subSection.id"
            :section="subSection"
            :parent-section="section"
            @field-change="handleSubSectionFieldChange"
          />
        </div>

        <!-- 空状态 -->
        <div
          v-if="showEmptyState"
          class="section-empty-state"
        >
          <el-empty
            :image="emptyStateConfig.icon"
            :description="emptyStateConfig.text"
          >
            <el-button
              v-if="emptyStateConfig.action.enabled"
              :type="emptyStateConfig.action.buttonType"
              :icon="emptyStateConfig.action.icon"
              @click="handleEmptyStateAction"
            >
              {{ emptyStateConfig.action.label }}
            </el-button>
          </el-empty>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useBreakpoints } from '@/composables/useBreakpoints'
import { useSectionVisibility } from '@/composables/useSectionVisibility'
import FieldRenderer from '@/components/engine/FieldRenderer.vue'

const props = defineProps({
  section: {
    type: Object,
    required: true
  },
  parentSection: {
    type: Object,
    default: null
  },
  responsive: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['field-change', 'collapse-change', 'drag-start'])

// 响应式断点
const { currentBreakpoint } = useBreakpoints()

// 区块可见性控制
const {
  isVisible,
  checkVisibility
} = useSectionVisibility(props.section)

// 区块折叠状态
const isCollapsed = ref(false)

// 区块配置
const config = computed(() => props.section.config || {})

// 布局配置
const layout = computed(() => {
  const responsive = props.responsive ? currentBreakpoint.value : 'desktop'
  return config.value.responsive?.[responsive] || config.value.layout || {}
})

// 交互配置
const interaction = computed(() => config.value.interaction || {})

// 样式配置
const style = computed(() => config.value.style || {})

// 显示规则配置
const display = computed(() => config.value.display || {})

// 内容配置
const content = computed(() => config.value.content || {})

// 是否可折叠
const collapsible = computed(() => interaction.value.collapsible !== false)

// 是否可拖拽
const draggable = computed(() => interaction.value.draggable !== false)

// 是否默认折叠
const defaultCollapsed = computed(() => {
  const responsive = props.responsive ? currentBreakpoint.value : 'desktop'
  const responsiveConfig = config.value.responsive?.[responsive]
  return responsiveConfig?.defaultCollapsed || interaction.value.defaultCollapsed || false
})

// 图标配置
const iconConfig = computed(() => {
  const titleStyle = style.value.title || {}
  return {
    enabled: titleStyle.icon?.enabled !== false,
    name: props.section.icon || titleStyle.icon?.name || 'InfoFilled',
    size: titleStyle.icon?.size || '18px',
    color: titleStyle.icon?.color || '#409EFF',
    position: titleStyle.icon?.position || 'before'
  }
})

// 区块类名
const sectionClasses = computed(() => {
  const classes = []

  // 自定义类名
  if (style.value.customClass) {
    classes.push(style.value.customClass)
  }

  // 折叠状态类
  if (isCollapsed.value) {
    classes.push('is-collapsed')
  }

  // 只读状态类
  if (isReadonly.value) {
    classes.push('is-readonly')
  }

  // 条件样式类
  if (activeConditionalStyle.value) {
    classes.push(activeConditionalStyle.value.className)
  }

  return classes
})

// 区块样式
const sectionStyles = computed(() => {
  const styles = {}
  const layoutConfig = layout.value

  if (layoutConfig.border) {
    styles.border = `${layoutConfig.borderWidth || '1px'} ${layoutConfig.borderStyle || 'solid'} ${layoutConfig.borderColor || '#DCDFE6'}`
    styles.borderRadius = layoutConfig.borderRadius || '4px'
  }

  if (layoutConfig.backgroundColor) {
    styles.backgroundColor = layoutConfig.backgroundColor
  }

  if (layoutConfig.margin) {
    styles.margin = layoutConfig.margin
  }

  if (layoutConfig.padding) {
    styles.padding = layoutConfig.padding
  }

  // 应用条件样式
  if (activeConditionalStyle.value?.styles) {
    Object.assign(styles, activeConditionalStyle.value.styles)
  }

  return styles
})

// 区块体样式
const bodyStyles = computed(() => {
  const styles = {}
  const layoutConfig = layout.value

  if (layoutConfig.padding) {
    styles.padding = layoutConfig.padding
  }

  return styles
})

// 区块体类名
const bodyClasses = computed(() => {
  const columns = layout.value.columns || 1
  return `section-columns-${columns}`
})

// 激活的条件样式
const activeConditionalStyle = computed(() => {
  const conditionalStyles = style.value.conditionalStyles || []
  return conditionalStyles.find(cs => evaluateCondition(cs.condition))
})

// 评估条件表达式
const evaluateCondition = (condition) => {
  // TODO: 实现条件表达式评估逻辑
  return true
}

// 是否只读
const isReadonly = computed(() => {
  return display.value.permissions?.readonlyOnNoPermission || false
})

// 是否显示头部
const showHeader = computed(() => {
  return props.section.name || props.section.icon
})

// 是否显示描述
const showDescription = computed(() => {
  return !isCollapsed.value && props.section.description
})

// 可见字段列表
const visibleFields = computed(() => {
  const fields = props.section.section_fields || []
  return fields.filter(f => f.field_config?.visible !== false)
})

// 是否有子区块
const hasSubSections = computed(() => {
  return props.section.sub_sections?.length > 0
})

// 子区块列表
const subSections = computed(() => {
  return props.section.sub_sections || []
})

// 是否显示空状态
const showEmptyState = computed(() => {
  return content.value.emptyState?.enabled && visibleFields.value.length === 0
})

// 空状态配置
const emptyStateConfig = computed(() => {
  return {
    icon: content.value.emptyState?.display?.icon || 'Box',
    text: content.value.emptyState?.display?.text || '暂无数据',
    action: content.value.emptyState?.display?.action || {}
  }
})

// 过渡动画名称
const transitionName = computed(() => {
  return interaction.value.animation?.enabled ? 'section-collapse' : ''
})

// 处理头部点击
const handleHeaderClick = () => {
  if (collapsible.value) {
    toggleCollapse()
  }
}

// 切换折叠状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  emit('collapse-change', isCollapsed.value)

  // 持久化折叠状态
  if (interaction.value.persistState) {
    localStorage.setItem(`section_collapsed_${props.section.id}`, isCollapsed.value)
  }
}

// 处理字段变化
const handleFieldChange = (field, value) => {
  emit('field-change', { field, value })
}

// 处理子区块字段变化
const handleSubSectionFieldChange = (data) => {
  emit('field-change', data)
}

// 处理拖拽开始
const handleDragStart = (e) => {
  emit('drag-start', {
    section: props.section,
    event: e
  })
}

// 处理空状态操作
const handleEmptyStateAction = () => {
  const action = emptyStateConfig.value.action
  if (action.handler) {
    // TODO: 调用处理器
    console.log('Execute action:', action.handler)
  }
}

// 动画钩子
const handleBeforeEnter = (el) => {
  el.style.height = '0'
}

const handleAfterLeave = (el) => {
  el.style.height = '0'
}

// 初始化
onMounted(() => {
  // 恢复折叠状态
  if (collapsible.value && interaction.value.persistState) {
    const savedState = localStorage.getItem(`section_collapsed_${props.section.id}`)
    if (savedState !== null) {
      isCollapsed.value = savedState === 'true'
    } else {
      isCollapsed.value = defaultCollapsed.value
    }
  } else {
    isCollapsed.value = defaultCollapsed.value
  }

  // 检查可见性
  checkVisibility()
})

// 监听断点变化
watch(currentBreakpoint, () => {
  // 响应式调整
})
</script>

<style scoped>
.section-block {
  transition: all 0.3s ease;
}

.section-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.3s;
}

.section-header:hover {
  background-color: #F5F7FA;
}

.section-drag-handle {
  margin-right: 8px;
  cursor: move;
  color: #909399;
}

.section-icon {
  margin-right: 8px;
  display: flex;
  align-items: center;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.section-description {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.section-collapse-icon {
  margin-left: 8px;
  transition: transform 0.3s;
}

.section-body {
  overflow: hidden;
  transition: all 0.3s ease-in-out;
}

.section-fields {
  display: grid;
  gap: 16px;
}

.section-columns-1 {
  grid-template-columns: 1fr;
}

.section-columns-2 {
  grid-template-columns: repeat(2, 1fr);
}

.section-columns-3 {
  grid-template-columns: repeat(3, 1fr);
}

.section-columns-4 {
  grid-template-columns: repeat(4, 1fr);
}

.section-empty-state {
  padding: 40px 0;
  text-align: center;
}

/* 折叠动画 */
.section-collapse-enter-active,
.section-collapse-leave-active {
  transition: height 0.3s ease-in-out, opacity 0.3s ease-in-out;
}

.section-collapse-enter-from,
.section-collapse-leave-to {
  height: 0 !important;
  opacity: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .section-fields {
    grid-template-columns: 1fr !important;
  }

  .section-header {
    padding: 10px 12px;
  }
}
</style>
```

### 10.2 useSectionVisibility Composable

```javascript
import { ref, computed, watch } from 'vue'
import { usePermissions } from '@/composables/usePermissions'
import { useFormula } from '@/composables/useFormula'

export function useSectionVisibility(section) {
  const isVisible = ref(true)
  const { hasPermission } = usePermissions()

  // 检查区块可见性
  const checkVisibility = () => {
    const display = section.config?.display || {}

    // 1. 基础可见性
    if (display.visible === false) {
      isVisible.value = false
      return
    }

    // 2. 权限检查
    if (display.permissions?.view?.length > 0) {
      const hasViewPermission = display.permissions.view.some(perm =>
        hasPermission(perm)
      )
      if (!hasViewPermission) {
        isVisible.value = !display.permissions.hideOnNoPermission
        return
      }
    }

    // 3. 条件显示
    if (display.condition) {
      const { evaluateFormula } = useFormula()
      const conditionMet = evaluateFormula(display.condition)
      const logic = display.logic || 'show_when_match'

      isVisible.value = logic === 'show_when_match' ? conditionMet : !conditionMet
      return
    }

    // 4. 动态区块检查
    if (display.dynamic?.enabled) {
      // TODO: 动态区块可见性检查
    }

    isVisible.value = true
  }

  // 监听条件变化
  watch(
    () => section.config?.display,
    () => {
      checkVisibility()
    },
    { deep: true }
  )

  return {
    isVisible,
    checkVisibility
  }
}
```

### 10.3 Section 渲染 API

```javascript
// src/api/layout.js

import request from '@/utils/request'

export default {
  /**
   * 获取指定布局的区块列表
   */
  getSections(layoutId) {
    return request({
      url: `/api/layouts/${layoutId}/sections/`,
      method: 'get'
    })
  },

  /**
   * 获取区块详情
   */
  getSection(sectionId) {
    return request({
      url: `/api/sections/${sectionId}/`,
      method: 'get'
    })
  },

  /**
   * 创建区块
   */
  createSection(layoutId, data) {
    return request({
      url: `/api/layouts/${layoutId}/sections/`,
      method: 'post',
      data
    })
  },

  /**
   * 更新区块
   */
  updateSection(sectionId, data) {
    return request({
      url: `/api/sections/${sectionId}/`,
      method: 'patch',
      data
    })
  },

  /**
   * 删除区块
   */
  deleteSection(sectionId) {
    return request({
      url: `/api/sections/${sectionId}/`,
      method: 'delete'
    })
  },

  /**
   * 批量更新区块排序
   */
  updateSectionOrder(layoutId, sectionOrders) {
    return request({
      url: `/api/layouts/${layoutId}/sections/order/`,
      method: 'post',
      data: { section_orders: sectionOrders }
    })
  },

  /**
   * 切换区块可见性
   */
  toggleSectionVisibility(sectionId, visible) {
    return request({
      url: `/api/sections/${sectionId}/visibility/`,
      method: 'post',
      data: { visible }
    })
  },

  /**
   * 获取区块树形结构
   */
  getSectionTree(layoutId) {
    return request({
      url: `/api/layouts/${layoutId}/sections/tree/`,
      method: 'get'
    })
  }
}
```

---

## 11. 最佳实践

### 11.1 区块设计原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **信息聚合** | 相关字段放在同一区块 | 资产编码、名称、分类放在"基本信息"区块 |
| **逻辑分组** | 按业务流程或信息层级分组 | 基本信息 > 详细信息 > 财务信息 |
| **适度分块** | 区块数量适中（3-7个） | 避免过多区块导致页面碎片化 |
| **命名清晰** | 区块名称简明扼要 | "基本信息"而非"资产基础相关信息" |
| **图标辅助** | 使用图标增强识别度 | 信息图标 + "基本信息" |
| **渐进展示** | 次要信息默认折叠 | 详细信息、历史记录默认收起 |

### 11.2 区块列数选择建议

| 场景 | 推荐列数 | 理由 |
|------|---------|------|
| **移动端表单** | 1列 | 确保可用性，避免横向滚动 |
| **标准表单** | 2列 | 平衡信息密度和可读性 |
| **简单字段表单** | 3-4列 | 短字段、选项类字段可多列排列 |
| **长文本字段** | 1列（span=总列数） | 确保文本输入区域足够宽 |
| **主从表单** | 主表1-2列，从表单列 | 主表简洁，从表突出 |

### 11.3 区块响应式策略

```json
{
  "responsive_strategy": {
    "desktop_first": {
      "description": "桌面优先，逐步降级",
      "steps": [
        "设计桌面端布局（2-3列）",
        "平板端调整为1-2列",
        "移动端强制1列",
        "非关键区块默认折叠"
      ]
    },
    "mobile_first": {
      "description": "移动优先，逐步增强",
      "steps": [
        "设计移动端布局（1列）",
        "平板端增加到2列",
        "桌面端增加到2-3列",
        "大屏端可增加到4列"
      ]
    }
  }
}
```

### 11.4 性能优化建议

| 优化点 | 配置 | 说明 |
|--------|------|------|
| **虚拟滚动** | 动态区块启用 | 大列表字段使用虚拟滚动 |
| **懒加载** | 折叠区块延迟渲染 | 仅在展开时渲染区块内容 |
| **防抖节流** | 字段变化联动 | 联动显示区块时添加防抖 |
| **缓存策略** | 动态区块数据 | 启用缓存，减少重复请求 |
| **动画优化** | 移动端关闭动画 | `animation.enabled: false` |
| **条件渲染** | 不可见区块不渲染 | 使用 `v-if` 而非 `v-show` |

### 11.5 可访问性建议

```json
{
  "accessibility": {
    "keyboard_navigation": {
      "enabled": true,
      "tabIndex": 0,
      "enterToCollapse": true
    },
    "screen_reader": {
      "announceCollapse": true,
      "announceFieldCount": true
    },
    "high_contrast": {
      "borderColor": "#000000",
      "titleColor": "#000000"
    },
    "focus_visible": {
      "enabled": true,
      "style": {
        "outline": "2px solid #409EFF",
        "outlineOffset": "2px"
      }
    }
  }
}
```

---

## 12. 常见问题

### 12.1 区块嵌套层级限制

**问题**: 区块最多支持几层嵌套？

**答案**: 最多支持 3 层嵌套（主区块 > 一级子区块 > 二级子区块）。过深嵌套会影响性能和用户体验。

### 12.2 区块内字段跨列

**问题**: 如何让某个字段独占一行？

**答案**: 设置字段 `span` 属性为区块总列数。例如在 2 列区块中，设置 `span: 2` 即可独占一行。

### 12.3 区块权限控制

**问题**: 无权限时应该隐藏还是禁用区块？

**答案**: 推荐隐藏（`hideOnNoPermission: true`）。如需提示用户存在该区块，可使用禁用模式（`disabledOnNoPermission: true`）配合权限提示。

### 12.4 区块性能优化

**问题**: 大量表单区块如何优化性能？

**答案**:
1. 启用区块懒加载（折叠区块延迟渲染）
2. 使用虚拟滚动处理大列表字段
3. 限制区块嵌套层级
4. 移动端关闭动画效果

### 12.5 区块样式冲突

**问题**: 多个条件样式同时满足时如何处理？

**答案**: 按配置数组顺序应用，后面的样式会覆盖前面的样式。建议将具体条件放在前面，通用条件放在后面。

---

## 附录

### A. 区块配置完整示例

参见章节 2.1 的完整 JSON 示例。

### B. Element Plus Icon 列表

参考官方文档: https://element-plus.org/zh-CN/component/icon.html

常用区块图标:
- `InfoFilled` - 信息
- `Document` - 文档
- `User` - 用户
- `Location` - 位置
- `Clock` - 时钟
- `Money` - 金钱
- `PriceTag` - 标签
- `Folder` - 文件夹
- `Setting` - 设置
- `Warning` - 警告
- `Lock` - 锁定
- `View` - 查看
- `Edit` - 编辑
- `Delete` - 删除
- `Plus` - 添加
- `ArrowDown` - 向下箭头
- `ArrowRight` - 向右箭头
- `Rank` - 排序/拖拽

### C. 响应式断点标准

```css
/* 移动端 */
@media (max-width: 767px) { }

/* 平板端（竖屏） */
@media (min-width: 768px) and (max-width: 991px) { }

/* 平板端（横屏） */
@media (min-width: 992px) and (max-width: 1199px) { }

/* 桌面端 */
@media (min-width: 1200px) and (max-width: 1919px) { }

/* 大屏 */
@media (min-width: 1920px) { }
```

### D. 参考资源

- Element Plus 组件库: https://element-plus.org/
- Vue 3 官方文档: https://vuejs.org/
- CSS Grid 布局: https://developer.mozilla.org/zh-CN/docs/Web/CSS/CSS_Grid_Layout
- Web Content Accessibility Guidelines (WCAG): https://www.w3.org/WAI/WCAG21/quickref/

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-15
**维护者**: GZEAMS 开发团队
