# Phase 2.4: 组织架构增强与数据权限 - API接口定义

## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

## 接口概览

### 部门管理API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/organizations/departments/` | 获取部门列表 |
| GET | `/api/organizations/departments/tree/` | 获取部门树 |
| GET | `/api/organizations/departments/{id}/` | 获取部门详情 |
| POST | `/api/organizations/departments/` | 创建部门 |
| PUT | `/api/organizations/departments/{id}/` | 更新部门 |
| DELETE | `/api/organizations/departments/{id}/` | 删除部门 |
| PUT | `/api/organizations/departments/{id}/leader/` | 设置部门负责人 |
| GET | `/api/organizations/departments/{id}/members/` | 获取部门成员 |
| GET | `/api/organizations/departments/{id}/descendants/` | 获取子部门（递归） |

### 用户部门关联API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/organizations/user-departments/` | 获取用户部门关联 |
| POST | `/api/organizations/user-departments/` | 添加用户部门关联 |
| PUT | `/api/organizations/user-departments/{id}/` | 更新用户部门关联 |
| DELETE | `/api/organizations/user-departments/{id}/` | 删除用户部门关联 |
| PUT | `/api/organizations/users/{id}/asset-department/` | 设置用户资产归属部门 |

### 资产操作API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/assets/transfers/` | 创建调拨单 |
| GET | `/api/assets/transfers/` | 获取调拨单列表 |
| GET | `/api/assets/transfers/{id}/` | 获取调拨单详情 |
| POST | `/api/assets/transfers/{id}/approve/` | 审批调拨单 |
| POST | `/api/assets/transfers/{id}/confirm/` | 确认接收调拨 |
| POST | `/api/assets/returns/` | 创建归还单 |
| GET | `/api/assets/returns/` | 获取归还单列表 |
| POST | `/api/assets/returns/{id}/confirm/` | 确认归还 |
| POST | `/api/assets/borrows/` | 创建借用单 |
| GET | `/api/assets/borrows/` | 获取借用单列表 |
| POST | `/api/assets/borrows/{id}/approve/` | 审批借用单 |
| POST | `/api/assets/borrows/{id}/return/` | 归还借用资产 |
| POST | `/api/assets/uses/` | 创建领用单 |
| GET | `/api/assets/uses/` | 获取领用单列表 |
| POST | `/api/assets/uses/{id}/approve/` | 审批领用单 |

### 数据权限API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/organizations/my-permissions/` | 获取我的权限范围 |
| GET | `/api/organizations/viewable-departments/` | 获取可查看的部门 |
| GET | `/api/organizations/viewable-users/` | 获取可查看的用户 |
| GET | `/api/organizations/subordinate-users/` | 获取下属用户列表 |
| GET | `/api/organizations/asset-statistics/` | 获取资产统计 |

---

## 1. 部门管理

### GET /api/organizations/departments/

获取部门列表（支持完整路径显示）

**请求参数：**

```json
{
  "keyword": "技术",     // 部门名称关键词（可选）
  "level": 1,            // 层级（可选）
  "parent_id": null,     // 父部门ID（可选）
  "include_inactive": false  // 是否包含已禁用（可选）
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "count": 10,
    "next": "https://api.example.com/api/organizations/departments/?page=2",
    "previous": null,
    "results": [
      {
        "id": "dept-uuid",
        "code": "TECH",
        "name": "技术部",
        "full_path": "总部/技术部",
        "full_path_name": "XX公司/总部/技术部",
        "level": 1,
        "parent_id": null,
        "order": 10,
        "leader_id": "user-uuid",
        "leader_name": "张三",
        "is_active": true,
        "member_count": 50,
        "asset_count": 120
      }
    ]
  }
}
```

### GET /api/organizations/departments/tree/

获取部门树结构

**响应数据：**
```json
{
  "success": true,
  "data": [
    {
      "id": "dept-uuid",
      "code": "HQ",
      "name": "总部",
      "full_path_name": "XX公司/总部",
      "level": 0,
      "leader_id": "user-uuid",
      "leader_name": "CEO",
      "children": [
        {
          "id": "dept-uuid-2",
          "code": "TECH",
          "name": "技术部",
          "full_path_name": "XX公司/总部/技术部",
          "level": 1,
          "children": [
            {
              "id": "dept-uuid-3",
              "code": "BACKEND",
              "name": "后端组",
              "full_path_name": "XX公司/总部/技术部/后端组",
              "level": 2,
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

### PUT /api/organizations/departments/{id}/leader/

设置部门负责人

**请求体：**

```json
{
  "leader_id": "user-uuid"
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "id": "dept-uuid",
    "leader_id": "user-uuid",
    "leader_name": "张三"
  }
}
```

### GET /api/organizations/departments/{id}/members/

获取部门成员（递归包含子部门）

**请求参数：**

```json
{
  "recursive": true,      // 是否递归获取子部门成员
  "include_leader": true  // 是否包含负责人信息
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "department_id": "dept-uuid",
    "department_name": "技术部",
    "members": [
      {
        "user_id": "user-uuid",
        "real_name": "张三",
        "avatar": "http://...",
        "position": "技术经理",
        "is_primary": true,
        "is_leader": true,
        "is_asset_department": true
      }
    ],
    "total_count": 50
  }
}
```

---

## 2. 用户部门关联

### GET /api/organizations/user-departments/

获取用户部门关联列表

**请求参数：**

```json
{
  "user_id": "user-uuid",   // 用户ID（可选，默认当前用户）
  "department_id": "dept-uuid"  // 部门ID（可选）
}
```

**响应数据：**
```json
{
  "success": true,
  "data": [
    {
      "id": "ud-uuid",
      "user_id": "user-uuid",
      "user_name": "张三",
      "department_id": "dept-uuid",
      "department_name": "技术部",
      "department_full_path": "总部/技术部",
      "is_primary": true,
      "is_asset_department": true,
      "is_leader": false,
      "position": "工程师"
    }
  ]
}
```

### POST /api/organizations/user-departments/

添加用户部门关联

**请求体：**

```json
{
  "user_id": "user-uuid",
  "department_id": "dept-uuid",
  "is_primary": false,
  "is_asset_department": false,
  "is_leader": false,
  "position": "工程师"
}
```

**响应数据：**
```json
{
  "success": true,
  "data": [
    {
      "id": "ud-uuid",
      "user_id": "user-uuid",
      "user_name": "张三",
      "department_id": "dept-uuid",
      "department_name": "技术部",
      "department_full_path": "总部/技术部",
      "is_primary": false,
      "is_asset_department": false,
      "is_leader": false,
      "position": "工程师"
    }
  ]
}
```

### PUT /api/organizations/users/{id}/asset-department/

设置用户资产归属部门

**请求体：**

```json
{
  "asset_department_id": "dept-uuid"
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "user_id": "user-uuid",
    "asset_department_id": "dept-uuid",
    "asset_department_name": "技术部",
    "asset_department_full_path": "总部/技术部"
  }
}
```

---

## 3. 资产调拨

### POST /api/assets/transfers/

创建资产调拨单

**请求体：**

```json
{
  "asset_ids": ["asset-1", "asset-2"],
  "to_department_id": "dept-uuid",
  "to_custodian_id": "user-uuid",
  "to_location_id": "loc-uuid",
  "reason": "项目需要"
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "id": "transfer-uuid",
    "transfer_code": "DB20240115001",
    "status": "pending",
    "items": [
      {
        "id": "item-uuid",
        "asset_id": "asset-1",
        "asset_code": "ZC001",
        "asset_name": "笔记本电脑"
      }
    ]
  }
}
```

### GET /api/assets/transfers/

获取调拨单列表

**请求参数：**

```json
{
  "status": "pending",      // 状态筛选（可选）
  "applicant_id": "user-uuid",  // 申请人（可选）
  "page": 1,
  "size": 20
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "count": 50,
    "next": "https://api.example.com/api/assets/transfers/?page=2",
    "previous": null,
    "results": [
      {
        "id": "transfer-uuid",
        "transfer_code": "DB20240115001",
        "from_department_name": "技术部",
        "from_custodian_name": "张三",
        "to_department_name": "销售部",
        "to_custodian_name": "李四",
        "status": "pending",
        "status_display": "待审批",
        "applicant_name": "王五",
        "applied_at": "2024-01-15T10:00:00Z",
        "item_count": 5
      }
    ]
  }
}
```

### POST /api/assets/transfers/{id}/approve/

审批调拨单

**请求体：**

```json
{
  "approved": true,
  "comment": "同意调拨"
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "id": "transfer-uuid",
    "status": "approved",
    "approver_name": "审批人",
    "approved_at": "2024-01-15T14:00:00Z"
  }
}
```

### POST /api/assets/transfers/{id}/confirm/

确认接收调拨资产

**请求体：**

```json
{
  "items": [
    {
      "item_id": "item-uuid",
      "confirmed": true,
      "actual_location_id": "loc-uuid",
      "actual_custodian_id": "user-uuid",
      "remark": ""
    }
  ]
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "confirmed_count": 5,
    "message": "确认成功"
  }
}
```

---

## 4. 资产归还

### POST /api/assets/returns/

创建资产归还单

**请求体：**

```json
{
  "asset_id": "asset-uuid",
  "return_location_id": "loc-uuid",
  "asset_status": "normal",
  "remark": "资产完好"
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "id": "return-uuid",
    "return_code": "GH20240115001",
    "status": "pending",
    "asset_code": "ZC001",
    "asset_name": "笔记本电脑"
  }
}
```

### GET /api/assets/returns/

获取归还单列表

**响应数据：**
```json
{
  "success": true,
  "data": {
    "count": 30,
    "next": "https://api.example.com/api/assets/returns/?page=2",
    "previous": null,
    "results": [
      {
        "id": "return-uuid",
        "return_code": "GH20240115001",
        "asset_code": "ZC001",
        "asset_name": "笔记本电脑",
        "returner_name": "张三",
        "returner_department": "技术部",
        "return_location": "库房A",
        "asset_status": "normal",
        "status": "pending",
        "returned_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### POST /api/assets/returns/{id}/confirm/

确认归还

**请求体：**

```json
{
  "confirmed": true
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "id": "return-uuid",
    "status": "confirmed",
    "confirmed_at": "2024-01-15T14:00:00Z"
  }
}
```

---

## 5. 资产借用

### POST /api/assets/borrows/

创建资产借用单

**请求体：**

```json
{
  "asset_id": "asset-uuid",
  "expected_return_date": "2024-02-15",
  "purpose": "项目演示使用"
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "id": "borrow-uuid",
    "borrow_code": "JY20240115001",
    "status": "pending",
    "asset_code": "ZC001",
    "asset_name": "投影仪"
  }
}
```

### GET /api/assets/borrows/

获取借用单列表

**响应数据：**
```json
{
  "success": true,
  "data": {
    "count": 20,
    "next": "https://api.example.com/api/assets/borrows/?page=2",
    "previous": null,
    "results": [
      {
        "id": "borrow-uuid",
        "borrow_code": "JY20240115001",
        "asset_code": "ZC001",
        "asset_name": "投影仪",
        "borrower_name": "张三",
        "borrower_department": "技术部",
        "borrow_date": "2024-01-15",
        "expected_return_date": "2024-02-15",
        "actual_return_date": null,
        "status": "borrowed",
        "purpose": "项目演示"
      }
    ]
  }
}
```

### POST /api/assets/borrows/{id}/return/

归还借用资产

**请求体：**

```json
{
  "remark": "完好归还"
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "id": "borrow-uuid",
    "status": "returned",
    "actual_return_date": "2024-02-10"
  }
}
```

---

## 6. 资产领用

### POST /api/assets/uses/

创建资产领用单

**请求体：**

```json
{
  "asset_id": "asset-uuid",
  "purpose": "日常工作使用"
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "id": "use-uuid",
    "use_code": "LY20240115001",
    "status": "pending",
    "asset_code": "ZC001",
    "asset_name": "办公电脑"
  }
}
```

### GET /api/assets/uses/

获取领用单列表

**响应数据：**
```json
{
  "success": true,
  "data": {
    "count": 40,
    "next": "https://api.example.com/api/assets/uses/?page=2",
    "previous": null,
    "results": [
      {
        "id": "use-uuid",
        "use_code": "LY20240115001",
        "asset_code": "ZC001",
        "asset_name": "办公电脑",
        "receiver_name": "张三",
        "receiver_department": "技术部",
        "use_date": "2024-01-15",
        "status": "completed",
        "purpose": "日常工作使用"
      }
    ]
  }
}
```

---

## 7. 数据权限

### GET /api/organizations/my-permissions/

获取我的权限范围

**响应数据：**
```json
{
  "success": true,
  "data": {
    "viewable_department_ids": ["dept-1", "dept-2"],
    "viewable_user_count": 50,
    "led_departments": [
      {
        "id": "dept-1",
        "name": "技术部",
        "full_path_name": "总部/技术部",
        "member_count": 30
      }
    ],
    "my_departments": [
      {
        "id": "dept-2",
        "name": "后端组",
        "is_primary": true,
        "is_asset_department": true
      }
    ]
  }
}
```

### GET /api/organizations/viewable-departments/

获取可查看的部门列表

**响应数据：**
```json
{
  "success": true,
  "data": [
    {
      "id": "dept-uuid",
      "name": "技术部",
      "full_path_name": "总部/技术部",
      "level": 1,
      "member_count": 50,
      "asset_count": 120,
      "is_led": true
    }
  ]
}
```

### GET /api/organizations/subordinate-users/

获取下属用户列表

**请求参数：**

```json
{
  "department_id": "dept-uuid",  // 部门ID（可选）
  "keyword": "张",               // 姓名关键词（可选）
  "page": 1,
  "size": 20
}
```

**响应数据：**
```json
{
  "success": true,
  "data": {
    "count": 30,
    "next": "https://api.example.com/api/organizations/subordinate-users/?page=2",
    "previous": null,
    "results": [
      {
        "id": "user-uuid",
        "real_name": "张三",
        "avatar": "http://...",
        "departments": [
          {
            "id": "dept-uuid",
            "name": "后端组",
            "full_path_name": "总部/技术部/后端组",
            "is_primary": true
          }
        ],
        "asset_count": 5,
        "position": "工程师"
      }
    ]
  }
}
```

### GET /api/organizations/asset-statistics/

获取资产统计（按部门）

**响应数据：**
```json
{
  "success": true,
  "data": {
    "total_assets": 500,
    "department_stats": [
      {
        "department_id": "dept-uuid",
        "department_name": "技术部",
        "full_path_name": "总部/技术部",
        "total": 120,
        "in_use": 100,
        "idle": 15,
        "in_transfer": 5
      }
    ]
  }
}
```

---

## Serializers

```python
# apps/organizations/serializers/department.py

from rest_framework import serializers
from apps.organizations.models import Department, UserDepartment


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""

    leader_name = serializers.CharField(source='leader.real_name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'code', 'name', 'full_path', 'full_path_name',
            'level', 'order', 'parent', 'parent_name',
            'leader', 'leader_name',
            'is_active', 'member_count'
        ]

    def get_member_count(self, obj):
        return UserDepartment.objects.filter(department=obj).count()


class DepartmentTreeSerializer(serializers.ModelSerializer):
    """部门树序列化器"""

    leader_name = serializers.CharField(source='leader.real_name', read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'code', 'name', 'full_path', 'full_path_name',
            'level', 'leader', 'leader_name', 'children'
        ]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('order')
        return DepartmentTreeSerializer(children, many=True).data


class UserDepartmentSerializer(serializers.ModelSerializer):
    """用户部门关联序列化器"""

    user_name = serializers.CharField(source='user.real_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_full_path = serializers.CharField(source='department.full_path', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = UserDepartment
        fields = [
            'id', 'user', 'user_name', 'user_avatar',
            'department', 'department_name', 'department_full_path',
            'is_primary', 'is_asset_department', 'is_leader', 'position'
        ]


# apps/assets/serializers/operations.py

class AssetTransferSerializer(serializers.ModelSerializer):
    """资产调拨序列化器"""

    from_department_name = serializers.CharField(source='from_department.full_path_name', read_only=True)
    from_custodian_name = serializers.CharField(source='from_custodian.real_name', read_only=True)
    to_department_name = serializers.CharField(source='to_department.full_path_name', read_only=True)
    to_custodian_name = serializers.CharField(source='to_custodian.real_name', read_only=True)
    applicant_name = serializers.CharField(source='applicant.real_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AssetTransfer
        fields = [
            'id', 'transfer_code', 'status', 'status_display',
            'from_department', 'from_department_name',
            'from_custodian', 'from_custodian_name',
            'to_department', 'to_department_name',
            'to_custodian', 'to_custodian_name',
            'applicant', 'applicant_name',
            'reason', 'applied_at', 'approved_at'
        ]


class AssetTransferItemSerializer(serializers.ModelSerializer):
    """调拨明细序列化器"""

    asset_code = serializers.CharField(source='asset.code', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = AssetTransferItem
        fields = [
            'id', 'asset', 'asset_code', 'asset_name',
            'status_before', 'confirmed', 'confirmed_at', 'remark'
        ]


class AssetReturnSerializer(serializers.ModelSerializer):
    """资产归还序列化器"""

    asset_code = serializers.CharField(source='asset.code', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    returner_name = serializers.CharField(source='returner.real_name', read_only=True)
    returner_department = serializers.CharField(source='returner_department.full_path_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AssetReturn
        fields = [
            'id', 'return_code', 'asset', 'asset_code', 'asset_name',
            'returner', 'returner_name', 'returner_department',
            'return_location', 'asset_status', 'status', 'status_display',
            'returned_at', 'remark'
        ]


class AssetBorrowSerializer(serializers.ModelSerializer):
    """资产借用序列化器"""

    asset_code = serializers.CharField(source='asset.code', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    borrower_name = serializers.CharField(source='borrower.real_name', read_only=True)
    borrower_department = serializers.CharField(source='borrower_department.full_path_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AssetBorrow
        fields = [
            'id', 'borrow_code', 'asset', 'asset_code', 'asset_name',
            'borrower', 'borrower_name', 'borrower_department',
            'borrow_date', 'expected_return_date', 'actual_return_date',
            'status', 'status_display', 'purpose', 'remark'
        ]


class AssetUseSerializer(serializers.ModelSerializer):
    """资产领用序列化器"""

    asset_code = serializers.CharField(source='asset.code', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.real_name', read_only=True)
    receiver_department = serializers.CharField(source='receiver_department.full_path_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AssetUse
        fields = [
            'id', 'use_code', 'asset', 'asset_code', 'asset_name',
            'receiver', 'receiver_name', 'receiver_department',
            'receiver_location', 'use_date', 'status', 'status_display',
            'purpose', 'remark'
        ]
```

---

## 后续任务

所有Phase已完成！
