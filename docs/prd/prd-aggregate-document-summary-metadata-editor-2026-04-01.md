# Aggregate Document Summary Metadata Editor PRD

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-04-01 |
| 涉及阶段 | Phase 7.2.54 |
| 作者/Agent | Codex |

## 1. 功能概述与业务场景

### 1.1 背景
当前 aggregate document 的 `documentSummarySections` 只能通过 [menu_config.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/system/menu_config.py) 等硬编码方式治理。运行时已经支持该协议，但元数据管理员无法在页面布局设计器内按对象/布局粒度调整 summary section 的顺序和 surface priority。

### 1.2 目标
- 在 Page Layout Designer 中暴露 aggregate document summary metadata 编辑能力。
- 允许管理员以结构化方式维护 `process_summary / record / workflow / batch_tools` 四个 section 的顺序与 `surfacePriority`。
- 保持运行时协议、后端校验、设计器保存链路一致，避免继续依赖手写 JSON 或 Python 配置。

### 1.3 非目标
- 本期不新增新的 summary section code。
- 本期不开放任意 workbench metadata 的通用 JSON 编辑器。
- 本期不修改 aggregate document 页面运行时渲染逻辑，仅补元数据入口与校验。

## 2. 用户角色与权限

| 角色 | 权限 | 说明 |
|------|------|------|
| 系统管理员 | 可访问 Page Layout 管理与设计器 | 负责统一运行时布局治理 |
| 元数据管理员 | 可编辑 `PageLayout` | 负责对象级布局与 workbench metadata 配置 |
| 业务用户 | 只读运行时结果 | 无法编辑元数据 |

## 3. 公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、`custom_fields` |
| Serializer | BaseModelSerializer | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 方法 |

说明：
- 本期核心承载对象仍为 `PageLayout`，不新增数据库表或独立业务对象。
- 运行时读取仍走统一动态对象路由 `/api/objects/{code}/runtime/`。

## 4. 数据模型设计

### 4.1 复用现有模型
- `PageLayout.layout_config`：继续作为布局元数据 JSON 容器。

### 4.2 新增元数据结构
在 `layout_config.workbench.document_summary_sections` 中保存 aggregate document summary sections：

```json
{
  "workbench": {
    "document_summary_sections": [
      { "code": "process_summary", "surface_priority": "primary" },
      { "code": "record", "surface_priority": "context" },
      { "code": "workflow", "surface_priority": "context" },
      { "code": "batch_tools", "surface_priority": "admin" }
    ]
  }
}
```

### 4.3 约束
- `code` 仅允许：
  - `process_summary`
  - `record`
  - `workflow`
  - `batch_tools`
- `surface_priority` 仅允许：
  - `primary`
  - `context`
  - `related`
  - `activity`
  - `admin`
- 后端需兼容 camelCase 输入：
  - `documentSummarySections`
  - `surfacePriority`

## 5. API接口设计

### 5.1 复用现有接口
- `POST /api/system/page-layouts/`
- `PATCH /api/system/page-layouts/{id}/`
- `POST /api/system/page-layouts/{id}/publish/`
- `GET /api/objects/{code}/runtime/`

### 5.2 请求示例

```json
{
  "layoutConfig": {
    "sections": [
      {
        "id": "section-basic",
        "type": "section",
        "title": "Basic",
        "fields": [
          { "fieldCode": "name", "label": "Name", "span": 12 }
        ]
      }
    ],
    "workbench": {
      "documentSummarySections": [
        { "code": "process_summary", "surfacePriority": "primary" },
        { "code": "record", "surfacePriority": "context" },
        { "code": "workflow", "surfacePriority": "context" },
        { "code": "batch_tools", "surfacePriority": "admin" }
      ]
    }
  }
}
```

### 5.3 校验与错误码
- 保存非法 `code` / `surface_priority` 时返回 `VALIDATION_ERROR`。
- `PageLayoutSerializer` 负责：
  - 结构规范化
  - camelCase/snake_case 兼容
  - workbench metadata 校验

## 6. 前端组件设计

### 6.1 设计器入口
- 页面：`PageLayoutDesigner`
- 设计器：`WysiwygLayoutDesigner`

### 6.2 新增组件
- `DesignerWorkbenchMetadataPanel.vue`
  - 位置：设计器右侧属性区下方
  - 职责：编辑 aggregate document summary section 的顺序与 surface priority

### 6.3 辅助模块
- `designerWorkbenchMetadata.ts`
  - 归一化默认 section
  - 输出稳定的排序与序列化结果

### 6.4 交互要求
- 默认展示四个固定 section。
- 支持：
  - 上移
  - 下移
  - priority 调整
  - 恢复默认
- 所有变更必须接入设计器历史记录、autosave 与保存/发布链路。

## 7. 测试用例

### 7.1 后端
- `PageLayoutSerializer` 接收 camelCase 的 `documentSummarySections` 并规范化为 snake_case。
- 非法 `surfacePriority` 被拒绝。

### 7.2 前端
- `DesignerWorkbenchMetadataPanel` 在部分 payload 下补齐四个默认 section。
- priority 调整后发出稳定 payload。
- 顺序调整后发出稳定 payload。
- `WysiwygLayoutDesigner` 原有 section selection 回归保持通过。
