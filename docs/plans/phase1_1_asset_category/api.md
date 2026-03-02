# Phase 1.1: 资产分类体系 - API接口定义

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
| GET | `/api/assets/categories/tree/` | 获取分类树 |
| GET | `/api/assets/categories/` | 获取分类列表 |
| GET | `/api/assets/categories/{id}/` | 获取分类详情 |
| POST | `/api/assets/categories/` | 创建分类 |
| PUT | `/api/assets/categories/{id}/` | 更新分类 |
| DELETE | `/api/assets/categories/{id}/` | 删除分类 |
| POST | `/api/assets/categories/{id}/add_child/` | 添加子分类 |
| GET | `/api/assets/categories/custom/` | 获取自定义分类 |
| POST | `/api/assets/categories/custom/` | 创建自定义分类 |

---

## 1. 获取分类树

**请求**
```
GET /api/assets/categories/tree/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "id": 1,
    "code": "2001",
    "name": "计算机设备",
    "full_name": "计算机设备",
    "level": 0,
    "is_custom": false,
    "depreciation_method": "straight_line",
    "default_useful_life": 60,
    "children": [
    {
      "id": 2,
      "code": "200101",
      "name": "台式机",
      "full_name": "计算机设备 > 台式机",
      "level": 1,
      "is_custom": false,
      "depreciation_method": "straight_line",
      "default_useful_life": 60,
      "children": []
    }
  ]
  }
}
```

---

## 2. 获取分类列表

**请求**
```
GET /api/assets/categories/?is_custom=true&parent_id=null
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| is_custom | boolean | 是否自定义分类 |
| parent_id | integer | 父分类ID |
| search | string | 搜索关键词 |

**响应**
```json
{
  "success": true,
  "data": {
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "code": "2001",
        "name": "计算机设备",
        "parent_id": null,
        "is_custom": false,
        "depreciation_method": "straight_line",
        "default_useful_life": 60,
        "residual_rate": 5.00,
        "sort_order": 0,
        "is_active": true
      }
    ]
  }
}
```

---

## 3. 创建分类

**请求**
```
POST /api/assets/categories/
Content-Type: application/json

{
  "code": "200105",
  "name": "工作站",
  "parent_id": 1,
  "depreciation_method": "straight_line",
  "default_useful_life": 60,
  "residual_rate": 5.00,
  "sort_order": 0
}
```

**响应**
```
HTTP 201 Created

{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 10,
    "code": "200105",
    "name": "工作站",
    "parent_id": 1,
    "is_custom": true,
    "depreciation_method": "straight_line",
    "default_useful_life": 60,
    "residual_rate": 5.00,
    "sort_order": 0,
    "is_active": true
  }
}
```

**错误响应**
```
HTTP 400 Bad Request

{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "分类编码已存在",
    "details": {
      "field": "code",
      "value": "2001"
    }
  }
}
```

---

## 4. 更新分类

**请求**
```
PUT /api/assets/categories/{id}/
Content-Type: application/json

{
  "name": "工作站（更新）",
  "default_useful_life": 72
}
```

**响应**
```
HTTP 200 OK

{
  "success": true,
  "message": "更新成功",
  "data": {
    "id": 10,
    "code": "200105",
    "name": "工作站（更新）",
    "default_useful_life": 72
  }
}
```

---

## 5. 删除分类

**请求**
```
DELETE /api/assets/categories/{id}/
```

**响应**
```
HTTP 200 OK

{
  "success": true,
  "message": "删除成功"
}
```

**错误响应 - 分类不存在**
```
HTTP 404 Not Found

{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "分类不存在"
  }
}
```

**错误响应 - 有子分类或资产**
```
HTTP 400 Bad Request

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "该分类下有子分类或资产，无法删除",
    "details": {
      "reason": "has_children_or_assets"
    }
  }
}
```

---

## 6. 添加子分类

**请求**
```
POST /api/assets/categories/{parent_id}/add_child/
Content-Type: application/json

{
  "code": "200106",
  "name": "服务器",
  "depreciation_method": "straight_line",
  "default_useful_life": 60
}
```

**响应**
```
HTTP 201 Created

{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 11,
    "code": "200106",
    "name": "服务器",
    "parent_id": 1
  }
}
```

---

## 错误码

本模块使用GZEAMS标准错误码，自定义错误情况通过 `details` 字段说明。

| 标准错误码 | HTTP状态 | 说明 | 使用场景 |
|-----------|----------|------|----------|
| VALIDATION_ERROR | 400 | 请求数据验证失败 | 编码重复、父分类无效、有子分类、有资产 |
| UNAUTHORIZED | 401 | 未授权访问 | 未登录、token无效 |
| PERMISSION_DENIED | 403 | 权限不足 | 无权限操作分类、编辑系统分类 |
| NOT_FOUND | 404 | 资源不存在 | 分类不存在 |
| CONFLICT | 409 | 资源冲突 | 编码已存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 | 跨组织访问 |

**自定义业务场景通过details说明**：
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求数据验证失败",
    "details": {
      "field": "code",
      "reason": "duplicate_code",
      "message": "分类编码已存在"
    }
  }
}
```

---

## 数据字典

### 折旧方法 (depreciation_method)

| 值 | 说明 |
|----|------|
| straight_line | 直线法 |
| double_declining | 双倍余额递减法 |
| sum_of_years | 年数总和法 |
| no_depreciation | 不计提折旧 |

### 分类状态

| 字段 | 说明 |
|------|------|
| is_custom | false=系统预置分类，true=用户自定义分类 |
| is_active | true=启用，false=停用 |
