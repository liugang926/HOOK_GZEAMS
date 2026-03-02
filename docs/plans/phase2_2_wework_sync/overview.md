# Phase 2.2: 企业微信通讯录同步 - 总览

## 概述

将企业微信通讯录（部门、用户）同步到本系统，保持组织架构一致，支持定时同步和手动同步。

---

## 1. 业务背景

### 1.1 同步需求

| 需求 | 说明 |
|------|------|
| **部门同步** | 同步企业微信部门结构 |
| **用户同步** | 同步企业微信用户信息 |
| **增量同步** | 仅同步变更数据 |
| **定时同步** | 自动定时执行同步 |

### 1.2 同步范围

- 部门：部门ID、名称、父部门、排序
- 用户：用户ID、姓名、手机、邮箱、部门
- 部门成员关系：用户所属部门、是否部门负责人

---

## 2. 功能架构

```
┌─────────────────────────────────────────────────────────────┐
│                    企业微信通讯录同步                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  部门同步   │  │  用户同步   │  │  关系同步   │         │
│  │             │  │             │  │             │         │
│  │ - 部门树结构│  │ - 基础信息  │  │ - 用户部门  │         │
│  │ - 部门排序  │  │ - 职务信息  │  │ - 负责人标识│         │
│  │ - 部门状态  │  │ - 状态信息  │  │ - 主部门    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   同步服务层                          │    │
│  │  WeWorkSyncService                                 │    │
│  │  - get_departments()                               │    │
│  │  - get_users()                                     │    │
│  │  - sync_departments()                              │    │
│  │  - sync_users()                                    │    │
│  │  - handle_department_deleted()                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   本地数据模型                        │    │
│  │  Department / User / UserDepartment                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 同步策略

### 3.1 全量同步

首次同步或需要完全重建时使用：
1. 拉取企业微信全量部门
2. 拉取企业微信全量用户
3. 对比本地数据，执行增删改
4. 记录同步日志

### 3.2 增量同步

日常定时同步使用：
1. 仅拉取变更的部门
2. 仅拉取变更的用户
3. 更新本地数据
4. 记录变更日志

### 3.3 删除处理

| 场景 | 处理方式 |
|------|----------|
| 部门删除 | 本地标记为已删除 |
| 用户删除 | 本地禁用账号 |
| 用户移出部门 | 删除用户部门关联 |

---

## 4. 数据模型

### 4.1 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

### 4.2 SyncLog（同步日志）

| 字段 | 说明 |
|------|------|
| sync_type | 同步类型（department/user/full） |
| sync_source | 同步来源（wework/dingtalk/feishu） |
| status | 状态（running/success/failed） |
| started_at | 开始时间 |
| finished_at | 结束时间 |
| summary | 同步摘要（JSON） |

**继承说明**：
- 继承 `BaseModel`，自动获得：
  - `organization`: 所属组织（外键）
  - `is_deleted`, `deleted_at`: 软删除字段
  - `created_at`, `updated_at`: 审计时间
  - `created_by`: 创建人（外键）
  - `custom_fields`: 动态字段（JSONB）

### 4.3 UserMapping（用户映射）

| 字段 | 说明 |
|------|------|
| user | 关联系统用户 |
| platform | 平台类型 |
| platform_user_id | 企业微信userid |
| platform_dept_id | 企业微信部门id |
| is_leader | 是否部门负责人 |

**继承说明**：
- 继承 `BaseModel`，自动获得公共字段（同SyncLog）

### 4.4 Department 扩展字段

| 字段 | 说明 |
|------|------|
| wework_dept_id | 企业微信部门ID |
| wework_parent_id | 企业微信父部门ID |

**继承说明**：
- Department 模型继承 `BaseModel`，新增企业微信关联字段

---

## 5. 同步接口

### 5.1 手动触发同步

```
POST /api/sso/wework/sync/
Request: {
    "sync_type": "full"  // full / department / user
}
Response: {
    "sync_log_id": 123,
    "status": "running"
}
```

### 5.2 查询同步状态

```
GET /api/sso/wework/sync/status/
Response: {
    "last_sync_at": "2024-01-15T10:00:00Z",
    "last_sync_status": "success",
    "next_sync_at": "2024-01-15T11:00:00Z"
}
```

### 5.3 同步日志查询

```
GET /api/sso/wework/sync/logs/
Response: {
    "results": [
        {
            "sync_type": "full",
            "status": "success",
            "summary": {...}
        }
    ]
}
```

---

## 6. 定时任务

### Celery Beat 配置

```python
# 每小时执行一次增量同步
CELERY_BEAT_SCHEDULE = {
    'wework-incremental-sync': {
        'task': 'apps.sso.tasks.incremental_sync',
        'schedule': crontab(minute=0),  # 每小时
    },
    # 每天凌晨2点执行全量同步
    'wework-full-sync': {
        'task': 'apps.sso.tasks.full_sync',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

---

## 7. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 同步服务、定时任务 |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 同步管理界面 |
| [test.md](./test.md) | 测试计划 |

---

## 8. 后续任务

1. 实现企业微信API调用封装
2. 实现部门同步逻辑
3. 实现用户同步逻辑
4. 配置Celery定时任务
5. 实现同步管理界面
