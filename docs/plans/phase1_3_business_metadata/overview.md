# Phase 1.3: 核心业务单据元数据配置 - 总览

## 概述

基于低代码元数据引擎，实现固定资产全生命周期核心业务单据的动态配置，支持字段定义、表单布局、数据存储的完全可配置化。

---

## 1. 业务背景

### 1.1 低代码驱动需求

| 痛点 | 解决方案 |
|------|----------|
| 字段变更需要改代码 | 元数据配置字段 |
| 表单布局固定死板 | 可视化布局配置 |
| 主子表关联复杂 | 内置关系支持 |
| 流程字段权限动态 | 绑定工作流引擎 |

### 1.2 核心目标

- **零代码扩展**：新增单据类型无需改代码
- **可视化配置**：拖拽式表单设计器
- **灵活存储**：PostgreSQL JSONB动态字段
- **无缝集成**：与工作流引擎深度集成

---

## 2. 功能架构

```
┌─────────────────────────────────────────────────────────────┐
│                    低代码元数据引擎                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐    │
│  │BusinessObject│───▶│FieldDefinition│───▶│  PageLayout  │    │
│  │  业务对象    │    │   字段定义    │    │   页面布局   │    │
│  │             │    │              │    │             │    │
│  │ - 资产卡片   │    │ - 基础字段   │    │ - 表单布局   │    │
│  │ - 领用单     │    │ - 自定义字段 │    │ - 列表布局   │    │
│  │ - 调拨单     │    │ - 公式字段   │    │ - 字段权限   │    │
│  │ - 盘点单     │    │ - 关联字段   │    │ - 显示规则   │    │
│  └─────────────┘    └──────────────┘    └─────────────┘    │
│         │                    │                     │         │
│         └────────────────────┼─────────────────────┘         │
│                              ▼                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Dynamic Object Routing Layer (新增)           │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ ObjectRegistry (对象注册表)                     │  │  │
│  │  │ - 启动时自动注册标准业务对象                     │  │  │
│  │  │ - 支持硬编码对象与动态对象共存                   │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ ObjectRouterViewSet (统一路由入口)              │  │  │
│  │  │ - /api/objects/{code}/ 动态路由                 │  │  │
│  │  │ - 自动分发到硬编码ViewSet或动态ViewSet           │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                              ▼                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           DynamicDataRepository (动态数据仓储)         │  │
│  │  - PostgreSQL JSONB存储自定义字段                      │  │
│  │  - 支持主子表关系存储                                  │  │
│  │  - 自动版本控制和审计                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 核心模型

### 3.1 BusinessObject（业务对象）

定义可配置的企业业务实体：

| 字段 | 说明 |
|------|------|
| code | 对象编码（唯一） |
| name | 对象名称 |
| enable_workflow | 是否启用工作流 |
| enable_version | 是否启用版本控制 |
| default_form_layout | 默认表单布局 |

### 3.2 FieldDefinition（字段定义）

定义业务对象的字段：

| 字段类型 | 说明 | 示例 |
|----------|------|------|
| text | 单行文本 | 资产名称 |
| textarea | 多行文本 | 备注 |
| number | 数字 | 金额、数量 |
| date | 日期 | 购入日期 |
| select | 下拉选择 | 资产状态 |
| user | 用户选择 | 保管人 |
| dept | 部门选择 | 使用部门 |
| reference | 关联引用 | 关联资产 |
| formula | 计算公式 | 折旧额 |
| subtable | 子表格 | 明细列表 |

### 3.3 PageLayout（页面布局）

定义表单和列表的展示布局：

```json
{
  "type": "form",
  "sections": [
    {
      "title": "基础信息",
      "columns": 2,
      "fields": ["asset_code", "asset_name", "category"]
    }
  ]
}
```

---

## 4. 字段类型支持

### 基础字段

| 类型 | 组件 | 校验 |
|------|------|------|
| text | el-input | 长度、正则 |
| textarea | el-input type="textarea" | 长度 |
| number | el-input-number | 范围 |
| date | el-date-picker | 日期范围 |
| select | el-select | 选项值 |

### 关联字段

| 类型 | 组件 | 数据源 |
|------|------|--------|
| user | UserPicker | 用户表 |
| dept | DeptTreePicker | 部门表 |
| reference | ReferenceSelector | 业务对象 |
| asset | AssetSelector | 资产表 |

### 高级字段

| 类型 | 特性 |
|------|------|
| formula | 自动计算 |
| subtable | 主子表 |
| location | 地图定位 |
| barcode | 扫码输入 |

---

## 5. 动态表单渲染

### 前端渲染流程

```
1. 加载业务对象元数据
   ↓
2. 加载字段定义
   ↓
3. 加载页面布局
   ↓
4. 渲染DynamicForm组件
   ↓
5. 用户交互/数据校验
   ↓
6. 提交到DynamicData API
```

### 数据存储结构

```json
{
  "id": 123,
  "business_object": "asset_card",
  "created_at": "2024-01-15",
  "custom_fields": {
    "asset_code": "ZC2024001",
    "asset_name": "MacBook Pro",
    "category": "电子设备",
    "purchase_price": 15000.00
  }
}
```

---

## 5. 公共模型引用声明

本模块完全遵循 **Common Base Features** 规范,所有组件继承公共基类:

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

---

## 6. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 元数据模型、动态存储 |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 动态表单渲染 |
| [test.md](./test.md) | 测试计划 |

---

## 7. 后续任务

1. 实现元数据模型和API
2. 实现前端DynamicForm组件
3. 实现表单设计器
4. 集成工作流引擎

---

## 8. 动态对象路由集成（新增）

### 8.1 统一API入口

所有通过元数据配置的业务对象，统一通过 `/api/objects/{code}/` 访问。

### 8.2 自动注册机制

系统启动时，ObjectRegistry 自动扫描并注册标准业务对象。

### 8.3 路由流程

```
前端请求: GET /api/objects/AssetPickup/
           ↓
ObjectRouterViewSet 接收
           ↓
获取 BusinessObject(code='AssetPickup')
           ↓
判断 is_hardcoded
    ↓              ↓
硬编码对象      动态对象
    ↓              ↓
使用原有     使用 MetadataDrivenViewSet
AssetPickupViewSet
           ↓
返回数据
```

### 8.4 元数据接口

GET /api/objects/{code}/metadata/

返回对象的字段定义、布局配置、权限等信息，供前端动态渲染。

---

## 9. 后续任务（更新）

1. 实现元数据模型和API
2. 实现前端DynamicForm组件
3. 实现表单设计器
4. 集成工作流引擎
5. **实现动态对象路由层**
   - 创建 ObjectRegistry 对象注册表
   - 实现 ObjectRouterViewSet 统一路由入口
   - 实现 MetadataDrivenViewSet 动态视图
   - 支持硬编码对象与动态对象共存
   - 提供元数据查询接口
6. **前端动态对象路由集成**
   - 更新 API 客户端支持统一入口
   - 实现基于元数据的动态表单/列表页
   - 优化路由配置
