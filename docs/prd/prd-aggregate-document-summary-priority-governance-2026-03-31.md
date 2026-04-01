# PRD: Aggregate Document Summary Priority 治理

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.53 |
| 作者/Agent | Codex |

## 1. 功能概述与业务场景

### 1.1 背景
Phase 7.2.52 已将 aggregate document 的 `workflow / stage / signal / navigation` 收敛到统一 `Process Summary`，但单据 summary surface 中剩余的 `Record / Workflow / Batch Tools` 仍然缺少首屏优先级治理。

现状问题：
- 单据页新增一个 summary block，就会继续直接进入首屏。
- `Record / Workflow / Batch Tools` 在模板层属于硬编码顺序，无法通过 runtime metadata 调整。
- 即使已有 `surfacePriority` 协议，aggregate document summary blocks 仍然没有进入这套治理体系。

### 1.2 目标
将 aggregate document summary blocks 也纳入优先级协议：
- 新增 `workbench.documentSummarySections`
- 支持为 `process_summary / record / workflow / batch_tools` 声明 `surfacePriority`
- 首屏仅展示 `primary / context` sections
- `related / admin` sections 下沉到二级折叠区，降低首屏密度

### 1.3 适用对象
- `PurchaseRequest`
- `AssetReceipt`
- `AssetPickup`
- `AssetTransfer`
- `AssetReturn`
- `AssetLoan`
- `DisposalRequest`

### 1.4 本阶段不做
- 不新增新的 summary tab
- 不修改 aggregate document API 路由
- 不引入新的数据库 schema
- 不把 section priority 暴露到后台 UI 编辑器

## 2. 用户角色与权限

| 角色 | 查看单据页 | 查看首屏摘要 | 查看次级折叠摘要 | 执行动作 |
|------|------------|--------------|------------------|----------|
| 资产管理员 | 是 | 是 | 是 | 是 |
| 单据经办人 | 是 | 是 | 是 | 是 |
| 审批人 | 是 | 是 | 按权限 | 按流程权限 |
| 普通查看用户 | 是 | 是 | 按权限 | 否 |

说明：
- 本阶段不新增权限点。
- section priority 只影响呈现层级，不改变数据可见性边界。

## 3. 公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、`custom_fields` |
| Serializer | BaseModelSerializer | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 方法 |

补充说明：
- 本阶段无模型变更，重点在 runtime metadata 与前端渲染治理。

## 4. 数据模型设计

### 4.1 持久化模型
本阶段无数据库 schema 变更。

### 4.2 运行时协议扩展

| 字段 | 位置 | 说明 |
|------|------|------|
| `documentSummarySections` | `RuntimeWorkbench` | 单据 summary 区块配置 |
| `document_summary_sections` | 后端 workbench payload | snake_case 兼容字段 |

Section code 范围：
- `process_summary`
- `record`
- `workflow`
- `batch_tools`

Section priority 范围：
- `primary`
- `context`
- `related`
- `activity`
- `admin`

### 4.3 展示规则
1. `primary / context` 区块直接进入 summary 首屏。
2. `related / admin` 区块下沉到折叠区 `More Summary`。
3. 未配置 `documentSummarySections` 的对象使用默认顺序：
   - `process_summary` → `primary`
   - `record` → `context`
   - `workflow` → `context`
   - `batch_tools` → `admin`
4. 如果 runtime metadata 只配置部分 sections，系统自动补齐缺失的默认 sections。

## 5. API 接口设计

本阶段不新增接口，仅扩展 runtime payload：

| 方法 | 接口 | 变更 |
|------|------|------|
| `GET` | `/api/system/objects/{code}/runtime/` | `workbench.documentSummarySections` |

错误码继续沿用：
- `VALIDATION_ERROR`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `SERVER_ERROR`

## 6. 前端组件设计

### 6.1 Runtime Contract / Resolver
- 新增 `documentSummarySections` 类型定义
- 新增 contract 校验
- 新增 runtime resolver 归一化

### 6.2 DocumentWorkbench
- 读取 `documentSummarySections`
- 按 section priority 划分 primary summary 与 secondary summary
- 低优先级 sections 放入折叠区

### 6.3 Menu Config
- 为 aggregate document workbench 补齐默认 `document_summary_sections`
- 保持 snake_case / camelCase 双兼容

## 7. 测试用例

### 7.1 前端
- runtime contract 接受合法 `documentSummarySections`
- runtime contract 拒绝非法 `documentSummarySections`
- runtime resolver 输出 `documentSummarySections`
- `DocumentWorkbench` 将 admin section 下沉到折叠区

### 7.2 后端
- runtime API 默认返回 `documentSummarySections: []`
- runtime 覆写能透传 `documentSummarySections`
- menu config 为目标 aggregate documents 补齐默认 sections

### 7.3 验收标准
- aggregate document summary surface 不再无限向首屏堆叠
- section 优先级进入 runtime metadata，可被后续对象复用
- `Process Summary` 继续保持首屏主位，`Batch Tools` 等低优先级块进入次级区域
