# Phase 2.1: 企业微信SSO登录 - 总览

## 概述

集成企业微信单点登录（SSO），用户使用企业微信账号直接登录系统，无需额外注册和记忆密码。

---

## 1. 业务背景

### 1.1 SSO集成价值

| 价值 | 说明 |
|------|------|
| **简化登录** | 无需记忆额外密码 |
| **统一身份** | 与企业通讯录一致 |
| **降低维护** | 减少账号管理工作 |
| **提升安全** | 利用企业微信安全机制 |

### 1.2 集成流程

```
┌─────────────────────────────────────────────────────────────┐
│                    企业微信SSO登录流程                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. 用户点击"企业微信登录"                                    │
│     ↓                                                         │
│  2. 跳转企业微信授权页面                                      │
│     ↓                                                         │
│  3. 用户在企微确认授权                                        │
│     ↓                                                         │
│  4. 企微回调本系统，带上code                                  │
│     ↓                                                         │
│  5. 后端通过code获取用户信息                                  │
│     ↓                                                         │
│  6. 匹配/创建系统账号                                         │
│     ↓                                                         │
│  7. 生成本系统Token，登录成功                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 技术架构

### 2.1 企业微信OAuth2授权

```
┌─────────────┐        授权请求         ┌─────────────┐
│   本系统    │ ────────────────────▶  │  企业微信    │
│             │                       │             │
│  redirect   │ ◀──────────────────── │  callback   │
│  _uri      │      带上code          │   + code    │
└─────────────┘                       └─────────────┘
       │                                     │
       │  通过code获取access_token和用户信息  │
       ▼                                     ▼
┌─────────────────────────────────────────────────────┐
│                   后端服务                           │
│  1. 用code换取access_token                           │
│  2. 用access_token获取用户userid                      │
│  3. 用userid获取用户详情                              │
│  4. 根据userid匹配/创建系统账号                       │
│  5. 生成本系统JWT Token                              │
└─────────────────────────────────────────────────────┘
```

### 2.2 用户映射机制

| 场景 | 处理方式 |
|------|----------|
| 用户已存在 | 直接登录 |
| 用户不存在 | 自动创建账号（可配置） |
| 禁用用户 | 拒绝登录 |

---

## 3. 数据模型

### 3.1 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

### 3.2 WeWorkConfig（企业微信配置）

| 字段 | 说明 |
|------|------|
| corp_id | 企业ID |
| corp_name | 企业名称 |
| agent_id | 应用ID |
| agent_secret | 应用Secret |
| auto_create_user | 是否自动创建用户 |
| default_role_id | 默认角色 |
| is_enabled | 是否启用 |

**继承说明**：
- 继承 `BaseModel`，自动获得：
  - `organization`: 所属组织（外键）
  - `is_deleted`, `deleted_at`: 软删除字段
  - `created_at`, `updated_at`: 审计时间
  - `created_by`: 创建人（外键）
  - `custom_fields`: 动态字段（JSONB）

### 3.3 UserMapping（用户映射）

| 字段 | 说明 |
|------|------|
| user | 关联系统用户 |
| platform | 平台类型（wework/dingtalk/feishu） |
| platform_user_id | 第三方用户ID |
| union_id | 跨应用唯一ID |
| platform_info | 第三方用户信息（JSON） |

**继承说明**：
- 继承 `BaseModel`，自动获得公共字段（同WeWorkConfig）

### 3.4 OAuthState（OAuth状态）

| 字段 | 说明 |
|------|------|
| state | 状态码（防CSRF） |
| platform | 平台类型 |
| session_data | 会话数据（JSON） |
| expires_at | 过期时间 |

**继承说明**：
- 继承 `BaseModel`，自动获得公共字段（同WeWorkConfig）

---

## 4. API接口

### 4.1 获取授权链接

```
GET /api/sso/wework/authorize/
Response: {
    "authorize_url": "https://open.work.weixin.qq.com/wwopen/sso/..."
}
```

### 4.2 回调处理

```
GET /api/sso/wework/callback/?code=xxx&state=yyy
Response: {
    "access_token": "jwt_token",
    "user_info": {...}
}
```

### 4.3 绑定账号

```
POST /api/sso/wework/bind/
Request: {
    "platform_user_id": "userid",
    "verification_code": "扫码验证码"
}
```

---

## 5. 前端实现

### 5.1 登录页面

提供两种登录方式：
- 账号密码登录（传统方式）
- 企业微信登录（SSO方式）

### 5.2 二维码登录

支持企业微信扫码登录：
- 显示二维码
- 用户扫码确认
- 自动跳转进入系统

---

## 6. 安全措施

| 措施 | 说明 |
|------|------|
| **state校验** | 防止CSRF攻击 |
| **code一次性** | 授权码只能使用一次 |
| **有效期控制** | code有效期5分钟 |
| **HTTPS** | 强制使用HTTPS传输 |
| **绑定验证** | 绑定账号需二次验证 |

---

## 7. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - OAuth2流程、用户映射 |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 登录组件 |
| [test.md](./test.md) | 测试计划 |

---

## 8. 后续任务

1. 实现企业微信OAuth2集成
2. 实现用户映射机制
3. 实现前端SSO登录组件
4. 支持钉钉/飞书SSO扩展
