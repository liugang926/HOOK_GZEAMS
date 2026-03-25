# Phase 2.4: 组织架构增强 - 快速参考指南

**项目**: GZEAMS - Hook固定资产低代码平台
**阶段**: Phase 2.4 组织架构增强与数据权限
**日期**: 2026-01-16

---

## 快速开始

### 1. 已实现的功能

#### 1.1 数据模型 ✅

**Department模型增强**:
- 层级结构 (level, path, full_path, full_path_name)
- 部门负责人 (leader字段)
- 第三方平台ID (wework_dept_id, dingtalk_dept_id, feishu_dept_id)
- 自动路径维护

**UserDepartment新模型**:
- 一人多部门支持
- 主部门标识 (is_primary)
- 资产部门标识 (is_asset_department)
- 职位和角色 (position, is_leader)

#### 1.2 序列化器 ✅

- DepartmentSerializer (基础序列化)
- DepartmentTreeSerializer (递归子部门)
- UserDepartmentSerializer (用户部门关联)
- UserDepartmentDetailSerializer (详细信息)

#### 1.3 过滤器 ✅

- DepartmentFilter (名称、编码、路径、负责人等)
- UserDepartmentFilter (用户、部门、职位等)

#### 1.4 服务层 ✅

**OrgDataPermissionService**:
```python
from apps.organizations.services.permission_service import OrgDataPermissionService

perm_service = OrgDataPermissionService(user)

# 获取可查看的部门
dept_ids = perm_service.get_viewable_department_ids()

# 检查资产权限
can_view = perm_service.can_view_asset(asset)
can_manage = perm_service.can_manage_asset(asset)

# 获取部门
primary_dept = perm_service.get_primary_department()
asset_dept = perm_service.get_asset_department()
```

---

## 2. 使用示例

### 2.1 创建部门

```python
from apps.organizations.models import Department

# 创建根部门
root = Department.objects.create(
    organization_id=org_id,
    code='HQ',
    name='总部',
    leader_id=user_id
)

# 创建子部门（自动设置层级和路径）
tech = Department.objects.create(
    organization_id=org_id,
    code='TECH',
    name='技术部',
    parent=root
)

# tech.full_path_name 自动为 "总部/技术部"
# tech.level 自动为 1
# tech.path 自动为 "/HQ/TECH"
```

### 2.2 用户多部门关联

```python
from apps.organizations.models import UserDepartment

# 主部门
UserDepartment.objects.create(
    user_id=user_id,
    department_id=dept1_id,
    organization_id=org_id,
    is_primary=True,  # 主部门
    position='技术经理'
)

# 兼职部门
UserDepartment.objects.create(
    user_id=user_id,
    department_id=dept2_id,
    organization_id=org_id,
    is_primary=False,  # 非主部门
    position='产品顾问'
)

# 用户只能有一个主部门，设置新的主部门会自动取消旧的主部门标识
```

### 2.3 数据权限查询

```python
from apps.organizations.services.permission_service import OrgDataPermissionService

# 初始化权限服务
perm_service = OrgDataPermissionService(current_user)

# 获取可查看的部门ID列表
dept_ids = perm_service.get_viewable_department_ids()
# 包括: 用户所属部门、用户负责的部门及其子部门

# 获取可查看的用户ID列表
user_ids = perm_service.get_viewable_user_ids()
# 包括: 可查看部门中的所有用户 + 用户自己

# 检查是否可查看资产
if perm_service.can_view_asset(asset):
    # 可以查看
    pass

# 检查是否可管理资产
if perm_service.can_manage_asset(asset):
    # 可以管理
    pass

# 获取用户主部门
primary_dept = perm_service.get_primary_department()
if primary_dept:
    print(f"主部门: {primary_dept.full_path_name}")

# 获取用户资产部门
asset_dept = perm_service.get_asset_department()
if asset_dept:
    print(f"资产部门: {asset_dept.full_path_name}")
```

### 2.4 查询部门成员

```python
from apps.organizations.models import UserDepartment

# 获取部门所有成员
members = UserDepartment.objects.filter(
    department_id=dept_id
).select_related('user')

for member in members:
    print(f"{member.user.real_name} - {member.position}")
    if member.is_leader:
        print("  [部门负责人]")
    if member.is_primary:
        print("  [主部门]")
```

---

## 3. 数据库迁移

### 3.1 生成迁移文件

```bash
cd backend
python manage.py makemigrations organizations
```

**预期输出**:
- 新增字段: level, path, full_path, full_path_name
- 修改字段: manager -> leader, sort_order -> order
- 新增模型: UserDepartment

### 3.2 执行迁移

```bash
python manage.py migrate organizations
```

### 3.3 验证迁移

```bash
python manage.py showmigrations organizations
```

---

## 4. API接口示例

### 4.1 创建部门

**请求**:
```http
POST /api/organizations/departments/
Content-Type: application/json

{
    "organization_id": "uuid-here",
    "code": "TECH",
    "name": "技术部",
    "parent_id": "parent-uuid",
    "leader_id": "leader-uuid",
    "is_active": true,
    "order": 1
}
```

**响应**:
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "new-dept-uuid",
        "code": "TECH",
        "name": "技术部",
        "level": 1,
        "path": "/HQ/TECH",
        "full_path_name": "总部/技术部",
        "leader_name": "张三",
        "member_count": 0,
        "created_at": "2026-01-16T10:30:00Z"
    }
}
```

### 4.2 获取部门树

**请求**:
```http
GET /api/organizations/departments/tree/?include_inactive=true
```

**响应**:
```json
{
    "success": true,
    "data": {
        "tree": [
            {
                "id": "dept-uuid",
                "code": "HQ",
                "name": "总部",
                "level": 0,
                "full_path_name": "总部",
                "leader_name": "李总",
                "member_count": 100,
                "children": [
                    {
                        "id": "tech-uuid",
                        "code": "TECH",
                        "name": "技术部",
                        "level": 1,
                        "full_path_name": "总部/技术部",
                        "children": []
                    }
                ]
            }
        ]
    }
}
```

### 4.3 创建用户部门关联

**请求**:
```http
POST /api/organizations/user-departments/
Content-Type: application/json

{
    "user_id": "user-uuid",
    "department_id": "dept-uuid",
    "organization_id": "org-uuid",
    "is_primary": true,
    "is_asset_department": true,
    "position": "技术经理",
    "is_leader": true
}
```

---

## 5. 关键概念

### 5.1 部门层级

- **level**: 层级深度（从0开始）
- **path**: 编码路径（如 "/HQ/TECH/BACKEND"）
- **full_path_name**: 名称路径（如 "总部/技术部/后端组"）

### 5.2 主部门 vs 资产部门

- **主部门 (is_primary)**: 用于资产归属，每个用户在每个组织只有一个
- **资产部门 (is_asset_department)**: 资产实际所在部门，可以有多个

### 5.3 数据权限

**可查看范围**:
- 用户所属的部门
- 用户负责的部门（及其子部门）

**可管理范围**:
- 用户是保管人的资产
- 用户是负责人的部门中的资产

---

## 6. 常见问题

### Q1: 如何获取部门的所有后代？

```python
dept = Department.objects.get(id=dept_id)
descendant_ids = dept.get_descendant_ids()
# 返回所有后代部门的ID列表（包括自己）
```

### Q2: 如何设置部门负责人？

```python
dept = Department.objects.get(id=dept_id)
dept.leader_id = user_id
dept.save()  # 自动更新
```

### Q3: 如何移动部门到新的父部门？

```python
dept = Department.objects.get(id=dept_id)
dept.parent_id = new_parent_id
dept.save()  # 自动更新层级、路径，并递归更新子部门
```

### Q4: 如何确保用户只有一个主部门？

```python
# UserDepartment的save方法已自动处理
# 设置新的主部门会自动取消旧的主部门标识
UserDepartment.objects.create(
    user_id=user_id,
    department_id=new_dept_id,
    is_primary=True  # 自动取消其他主部门
)
```

### Q5: 如何检查用户是否为部门负责人？

```python
from apps.organizations.services.permission_service import OrgDataPermissionService

perm_service = OrgDataPermissionService(user)
is_leader = perm_service.is_department_leader(department)
```

---

## 7. 性能优化建议

### 7.1 查询优化

```python
# ❌ 不好：N+1查询
depts = Department.objects.all()
for dept in depts:
    print(dept.leader.username)  # 每次都查询

# ✅ 好：使用select_related
depts = Department.objects.select_related('leader').all()
for dept in depts:
    print(dept.leader.username)  # 无额外查询
```

### 7.2 缓存建议

```python
# 缓存部门树（高频读取，低频修改）
from django.core.cache import cache

def get_department_tree(org_id):
    cache_key = f'dept_tree_{org_id}'
    tree = cache.get(cache_key)
    if not tree:
        tree = Department.get_full_path_tree(org_id)
        cache.set(cache_key, tree, 3600)  # 缓存1小时
    return tree
```

---

## 8. 测试代码示例

### 8.1 模型测试

```python
from django.test import TestCase
from apps.organizations.models import Department, UserDepartment

class DepartmentModelTest(TestCase):
    def test_path_generation(self):
        """测试路径自动生成"""
        root = Department.objects.create(
            organization_id=self.org_id,
            code='HQ',
            name='总部'
        )
        child = Department.objects.create(
            organization_id=self.org_id,
            code='TECH',
            name='技术部',
            parent=root
        )

        self.assertEqual(child.level, 1)
        self.assertEqual(child.path, '/HQ/TECH')
        self.assertEqual(child.full_path_name, '总部/技术部')

    def test_primary_department_unique(self):
        """测试主部门唯一性"""
        UserDepartment.objects.create(
            user_id=self.user_id,
            department_id=self.dept1_id,
            is_primary=True
        )

        UserDepartment.objects.create(
            user_id=self.user_id,
            department_id=self.dept2_id,
            is_primary=True  # 应该自动取消dept1的主部门标识
        )

        # 验证只有一个主部门
        primary_count = UserDepartment.objects.filter(
            user_id=self.user_id,
            is_primary=True
        ).count()
        self.assertEqual(primary_count, 1)
```

### 8.2 服务测试

```python
from django.test import TestCase
from apps.organizations.services.permission_service import OrgDataPermissionService

class PermissionServiceTest(TestCase):
    def test_get_viewable_departments(self):
        """测试获取可查看部门"""
        perm_service = OrgDataPermissionService(self.user)
        dept_ids = perm_service.get_viewable_department_ids()

        # 应该包含用户所属部门
        self.assertIn(self.user_dept_id, dept_ids)

        # 如果用户是部门负责人，应该包含子部门
        if self.user.is_leader:
            self.assertIn(self.child_dept_id, dept_ids)
```

---

## 9. 下一步工作

### 9.1 待实现功能

- [ ] ViewSet实现 (DepartmentViewSet, UserDepartmentViewSet)
- [ ] URL路由配置
- [ ] 前端API封装
- [ ] 前端组件（部门选择器、保管人选择器）
- [ ] 前端页面（部门列表、用户部门关联）
- [ ] 测试用例编写
- [ ] 文档完善

### 9.2 优先级

**高优先级**:
1. ViewSet和URL路由（核心功能）
2. 前端API封装（前端依赖）
3. 前端组件（用户体验）

**中优先级**:
4. 前端页面（完整功能）
5. 测试用例（质量保证）

**低优先级**:
6. 文档完善（维护性）

---

## 10. 相关文档

- **完整实现报告**: `PHASE2_4_FINAL_IMPLEMENTATION_REPORT.md`
- **文件清单**: `PHASE2_4_FILES_MANIFEST.md`
- **PRD文档**: `docs/plans/phase2_4_org_enhancement/backend.md`
- **前端PRD**: `docs/plans/phase2_4_org_enhancement/frontend.md`

---

**快速参考生成时间**: 2026-01-16
**维护人**: GZEAMS开发团队
