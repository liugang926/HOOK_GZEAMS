# Phase 7.2: 资产项目管理 - 后端实现

## 1. 功能概述

### 1.1 业务场景

实现资产与项目的关联管理，支持项目资产分配、使用追踪、成本核算和回收管理。

| 业务类型 | 场景 | 核心价值 |
|---------|------|----------|
| **项目立项** | 创建项目，定义项目基本信息和成员 | 建立资产使用主体 |
| **资产分配** | 将资产分配给项目使用 | 明确资产使用责任 |
| **项目资产视图** | 按项目查看资产清单和使用情况 | 资产使用透明化 |
| **成本核算** | 统计项目占用的资产成本和折旧分摊 | 项目成本准确化 |
| **项目结项** | 项目结束后资产回收处理 | 资产及时回收 |

### 1.2 用户角色与权限

| 角色 | 权限 |
|------|------|
| **项目经理** | 创建项目、分配/收回资产、发起结项、查看项目信息 |
| **资产管理员** | 审批资产分配、查看所有项目、跨项目调配 |
| **部门负责人** | 审批项目立项、审批项目结项 |
| **财务人员** | 查看项目成本统计 |
| **项目成员** | 查看所在项目资产 |

---

## 2. 公共模型引用声明

### 2.1 后端公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作、审计字段设置 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤、状态过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法、组织隔离、分页查询 |

---

## 3. 数据模型设计

### 3.1 AssetProject（项目定义）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **基础信息** |
| project_code | string | max_length=50, unique, db_index | 项目编号 (XM+YYYYMM+序号) |
| project_name | string | max_length=200 | 项目名称 |
| project_alias | string | max_length=100, blank | 项目简称 |
| **关联** |
| project_manager | FK(User) | PROTECT, related_name='managed_projects' | 项目经理 |
| department | FK(Department) | PROTECT, related_name='department_projects' | 所属部门 |
| **项目属性** |
| project_type | string | max_length=20, choices | 项目类型: research/development/infrastructure/other |
| status | string | max_length=20, choices | 状态: planning/active/suspended/completed/cancelled |
| **时间** |
| start_date | date | - | 计划开始日期 |
| end_date | date | null=True | 计划结束日期 |
| actual_start_date | date | null=True | 实际开始日期 |
| actual_end_date | date | null=True | 实际结束日期 |
| **财务** |
| planned_budget | DecimalField | max_digits=14, decimal_places=2, null=True | 计划预算 |
| actual_cost | DecimalField | max_digits=14, decimal_places=2, default=0 | 实际成本 |
| asset_cost | DecimalField | max_digits=14, decimal_places=2, default=0 | 资产占用成本 |
| **描述** |
| description | TextField | blank=True | 项目描述 |
| technical_requirements | TextField | blank=True | 技术要求 |
| **统计** |
| total_assets | int | default=0 | 分配资产总数 |
| active_assets | int | default=0 | 在用资产数 |
| completed_milestones | int | default=0 | 已完成里程碑数 |
| total_milestones | int | default=0 | 总里程碑数 |

**状态说明**：

```
planning (筹备中) → active (进行中) → suspended (暂停) → completed (已完成)
                ↓                                  ↓
            cancelled (已取消)                  cancelled (已取消)
```

### 3.2 ProjectAsset（资产分配）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| project | FK(AssetProject) | PROTECT, related_name='project_assets' | 项目 |
| asset | FK(Asset) | PROTECT, related_name='project_allocations' | 资产 |
| **分配信息** |
| allocation_no | string | max_length=50, unique, db_index | 分配单号 (FP+YYYYMM+序号) |
| allocation_date | date | - | 分配日期 |
| allocation_type | string | max_length=20, choices | 分配类型: permanent/temporary/shared |
| **人员** |
| allocated_by | FK(User) | PROTECT, related_name='allocated_assets' | 分配人 |
| custodian | FK(User) | SET_NULL, null=True, related_name='+' | 保管人 |
| **归还信息** |
| return_date | date | null=True | 计划归还日期 |
| actual_return_date | date | null=True | 实际归还日期 |
| return_status | string | max_length=20, choices | 归还状态: in_use/returned/transferred |
| **成本信息** |
| allocation_cost | DecimalField | max_digits=14, decimal_places=2 | 分配时资产价值 |
| depreciation_rate | DecimalField | max_digits=5, decimal_places=4 | 折旧分摊比例 |
| monthly_depreciation | DecimalField | max_digits=12, decimal_places=2 | 月折旧额 |
| **用途** |
| purpose | TextField | blank=True | 用途说明 |
| usage_location | string | max_length=200, blank=True | 使用地点 |
| **资产快照** |
| asset_snapshot | JSONField | default=dict | 资产快照（记录分配时状态） |

**资产快照结构**：

```json
{
  "asset_code": "ZC001",
  "asset_name": "MacBook Pro",
  "category_name": "电子设备",
  "original_cost": "12000.00",
  "purchase_date": "2024-01-01",
  "status": "idle"
}
```

### 3.3 ProjectMember（项目成员）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| project | FK(AssetProject) | CASCADE, related_name='members' | 项目 |
| user | FK(User) | PROTECT, related_name='project_memberships' | 用户 |
| **角色** |
| role | string | max_length=20, choices | 角色: manager/member/observer |
| is_primary | boolean | default=False | 是否为主要成员 |
| **时间** |
| join_date | date | - | 加入日期 |
| leave_date | date | null=True | 离开日期 |
| **状态** |
| is_active | boolean | default=True | 是否在职 |
| **职责** |
| responsibilities | TextField | blank=True | 职责描述 |
| **权限** |
| can_allocate_asset | boolean | default=False | 是否可分配资产 |
| can_view_cost | boolean | default=False | 是否可查看成本 |

**复合唯一索引**：`(project, user)`

### 3.4 ProjectCost（项目成本统计，通过视图/聚合实现）

| 字段 | 说明 |
|------|------|
| project_id | 项目ID |
| total_asset_cost | 资产总成本 |
| monthly_depreciation | 月折旧总额 |
| accumulated_depreciation | 累计折旧 |
| net_asset_value | 资产净值 |
| allocation_count | 分配资产数量 |
| calculation_date | 计算日期 |

---

## 4. 序列化器设计

### 4.1 AssetProjectSerializer

```python
from apps.common.serializers.base import BaseModelSerializer
from apps.accounts.serializers import UserSerializer
from apps.organizations.serializers import DepartmentSerializer

class AssetProjectSerializer(BaseModelSerializer):
    """项目序列化器"""

    project_manager_detail = UserSerializer(source='project_manager', read_only=True)
    department_detail = DepartmentSerializer(source='department', read_only=True)
    asset_count = serializers.SerializerMethodField()
    active_asset_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    days_elapsed = serializers.IntegerField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetProject
        fields = BaseModelSerializer.Meta.fields + [
            'project_code', 'project_name', 'project_alias',
            'project_manager', 'project_manager_detail',
            'department', 'department_detail',
            'project_type', 'status',
            'start_date', 'end_date',
            'actual_start_date', 'actual_end_date',
            'planned_budget', 'actual_cost', 'asset_cost',
            'description', 'technical_requirements',
            'total_assets', 'active_assets',
            'completed_milestones', 'total_milestones',
            'asset_count', 'active_asset_count', 'member_count',
            'progress', 'days_elapsed', 'days_remaining',
        ]

    def get_asset_count(self, obj):
        """获取资产总数"""
        return obj.project_assets.count()

    def get_active_asset_count(self, obj):
        """获取在用资产数"""
        return obj.project_assets.filter(return_status='in_use').count()

    def get_member_count(self, obj):
        """获取成员数"""
        return obj.members.filter(is_active=True).count()

    def get_progress(self, obj):
        """获取项目进度"""
        if obj.total_milestones == 0:
            return 0
        return round(obj.completed_milestones / obj.total_milestones * 100, 2)
```

### 4.2 ProjectAssetSerializer

```python
class ProjectAssetSerializer(BaseModelSerializer):
    """项目资产序列化器"""

    project_name = serializers.CharField(source='project.project_name', read_only=True)
    project_code = serializers.CharField(source='project.project_code', read_only=True)
    asset_detail = serializers.SerializerMethodField()
    allocated_by_detail = UserSerializer(source='allocated_by', read_only=True)
    custodian_detail = UserSerializer(source='custodian', read_only=True)
    allocation_type_display = serializers.CharField(source='get_allocation_type_display', read_only=True)
    return_status_display = serializers.CharField(source='get_return_status_display', read_only=True)
    days_in_use = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ProjectAsset
        fields = BaseModelSerializer.Meta.fields + [
            'project', 'project_name', 'project_code',
            'asset', 'asset_detail',
            'allocation_no', 'allocation_date', 'allocation_type', 'allocation_type_display',
            'allocated_by', 'allocated_by_detail',
            'custodian', 'custodian_detail',
            'return_date', 'actual_return_date',
            'return_status', 'return_status_display',
            'allocation_cost', 'depreciation_rate', 'monthly_depreciation',
            'purpose', 'usage_location',
            'asset_snapshot',
            'days_in_use', 'is_overdue',
        ]

    def get_asset_detail(self, obj):
        """获取资产详情"""
        return {
            'id': obj.asset.id,
            'asset_code': obj.asset.asset_code,
            'asset_name': obj.asset.asset_name,
            'category_name': obj.asset.category.name if obj.asset.category else '',
            'specification': obj.asset.specification,
            'original_cost': str(obj.asset.purchase_price) if obj.asset.purchase_price else '0.00',
        }

class ProjectAssetCreateSerializer(serializers.Serializer):
    """资产分配创建序列化器"""

    project_id = serializers.UUIDField(required=True)
    assets = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    allocation_type = serializers.ChoiceField(
        choices=['permanent', 'temporary', 'shared'],
        default='temporary'
    )
    allocation_date = serializers.DateField(required=False)
    return_date = serializers.DateField(required=False)
    purpose = serializers.CharField(max_length=500, required=False, allow_blank=True)
    usage_location = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_project_id(self, value):
        """验证项目"""
        project = AssetProject.objects.filter(id=value).first()
        if not project:
            raise serializers.ValidationError("项目不存在")
        if project.status != 'active':
            raise serializers.ValidationError("只有进行中的项目才能分配资产")
        return value

    def validate_assets(self, value):
        """验证资产列表"""
        if not value:
            raise serializers.ValidationError("请至少选择一项资产")
        return value
```

### 4.3 ProjectMemberSerializer

```python
class ProjectMemberSerializer(BaseModelSerializer):
    """项目成员序列化器"""

    user_detail = UserSerializer(source='user', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    days_in_project = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ProjectMember
        fields = BaseModelSerializer.Meta.fields + [
            'project', 'user', 'user_detail',
            'role', 'role_display', 'is_primary',
            'join_date', 'leave_date',
            'is_active',
            'responsibilities',
            'can_allocate_asset', 'can_view_cost',
            'days_in_project',
        ]
```

---

## 5. ViewSet 设计

### 5.1 AssetProjectViewSet

```python
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.projects.services import AssetProjectService

class AssetProjectViewSet(BaseModelViewSetWithBatch):
    """项目ViewSet"""

    queryset = AssetProject.objects.select_related(
        'project_manager', 'department'
    ).prefetch_related('members', 'project_assets')
    serializer_class = AssetProjectSerializer
    filterset_class = AssetProjectFilter
    service = AssetProjectService()

    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        user = self.request.user

        # 项目经理只看自己管理的项目
        if not user.is_admin and not user.is_asset_admin:
            queryset = queryset.filter(
                models.Q(project_manager=user) |
                models.Q(members__user=user, members__is_active=True)
            ).distinct()

        return queryset

    @action(detail=True, methods=['get'])
    def assets(self, request, pk=None):
        """获取项目资产"""
        project = self.get_object()
        assets = project.project_assets.select_related('asset', 'custodian').filter(
            return_status='in_use'
        )

        page = self.paginate_queryset(assets)
        if page is not None:
            serializer = ProjectAssetSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProjectAssetSerializer(assets, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """获取项目成员"""
        project = self.get_object()
        members = project.members.filter(is_active=True).select_related('user')

        page = self.paginate_queryset(members)
        if page is not None:
            serializer = ProjectMemberSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProjectMemberSerializer(members, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=True, methods=['get'])
    def cost_summary(self, request, pk=None):
        """获取项目成本汇总"""
        project = self.get_object()
        cost_summary = self.service.calculate_cost_summary(project)

        return Response({
            'success': True,
            'data': cost_summary
        })

    @action(detail=True, methods=['post'])
    def allocate_assets(self, request, pk=None):
        """分配资产"""
        project = self.get_object()

        if project.status != 'active':
            return Response({
                'success': False,
                'error': {
                    'code': 'PROJECT_NOT_ACTIVE',
                    'message': '只有进行中的项目才能分配资产'
                }
            }, status=400)

        serializer = ProjectAssetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        allocations = self.service.allocate_assets(
            project=project,
            assets_data=serializer.validated_data['assets'],
            allocation_type=serializer.validated_data.get('allocation_type', 'temporary'),
            allocation_date=serializer.validated_data.get('allocation_date'),
            return_date=serializer.validated_data.get('return_date'),
            purpose=serializer.validated_data.get('purpose', ''),
            usage_location=serializer.validated_data.get('usage_location', ''),
            allocated_by=request.user
        )

        return Response({
            'success': True,
            'message': f'成功分配{len(allocations)}项资产',
            'data': ProjectAssetSerializer(allocations, many=True).data
        })

    @action(detail=True, methods=['post'])
    def return_assets(self, request, pk=None):
        """归还资产"""
        project = self.get_object()

        asset_ids = request.data.get('asset_ids', [])
        return_type = request.data.get('return_type', 'to_inventory')  # to_inventory/transfer_project
        target_project_id = request.data.get('target_project_id')
        notes = request.data.get('notes', '')

        if not asset_ids:
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': '请选择要归还的资产'}
            }, status=400)

        results = self.service.return_assets(
            project=project,
            asset_ids=asset_ids,
            return_type=return_type,
            target_project_id=target_project_id,
            notes=notes,
            operator=request.user
        )

        return Response({
            'success': True,
            'message': '资产归还完成',
            'summary': {
                'total': len(asset_ids),
                'returned': results.get('returned_count', 0),
                'transferred': results.get('transferred_count', 0)
            },
            'data': results.get('details', [])
        })

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """关闭项目"""
        project = self.get_object()

        if project.status == 'completed':
            return Response({
                'success': False,
                'error': {'code': 'PROJECT_ALREADY_COMPLETED', 'message': '项目已完成'}
            }, status=400)

        # 检查是否有未归还的资产
        unreturned_count = project.project_assets.filter(
            return_status='in_use'
        ).count()

        if unreturned_count > 0:
            return Response({
                'success': False,
                'error': {
                    'code': 'ASSETS_NOT_RETURNED',
                    'message': f'还有{unreturned_count}项资产未归还'
                }
            }, status=400)

        # 更新项目状态
        project.status = 'completed'
        project.actual_end_date = timezone.now().date()
        project.save()

        return Response({
            'success': True,
            'message': '项目已关闭',
            'data': AssetProjectSerializer(project).data
        })

    @action(detail=False, methods=['get'])
    def my_projects(self, request):
        """获取我的项目"""
        user = request.user
        projects = self.get_queryset().filter(
            models.Q(project_manager=user) |
            models.Q(members__user=user, members__is_active=True)
        ).distinct()

        page = self.paginate_queryset(projects)
        if page is not None:
            serializer = AssetProjectSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AssetProjectSerializer(projects, many=True)
        return Response({'success': True, 'data': serializer.data})
```

### 5.2 ProjectAssetViewSet

```python
class ProjectAssetViewSet(BaseModelViewSetWithBatch):
    """项目资产ViewSet"""

    queryset = ProjectAsset.objects.select_related(
        'project', 'asset', 'allocated_by', 'custodian'
    )
    serializer_class = ProjectAssetSerializer
    filterset_class = ProjectAssetFilter

    @action(detail=False, methods=['get'])
    def my_allocations(self, request):
        """获取我负责的资产"""
        user = request.user
        allocations = self.get_queryset().filter(
            custodian=user,
            return_status='in_use'
        )

        page = self.paginate_queryset(allocations)
        if page is not None:
            serializer = ProjectAssetSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ProjectAssetSerializer(allocations, many=True)
        return Response({'success': True, 'data': serializer.data})

    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """转移资产到其他项目"""
        allocation = self.get_object()

        if allocation.return_status != 'in_use':
            return Response({
                'success': False,
                'error': {'code': 'ASSET_NOT_IN_USE', 'message': '资产不在使用中'}
            }, status=400)

        target_project_id = request.data.get('target_project_id')
        transfer_reason = request.data.get('reason', '')

        if not target_project_id:
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': '请选择目标项目'}
            }, status=400)

        service = AssetProjectService()
        result = service.transfer_asset(
            allocation=allocation,
            target_project_id=target_project_id,
            reason=transfer_reason,
            operator=request.user
        )

        return Response({
            'success': True,
            'message': '资产转移成功',
            'data': ProjectAssetSerializer(result).data
        })
```

---

## 6. Service 设计

### 6.1 AssetProjectService

```python
from apps.common.services.base_crud import BaseCRUDService
from django.db import transaction
from decimal import Decimal

class AssetProjectService(BaseCRUDService):
    """项目服务"""

    def __init__(self):
        super().__init__(AssetProject)

    @transaction.atomic
    def allocate_assets(self, project, assets_data, allocation_type, allocation_date,
                       return_date, purpose, usage_location, allocated_by):
        """分配资产到项目"""
        from apps.projects.models import ProjectAsset

        allocations = []
        allocation_date = allocation_date or timezone.now().date()

        for asset_data in assets_data:
            asset_id = asset_data.get('asset_id')
            custodian_id = asset_data.get('custodian_id')

            # 获取资产
            asset = Asset.objects.get(id=asset_id)

            # 创建分配记录
            allocation = ProjectAsset.objects.create(
                organization=project.organization,
                project=project,
                asset=asset,
                allocation_no=self._generate_allocation_no(),
                allocation_date=allocation_date,
                allocation_type=allocation_type,
                allocated_by=allocated_by,
                custodian_id=custodian_id,
                return_date=return_date,
                purpose=purpose,
                usage_location=usage_location,
                allocation_cost=asset.purchase_price or Decimal('0'),
                depreciation_rate=self._calculate_depreciation_rate(asset),
                asset_snapshot={
                    'asset_code': asset.asset_code,
                    'asset_name': asset.asset_name,
                    'category_name': asset.category.name if asset.category else '',
                    'original_cost': str(asset.purchase_price) if asset.purchase_price else '0',
                    'purchase_date': str(asset.purchase_date) if asset.purchase_date else None,
                    'status': asset.asset_status,
                },
                created_by=allocated_by
            )

            # 更新资产状态
            if allocation_type == 'permanent':
                asset.asset_status = 'project_assigned'
                asset.save()

            allocations.append(allocation)

        # 更新项目统计
        project.total_assets += len(allocations)
        project.active_assets += len(allocations)
        project.save()

        return allocations

    def return_assets(self, project, asset_ids, return_type, target_project_id, notes, operator):
        """归还资产"""
        from apps.projects.models import ProjectAsset

        allocations = ProjectAsset.objects.filter(
            project=project,
            asset_id__in=asset_ids,
            return_status='in_use'
        )

        results = {
            'returned_count': 0,
            'transferred_count': 0,
            'details': []
        }

        for allocation in allocations:
            if return_type == 'to_inventory':
                # 归还到库存
                allocation.return_status = 'returned'
                allocation.actual_return_date = timezone.now().date()
                allocation.save()

                # 更新资产状态
                allocation.asset.asset_status = 'idle'
                allocation.asset.save()

                results['returned_count'] += 1

            elif return_type == 'transfer_project':
                # 转移到其他项目
                target_allocation = self._transfer_to_project(
                    allocation, target_project_id, notes, operator
                )
                results['transferred_count'] += 1

            project.active_assets -= 1
            project.save()

        return results

    def transfer_asset(self, allocation, target_project_id, reason, operator):
        """转移资产到其他项目"""
        from apps.projects.models import AssetProject, ProjectAsset

        target_project = AssetProject.objects.get(id=target_project_id)

        if target_project.status != 'active':
            raise ValueError("目标项目状态不正确")

        # 创建新的分配记录
        new_allocation = ProjectAsset.objects.create(
            organization=target_project.organization,
            project=target_project,
            asset=allocation.asset,
            allocation_no=self._generate_allocation_no(),
            allocation_date=timezone.now().date(),
            allocation_type=allocation.allocation_type,
            allocated_by=operator,
            custodian=allocation.custodian,
            allocation_cost=allocation.allocation_cost,
            depreciation_rate=allocation.depreciation_rate,
            asset_snapshot=allocation.asset_snapshot,
            purpose=f'从项目{allocation.project.project_code}转入: {reason}',
            created_by=operator
        )

        # 更新原分配记录
        allocation.return_status = 'transferred'
        allocation.actual_return_date = timezone.now().date()
        allocation.save()

        # 更新项目统计
        allocation.project.active_assets -= 1
        allocation.project.save()

        target_project.active_assets += 1
        target_project.save()

        return new_allocation

    def calculate_cost_summary(self, project):
        """计算项目成本汇总"""
        from django.db.models import Sum, F

        allocations = project.project_assets.filter(return_status='in_use')

        total_cost = allocations.aggregate(
            total=Sum('allocation_cost')
        )['total'] or Decimal('0')

        monthly_depreciation = allocations.aggregate(
            total=Sum('monthly_depreciation')
        )['total'] or Decimal('0')

        # 计算累计折旧
        accumulated_depreciation = Decimal('0')
        for alloc in allocations:
            days_used = (timezone.now().date() - alloc.allocation_date).days
            monthly_dep = alloc.monthly_depreciation or Decimal('0')
            accumulated_depreciation += monthly_dep * Decimal(days_used) / Decimal('30')

        net_value = total_cost - accumulated_depreciation

        return {
            'project_id': str(project.id),
            'project_code': project.project_code,
            'project_name': project.project_name,
            'total_asset_cost': str(total_cost),
            'monthly_depreciation': str(monthly_depreciation),
            'accumulated_depreciation': str(accumulated_depreciation.quantize(Decimal('0.01'))),
            'net_asset_value': str(net_value.quantize(Decimal('0.01'))),
            'allocation_count': allocations.count(),
            'calculation_date': timezone.now().date().isoformat()
        }

    def _calculate_depreciation_rate(self, asset):
        """计算月折旧率"""
        if not asset.purchase_price or not asset.category:
            return Decimal('0')

        useful_life = asset.category.default_useful_life  # 月数
        if not useful_life or useful_life <= 0:
            return Decimal('0')

        return (asset.purchase_price / Decimal(useful_life)).quantize(Decimal('0.01'))

    def _generate_allocation_no(self):
        """生成分配单号"""
        today = timezone.now().strftime('%Y%m')
        prefix = f'FP{today}'
        count = ProjectAsset.objects.filter(
            allocation_no__startswith=prefix
        ).count()
        return f'{prefix}{(count + 1):04d}'

    def _transfer_to_project(self, allocation, target_project_id, reason, operator):
        """内部转移方法"""
        return self.transfer_asset(allocation, target_project_id, reason, operator)
```

---

## 7. 数据库迁移

```python
# Generated by Django 5.0 on 2025-01-20

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('organizations', '0001_initial'),
        ('assets', '0001_initial'),
    ]

    operations = [
        # ========== AssetProject 模型 ==========
        migrations.CreateModel(
            name='AssetProject',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('project_code', models.CharField(max_length=50, unique=True, db_index=True)),
                ('project_name', models.CharField(max_length=200)),
                ('project_alias', models.CharField(max_length=100, blank=True)),
                ('project_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('research', '研发项目'),
                        ('development', '开发项目'),
                        ('infrastructure', '基建项目'),
                        ('other', '其他')
                    ],
                    default='other'
                )),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('planning', '筹备中'),
                        ('active', '进行中'),
                        ('suspended', '已暂停'),
                        ('completed', '已完成'),
                        ('cancelled', '已取消')
                    ],
                    default='planning'
                )),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(null=True, blank=True)),
                ('actual_start_date', models.DateField(null=True, blank=True)),
                ('actual_end_date', models.DateField(null=True, blank=True)),
                ('planned_budget', models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)),
                ('actual_cost', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('asset_cost', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('description', models.TextField(blank=True)),
                ('technical_requirements', models.TextField(blank=True)),
                ('total_assets', models.IntegerField(default=0)),
                ('active_assets', models.IntegerField(default=0)),
                ('completed_milestones', models.IntegerField(default=0)),
                ('total_milestones', models.IntegerField(default=0)),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT)),
                ('custom_fields', models.JSONField(default=dict)),
                # Foreign keys
                ('project_manager', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='managed_projects'
                )),
                ('department', models.ForeignKey(
                    'organizations.Department',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='department_projects'
                )),
            ],
            options={
                'db_table': 'asset_project',
                'indexes': [
                    models.Index(fields=['organization', 'status']),
                    models.Index(fields=['project_manager']),
                    models.Index(fields=['start_date', 'end_date']),
                ],
            },
        ),

        # ========== ProjectAsset 模型 ==========
        migrations.CreateModel(
            name='ProjectAsset',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('allocation_no', models.CharField(max_length=50, unique=True, db_index=True)),
                ('allocation_date', models.DateField()),
                ('allocation_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('permanent', '永久分配'),
                        ('temporary', '临时分配'),
                        ('shared', '共享分配')
                    ],
                    default='temporary'
                )),
                ('return_date', models.DateField(null=True, blank=True)),
                ('actual_return_date', models.DateField(null=True, blank=True)),
                ('return_status', models.CharField(
                    max_length=20,
                    choices=[
                        ('in_use', '使用中'),
                        ('returned', '已归还'),
                        ('transferred', '已转移')
                    ],
                    default='in_use'
                )),
                ('allocation_cost', models.DecimalField(max_digits=14, decimal_places=2)),
                ('depreciation_rate', models.DecimalField(max_digits=5, decimal_places=4)),
                ('monthly_depreciation', models.DecimalField(max_digits=12, decimal_places=2)),
                ('purpose', models.TextField(blank=True)),
                ('usage_location', models.CharField(max_length=200, blank=True)),
                ('asset_snapshot', models.JSONField(default=dict)),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT)),
                ('custom_fields', models.JSONField(default=dict)),
                # Foreign keys
                ('project', models.ForeignKey(
                    'projects.AssetProject',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='project_assets'
                )),
                ('asset', models.ForeignKey(
                    'assets.Asset',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='project_allocations'
                )),
                ('allocated_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='allocated_assets'
                )),
                ('custodian', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    related_name='custodied_assets'
                )),
            ],
            options={
                'db_table': 'project_asset',
                'indexes': [
                    models.Index(fields=['project', 'return_status']),
                    models.Index(fields=['asset', 'return_status']),
                    models.Index(fields=['allocation_date']),
                ],
            },
        ),

        # ========== ProjectMember 模型 ==========
        migrations.CreateModel(
            name='ProjectMember',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('role', models.CharField(
                    max_length=20,
                    choices=[
                        ('manager', '项目经理'),
                        ('member', '项目成员'),
                        ('observer', '观察者')
                    ],
                    default='member'
                )),
                ('is_primary', models.BooleanField(default=False)),
                ('join_date', models.DateField()),
                ('leave_date', models.DateField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('responsibilities', models.TextField(blank=True)),
                ('can_allocate_asset', models.BooleanField(default=False)),
                ('can_view_cost', models.BooleanField(default=False)),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT)),
                ('custom_fields', models.JSONField(default=dict)),
                # Foreign keys
                ('project', models.ForeignKey(
                    'projects.AssetProject',
                    on_delete=models.CASCADE,
                    related_name='members'
                )),
                ('user', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='project_memberships'
                )),
            ],
            options={
                'db_table': 'project_member',
                'indexes': [
                    models.Index(fields=['project', 'user', 'is_active']),
                    models.Index(fields=['user', 'is_active']),
                ],
                'constraints': [
                    models.UniqueConstraint(
                        fields=['project', 'user'],
                        name='unique_project_user'
                    ),
                ],
            },
        ),
    ]
```

---

## 8. API错误码

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| `PROJECT_NOT_ACTIVE` | 400 | 项目状态不正确，无法操作 |
| `PROJECT_ALREADY_COMPLETED` | 400 | 项目已完成 |
| `ASSETS_NOT_RETURNED` | 400 | 存在未归还资产 |
| `ASSET_ALREADY_ALLOCATED` | 400 | 资产已分配给其他项目 |
| `INVALID_TARGET_PROJECT` | 400 | 目标项目无效 |
| `NOT_PROJECT_MEMBER` | 403 | 不是项目成员 |
| `CANNOT_ALLOCATE_ASSET` | 403 | 无权限分配资产 |
| `ASSET_NOT_FOUND_IN_PROJECT` | 404 | 资产不属于该项目 |
