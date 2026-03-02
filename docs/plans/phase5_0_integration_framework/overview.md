# Phase 5.0: 通用ERP集成框架 - 总览

## 概述

建立通用的第三方系统集成框架，支持对接多种ERP系统（万达宝M18、SAP、金蝶、用友等），统一配置管理、数据映射、同步任务和日志监控。

---

## 1. 业务背景

### 1.1 集成需求

| 需求 | 说明 |
|------|------|
| **采购同步** | 采购订单从ERP同步到资产系统 |
| **财务对接** | 资产折旧数据推送ERP财务 |
| **组织同步** | 组织架构与ERP保持一致 |
| **数据映射** | 字段映射和数据转换 |

### 1.2 支持的系统

| 系统 | 类型 | 模块 |
|------|------|------|
| 万达宝M18 | ERP | 采购、财务、库存 |
| SAP | ERP | 采购、财务 |
| 金蝶 | ERP | 财务 |
| 用友 | ERP | 财务 |
| Odoo | ERP | 全模块 |

---

## 2. 功能架构

```
┌─────────────────────────────────────────────────────────────┐
│                    通用ERP集成框架                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   配置管理层                          │    │
│  │  IntegrationConfig                                  │    │
│  │  - 系统类型                                         │    │
│  │  - 连接配置                                         │    │
│  │  - 认证信息                                         │    │
│  │  - 同步配置                                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   数据映射层                          │    │
│  │  FieldMapping                                       │    │
│  │  - 源字段 → 目标字段                                 │    │
│  │  - 数据转换规则                                      │    │
│  │  - 默认值设置                                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   适配器层                            │    │
│  │  BaseIntegrationAdapter (抽象基类)                   │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │    │
│  │  │  M18   │ │  SAP   │ │ 金蝶  │ │ 用友   │      │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘      │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   任务调度层                          │    │
│  │  IntegrationTask                                    │    │
│  │  - 定时任务                                         │    │
│  │  - 手动触发                                         │    │
│  │  - 失败重试                                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   监控日志层                          │    │
│  │  IntegrationLog                                     │    │
│  │  - 请求记录                                         │    │
│  │  - 响应记录                                         │    │
│  │  - 错误日志                                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 核心模型

### 3.1 IntegrationConfig（集成配置）

| 字段 | 说明 |
|------|------|
| system_type | 系统类型（m18/sap/kingdee/yonyou） |
| system_name | 系统名称 |
| api_endpoint | API地址 |
| auth_config | 认证配置(JSON) |
| sync_config | 同步配置(JSON) |
| is_enabled | 是否启用 |

### 3.2 FieldMapping（字段映射）

| 字段 | 说明 |
|------|------|
| config | 关联集成配置 |
| business_object | 业务对象 |
| source_field | 源字段 |
| target_field | 目标字段 |
| transform_rule | 转换规则 |
| default_value | 默认值 |

### 3.3 IntegrationTask（同步任务）

| 字段 | 说明 |
|------|------|
| config | 关联集成配置 |
| task_type | 任务类型 |
| sync_direction | 同步方向 |
| status | 状态 |
| scheduled_at | 计划时间 |

### 3.4 IntegrationLog（集成日志）

| 字段 | 说明 |
|------|------|
| task | 关联任务 |
| request_data | 请求数据(JSON) |
| response_data | 响应数据(JSON) |
| status_code | 状态码 |
| error_message | 错误信息 |
| duration | 执行时长(ms) |

---

## 4. 适配器设计

### 4.1 基类接口

```python
class BaseIntegrationAdapter(ABC):
    """集成适配器基类"""

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        pass

    @abstractmethod
    def pull_data(self, object_type, params) -> List[Dict]:
        """拉取数据"""
        pass

    @abstractmethod
    def push_data(self, object_type, data) -> Dict[str, Any]:
        """推送数据"""
        pass

    @abstractmethod
    def transform_data(self, data, mapping) -> Dict[str, Any]:
        """数据转换"""
        pass
```

### 4.2 具体适配器

```python
class M18Adapter(BaseIntegrationAdapter):
    """万达宝M18适配器"""
    adapter_type = 'm18'

class SAPAdapter(BaseIntegrationAdapter):
    """SAP适配器"""
    adapter_type = 'sap'

class KingdeeAdapter(BaseIntegrationAdapter):
    """金蝶适配器"""
    adapter_type = 'kingdee'
```

---

## 5. 同步方向

| 方向 | 代码 | 说明 |
|------|------|------|
| 拉取 | pull | 第三方 → 本系统 |
| 推送 | push | 本系统 → 第三方 |
| 双向 | bidirectional | 双向同步 |

---

## 6. API接口

### 6.1 测试连接

```
POST /api/integration/configs/{id}/test/
Response: {
    "success": true,
    "message": "连接成功",
    "details": {...}
}
```

### 6.2 手动同步

```
POST /api/integration/sync/run/
Request: {
    "config_id": 1,
    "sync_type": "purchase_order",
    "direction": "pull"
}
```

### 6.3 查询同步日志

```
GET /api/integration/logs/?config_id=1
Response: {
    "results": [
        {
            "task_type": "purchase_order",
            "status": "success",
            "duration": 1250
        }
    ]
}
```

---

## 7. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 框架模型、适配器 |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 集成配置界面 |
| [test.md](./test.md) | 测试计划 |

---

## 8. 后续任务

1. 实现通用集成框架
2. 实现数据映射引擎
3. 实现任务调度
4. 实现M18适配器
5. 实现日志监控
