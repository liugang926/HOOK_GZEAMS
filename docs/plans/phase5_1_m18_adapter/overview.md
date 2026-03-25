# Phase 5.1: 万达宝M18适配器 - 总览

## 概述

基于通用集成框架实现万达宝M18 ERP适配器，支持采购订单、收货单等业务数据同步。

---

## 1. 业务背景

### 1.1 M18系统

万达宝M18是一套ERP系统，涵盖：
- 采购管理
- 财务核算
- 库存管理
- 人力资源管理

### 1.2 集成场景

| 场景 | 方向 | 说明 |
|------|------|------|
| 采购订单同步 | pull | M18采购订单 → 资产系统 |
| 收货单同步 | pull | M18收货单 → 资产入库 |
| 折旧数据推送 | push | 资产折旧 → M18财务 |

---

## 2. 功能架构

```
┌─────────────────────────────────────────────────────────────┐
│                    万达宝M18适配器                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   M18API                             │    │
│  │  - OAuth2认证                                       │    │
│  │  - RESTful接口                                      │    │
│  │  - 分页查询                                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  M18Adapter                          │    │
│  │  - test_connection()    测试连接                    │    │
│  │  - pull_purchase_orders() 拉取采购订单               │    │
│  │  - pull_grn_notes()      拉取收货单                  │    │
│  │  - push_depreciation()   推送折旧数据                │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  数据映射                             │    │
│  │  M18字段 → 资产系统字段                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  资产业务对象                          │    │
│  │  PurchaseRequest / AssetReceipt                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. M18 API

### 3.1 认证接口

```
POST /oauth/token
Request: {
    "grant_type": "client_credentials",
    "client_id": "xxx",
    "client_secret": "xxx"
}
Response: {
    "access_token": "xxx",
    "expires_in": 7200
}
```

### 3.2 采购订单查询

```
GET /api/purchase-orders
Headers: {
    "Authorization": "Bearer {token}"
}
Query: {
    "date_from": "2024-01-01",
    "date_to": "2024-01-31",
    "page": 1,
    "page_size": 100
}
```

### 3.3 收货单查询

```
GET /api/goods-receipt-notes
Query: {
    "po_number": "PO20240115001",
    "page": 1,
    "page_size": 100
}
```

---

## 4. 数据映射

### 4.1 采购订单映射

| M18字段 | 资产系统字段 | 转换规则 |
|---------|-------------|----------|
| poNumber | purchase_no | 直接映射 |
| supplierCode | supplier_id | 查找转换 |
| orderDate | purchase_date | 格式转换 |
| lines | items | 列表转换 |
| lines.itemCode | asset_code | 映射 |
| lines.quantity | quantity | 直接映射 |
| lines.unitPrice | unit_price | 直接映射 |

### 4.2 收货单映射

| M18字段 | 资产系统字段 | 转换规则 |
|---------|-------------|----------|
| grnNumber | receipt_no | 直接映射 |
| poNumber | purchase_no | 关联 |
| receiptDate | receipt_date | 格式转换 |
| lines | items | 列表转换 |
| lines.actualQty | actual_quantity | 直接映射 |

---

## 5. 同步流程

### 5.1 拉取采购订单

```
1. 获取M18 access_token
2. 调用采购订单API
3. 分页处理所有数据
4. 按映射规则转换
5. 创建/更新本地采购单
6. 记录同步日志
```

### 5.2 拉取收货单

```
1. 获取M18 access_token
2. 调用收货单API
3. 关联本地采购单
4. 创建资产卡片
5. 更新采购单状态
6. 记录同步日志
```

### 5.3 推送折旧数据

```
1. 查询已审核折旧记录
2. 按映射规则转换
3. 调用M18财务接口
4. 记录推送结果
5. 更新推送状态
```

---

## 6. API接口

### 6.1 测试连接

```
POST /api/integration/m18/test/
Request: {
    "api_endpoint": "https://m18.example.com/api",
    "client_id": "xxx",
    "client_secret": "xxx"
}
Response: {
    "success": true,
    "company_name": "测试公司"
}
```

### 6.2 同步采购订单

```
POST /api/integration/m18/sync/purchase-orders/
Request: {
    "date_from": "2024-01-01",
    "date_to": "2024-01-31"
}
Response: {
    "synced_count": 50,
    "failed_count": 0
}
```

### 6.3 同步收货单

```
POST /api/integration/m18/sync/grn-notes/
Request: {
    "po_numbers": ["PO001", "PO002"]
}
Response: {
    "synced_count": 2,
    "assets_created": 20
}
```

---

## 7. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - M18适配器 |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 同步配置界面 |
| [test.md](./test.md) | 测试计划 |

---

## 8. 后续任务

1. 实现M18认证
2. 实现采购订单同步
3. 实现收货单同步
4. 实现折旧数据推送
5. 实现同步日志查询
