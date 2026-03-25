# Phase 7.2: 资产项目管理 - API接口设计

## 1. 项目管理接口

### 1.1 项目列表

**请求**：
```http
GET /api/projects/
```

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 状态筛选 |
| project_type | string | 项目类型筛选 |
| project_manager | uuid | 项目经理筛选 |
| department | uuid | 部门筛选 |
| keyword | string | 搜索关键词 |

**响应**：
```json
{
    "success": true,
    "data": {
        "count": 20,
        "results": [
            {
                "id": "uuid-1",
                "project_code": "XM2025010001",
                "project_name": "AI平台研发项目",
                "project_alias": "AI平台",
                "project_type": "development",
                "status": "active",
                "start_date": "2025-01-01",
                "end_date": "2025-06-30",
                "project_manager": {
                    "id": "user-uuid",
                    "username": "zhangsan",
                    "full_name": "张三"
                },
                "department": {
                    "id": "dept-uuid",
                    "name": "研发部"
                },
                "planned_budget": "500000.00",
                "actual_cost": "120000.00",
                "asset_cost": "80000.00",
                "total_assets": 15,
                "active_assets": 12,
                "member_count": 8,
                "progress": 35.5,
                "days_elapsed": 20,
                "days_remaining": 161
            }
        ]
    }
}
```

### 1.2 创建项目

**请求**：
```http
POST /api/projects/
Content-Type: application/json
```

**请求体**：
```json
{
    "project_name": "AI平台研发项目",
    "project_alias": "AI平台",
    "project_type": "development",
    "project_manager": "user-uuid",
    "department": "dept-uuid",
    "start_date": "2025-01-01",
    "end_date": "2025-06-30",
    "planned_budget": "500000.00",
    "description": "企业级AI平台研发",
    "technical_requirements": "Python、TensorFlow、GPU服务器"
}
```

**响应**：
```json
{
    "success": true,
    "message": "项目创建成功",
    "data": {
        "id": "new-uuid",
        "project_code": "XM2025010002",
        "status": "planning",
        ...
    }
}
```

### 1.3 分配资产到项目

**请求**：
```http
POST /api/projects/{id}/allocate-assets/
Content-Type: application/json
```

**请求体**：
```json
{
    "assets": [
        {
            "asset_id": "asset-uuid-1",
            "custodian_id": "user-uuid-1"
        },
        {
            "asset_id": "asset-uuid-2",
            "custodian_id": "user-uuid-2"
        }
    ],
    "allocation_type": "temporary",
    "allocation_date": "2025-01-15",
    "return_date": "2025-06-30",
    "purpose": "用于AI模型训练",
    "usage_location": "数据中心A区"
}
```

**响应**：
```json
{
    "success": true,
    "message": "成功分配2项资产",
    "data": [
        {
            "id": "allocation-uuid-1",
            "allocation_no": "FP2025010001",
            "asset": {
                "asset_code": "ZC001",
                "asset_name": "GPU服务器"
            },
            "allocation_date": "2025-01-15",
            "return_status": "in_use"
        }
    ]
}
```

### 1.4 归还项目资产

**请求**：
```http
POST /api/projects/{id}/return-assets/
Content-Type: application/json
```

**请求体**：
```json
{
    "asset_ids": ["asset-uuid-1", "asset-uuid-2"],
    "return_type": "to_inventory",
    "notes": "项目结束，归还资产"
}
```

**归还类型**：
- `to_inventory` - 归还到库存
- `transfer_project` - 转移到其他项目

**响应**：
```json
{
    "success": true,
    "message": "资产归还完成",
    "summary": {
        "total": 2,
        "returned": 2,
        "transferred": 0
    }
}
```

### 1.5 获取项目成本汇总

**请求**：
```http
GET /api/projects/{id}/cost-summary/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "project_code": "XM2025010001",
        "project_name": "AI平台研发项目",
        "total_asset_cost": "80000.00",
        "monthly_depreciation": "1333.33",
        "accumulated_depreciation": "888.89",
        "net_asset_value": "79111.11",
        "allocation_count": 12,
        "calculation_date": "2025-01-20"
    }
}
```

### 1.6 获取我的项目

**请求**：
```http
GET /api/projects/my-projects/
```

**响应**：同项目列表，只返回当前用户相关的项目。

---

## 2. 项目资产接口

### 2.1 项目资产列表

**请求**：
```http
GET /api/projects/assets/
```

**查询参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| project | uuid | 项目ID筛选 |
| asset | uuid | 资产ID筛选 |
| allocation_type | string | 分配类型筛选 |
| return_status | string | 归还状态筛选 |

**响应**：
```json
{
    "success": true,
    "data": {
        "count": 12,
        "results": [
            {
                "id": "allocation-uuid",
                "project": {
                    "id": "project-uuid",
                    "project_code": "XM2025010001",
                    "project_name": "AI平台研发项目"
                },
                "asset": {
                    "id": "asset-uuid",
                    "asset_code": "ZC001",
                    "asset_name": "GPU服务器",
                    "category_name": "电子设备"
                },
                "allocation_no": "FP2025010001",
                "allocation_date": "2025-01-15",
                "allocation_type": "temporary",
                "custodian": {
                    "id": "user-uuid",
                    "full_name": "李四"
                },
                "return_date": "2025-06-30",
                "return_status": "in_use",
                "allocation_cost": "50000.00",
                "monthly_depreciation": "833.33",
                "purpose": "用于AI模型训练",
                "days_in_use": 5,
                "is_overdue": false
            }
        ]
    }
}
```

### 2.2 转移资产

**请求**：
```http
POST /api/projects/assets/{id}/transfer/
Content-Type: application/json
```

**请求体**：
```json
{
    "target_project_id": "project-uuid-2",
    "reason": "项目调整，转移到其他项目"
}
```

**响应**：
```json
{
    "success": true,
    "message": "资产转移成功",
    "data": {
        "id": "new-allocation-uuid",
        "project": {
            "project_code": "XM2025010002",
            "project_name": "数据中台项目"
        },
        "allocation_date": "2025-01-20",
        "return_status": "in_use"
    }
}
```

---

## 3. 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| `PROJECT_NOT_ACTIVE` | 400 | 项目状态不正确 |
| `PROJECT_ALREADY_COMPLETED` | 400 | 项目已完成 |
| `ASSETS_NOT_RETURNED` | 400 | 存在未归还资产 |
| `ASSET_ALREADY_ALLOCATED` | 400 | 资产已分配 |
| `INVALID_TARGET_PROJECT` | 400 | 目标项目无效 |
| `NOT_PROJECT_MEMBER` | 403 | 不是项目成员 |
| `ASSET_NOT_FOUND_IN_PROJECT` | 404 | 资产不属于项目 |
