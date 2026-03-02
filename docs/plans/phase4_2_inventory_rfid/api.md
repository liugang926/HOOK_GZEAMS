# Phase 4.2: RFID批量盘点 - API接口定义

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
| GET | `/api/inventory/rfid/reader_presets/` | 获取预置读写器配置 |
| POST | `/api/inventory/rfid/test_connection/` | 测试读写器连接 |
| POST | `/api/inventory/rfid/start_scan/` | 启动RFID扫描 |
| GET | `/api/inventory/rfid/scan_status/` | 获取扫描状态 |

---

## 1. 读写器配置

### 1.1 获取预置配置

**请求**
```
GET /api/inventory/rfid/reader_presets/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "data": [
    {
      "name": "Impinj R420",
      "type": "impinj",
      "default_port": 5084,
      "description": "Impinj R420 超高频RFID读写器"
    },
    {
      "name": "通用超高频读写器",
      "type": "generic",
      "default_port": 5084,
      "description": "符合LLRP协议的通用超高频RFID读写器"
    }
  ]
}
```

---

## 2. 连接测试

### 2.1 测试连接

**请求**
```
POST /api/inventory/rfid/test_connection/
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "generic",
  "host": "192.168.1.100",
  "port": 5084
}
```

**响应（成功）**
```json
{
  "success": true,
  "info": {
    "type": "GenericLLRP",
    "host": "192.168.1.100",
    "port": 5084,
    "connected": true
  }
}
```

**响应（失败）**
```json
{
  "success": false,
  "error": {
    "code": "CONNECTION_FAILED",
    "message": "连接超时"
  }
}
```

---

## 3. 扫描操作

### 3.1 启动扫描

**请求**
```
POST /api/inventory/rfid/start_scan/
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_id": 1,
  "reader_config": {
    "type": "impinj",
    "host": "192.168.1.100",
    "port": 5084,
    "duration": 60
  }
}
```

**响应**
```json
{
  "success": true,
  "message": "RFID扫描任务已启动",
  "data": {
    "task_id": "celery-task-id-123"
  }
}
```

### 3.2 获取扫描状态

**请求**
```
GET /api/inventory/rfid/scan_status/?task_id=celery-task-id-123
Authorization: Bearer <token>
```

**响应（进行中）**
```json
{
  "success": true,
  "message": "扫描进行中",
  "data": {
    "task_id": "celery-task-id-123",
    "status": "PROGRESS",
    "meta": {
      "progress": 45,
      "scanned": 225,
      "total": 500,
      "latest": {
        "asset_id": 123,
        "asset_code": "ZC001",
        "asset_name": "MacBook Pro",
        "scan_time": "2024-01-20T10:30:00Z"
      }
    }
  }
}
```

**响应（完成）**
```json
{
  "success": true,
  "message": "扫描完成",
  "data": {
    "task_id": "celery-task-id-123",
    "status": "SUCCESS",
    "result": {
      "status": "completed",
      "total_scanned": 498,
      "results": [
        {
          "asset_id": 123,
          "asset_code": "ZC001",
          "asset_name": "MacBook Pro",
          "epc": "3034A2B3C4D5E6F708192A3B4C5D6E7F",
          "scan_time": "2024-01-20T10:30:00Z"
        }
      ]
    }
  }
}
```

**响应（失败）**
```json
{
  "success": false,
  "error": {
    "code": "SERVER_ERROR",
    "message": "连接读写器失败"
  }
}
```

---

## 4. 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| SERVER_ERROR | 500 | 连接读写器失败 |
| SERVER_ERROR | 504 | 连接超时 |
| NOT_FOUND | 404 | 读写器不存在 |
| NOT_FOUND | 404 | 盘点任务不存在 |
| VALIDATION_ERROR | 400 | 扫描任务已在运行 |
| VALIDATION_ERROR | 400 | 无效的读写器配置 |

---

## 后续任务

1. Phase 4.3: 实现盘点快照和差异处理
2. Phase 5.1: 实现万达宝M18采购对接
