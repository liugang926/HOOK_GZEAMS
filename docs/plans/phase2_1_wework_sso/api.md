# Phase 2.1: 企业微信SSO登录 - API接口定义

## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

## 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sso/wework/config/` | 获取企业微信登录配置 |
| GET | `/api/sso/wework/auth-url/` | 获取企业微信授权URL |
| GET | `/api/sso/wework/qr-url/` | 获取企业微信扫码登录URL |
| POST | `/api/sso/wework/callback/` | 处理企业微信OAuth回调 |
| POST | `/api/sso/wework/bind/` | 绑定企业微信账号 |
| DELETE | `/api/sso/wework/unbind/` | 解绑企业微信账号 |
| POST | `/api/auth/login/` | 账号密码登录 |
| POST | `/api/auth/logout/` | 登出 |
| GET | `/api/auth/me/` | 获取当前用户信息 |

---

## 1. 企业微信登录接口

### 1.1 获取登录配置

**请求**
```
GET /api/sso/wework/config/
```

**响应**
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "corp_name": "示例企业",
    "agent_id": 1000001
  }
}
```

**响应（未启用）**
```json
{
  "success": true,
  "data": {
    "enabled": false,
    "message": "企业微信未配置或未启用"
  }
}
```

### 1.2 获取授权URL

**请求**
```
GET /api/sso/wework/auth-url/
```

**响应**
```json
{
  "success": true,
  "data": {
    "auth_url": "https://open.weixin.qq.com/connect/oauth2/authorize?appid=ww123&redirect_uri=https%3A%2F%2Fexample.com%2Fsso%2Fwework%2Fcallback&response_type=code&scope=snsapi_base&agentid=1000001&state=abc123#wechat_redirect"
  }
}
```

### 1.3 获取扫码登录URL

**请求**
```
GET /api/sso/wework/qr-url/
```

**响应**
```json
{
  "success": true,
  "data": {
    "qr_url": "https://open.work.weixin.qq.com/wwopen/sso/qrConnect?appid=ww123&agentid=1000001&redirect_uri=https%3A%2F%2Fexample.com%2Fsso%2Fwework%2Fcallback&state=abc123&usertype=member"
  }
}
```

### 1.4 处理OAuth回调

**请求**
```
POST /api/sso/wework/callback/
Content-Type: application/json

{
  "code": "abc123def456",
  "state": "random_state_string"
}
```

**响应（成功）**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 123,
      "username": "zhangsan",
      "real_name": "张三",
      "email": "zhangsan@example.com",
      "mobile": "13800138000",
      "avatar": "https://example.com/avatar.jpg",
      "department": 5,
      "roles": ["employee"]
    }
  }
}
```

**响应（失败）**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "无效的state参数"
  }
}
```

---

## 2. 账号绑定接口

### 2.1 绑定企业微信账号

**请求**
```
POST /api/sso/wework/bind/
Content-Type: application/json

{
  "wework_userid": "zhangsan"
}
```

或通过手机号绑定：
```json
{
  "mobile": "13800138000"
}
```

**响应**
```json
{
  "success": true,
  "message": "绑定成功"
}
```

**响应（失败）**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "未找到对应的企业微信账号"
  }
}
```

### 2.2 解绑企业微信账号

**请求**
```
DELETE /api/sso/wework/unbind/
```

**响应**
```json
{
  "success": true,
  "message": "解绑成功"
}
```

---

## 3. 账号密码登录接口

### 3.1 账号密码登录

**请求**
```
POST /api/auth/login/
Content-Type: application/json

{
  "username": "zhangsan",
  "password": "password123"
}
```

**响应**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 123,
      "username": "zhangsan",
      "real_name": "张三",
      "email": "zhangsan@example.com",
      "mobile": "13800138000",
      "avatar": "https://example.com/avatar.jpg",
      "department": {
        "id": 5,
        "name": "研发部"
      },
      "roles": ["employee"]
    }
  }
}
```

**错误响应**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "用户名或密码错误"
  }
}
```

### 3.2 登出

**请求**
```
POST /api/auth/logout/
```

**Headers**
```
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "登出成功"
}
```

### 3.3 获取当前用户信息

**请求**
```
GET /api/auth/me/
```

**Headers**
```
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "username": "zhangsan",
    "real_name": "张三",
    "email": "zhangsan@example.com",
    "mobile": "13800138000",
    "avatar": "https://example.com/avatar.jpg",
    "organization": {
      "id": 1,
      "name": "示例企业"
    },
    "department": {
      "id": 5,
      "name": "研发部",
      "path": "总部/技术中心/研发部"
    },
    "roles": [
      {
        "id": 3,
        "code": "employee",
        "name": "普通员工"
      }
    ],
    "permissions": [
      "assets:view",
      "assets:edit",
      "consumables:view"
    ]
  }
}
```

**错误响应**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Token已过期"
  }
}
```

---

## 4. Token刷新接口

### 4.1 刷新Token

**请求**
```
POST /api/auth/refresh/
```

**Headers**
```
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "Token刷新成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

---

## 企业微信相关URL

| 环境 | URL |
|------|-----|
| 生产环境 | https://qyapi.weixin.qq.com |
| 体验环境 | https://qyapi.weixin.qq.com |

## 企业微信API端点

| 功能 | 端点 | 说明 |
|------|------|------|
| 获取access_token | /cgi-bin/gettoken | 获取应用凭证 |
| 获取用户信息 | /cgi-bin/auth/getuserinfo | 通过code获取成员userid |
| 获取成员详情 | /cgi-bin/user/get | 获取成员详细信息 |
| 获取部门列表 | /cgi-bin/department/list | 获取全部部门列表 |
| 获取部门成员 | /cgi-bin/user/list | 获取部门成员详情 |

---

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| invalid_credentials | 401 | 用户名或密码错误 |
| token_expired | 401 | Token已过期 |
| invalid_token | 401 | 无效的Token |
| wework_not_enabled | 400 | 企业微信未启用 |
| invalid_state | 400 | 无效的state参数 |
| user_not_found | 404 | 用户不存在 |
| user_disabled | 403 | 用户已被禁用 |
| invalid_oauth_code | 400 | OAuth授权码无效 |
| oauth_access_denied | 403 | OAuth授权被拒绝 |

---

## JWT Token结构

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": 123,
    "username": "zhangsan",
    "org_id": 1,
    "exp": 1718720000,
    "iat": 1718115200
  }
}
```

| 字段 | 说明 |
|------|------|
| user_id | 用户ID |
| username | 用户名 |
| org_id | 组织ID |
| exp | 过期时间（Unix时间戳） |
| iat | 签发时间（Unix时间戳） |
