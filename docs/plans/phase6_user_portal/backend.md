# Phase 6: User Portal (用户门户) - 后端设计

## 功能概述与业务场景

用户门户是企业固定资产管理系统中面向普通员工的核心入口，提供个人资产管理、申请记录查询、待办事项处理等功能。员工可以通过门户快速查看和管理自己的资产，提交各类申请，处理审批流程，提高工作效率。

### 核心业务场景
1. **资产查看与管理**：员工查看自己保管的、借用的、领用的资产
2. **申请流程处理**：提交资产领用、调拨、退库、借用等申请
3. **待办事项处理**：审批申请、确认盘点结果、处理提醒事项
4. **移动端支持**：扫码盘点、快速提交申请、移动审批

---

## 用户角色与权限

### 支持的角色
1. **普通员工**：查看个人资产、提交申请、处理个人待办
2. **部门负责人**：部门资产总览、审批本部门申请、管理部门资产
3. **资产管理员**：全资产查看、系统管理、盘点管理
4. **管理员**：系统配置、权限管理、数据统计

### 权限控制
- **数据隔离**：基于组织架构的权限控制，用户只能查看和操作自己权限范围内的数据
- **操作权限**：不同角色拥有不同的操作权限（申请、审批、管理等）
- **字段级权限**：根据工作流和业务规则控制字段的可见性和可编辑性

---

## 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、组织隔离 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤 |

---

## 数据模型设计

### 1.1 用户资产视图 (UserAssetView)

用于聚合用户相关的资产信息，无需额外表，通过查询构建。

```python
# apps/portal/services.py

from typing import List, Dict, Optional
from django.db.models import QuerySet
from apps.assets.models import Asset, AssetPickup, AssetLoan, AssetTransfer
from apps.organizations.models import UserDepartment
from apps.common.services.base_crud import BaseCRUDService


class UserAssetService(BaseCRUDService):
    """用户资产服务 - 继承公共CRUD基类"""

    def __init__(self):
        """初始化服务，设置模型类"""
        super().__init__(Asset)

    def get_my_assets(self, user_id: int, filters: Optional[Dict] = None) -> Dict:
        """
        获取用户的资产列表

        包括:
        - 保管中的资产 (custodian = user)
        - 借用中的资产 (借用单状态为 borrowed)
        - 领用的资产 (领用单状态为 completed)
        """
        from apps.accounts.models import User

        user = User.objects.get(id=user_id)
        base_qs = Asset.objects.filter(organization=user.organization)

        # 1. 直接保管的资产
        custodied_assets = base_qs.filter(custodian=user)

        # 2. 借用中的资产
        borrowed_asset_ids = AssetLoan.objects.filter(
            borrower=user,
            status='borrowed'
        ).values_list('items__asset_id', flat=True)
        borrowed_assets = base_qs.filter(id__in=borrowed_asset_ids)

        # 3. 领用的资产（通过领用单）
        pickup_asset_ids = AssetPickup.objects.filter(
            applicant=user,
            status='completed'
        ).values_list('items__asset_id', flat=True)
        pickup_assets = base_qs.filter(id__in=pickup_asset_ids)

        # 合并去重
        all_assets = (custodied_assets | borrowed_assets | pickup_assets).distinct()

        # 应用过滤
        if filters:
            if filters.get('status'):
                all_assets = all_assets.filter(asset_status=filters['status'])
            if filters.get('category'):
                all_assets = all_assets.filter(asset_category=filters['category'])
            if filters.get('keyword'):
                keyword = filters['keyword']
                all_assets = all_assets.filter(
                    Q(asset_name__icontains=keyword) |
                    Q(asset_code__icontains=keyword) |
                    Q(serial_number__icontains=keyword)
                )

        # 分页
        page = filters.get('page', 1) if filters else 1
        page_size = filters.get('page_size', 20) if filters else 20

        from django.core.paginator import Paginator
        paginator = Paginator(all_assets, page_size)
        page_obj = paginator.get_page(page)

        # 构建响应
        assets_data = []
        for asset in page_obj:
            # 确定资产与用户的关系
            relation = self._get_asset_relation(asset, user)
            # 获取资产操作记录
            recent_operations = self._get_asset_operations(asset, user)

            assets_data.append({
                'id': asset.id,
                'asset_code': asset.asset_code,
                'asset_name': asset.asset_name,
                'category': {
                    'id': asset.asset_category_id,
                    'name': asset.asset_category.name
                },
                'specification': asset.specification,
                'serial_number': asset.serial_number,
                'asset_status': asset.asset_status,
                'asset_status_label': asset.get_asset_status_display(),
                'relation': relation,  # 'custodian', 'borrowed', 'pickup'
                'relation_label': self._get_relation_label(relation),
                'department': {
                    'id': asset.department_id,
                    'name': asset.department.name if asset.department else None
                },
                'location': {
                    'id': asset.location_id,
                    'name': asset.location.name if asset.location else None
                },
                'purchase_price': float(asset.purchase_price) if asset.purchase_price else None,
                'purchase_date': asset.purchase_date.isoformat() if asset.purchase_date else None,
                'qr_code': asset.qr_code,
                'image': asset.image.url if asset.image else None,
                'recent_operations': recent_operations,
                'can_return': self._can_return_asset(asset, user, relation),
                'can_transfer': self._can_transfer_asset(asset, user, relation),
            })

        return {
            'total': paginator.count,
            'page': page,
            'page_size': page_size,
            'items': assets_data,
            'summary': {
                'total_count': paginator.count,
                'custodian_count': custodied_assets.count(),
                'borrowed_count': borrowed_assets.count(),
                'pickup_count': pickup_assets.count(),
                'by_status': self._get_status_summary(all_assets)
            }
        }

    def _get_asset_relation(self, asset, user) -> str:
        """获取资产与用户的关系"""
        if asset.custodian_id == user.id:
            return 'custodian'
        if AssetLoan.objects.filter(
            borrower=user, items__asset=asset, status='borrowed'
        ).exists():
            return 'borrowed'
        if AssetPickup.objects.filter(
            applicant=user, items__asset=asset, status='completed'
        ).exists():
            return 'pickup'
        return 'unknown'

    def _get_relation_label(self, relation: str) -> str:
        """获取关系标签"""
        labels = {
            'custodian': '保管中',
            'borrowed': '借用中',
            'pickup': '领用',
            'unknown': '其他'
        }
        return labels.get(relation, '未知')

    def _get_asset_operations(self, asset, user, limit: int = 3) -> List[Dict]:
        """获取资产最近操作记录"""
        from apps.assets.models import AssetStatusLog

        logs = AssetStatusLog.objects.filter(
            asset=asset
        ).order_by('-created_at')[:limit]

        return [{
            'id': log.id,
            'action': log.action,
            'action_label': log.get_action_display(),
            'from_status': log.old_status,
            'to_status': log.new_status,
            'operator': log.created_by.real_name if log.created_by else None,
            'reason': log.reason,
            'created_at': log.created_at.isoformat()
        } for log in logs]

    def _can_return_asset(self, asset, user, relation: str) -> bool:
        """判断是否可以归还"""
        if relation == 'borrowed':
            return True
        if relation == 'pickup':
            # 已领用资产需要退库单
            return True
        return False

    def _can_transfer_asset(self, asset, user, relation: str) -> bool:
        """判断是否可以申请调拨"""
        # 只有保管人或领用人可以申请调拨
        return relation in ['custodian', 'pickup']

    def _get_status_summary(self, queryset: QuerySet) -> Dict:
        """获取状态汇总"""
        return dict(queryset.values_list('asset_status').annotate(
            count=Count('id')
        ).values_list('asset_status', 'count'))

    def get_asset_detail(self, asset_id: int, user_id: int) -> Dict:
        """获取资产详情"""
        from apps.accounts.models import User

        user = User.objects.get(id=user_id)
        asset = Asset.objects.get(id=asset_id, organization=user.organization)

        relation = self._get_asset_relation(asset, user)

        return {
            'asset': {
                'id': asset.id,
                'asset_code': asset.asset_code,
                'asset_name': asset.asset_name,
                'category': {
                    'id': asset.asset_category_id,
                    'name': asset.asset_category.name,
                    'code': asset.asset_category.code
                },
                'specification': asset.specification,
                'serial_number': asset.serial_number,
                'asset_status': asset.asset_status,
                'asset_status_label': asset.get_asset_status_display(),
                'department': {
                    'id': asset.department_id,
                    'name': asset.department.name if asset.department else None,
                    'full_path': asset.department.full_path_name if asset.department else None
                },
                'location': {
                    'id': asset.location_id,
                    'name': asset.location.name if asset.location else None,
                    'path': asset.location.path if asset.location else None
                },
                'custodian': {
                    'id': asset.custodian_id,
                    'name': asset.custodian.real_name if asset.custodian else None,
                    'avatar': asset.custodian.avatar.url if asset.custodian and asset.custodian.avatar else None,
                    'department': asset.custodian.get_primary_department().name if asset.custodian else None
                },
                'purchase_price': float(asset.purchase_price) if asset.purchase_price else None,
                'purchase_date': asset.purchase_date.isoformat() if asset.purchase_date else None,
                'supplier': {
                    'id': asset.supplier_id,
                    'name': asset.supplier.name if asset.supplier else None
                },
                'qr_code': asset.qr_code,
                'image': asset.image.url if asset.image else None,
                'warranty_expire_date': asset.warranty_expire_date.isoformat() if asset.warranty_expire_date else None,
                'depreciation_method': asset.depreciation_method,
                'useful_life': asset.useful_life,
                'net_value': float(asset.net_value) if asset.net_value else None,
                'custom_fields': asset.custom_fields
            },
            'relation': relation,
            'relation_label': self._get_relation_label(relation),
            'history': self._get_asset_operations(asset, user, limit=10),
            'related_documents': self._get_related_documents(asset, user),
            'available_actions': self._get_available_actions(asset, user, relation)
        }

    def _get_related_documents(self, asset, user) -> List[Dict]:
        """获取关联单据"""
        documents = []

        # 领用单
        pickups = AssetPickup.objects.filter(
            items__asset=asset, applicant=user
        ).distinct()
        for pickup in pickups:
            documents.append({
                'type': 'pickup',
                'type_label': '领用单',
                'id': pickup.id,
                'no': pickup.pickup_no,
                'status': pickup.status,
                'status_label': pickup.get_status_display(),
                'created_at': pickup.created_at.isoformat()
            })

        # 借用单
        loans = AssetLoan.objects.filter(
            items__asset=asset, borrower=user
        ).distinct()
        for loan in loans:
            documents.append({
                'type': 'loan',
                'type_label': '借用单',
                'id': loan.id,
                'no': loan.loan_no,
                'status': loan.status,
                'status_label': loan.get_status_display(),
                'created_at': loan.created_at.isoformat(),
                'expected_return_date': loan.expected_return_date.isoformat() if loan.expected_return_date else None,
                'is_overdue': loan.is_overdue() if hasattr(loan, 'is_overdue') else False
            })

        # 调拨单
        transfers = AssetTransfer.objects.filter(
            items__asset=asset
        ).filter(
            Q(from_department__in=user.departments.all()) |
            Q(to_department__in=user.departments.all())
        ).distinct()

        for transfer in transfers:
            documents.append({
                'type': 'transfer',
                'type_label': '调拨单',
                'id': transfer.id,
                'no': transfer.transfer_no,
                'status': transfer.status,
                'status_label': transfer.get_status_display(),
                'created_at': transfer.created_at.isoformat()
            })

        return sorted(documents, key=lambda x: x['created_at'], reverse=True)

    def _get_available_actions(self, asset, user, relation: str) -> List[str]:
        """获取可用操作"""
        actions = []

        if relation in ['custodian', 'pickup']:
            actions.append('apply_transfer')  # 申请调拨

        if relation == 'borrowed':
            actions.append('apply_return')  # 申请归还

        # 检查是否可以发起盘点
        if hasattr(asset, 'can_start_inventory'):
            actions.append('start_inventory')

        return actions
```

### 1.2 用户申请服务 (UserRequestService)

```python
# apps/portal/services.py (续)

from apps.common.services.base_crud import BaseCRUDService

class UserRequestService(BaseCRUDService):
    """用户申请服务 - 聚合所有类型申请，继承公共CRUD基类"""

    # 申请类型映射
    REQUEST_TYPES = {
        'pickup': {
            'model': AssetPickup,
            'name': '资产领用',
            'api_prefix': 'pickups',
            'fields': ['pickup_no', 'pickup_date', 'pickup_reason', 'status']
        },
        'transfer': {
            'model': AssetTransfer,
            'name': '资产调拨',
            'api_prefix': 'transfers',
            'fields': ['transfer_no', 'transfer_date', 'transfer_reason', 'status']
        },
        'return': {
            'model': AssetReturn,
            'name': '资产退库',
            'api_prefix': 'returns',
            'fields': ['return_no', 'return_date', 'return_reason', 'status']
        },
        'loan': {
            'model': AssetLoan,
            'name': '资产借用',
            'api_prefix': 'loans',
            'fields': ['loan_no', 'borrow_date', 'loan_reason', 'status']
        },
        'consumable_issue': {
            'model': ConsumableIssue,
            'name': '易耗品领用',
            'api_prefix': 'consumables/issues',
            'fields': ['issue_no', 'issue_date', 'purpose', 'status']
        },
        'consumable_purchase': {
            'model': ConsumablePurchase,
            'name': '易耗品采购',
            'api_prefix': 'consumables/purchases',
            'fields': ['purchase_no', 'purchase_date', 'remark', 'status']
        }
    }

    def get_my_requests(self, user_id: int, filters: Optional[Dict] = None) -> Dict:
        """
        获取我的所有申请

        聚合来自不同模块的申请记录:
        - 资产领用单 (AssetPickup)
        - 资产调拨单 (AssetTransfer)
        - 资产退库单 (AssetReturn)
        - 资产借用单 (AssetLoan)
        - 易耗品领用单 (ConsumableIssue)
        - 易耗品采购单 (ConsumablePurchase)
        """
        from apps.accounts.models import User

        user = User.objects.get(id=user_id)
        results = []

        # 获取各类型申请
        for req_type, config in self.REQUEST_TYPES.items():
            model = config['model']
            items = self._get_user_requests_by_type(user, model, req_type)

            for item in items:
                results.append({
                    'id': f"{req_type}_{item.id}",
                    'request_type': req_type,
                    'request_type_label': config['name'],
                    'no': self._get_request_no(item, req_type),
                    'status': item.status,
                    'status_label': self._get_status_label(item, req_type),
                    'created_at': item.created_at.isoformat(),
                    'updated_at': item.updated_at.isoformat(),
                    'summary': self._get_request_summary(item, req_type),
                    'can_cancel': self._can_cancel_request(item, req_type),
                    'can_edit': self._can_edit_request(item, req_type),
                    'can_withdraw': self._can_withdraw_request(item, req_type),
                })

        # 排序和过滤
        results.sort(key=lambda x: x['created_at'], reverse=True)

        if filters:
            if filters.get('status'):
                results = [r for r in results if r['status'] == filters['status']]
            if filters.get('type'):
                results = [r for r in results if r['request_type'] == filters['type']]
            if filters.get('keyword'):
                keyword = filters['keyword'].lower()
                results = [r for r in results if keyword in r['no'].lower() or keyword in r['summary'].lower()]

        # 分页
        page = filters.get('page', 1) if filters else 1
        page_size = filters.get('page_size', 20) if filters else 20

        from django.core.paginator import Paginator
        paginator = Paginator(results, page_size)
        page_obj = paginator.get_page(page)

        return {
            'total': paginator.count,
            'page': page,
            'page_size': page_size,
            'items': list(page_obj),
            'summary': self._get_requests_summary(results)
        }

    def _get_user_requests_by_type(self, user, model, req_type: str) -> QuerySet:
        """获取指定类型的用户申请"""
        # 根据不同类型使用不同的查询条件
        if req_type in ['pickup', 'loan']:
            return model.objects.filter(applicant=user)
        elif req_type == 'transfer':
            # 调拨单可能是申请人或相关方
            return model.objects.filter(
                Q(applicant=user) |
                Q(from_department__in=user.departments.all()) |
                Q(to_department__in=user.departments.all())
            )
        elif req_type == 'return':
            return model.objects.filter(returner=user)
        elif req_type in ['consumable_issue', 'consumable_purchase']:
            return model.objects.filter(applicant=user)
        return model.objects.none()

    def _get_request_no(self, item, req_type: str) -> str:
        """获取申请单号"""
        no_fields = {
            'pickup': 'pickup_no',
            'transfer': 'transfer_no',
            'return': 'return_no',
            'loan': 'loan_no',
            'consumable_issue': 'issue_no',
            'consumable_purchase': 'purchase_no'
        }
        field = no_fields.get(req_type, 'no')
        return getattr(item, field, f'{req_type}_{item.id}')

    def _get_status_label(self, item, req_type: str) -> str:
        """获取状态标签"""
        if hasattr(item, 'get_status_display'):
            return item.get_status_display()
        status_labels = {
            'draft': '草稿',
            'pending': '待审批',
            'approved': '已批准',
            'rejected': '已拒绝',
            'completed': '已完成',
            'cancelled': '已取消'
        }
        return status_labels.get(item.status, item.status)

    def _get_request_summary(self, item, req_type: str) -> str:
        """获取申请摘要"""
        if req_type == 'pickup':
            return f"{item.items.count()} 项资产 - {item.pickup_reason or ''}"
        elif req_type == 'transfer':
            return f"{item.from_department.name} → {item.to_department.name}"
        elif req_type == 'return':
            return f"{item.items.count()} 项资产"
        elif req_type == 'loan':
            return f"{item.items.count()} 项资产 - {item.loan_reason or ''}"
        elif req_type == 'consumable_issue':
            return f"{item.items.count()} 种耗材"
        elif req_type == 'consumable_purchase':
            return f"{item.items.count()} 种耗材"
        return ''

    def _can_cancel_request(self, item, req_type: str) -> bool:
        """是否可以取消"""
        return item.status in ['draft', 'pending']

    def _can_edit_request(self, item, req_type: str) -> bool:
        """是否可以编辑"""
        return item.status == 'draft'

    def _can_withdraw_request(self, item, req_type: str) -> bool:
        """是否可以撤回"""
        return item.status == 'pending'

    def _get_requests_summary(self, results: List) -> Dict:
        """获取申请汇总统计"""
        summary = {
            'total': len(results),
            'by_status': {},
            'by_type': {}
        }

        for r in results:
            # 按状态统计
            status = r['status']
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1

            # 按类型统计
            req_type = r['request_type']
            summary['by_type'][req_type] = summary['by_type'].get(req_type, 0) + 1

        return summary

    def get_request_detail(self, request_type: str, request_id: int, user_id: int) -> Dict:
        """获取申请详情"""
        from apps.accounts.models import User

        config = self.REQUEST_TYPES.get(request_type)
        if not config:
            raise ValueError(f'Unknown request type: {request_type}')

        user = User.objects.get(id=user_id)
        model = config['model']

        try:
            item = model.objects.get(id=request_id)
        except model.DoesNotExist:
            raise ValueError(f'{config["name"]} not found')

        # 验证权限
        if not self._can_view_request(item, user, request_type):
            raise PermissionError('No permission to view this request')

        return self._build_request_detail(item, request_type, config)

    def _can_view_request(self, item, user, request_type: str) -> bool:
        """验证查看权限"""
        if item.applicant == user:
            return True
        if request_type == 'transfer':
            # 调拨单相关方可以查看
            return user.departments.filter(
                id__in=[item.from_department_id, item.to_department_id]
            ).exists()
        return False

    def _build_request_detail(self, item, request_type: str, config: Dict) -> Dict:
        """构建申请详情"""
        detail = {
            'request_type': request_type,
            'request_type_label': config['name'],
            'id': item.id,
            'no': self._get_request_no(item, request_type),
            'status': item.status,
            'status_label': self._get_status_label(item, request_type),
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
        }

        # 根据类型添加特定字段
        if request_type == 'pickup':
            detail.update({
                'applicant': {
                    'id': item.applicant_id,
                    'name': item.applicant.real_name,
                    'department': item.applicant.get_primary_department().name
                },
                'department': {
                    'id': item.department_id,
                    'name': item.department.name
                },
                'pickup_date': item.pickup_date.isoformat(),
                'pickup_reason': item.pickup_reason,
                'items': self._build_pickup_items(item),
                'approvals': self._build_approvals(item)
            })

        elif request_type == 'loan':
            detail.update({
                'borrower': {
                    'id': item.borrower_id,
                    'name': item.borrower.real_name
                },
                'borrow_date': item.borrow_date.isoformat(),
                'expected_return_date': item.expected_return_date.isoformat() if item.expected_return_date else None,
                'actual_return_date': item.actual_return_date.isoformat() if item.actual_return_date else None,
                'loan_reason': item.loan_reason,
                'items': self._build_loan_items(item),
                'is_overdue': item.is_overdue() if hasattr(item, 'is_overdue') else False
            })

        # ... 其他类型处理

        return detail

    def cancel_request(self, request_type: str, request_id: int, user_id: int) -> Dict:
        """取消申请"""
        from apps.accounts.models import User

        user = User.objects.get(id=user_id)
        config = self.REQUEST_TYPES.get(request_type)
        if not config:
            raise ValueError(f'Unknown request type: {request_type}')

        item = config['model'].objects.get(id=request_id)

        if item.applicant != user:
            raise PermissionError('Only applicant can cancel')

        if not self._can_cancel_request(item, request_type):
            raise ValueError(f'Cannot cancel request in {item.status} status')

        # 调用各模块的取消方法
        if request_type == 'pickup':
            item.cancel()
        elif request_type == 'loan':
            item.cancel()
        # ... 其他类型

        return {
            'success': True,
            'status': item.status,
            'status_label': self._get_status_label(item, request_type)
        }
```

### 1.3 用户待办服务 (UserTaskService)

```python
# apps/portal/services.py (续)

from apps.common.services.base_crud import BaseCRUDService

class UserTaskService(BaseCRUDService):
    """用户待办服务 - 聚合所有待办事项，继承公共CRUD基类"""

    def __init__(self):
        """初始化服务，使用WorkflowTask作为主模型"""
        from apps.workflows.models import WorkflowTask
        super().__init__(WorkflowTask)

    def get_my_tasks(self, user_id: int, filters: Optional[Dict] = None) -> Dict:
        """
        获取我的待办事项

        包括:
        - 工作流待审批任务
        - 盘点任务
        - 需要确认的退库单
        - 即将到期的借用归还提醒
        """
        from apps.accounts.models import User

        user = User.objects.get(id=user_id)
        tasks = []

        # 1. 工作流审批任务
        workflow_tasks = self._get_workflow_tasks(user)
        tasks.extend(workflow_tasks)

        # 2. 盘点任务
        inventory_tasks = self._get_inventory_tasks(user)
        tasks.extend(inventory_tasks)

        # 3. 待确认退库
        return_confirm_tasks = self._get_return_confirm_tasks(user)
        tasks.extend(return_confirm_tasks)

        # 4. 即将到期的借用
        due_loan_reminders = self._get_due_loan_reminders(user)
        tasks.extend(due_loan_reminders)

        # 5. 待领取资产提醒
        pickup_reminders = self._get_pickup_reminders(user)
        tasks.extend(pickup_reminders)

        # 排序
        tasks.sort(key=lambda x: (
            0 if x.get('priority') == 'urgent' else
            1 if x.get('priority') == 'high' else 2
        , x.get('due_date', '')), reverse=False)

        # 过滤
        if filters:
            if filters.get('task_type'):
                tasks = [t for t in tasks if t['task_type'] == filters['task_type']]
            if filters.get('status'):
                tasks = [t for t in tasks if t['status'] == filters['status']]

        # 分页
        page = filters.get('page', 1) if filters else 1
        page_size = filters.get('page_size', 20) if filters else 20

        from django.core.paginator import Paginator
        paginator = Paginator(tasks, page_size)
        page_obj = paginator.get_page(page)

        return {
            'total': paginator.count,
            'page': page,
            'page_size': page_size,
            'items': list(page_obj),
            'summary': {
                'total': len(tasks),
                'urgent': len([t for t in tasks if t.get('priority') == 'urgent']),
                'high': len([t for t in tasks if t.get('priority') == 'high']),
                'normal': len([t for t in tasks if t.get('priority') == 'normal']),
                'by_type': self._get_task_type_summary(tasks)
            }
        }

    def _get_workflow_tasks(self, user) -> List[Dict]:
        """获取工作流审批任务"""
        from apps.workflows.models import WorkflowTask

        tasks = WorkflowTask.objects.filter(
            assignee=user,
            status='pending'
        ).select_related('instance', 'instance__definition')

        return [{
            'id': f"workflow_{t.id}",
            'task_type': 'workflow_approval',
            'task_type_label': '流程审批',
            'title': t.instance.title or t.instance.definition.name,
            'description': t.node_name,
            'priority': self._get_workflow_priority(t),
            'status': t.status,
            'status_label': '待审批',
            'due_date': t.due_date.isoformat() if t.due_date else None,
            'created_at': t.created_at.isoformat(),
            'action_url': f'/workflows/tasks/{t.id}',
            'instance': {
                'id': t.instance_id,
                'no': t.instance.instance_no,
                'definition': t.instance.definition.name
            }
        } for t in tasks]

    def _get_workflow_priority(self, task) -> str:
        """获取工作流任务优先级"""
        if task.due_date:
            from django.utils import timezone
            days_until_due = (task.due_date - timezone.now().date()).days
            if days_until_due <= 0:
                return 'urgent'
            elif days_until_due <= 2:
                return 'high'
        return 'normal'

    def _get_inventory_tasks(self, user) -> List[Dict]:
        """获取盘点任务"""
        from apps.inventory.models import InventoryTaskAssignment

        assignments = InventoryTaskAssignment.objects.filter(
            assigned_to=user
        ).filter(
            Q(status='pending') | Q(status='in_progress')
        ).select_related('task', 'task__inventory')

        tasks = []
        for assignment in assignments:
            task = assignment.task
            inventory = task.inventory

            # 检查是否逾期
            from django.utils import timezone
            is_overdue = inventory.end_date and timezone.now().date() > inventory.end_date

            tasks.append({
                'id': f"inventory_{assignment.id}",
                'task_type': 'inventory',
                'task_type_label': '资产盘点',
                'title': inventory.inventory_name,
                'description': f'待盘点 {assignment.pending_count} 项资产',
                'priority': 'urgent' if is_overdue else 'normal',
                'status': assignment.status,
                'status_label': assignment.get_status_display(),
                'due_date': inventory.end_date.isoformat() if inventory.end_date else None,
                'progress': {
                    'total': assignment.total_count,
                    'completed': assignment.completed_count,
                    'pending': assignment.pending_count
                },
                'action_url': f'/inventory/my/{assignment.id}',
                'is_overdue': is_overdue
            })

        return tasks

    def _get_return_confirm_tasks(self, user) -> List[Dict]:
        """获取待确认退库任务（资产管理员）"""
        # 检查用户是否是资产管理员
        if not user.has_role('asset_admin'):
            return []

        from apps.assets.models import AssetReturn

        returns = AssetReturn.objects.filter(
            status='pending'
        ).select_related('returner')

        return [{
            'id': f"return_confirm_{r.id}",
            'task_type': 'return_confirm',
            'task_type_label': '退库确认',
            'title': f'{r.returner.real_name} 的退库申请',
            'description': f'{r.items.count()} 项资产待确认',
            'priority': 'normal',
            'status': r.status,
            'status_label': '待确认',
            'due_date': r.return_date.isoformat() if r.return_date else None,
            'action_url': f'/assets/returns/{r.id}'
        } for r in returns]

    def _get_due_loan_reminders(self, user) -> List[Dict]:
        """获取即将到期的借用提醒"""
        from apps.assets.models import AssetLoan
        from django.utils import timezone

        # 获取用户借用中且即将到期的资产（7天内）
        upcoming_date = timezone.now().date() + timezone.timedelta(days=7)

        loans = AssetLoan.objects.filter(
            borrower=user,
            status='borrowed',
            expected_return_date__lte=upcoming_date
        ).select_related('items__asset')

        tasks = []
        for loan in loans:
            days_left = (loan.expected_return_date - timezone.now().date()).days
            is_overdue = days_left < 0

            tasks.append({
                'id': f"loan_due_{loan.id}",
                'task_type': 'loan_return',
                'task_type_label': '借用归还',
                'title': f'借用资产归还提醒',
                'description': f'{loan.items.count()} 项资产{"已逾期" if is_overdue else f"将在{days_left}天后到期"}',
                'priority': 'urgent' if is_overdue else 'high',
                'status': 'pending',
                'status_label': '待归还',
                'due_date': loan.expected_return_date.isoformat(),
                'days_left': days_left,
                'is_overdue': is_overdue,
                'action_url': f'/assets/loans/{loan.id}'
            })

        return tasks

    def _get_pickup_reminders(self, user) -> List[Dict]:
        """获取待领取资产提醒"""
        from apps.assets.models import AssetPickup
        from django.utils import timezone

        pickups = AssetPickup.objects.filter(
            applicant=user,
            status='approved'
        ).select_related('items__asset')

        tasks = []
        for pickup in pickups:
            # 检查审批通过天数
            days_passed = (timezone.now().date() - pickup.approved_at.date()).days

            tasks.append({
                'id': f"pickup_{pickup.id}",
                'task_type': 'pickup',
                'task_type_label': '资产领取',
                'title': f'待领取资产',
                'description': f'{pickup.items.count()} 项资产已审批通过，请及时领取',
                'priority': 'high' if days_passed > 3 else 'normal',
                'status': pickup.status,
                'status_label': '待领取',
                'approved_at': pickup.approved_at.isoformat(),
                'days_passed': days_passed,
                'action_url': f'/assets/pickups/{pickup.id}'
            })

        return tasks

    def _get_task_type_summary(self, tasks: List) -> Dict:
        """按类型统计任务"""
        summary = {}
        for task in tasks:
            task_type = task['task_type']
            summary[task_type] = summary.get(task_type, 0) + 1
        return summary
```

---

## 2. 序列化器设计

### 2.1 门户序列化器

```python
# apps/portal/serializers.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.accounts.serializers import UserSerializer
from apps.organizations.serializers import OrganizationSerializer, DepartmentSerializer
from apps.assets.serializers import AssetSerializer


class PortalAssetSerializer(BaseModelSerializer):
    """门户资产序列化器 - 继承公共基类"""

    # 额外的关联信息
    custodian = UserSerializer(read_only=True, allow_null=True)
    department = DepartmentSerializer(read_only=True, allow_null=True)
    asset_category = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + [
            'asset_code', 'asset_name', 'specification', 'serial_number',
            'asset_status', 'custodian', 'department', 'asset_category',
            'purchase_price', 'purchase_date', 'qr_code'
        ]

    def get_asset_category(self, obj):
        """获取资产分类信息"""
        if obj.asset_category:
            return {
                'id': obj.asset_category.id,
                'code': obj.asset_category.code,
                'name': obj.asset_category.name
            }
        return None


class MyAssetSummarySerializer(BaseModelSerializer):
    """我的资产汇总序列化器"""

    asset_count = serializers.IntegerField(read_only=True)
    custodian_count = serializers.IntegerField(read_only=True)
    borrowed_count = serializers.IntegerField(read_only=True)
    pickup_count = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        fields = BaseModelSerializer.Meta.fields + [
            'asset_count', 'custodian_count', 'borrowed_count', 'pickup_count'
        ]


class RequestSummarySerializer(BaseModelSerializer):
    """申请汇总序列化器"""

    request_type = serializers.CharField(read_only=True)
    request_type_label = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_label = serializers.CharField(read_only=True)
    summary = serializers.CharField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        fields = BaseModelSerializer.Meta.fields + [
            'request_type', 'request_type_label', 'status', 'status_label', 'summary'
        ]


class TaskSummarySerializer(BaseModelSerializer):
    """待办汇总序列化器"""

    task_type = serializers.CharField(read_only=True)
    task_type_label = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    due_date = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        fields = BaseModelSerializer.Meta.fields + [
            'task_type', 'task_type_label', 'priority', 'due_date'
        ]
```

---

## 3. 权限控制

### 3.1 门户访问权限

```python
# apps/portal/permissions.py

from rest_framework import permissions
from apps.organizations.models import Organization


class PortalAccessPermission(permissions.BasePermission):
    """门户访问权限"""

    def has_permission(self, request, view):
        # 所有已登录用户都可以访问门户
        return request.user and request.user.is_authenticated


class MyAssetPermission(permissions.BasePermission):
    """我的资产查看权限"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 只能查看自己组织的资产
        return obj.organization == request.user.organization


class MyRequestPermission(permissions.BasePermission):
    """我的申请权限"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 只能查看/操作自己的申请
        return getattr(obj, 'applicant', None) == request.user or \
               getattr(obj, 'borrower', None) == request.user or \
               getattr(obj, 'returner', None) == request.user
```

---

## 4. API设计

### 4.1 门户概览API

```python
# apps/portal/api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.portal.services import UserAssetService, UserRequestService, UserTaskService
from apps.portal.serializers import (
    PortalAssetSerializer, MyAssetSummarySerializer,
    RequestSummarySerializer, TaskSummarySerializer
)


class PortalOverviewView(APIView):
    """门户概览 - 获取用户门户首页数据"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 并行获取各模块数据
        asset_service = UserAssetService()
        request_service = UserRequestService()
        task_service = UserTaskService()

        # 资产概览
        my_assets = asset_service.get_my_assets(user.id, filters={'page_size': 5})
        asset_summary = my_assets['summary']

        # 申请概览
        my_requests = request_service.get_my_requests(user.id, filters={'page_size': 5})
        request_summary = my_requests['summary']

        # 待办概览
        my_tasks = task_service.get_my_tasks(user.id, filters={'page_size': 10})
        task_summary = my_tasks['summary']

        # 待处理数量
        pending_count = task_summary.get('urgent', 0) + task_summary.get('high', 0)

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'avatar': user.avatar.url if user.avatar else None,
                'primary_department': {
                    'id': user.get_primary_department().id if user.get_primary_department() else None,
                    'name': user.get_primary_department().name if user.get_primary_department() else None
                },
                'organization': {
                    'id': user.organization.id,
                    'name': user.organization.name
                }
            },
            'assets': {
                'total': asset_summary['total_count'],
                'custodian': asset_summary['custodian_count'],
                'borrowed': asset_summary['borrowed_count'],
                'pickup': asset_summary['pickup_count'],
                'recent': my_assets['items'][:3]
            },
            'requests': {
                'total': request_summary['total'],
                'by_status': request_summary['by_status'],
                'recent': my_requests['items'][:3]
            },
            'tasks': {
                'total': task_summary['total'],
                'pending': pending_count,
                'urgent': task_summary.get('urgent', 0),
                'high': task_summary.get('high', 0),
                'normal': task_summary.get('normal', 0),
                'items': my_tasks['items'][:5]
            },
            'quick_actions': self._get_quick_actions(user)
        })

    def _get_quick_actions(self, user) -> List[Dict]:
        """获取快捷操作"""
        actions = [
            {
                'id': 'scan_qr',
                'name': '扫码查看',
                'icon': 'qr-scan',
                'description': '扫描资产二维码查看详情',
                'action': 'scan'
            },
            {
                'id': 'my_assets',
                'name': '我的资产',
                'icon': 'box',
                'description': '查看我保管的资产',
                'action': 'navigate',
                'url': '/portal/my-assets'
            },
            {
                'id': 'apply_pickup',
                'name': '领用申请',
                'icon': 'shopping-cart',
                'description': '申请领用资产',
                'action': 'navigate',
                'url': '/assets/pickups/create'
            },
            {
                'id': 'apply_loan',
                'name': '借用申请',
                'icon': 'hand-holding',
                'description': '临时借用资产',
                'action': 'navigate',
                'url': '/assets/loans/create'
            }
        ]

        # 管理员额外操作
        if user.has_role('asset_admin'):
            actions.extend([
                {
                    'id': 'inventory_list',
                    'name': '盘点管理',
                    'icon': 'clipboard-list',
                    'description': '管理盘点任务',
                    'action': 'navigate',
                    'url': '/inventory/tasks'
                },
                {
                    'id': 'pending_approvals',
                    'name': '待审批',
                    'icon': 'approval',
                    'description': f'{self._get_pending_approval_count(user)} 条待审批',
                    'action': 'navigate',
                    'url': '/workflows/my-tasks'
                }
            ])

        return actions
```

### 4.2 我的资产ViewSet

```python
# apps/portal/api/views.py (续)

from rest_framework import viewsets
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.filters.base import BaseModelFilter
from apps.portal.serializers import PortalAssetSerializer
from apps.portal.services import UserAssetService
from apps.assets.models import Asset


class MyAssetFilter(BaseModelFilter):
    """我的资产过滤器 - 继承公共基类"""

    # 额外的业务字段过滤
    asset_code = django_filters.CharFilter(lookup_expr='icontains', label='资产编码')
    asset_name = django_filters.CharFilter(lookup_expr='icontains', label='资产名称')
    asset_status = django_filters.ChoiceFilter(choices=Asset.AssetStatus.choices, label='资产状态')
    relation = django_filters.ChoiceFilter(
        choices=[
            ('custodian', '保管中'),
            ('borrowed', '借用中'),
            ('pickup', '领用')
        ],
        method='filter_relation',
        label='资产关系'
    )

    class Meta(BaseModelFilter.Meta):
        model = Asset
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'asset_code', 'asset_name', 'asset_status', 'relation'
        ]

    def filter_relation(self, queryset, name, value):
        """按资产关系过滤"""
        user = self.request.user
        if value == 'custodian':
            return queryset.filter(custodian=user)
        elif value == 'borrowed':
            from apps.assets.models import AssetLoan
            borrowed_ids = AssetLoan.objects.filter(
                borrower=user, status='borrowed'
            ).values_list('items__asset_id', flat=True)
            return queryset.filter(id__in=borrowed_ids)
        elif value == 'pickup':
            from apps.assets.models import AssetPickup
            pickup_ids = AssetPickup.objects.filter(
                applicant=user, status='completed'
            ).values_list('items__asset_id', flat=True)
            return queryset.filter(id__in=pickup_ids)
        return queryset


class MyAssetViewSet(BaseModelViewSetWithBatch):
    """我的资产 ViewSet - 继承公共基类，自动获得所有CRUD和批量操作功能"""

    serializer_class = PortalAssetSerializer
    filterset_class = MyAssetFilter
    # 自动获得：
    # - 组织隔离
    # - 软删除
    # - 批量删除/恢复/更新
    # - 已删除列表查询
    # - 审计字段自动设置

    def get_queryset(self):
        """获取当前用户相关的资产"""
        user = self.request.user
        service = UserAssetService()

        # 获取基础查询集
        from apps.assets.models import Asset
        queryset = Asset.objects.filter(organization=user.organization)

        # 获取用户相关的资产ID
        custodied_ids = queryset.filter(custodian=user).values_list('id', flat=True)

        from apps.assets.models import AssetLoan, AssetPickup
        borrowed_ids = AssetLoan.objects.filter(
            borrower=user, status='borrowed'
        ).values_list('items__asset_id', flat=True)

        pickup_ids = AssetPickup.objects.filter(
            applicant=user, status='completed'
        ).values_list('items__asset_id', flat=True)

        # 合并去重
        all_ids = set(custodied_ids) | set(borrowed_ids) | set(pickup_ids)
        return queryset.filter(id__in=all_ids)

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """获取资产详情（增强版）"""
        asset = self.get_object()
        service = UserAssetService()
        detail = service.get_asset_detail(asset.id, request.user.id)
        return Response(detail)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """获取资产汇总统计"""
        user = request.user
        service = UserAssetService()
        result = service.get_my_assets(user.id, filters={'page_size': 1})
        return Response(result['summary'])


class MyRequestViewSet(viewsets.ViewSet):
    """我的申请 ViewSet - 聚合视图"""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """获取我的所有申请"""
        service = UserRequestService()
        filters = {
            'page': request.query_params.get('page', 1),
            'page_size': request.query_params.get('page_size', 20),
            'status': request.query_params.get('status'),
            'type': request.query_params.get('type'),
            'keyword': request.query_params.get('keyword')
        }
        result = service.get_my_requests(request.user.id, filters=filters)
        return Response(result)

    def retrieve(self, request, pk=None):
        """获取申请详情"""
        # pk 格式: "requesttype_id"
        parts = pk.split('_')
        if len(parts) < 2:
            return Response({'detail': 'Invalid ID format'}, status=400)

        request_type = parts[0]
        request_id = int(parts[1])

        service = UserRequestService()
        detail = service.get_request_detail(request_type, request_id, request.user.id)
        return Response(detail)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消申请"""
        parts = pk.split('_')
        request_type = parts[0]
        request_id = int(parts[1])

        service = UserRequestService()
        result = service.cancel_request(request_type, request_id, request.user.id)
        return Response(result)


class MyTaskViewSet(viewsets.ViewSet):
    """我的待办 ViewSet - 聚合视图"""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """获取我的所有待办"""
        service = UserTaskService()
        filters = {
            'page': request.query_params.get('page', 1),
            'page_size': request.query_params.get('page_size', 20),
            'task_type': request.query_params.get('task_type'),
            'status': request.query_params.get('status')
        }
        result = service.get_my_tasks(request.user.id, filters=filters)
        return Response(result)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """获取待办汇总"""
        service = UserTaskService()
        result = service.get_my_tasks(request.user.id, filters={'page_size': 1})
        return Response(result['summary'])
```

---

## 5. 数据缓存策略

```python
# apps/portal/cache.py

from django.core.cache import cache
from django.conf import settings
import hashlib


class PortalCache:
    """门户缓存管理"""

    CACHE_PREFIX = 'portal'
    CACHE_TIMEOUT = getattr(settings, 'PORTAL_CACHE_TIMEOUT', 300)  # 5分钟

    @classmethod
    def get_my_assets_cache_key(cls, user_id: int, filters: Dict) -> str:
        """生成我的资产缓存键"""
        filter_str = str(sorted(filters.items()))
        filter_hash = hashlib.md5(filter_str.encode()).hexdigest()[:8]
        return f'{cls.CACHE_PREFIX}:assets:{user_id}:{filter_hash}'

    @classmethod
    def get_my_requests_cache_key(cls, user_id: int, filters: Dict) -> str:
        """生成我的申请缓存键"""
        filter_str = str(sorted(filters.items()))
        filter_hash = hashlib.md5(filter_str.encode()).hexdigest()[:8]
        return f'{cls.CACHE_PREFIX}:requests:{user_id}:{filter_hash}'

    @classmethod
    def get_my_tasks_cache_key(cls, user_id: int) -> str:
        """生成我的待办缓存键"""
        return f'{cls.CACHE_PREFIX}:tasks:{user_id}'

    @classmethod
    def invalidate_user_cache(cls, user_id: int):
        """清除用户相关缓存"""
        # 清除所有该用户的缓存
        cache.delete_many([f'{cls.CACHE_PREFIX}:{user_id}:*'])
```

---

## 6. URL路由配置

```python
# apps/portal/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.portal.api.views import (
    PortalOverviewView, MobilePortalView,
    MyAssetViewSet, MyRequestViewSet, MyTaskViewSet
)

router = DefaultRouter()
router.register(r'my-assets', MyAssetViewSet, basename='portal-my-assets')
router.register(r'my-requests', MyRequestViewSet, basename='portal-my-requests')
router.register(r'my-tasks', MyTaskViewSet, basename='portal-my-tasks')

urlpatterns = [
    path('', include(router.urls)),
    path('overview/', PortalOverviewView.as_view(), name='portal-overview'),
    path('mobile/', MobilePortalView.as_view(), name='portal-mobile'),
]

# 主路由配置
# backend/config/urls.py
urlpatterns = [
    ...
    path('api/portal/', include('apps.portal.urls')),
]
```

---

## 7. 移动端适配

```python
# apps/portal/api/views.py (续)

class MobilePortalView(PortalOverviewView):
    """移动端门户 - 精简版"""

    def get(self, request):
        # 获取基础数据
        data = super().get(request)

        # 移动端精简处理
        return Response({
            'user': data['user'],
            'summary': {
                'assets_count': data['assets']['total'],
                'tasks_count': data['tasks']['pending'],
                'notifications_count': self._get_unread_notifications(request.user)
            },
            'quick_actions': data['quick_actions'][:4],  # 只显示前4个
            'pending_tasks': data['tasks']['items'][:3]   # 只显示前3个待办
        })

    def _get_unread_notifications(self, user) -> int:
        """获取未读通知数"""
        from apps.notifications.models import UserNotification
        return UserNotification.objects.filter(
            user=user,
            is_read=False
        ).count()
```

---

## 7.1 前端组件设计

基于公共前端组件规范，门户模块采用以下组件架构：

### 7.1.1 页面组件 (Pages)
- **PortalHomePage** (`/src/views/portal/PortalHomePage.vue`)
  - 使用 `BaseListPage` 基类
  - 继承公共布局、搜索、分页功能
  - 包含资产概览卡片、待办事项、快捷操作入口
- **MyAssetsPage** (`/src/views/portal/assets/MyAssetsPage.vue`)
  - 使用 `BaseListPage` + AssetList 组件
  - 支持多条件搜索、状态筛选、批量操作
- **MyRequestsPage** (`/src/views/portal/requests/MyRequestsPage.vue`)
  - 使用 `BaseListPage` + RequestList 组件
  - 按申请类型分组展示，支持状态跟踪
- **MyTasksPage** (`/src/views/portal/tasks/MyTasksPage.vue`)
  - 使用 `BaseListPage` + TaskList 组件
  - 集成工作流待办、盘点任务、提醒事项

### 7.1.2 业务组件 (Business Components)
- **AssetList** (`/src/components/portal/assets/AssetList.vue`)
  - 继承 `BaseTable`，实现资产列表展示
  - 支持扫码功能、快速操作按钮
- **AssetCard** (`/src/components/portal/assets/AssetCard.vue`)
  - 资产卡片组件，展示关键信息
  - 支持扫码、查看详情、快速操作
- **RequestForm** (`/src/components/portal/requests/RequestForm.vue`)
  - 申请表单组件，支持多种申请类型
  - 使用 `DynamicForm` 动态渲染
- **TaskItem** (`/src/components/portal/tasks/TaskItem.vue`)
  - 待办事项组件，展示任务信息和操作按钮
- **ScanInput** (`/src/components/common/ScanInput.vue`)
  - 扫码输入组件，支持移动端扫码

### 7.1.3 基础组件 (Base Components)
门户模块复用以下公共基础组件：
- **BaseListPage** (`/src/components/common/BaseListPage.vue`) - 列表页面基类
- **BaseFormPage** (`/src/components/common/BaseFormPage.vue`) - 表单页面基类
- **BaseSearchBar** (`/src/components/common/BaseSearchBar.vue`) - 搜索栏基类
- **BaseTable** (`/src/components/common/BaseTable.vue`) - 表格基类
- **BasePagination** (`/src/components/common/BasePagination.vue`) - 分页基类
- **BaseAuditInfo** (`/src/components/common/BaseAuditInfo.vue`) - 审计信息组件
- **BaseFileUpload** (`/src/components/common/BaseFileUpload.vue`) - 文件上传组件

### 7.1.4 移动端优化组件
- **MobileAssetScanner** (`/src/mobile/components/AssetScanner.vue`)
  - 移动端扫码组件，支持离线缓存
- **MobileQuickActions** (`/src/mobile/components/QuickActions.vue`)
  - 移动端快捷操作面板
- **MobileTaskList** (`/src/mobile/components/TaskList.vue`)
  - 移动端待办列表，支持下拉刷新

### 7.1.5 组件通信与状态管理
- **状态管理**：使用 Pinia store，统一管理门户状态
- **组件通信**：通过事件总线 + props 实现组件间通信
- **API封装**：统一调用 portal 相关的 API 接口

### 7.1.6 权限控制集成
- **v-permission 指令**：按钮级别的权限控制
- **PermissionButton 组件**：权限按钮封装
- **动态路由**：根据用户权限动态加载组件

---

## 8. 后台任务

```python
# apps/portal/tasks.py

from celery import shared_task
from django.utils import timezone
from apps.assets.models import AssetLoan
from apps.notifications.services import NotificationService


@shared_task
def check_due_loans():
    """检查即将到期的借用，发送提醒"""
    from django.utils import timezone

    upcoming_date = timezone.now().date() + timezone.timedelta(days=3)

    due_loans = AssetLoan.objects.filter(
        status='borrowed',
        expected_return_date__lte=upcoming_date,
        reminder_sent=False
    ).select_related('borrower')

    notification_service = NotificationService()

    for loan in due_loans:
        days_left = (loan.expected_return_date - timezone.now().date()).days

        if days_left <= 0:
            title = '借用已逾期'
            content = f'您借用的资产已逾期{-days_left}天，请及时归还'
        else:
            title = '借用即将到期'
            content = f'您借用的资产将在{days_left}天后到期，请准备归还'

        notification_service.send_notification(
            user=loan.borrower,
            title=title,
            content=content,
            link=f'/portal/assets/loans/{loan.id}',
            notification_type='loan_reminder'
        )

        loan.reminder_sent = True
        loan.save()


@shared_task
def update_portal_statistics():
    """更新门户统计数据（每小时执行一次）"""
    from django.contrib.auth import get_user_model
    from apps.portal.cache import PortalCache

    User = get_user_model()
    active_users = User.objects.filter(is_active=True)

    for user in active_users:
        # 清除缓存，下次访问时重新计算
        PortalCache.invalidate_user_cache(user.id)
```

---

## 9. 文件结构总结

### 9.1 完整文件结构

```
backend/apps/portal/
├── __init__.py
├── apps.py                      # Django App配置
├── models.py                    # 无需额外模型（使用现有模型）
├── serializers.py               # 序列化器（继承BaseModelSerializer）
├── services.py                  # 业务服务（继承BaseCRUDService）
│   ├── UserAssetService       # 用户资产服务
│   ├── UserRequestService     # 用户申请服务
│   └── UserTaskService        # 用户待办服务
├── filters.py                   # 过滤器（继承BaseModelFilter）
│   └── MyAssetFilter          # 我的资产过滤器
├── permissions.py               # 权限控制
├── cache.py                     # 缓存策略
├── tasks.py                     # Celery后台任务
├── api/
│   ├── __init__.py
│   ├── views.py                # API视图
│   │   ├── PortalOverviewView  # 门户概览
│   │   ├── MobilePortalView    # 移动端门户
│   │   ├── MyAssetViewSet      # 我的资产ViewSet
│   │   ├── MyRequestViewSet    # 我的申请ViewSet
│   │   └── MyTaskViewSet       # 我的待办ViewSet
│   └── urls.py                 # API路由
└── tests/
    ├── __init__.py
    ├── test_services.py        # 服务测试
    ├── test_views.py           # 视图测试
    └── test_permissions.py     # 权限测试
```

### 9.2 依赖关系

```
apps/portal/
├── 依赖 apps/common/           # 公共基类模块
│   ├── serializers.base       # BaseModelSerializer
│   ├── viewsets.base          # BaseModelViewSetWithBatch
│   ├── services.base_crud     # BaseCRUDService
│   └── filters.base           # BaseModelFilter
├── 依赖 apps/assets/           # 资产模块
│   ├── models                 # Asset, AssetPickup, AssetLoan等
│   └── services               # 资产相关服务
├── 依赖 apps/workflows/        # 工作流模块
│   └── models                 # WorkflowTask
├── 依赖 apps/inventory/        # 盘点模块
│   └── models                 # InventoryTaskAssignment
├── 依赖 apps/accounts/         # 用户模块
│   └── models                 # User
└── 依赖 apps/organizations/    # 组织模块
    └── models                 # Organization, Department
```

---

## 10. 测试策略

```python
# apps/portal/tests/test_services.py

from django.test import TestCase
from apps.portal.services import UserAssetService, UserRequestService
from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory, AssetPickup
from apps.organizations.models import Organization, Department


class UserAssetServiceTest(TestCase):
    """用户资产服务测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试公司')
        self.dept = Department.objects.create(
            organization=self.org,
            name='研发部'
        )
        self.user = User.objects.create_user(
            username='testuser',
            organization=self.org
        )
        self.user.departments.add(self.dept)

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='1001',
            name='计算机设备'
        )

    def test_get_my_assets_custodian(self):
        """测试获取保管的资产"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试电脑',
            custodian=self.user,
            asset_status='in_use'
        )

        service = UserAssetService()
        result = service.get_my_assets(self.user.id)

        self.assertEqual(result['summary']['custodian_count'], 1)
        self.assertEqual(result['items'][0]['relation'], 'custodian')

    def test_get_my_assets_borrowed(self):
        """测试获取借用的资产"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试电脑'
        )

        loan = AssetLoan.objects.create(
            borrower=self.user,
            borrow_date='2024-01-01',
            expected_return_date='2024-01-15',
            status='borrowed'
        )
        # 添加借用明细...

        service = UserAssetService()
        result = service.get_my_assets(self.user.id)

        self.assertEqual(result['summary']['borrowed_count'], 1)


class UserRequestServiceTest(TestCase):
    """用户申请服务测试"""

    def setUp(self):
        # 类似 setUp
        pass

    def test_get_my_requests_aggregation(self):
        """测试申请聚合功能"""
        # 创建不同类型的申请
        # 验证正确聚合

        service = UserRequestService()
        result = service.get_my_requests(self.user.id)

        self.assertIn('by_type', result['summary'])
        self.assertGreater(result['summary']['total'], 0)
```

---

## 11. 实现检查清单

### 11.1 基础设施
- [ ] 创建 `apps/portal` 目录结构
- [ ] 配置 `apps.py`（Django App配置）
- [ ] 在 `INSTALLED_APPS` 中注册portal应用
- [ ] 配置URL路由（`backend/config/urls.py`）

### 11.2 序列化器（继承BaseModelSerializer）
- [ ] `PortalAssetSerializer` - 门户资产序列化器
- [ ] `MyAssetSummarySerializer` - 资产汇总序列化器
- [ ] `RequestSummarySerializer` - 申请汇总序列化器
- [ ] `TaskSummarySerializer` - 待办汇总序列化器

### 11.3 过滤器（继承BaseModelFilter）
- [ ] `MyAssetFilter` - 我的资产过滤器
  - [ ] 资产编码过滤
  - [ ] 资产名称过滤
  - [ ] 资产状态过滤
  - [ ] 资产关系过滤（保管/借用/领用）
  - [ ] 继承公共时间范围过滤

### 11.4 服务类（继承BaseCRUDService）
- [ ] `UserAssetService` - 用户资产服务
  - [ ] `get_my_assets()` - 获取我的资产
  - [ ] `get_asset_detail()` - 获取资产详情
  - [ ] `_get_asset_relation()` - 获取资产关系
  - [ ] `_get_asset_operations()` - 获取资产操作记录
  - [ ] `_can_return_asset()` - 判断是否可归还
  - [ ] `_can_transfer_asset()` - 判断是否可调拨
- [ ] `UserRequestService` - 用户申请服务
  - [ ] `get_my_requests()` - 获取我的申请
  - [ ] `get_request_detail()` - 获取申请详情
  - [ ] `cancel_request()` - 取消申请
  - [ ] 各类型申请的聚合查询
- [ ] `UserTaskService` - 用户待办服务
  - [ ] `get_my_tasks()` - 获取我的待办
  - [ ] `_get_workflow_tasks()` - 工作流任务
  - [ ] `_get_inventory_tasks()` - 盘点任务
  - [ ] `_get_return_confirm_tasks()` - 退库确认任务
  - [ ] `_get_due_loan_reminders()` - 借用到期提醒
  - [ ] `_get_pickup_reminders()` - 待领取提醒

### 11.5 ViewSet（继承BaseModelViewSetWithBatch）
- [ ] `MyAssetViewSet` - 我的资产ViewSet
  - [ ] 自动获得CRUD操作
  - [ ] 自动获得批量操作（删除/恢复/更新）
  - [ ] 自定义 `detail` action
  - [ ] 自定义 `summary` action
- [ ] `MyRequestViewSet` - 我的申请ViewSet
  - [ ] `list` action
  - [ ] `retrieve` action
  - [ ] `cancel` action
- [ ] `MyTaskViewSet` - 我的待办ViewSet
  - [ ] `list` action
  - [ ] `summary` action

### 11.6 API视图
- [ ] `PortalOverviewView` - 门户概览视图
  - [ ] 获取用户信息
  - [ ] 获取资产概览
  - [ ] 获取申请概览
  - [ ] 获取待办概览
  - [ ] 获取快捷操作
- [ ] `MobilePortalView` - 移动端门户视图
  - [ ] 精简版数据返回

### 11.7 权限控制
- [ ] `PortalAccessPermission` - 门户访问权限
- [ ] `MyAssetPermission` - 我的资产权限
- [ ] `MyRequestPermission` - 我的申请权限

### 11.8 缓存策略
- [ ] `PortalCache` - 门户缓存管理
  - [ ] `get_my_assets_cache_key()` - 资产缓存键
  - [ ] `get_my_requests_cache_key()` - 申请缓存键
  - [ ] `get_my_tasks_cache_key()` - 待办缓存键
  - [ ] `invalidate_user_cache()` - 清除用户缓存

### 11.9 后台任务（Celery）
- [ ] `check_due_loans()` - 检查即将到期的借用
- [ ] `update_portal_statistics()` - 更新门户统计数据

### 11.10 测试
- [ ] 服务单元测试
  - [ ] `UserAssetServiceTest` - 用户资产服务测试
  - [ ] `UserRequestServiceTest` - 用户申请服务测试
  - [ ] `UserTaskServiceTest` - 用户待办服务测试
- [ ] API集成测试
- [ ] 权限测试
- [ ] 性能测试（缓存验证）

---

## 11. API接口规范

本模块的API接口严格遵循 `common_base_features/api.md` 中定义的统一响应格式和错误处理规范。

### 11.1 统一响应格式

#### 成功响应格式

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        ...
    }
}
```

#### 列表响应（分页）

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

#### 错误响应格式

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {...}
    }
}
```

### 11.2 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已删除 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

### 11.3 标准 CRUD 端点

继承 `BaseModelViewSet` 的ViewSet自动提供以下标准端点：

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/portal/my-assets/` | 列表查询（分页、过滤、搜索） |
| GET | `/api/portal/my-assets/{id}/` | 获取单条记录 |
| POST | `/api/portal/my-assets/` | 创建新记录 |
| PUT | `/api/portal/my-assets/{id}/` | 完整更新 |
| PATCH | `/api/portal/my-assets/{id}/` | 部分更新 |
| DELETE | `/api/portal/my-assets/{id}/` | 软删除 |
| GET | `/api/portal/my-assets/deleted/` | 查看已删除记录 |
| POST | `/api/portal/my-assets/{id}/restore/` | 恢复已删除记录 |
| POST | `/api/portal/my-assets/batch-delete/` | 批量软删除 |
| POST | `/api/portal/my-assets/batch-restore/` | 批量恢复 |
| POST | `/api/portal/my-assets/batch-update/` | 批量更新 |

### 11.4 批量操作规范

#### 批量删除请求

```http
POST /api/portal/my-assets/batch-delete/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001",
        "550e8400-e29b-41d4-a716-446655440002"
    ]
}
```

#### 批量删除响应（全部成功）

```http
HTTP/1.1 200 OK

{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440001", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440002", "success": true}
    ]
}
```

#### 批量删除响应（部分失败）

```http
HTTP/1.1 207 Multi-Status

{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440001", "success": false, "error": "记录不存在"},
        {"id": "550e8400-e29b-41d4-a716-446655440002", "success": true}
    ]
}
```

### 11.5 自定义端点

#### 门户概览

```http
GET /api/portal/overview/

# 响应
{
    "success": true,
    "data": {
        "user": {...},
        "assets": {...},
        "requests": {...},
        "tasks": {...},
        "quick_actions": [...]
    }
}
```

#### 我的资产汇总

```http
GET /api/portal/my-assets/summary/

# 响应
{
    "success": true,
    "data": {
        "total_count": 150,
        "custodian_count": 100,
        "borrowed_count": 30,
        "pickup_count": 20,
        "by_status": {
            "idle": 50,
            "in_use": 80,
            "maintenance": 15,
            "scrapped": 5
        }
    }
}
```

#### 资产增强详情

```http
GET /api/portal/my-assets/{id}/detail/

# 响应
{
    "success": true,
    "data": {
        "asset": {...},
        "relation": "custodian",
        "relation_label": "保管中",
        "history": [...],
        "related_documents": [...],
        "available_actions": [...]
    }
}
```

#### 取消申请

```http
POST /api/portal/my-requests/{id}/cancel/

# 响应
{
    "success": true,
    "message": "申请已取消",
    "data": {
        "status": "cancelled",
        "status_label": "已取消"
    }
}
```

### 11.6 过滤和排序

#### 列表查询支持的参数

```http
GET /api/portal/my-assets/?page=1&page_size=20&asset_status=in_use&search=电脑

# 支持的查询参数：
# - page: 页码
# - page_size: 每页数量
# - ordering: 排序字段 (如：-created_at)
# - search: 搜索关键词
# - created_at_from: 创建时间起始
# - created_at_to: 创建时间结束
# - created_by: 创建人ID
# - 以及各模块自定义的过滤字段
```

#### 我的资产过滤参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `asset_code` | string | 资产编码（模糊匹配） | `?asset_code=ASSET001` |
| `asset_name` | string | 资产名称（模糊匹配） | `?asset_name=电脑` |
| `asset_status` | string | 资产状态 | `?asset_status=in_use` |
| `relation` | string | 资产关系 | `?relation=custodian` |
| `created_at_from` | date | 创建时间起始 | `?created_at_from=2024-01-01` |
| `created_at_to` | date | 创建时间结束 | `?created_at_to=2024-12-31` |
| `search` | string | 全文搜索 | `?search=关键词` |

#### 我的申请过滤参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `status` | string | 申请状态 | `?status=pending` |
| `type` | string | 申请类型 | `?type=pickup` |
| `keyword` | string | 搜索关键词 | `?keyword=单号` |

### 11.7 分页规范

所有列表接口默认支持分页：

**请求参数：**
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20，最大100）

**响应格式：**
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/portal/my-assets/?page=2",
        "previous": null,
        "results": [...]
    }
}
```

### 11.8 WebSocket实时通知

#### 连接端点

```
ws://api.example.com/ws/portal/
```

#### 消息格式

**订阅通知类型：**
```json
{
    "type": "subscribe",
    "types": ["application_status", "asset_reminder", "system_notification"]
}
```

**接收通知：**
```json
{
    "type": "application_status",
    "data": {
        "application_id": "...",
        "status": "approved",
        "message": "您的领用申请已批准"
    }
}
```

**心跳响应：**
```json
{
    "type": "pong",
    "timestamp": "2026-01-15T10:30:00Z"
}
```

---

## 12. API端点总结

### 12.1 门户概览
```
GET  /api/portal/overview/           # 门户首页数据
GET  /api/portal/mobile/             # 移动端门户数据
```

### 12.2 我的资产
```
GET    /api/portal/my-assets/              # 获取我的资产列表
POST   /api/portal/my-assets/              # (可选) 创建资产
GET    /api/portal/my-assets/{id}/         # 获取资产详情
PUT    /api/portal/my-assets/{id}/         # 更新资产
PATCH  /api/portal/my-assets/{id}/         # 部分更新
DELETE /api/portal/my-assets/{id}/         # 删除资产（软删除）
GET    /api/portal/my-assets/{id}/detail/  # 获取增强详情
GET    /api/portal/my-assets/summary/      # 获取汇总统计

# 批量操作（自动继承）
POST   /api/portal/my-assets/batch-delete/   # 批量删除
POST   /api/portal/my-assets/batch-restore/  # 批量恢复
POST   /api/portal/my-assets/batch-update/   # 批量更新
GET    /api/portal/my-assets/deleted/        # 已删除列表
POST   /api/portal/my-assets/{id}/restore/   # 恢复单个

# 过滤参数
?asset_code=CONTAINS       # 资产编码
?asset_name=CONTAINS       # 资产名称
?asset_status=in_use       # 资产状态
?relation=custodian        # 资产关系
?created_at_from=2024-01-01  # 创建时间起始
?created_at_to=2024-12-31    # 创建时间结束
```

### 12.3 我的申请
```
GET    /api/portal/my-requests/           # 获取我的申请列表
GET    /api/portal/my-requests/{id}/      # 获取申请详情
POST   /api/portal/my-requests/{id}/cancel/  # 取消申请

# 过滤参数
?status=pending              # 申请状态
?type=pickup                # 申请类型
?keyword=搜索关键词         # 搜索
```

### 12.4 我的待办
```
GET    /api/portal/my-tasks/          # 获取我的待办列表
GET    /api/portal/my-tasks/summary/  # 获取待办汇总

# 过滤参数
?task_type=workflow_approval  # 任务类型
?status=pending              # 任务状态
```

---

## 13. 关键特性说明

### 13.1 继承公共基类的优势

通过继承 `apps/common` 模块提供的公共基类，门户模块自动获得以下功能：

**序列化器（继承BaseModelSerializer）**
- ✅ 自动序列化BaseModel的所有公共字段（id, organization, is_deleted等）
- ✅ 自动处理审计字段（created_at, updated_at, created_by）
- ✅ 自动处理custom_fields动态字段
- ✅ 支持嵌套序列化（organization, created_by）

**ViewSet（继承BaseModelViewSetWithBatch）**
- ✅ 自动应用组织隔离（自动过滤当前用户组织的数据）
- ✅ 自动过滤软删除数据（只返回未删除的记录）
- ✅ 自动设置审计字段（创建时设置created_by，更新时设置updated_by）
- ✅ 自动使用软删除（DELETE请求调用soft_delete()而非物理删除）
- ✅ 自动提供批量操作接口（batch_delete, batch_restore, batch_update）
- ✅ 自动提供已删除记录查询（/deleted/接口）
- ✅ 自动提供单个记录恢复（/{id}/restore/接口）

**服务类（继承BaseCRUDService）**
- ✅ 提供标准CRUD方法（create, update, delete, restore, get, query, paginate）
- ✅ 自动处理组织隔离
- ✅ 自动处理软删除
- ✅ 支持复杂查询（过滤、搜索、排序）
- ✅ 支持分页查询

**过滤器（继承BaseModelFilter）**
- ✅ 自动支持公共字段过滤（created_at, updated_at, created_by, is_deleted）
- ✅ 自动支持时间范围查询（created_at_from, created_at_to）
- ✅ 只需定义业务特定的过滤字段

### 13.2 聚合查询模式

门户模块的核心设计理念是**聚合查询**，而非创建新的数据表：

**用户资产聚合**
- 从Asset表查询：保管中的资产（custodian = user）
- 从AssetLoan表查询：借用中的资产
- 从AssetPickup表查询：领用的资产
- 合并去重后返回统一列表

**用户申请聚合**
- 从AssetPickup表查询：资产领用单
- 从AssetTransfer表查询：资产调拨单
- 从AssetReturn表查询：资产退库单
- 从AssetLoan表查询：资产借用单
- 从ConsumableIssue表查询：易耗品领用单
- 从ConsumablePurchase表查询：易耗品采购单
- 统一格式返回

**用户待办聚合**
- 从WorkflowTask表查询：工作流审批任务
- 从InventoryTaskAssignment表查询：盘点任务
- 从AssetReturn表查询：待确认退库（资产管理员）
- 计算即将到期的借用提醒
- 计算待领取资产提醒
- 统一格式返回

### 13.3 移动端优化

- 移动端API返回精简数据（减少网络传输）
- 快捷操作只显示前4个（屏幕空间限制）
- 待办任务只显示前3个（优先级排序）
- 支持二维码扫描查看资产详情

### 13.4 性能优化

- **缓存策略**：门户数据缓存5分钟（PORTAL_CACHE_TIMEOUT）
- **查询优化**：使用select_related减少数据库查询
- **分页查询**：所有列表接口支持分页
- **后台任务**：定期更新统计数据（避免实时计算）

---

## 14. 与NIIMBOT对标

### 14.1 功能对标

| 功能模块 | NIIMBOT | GZEAMS实现 | 状态 |
|---------|---------|-----------|------|
| 我的资产 | ✅ | MyAssetViewSet + UserAssetService | ✅ 已设计 |
| 我的申请 | ✅ | MyRequestViewSet + UserRequestService | ✅ 已设计 |
| 我的待办 | ✅ | MyTaskViewSet + UserTaskService | ✅ 已设计 |
| 门户首页 | ✅ | PortalOverviewView | ✅ 已设计 |
| 移动端门户 | ✅ | MobilePortalView | ✅ 已设计 |
| 扫码查看 | ✅ | 二维码扫描功能（前端实现） | ✅ 已设计 |

### 14.2 UI/UX对标

- ✅ 简洁的门户首页布局
- ✅ 快捷操作入口
- ✅ 待办事项提醒（优先级标识）
- ✅ 移动端优化体验
- ✅ 资产详情展示完整信息

---

## 15. 后续优化方向

### 15.1 功能增强
- [ ] 添加资产搜索建议（自动完成）
- [ ] 添加申请模板功能
- [ ] 添加待办任务日历视图
- [ ] 添加数据导出功能（Excel/PDF）

### 15.2 性能优化
- [ ] 使用Redis缓存热点数据
- [ ] 使用数据库查询优化（索引）
- [ ] 使用CDN加速静态资源
- [ ] 使用异步任务处理复杂聚合

### 15.3 用户体验
- [ ] 添加WebSocket实时通知
- [ ] 添加离线功能支持
- [ ] 添加个性化配置（门户布局自定义）
- [ ] 添加数据可视化（图表统计）

---

## 16. 错误处理机制

### 16.1 服务层错误处理

#### 16.1.1 用户资产服务错误处理

```python
# apps/portal/services/asset_service.py

from decimal import Decimal
from typing import Optional, Dict
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from apps.common.services.base_crud import BaseCRUDService
from apps.assets.models import Asset, AssetPickup, AssetLoan, AssetTransfer

class UserAssetService(BaseCRUDService):
    """用户资产服务 - 增强版错误处理"""

    def get_my_assets(self, user_id: int, filters: Optional[Dict] = None) -> Dict:
        """
        获取用户的资产列表（增强错误处理版）

        异常处理场景：
        1. 用户不存在
        2. 数据库查询错误
        3. 权限验证失败
        4. 查询超时
        """
        from apps.accounts.models import User

        try:
            # 1. 验证用户存在
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise ValueError(f"用户不存在: {user_id}")

            if not user.organization:
                raise ValueError("用户未关联组织")

            # 2. 构建基础查询
            try:
                base_qs = Asset.objects.filter(organization=user.organization)
                base_qs = base_qs.select_related('category', 'location')
                base_qs = base_qs.prefetch_related(
                    'depreciations',
                    'maintenance_records'
                )
            except DatabaseError as e:
                raise DatabaseError(f"数据库查询失败: {str(e)}")

            # 3. 获取各类资产
            try:
                # 直接保管的资产
                custodied_assets = base_qs.filter(custodian=user)

                # 借用中的资产
                borrowed_asset_ids = AssetLoan.objects.filter(
                    borrower=user,
                    status='borrowed'
                ).values_list('items__asset_id', flat=True)

                borrowed_assets = base_qs.filter(id__in=borrowed_asset_ids)

                # 领用的资产
                pickup_asset_ids = AssetPickup.objects.filter(
                    applicant=user,
                    status='completed'
                ).values_list('items__asset_id', flat=True)

                pickup_assets = base_qs.filter(id__in=pickup_asset_ids)

                # 合并去重
                all_assets = (custodied_assets | borrowed_assets | pickup_assets).distinct()

                # 应用过滤
                if filters:
                    all_assets = self._apply_filters(all_assets, filters)

                # 限制查询结果数量，避免内存溢出
                if all_assets.count() > 10000:
                    all_assets = all_assets[:10000]
                    warning = "数据量过大，仅显示前10000条记录"
                else:
                    warning = None

                return {
                    'success': True,
                    'total_count': all_assets.count(),
                    'assets': list(all_assets),
                    'warning': warning
                }

            except DatabaseError as e:
                raise DatabaseError(f"资产查询失败: {str(e)}")

        except PermissionError:
            raise  # 权限错误直接抛出
        except Exception as e:
            if isinstance(e, (ValueError, ValidationError, DatabaseError)):
                raise  # 已知异常直接抛出
            else:
                # 未知异常，记录日志并返回友好提示
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"获取用户资产列表失败: {str(e)}", exc_info=True)
                raise DatabaseError("系统繁忙，请稍后重试")

    def apply_asset_action(self, user_id: int, action: str, asset_id: str, **kwargs) -> Dict:
        """
        应用资产操作（申请、借用、归还等）

        异常处理：
        1. 资产不存在
        2. 权限不足
        3. 业务规则冲突
        4. 并发操作冲突
        """
        from apps.accounts.models import User

        try:
            # 1. 验证用户
            user = User.objects.get(id=user_id)

            # 2. 验证资产
            try:
                asset = Asset.objects.get(id=asset_id, organization=user.organization)
            except Asset.DoesNotExist:
                raise ValueError(f"资产不存在: {asset_id}")

            # 3. 检查权限
            if not self._has_permission(user, action, asset):
                raise PermissionError(f"没有权限执行此操作: {action}")

            # 4. 执行操作
            with transaction.atomic():
                result = self._execute_asset_action(user, asset, action, **kwargs)

                # 记录操作日志
                self._log_asset_action(user, asset, action, result)

                return {
                    'success': True,
                    'message': f'{action}操作成功',
                    'data': result
                }

        except Asset.DoesNotExist:
            raise ValueError(f"资产不存在或无权限访问")
        except PermissionError:
            raise  # 权限错误直接抛出
        except transaction.TransactionManagementError:
            raise DatabaseError("操作失败，请重试")
        except Exception as e:
            if isinstance(e, (ValueError, PermissionError)):
                raise
            else:
                # 业务异常
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"资产操作失败: action={action}, asset_id={asset_id}, error={str(e)}")

                # 根据操作类型返回不同的错误提示
                error_messages = {
                    'pickup': '资产申请失败，请检查资产状态',
                    'loan': '借用操作失败，资产可能已被借出',
                    'return': '归还操作失败，请确认资产信息',
                    'transfer': '调拨操作失败，请联系管理员'
                }

                message = error_messages.get(action, '操作失败，请重试')
                raise ValueError(message)
```

#### 16.1.2 申请服务错误处理

```python
# apps/portal/services/request_service.py

from django.core.exceptions import ValidationError
from django.db import transaction, DatabaseError
from apps.common.services.base_crud import BaseCRUDService
from apps.accounts.models import User
from apps.assets.models import AssetPickup, AssetLoan, AssetTransfer, AssetDisposal
import logging

logger = logging.getLogger(__name__)

class RequestService(BaseCRUDService):
    """申请服务 - 增强版错误处理"""

    REQUEST_TYPES = {
        'pickup': {
            'name': '资产领用',
            'model': AssetPickup,
            'fields': ['asset', 'quantity', 'reason', 'urgency']
        },
        'loan': {
            'name': '资产借用',
            'model': AssetLoan,
            'fields': ['asset', 'borrower', 'loan_date', 'return_date', 'purpose']
        },
        'transfer': {
            'name': '资产调拨',
            'model': AssetTransfer,
            'fields': ['asset', 'from_org', 'to_org', 'reason']
        },
        'disposal': {
            'name': '资产处置',
            'model': AssetDisposal,
            'fields': ['asset', 'disposal_type', 'disposal_reason', 'disposal_date']
        }
    }

    def submit_request(self, user_id: int, request_type: str, data: Dict) -> Dict:
        """
        提交申请（增强错误处理版）

        异常处理场景：
        1. 请求类型不支持
        2. 用户不存在或无权限
        3. 数据验证失败
        4. 业务规则冲突
        5. 并发提交冲突
        """
        try:
            # 1. 验证请求类型
            config = self.REQUEST_TYPES.get(request_type)
            if not config:
                raise ValueError(f'不支持的申请类型: {request_type}')

            # 2. 验证用户
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise ValueError(f'用户不存在: {user_id}')

            # 3. 验证请求数据
            validation_errors = self._validate_request_data(user, request_type, data)
            if validation_errors:
                raise ValidationError(validation_errors)

            # 4. 检查业务规则
            self._check_business_rules(user, request_type, data)

            # 5. 创建申请（事务处理）
            try:
                with transaction.atomic():
                    request_obj = self._create_request(user, request_type, data)

                    # 发送通知
                    self._send_request_notification(request_obj, user, request_type)

                    return {
                        'success': True,
                        'message': f'{config["name"]}申请提交成功',
                        'request_id': str(request_obj.id),
                        'status': request_obj.status
                    }

            except DatabaseError as e:
                logger.error(f"创建申请失败: {str(e)}")
                raise DatabaseError("申请提交失败，请重试")

        except ValueError as e:
            raise  # 参数错误直接抛出
        except ValidationError as e:
            raise  # 验证错误直接抛出
        except PermissionError as e:
            raise  # 权限错误直接抛出
        except Exception as e:
            logger.error(f"提交申请失败: type={request_type}, user_id={user_id}, error={str(e)}")

            # 返回用户友好的错误信息
            error_map = {
                'pickup': '资产领用申请失败，请检查资产可用性',
                'loan': '资产借用申请失败，请确认借用期限',
                'transfer': '资产调拨申请失败，请检查组织信息',
                'disposal': '资产处置申请失败，请联系管理员'
            }

            message = error_map.get(request_type, '申请提交失败，请重试')
            raise ValueError(message)

    def _validate_request_data(self, user: User, request_type: str, data: Dict) -> Dict:
        """验证请求数据"""
        errors = {}
        config = self.REQUEST_TYPES[request_type]

        # 检查必填字段
        for field in config['fields']:
            if field not in data or data[field] is None:
                errors[field] = f'{field} 是必填项'

        # 特定验证规则
        if request_type == 'loan':
            if data.get('return_date') and data.get('loan_date'):
                if data['return_date'] <= data['loan_date']:
                    errors['return_date'] = '归还日期必须晚于借用日期'

        if request_type == 'pickup':
            if data.get('quantity', 0) <= 0:
                errors['quantity'] = '领用数量必须大于0'

        return errors

    def _check_business_rules(self, user: User, request_type: str, data: Dict):
        """检查业务规则"""
        from apps.assets.models import Asset

        if request_type == 'pickup':
            # 检查资产可用性
            asset = Asset.objects.get(id=data['asset'])
            if asset.status not in ['available', 'maintenance']:
                raise ValueError(f'资产当前状态不允许领用: {asset.status}')

        elif request_type == 'loan':
            # 检查借用权限
            if not user.has_perm('assets.can_borrow'):
                raise PermissionError('没有借用权限')

        elif request_type == 'transfer':
            # 检查调拨权限和组织存在性
            from apps.organizations.models import Organization
            try:
                Organization.objects.get(id=data['to_org'])
            except Organization.DoesNotExist:
                raise ValueError('目标组织不存在')
```

### 16.2 API层错误处理

#### 16.2.1 全局异常处理器

```python
# apps/portal/exceptions.py

from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import DatabaseError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)

class PortalAPIException(APIException):
    """用户门户自定义API异常"""
    def __init__(self, detail=None, code=None, user_message=None):
        super().__init__(detail, code)
        self.user_message = user_message or detail

class AssetNotAvailableException(PortalAPIException):
    """资产不可用异常"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '资产当前不可用'
    default_code = 'asset_not_available'

class InsufficientPermissionException(PortalAPIException):
    """权限不足异常"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '权限不足'
    default_code = 'insufficient_permission'

class RequestProcessingException(PortalAPIException):
    """申请处理异常"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '申请处理失败'
    default_code = 'request_processing_failed'

def portal_exception_handler(exc, context):
    """
    用户门户全局异常处理器
    """
    from rest_framework.views import exception_handler

        # 获取请求信息
        request = context.get('request')
        view = context.get('view')

        # DRF默认异常处理
        response = exception_handler(exc, context)

        if response is None:
            # 未被DRF处理的异常
            if isinstance(exc, AssetNotAvailableException):
                response = exception_handler(exc, context)
            elif isinstance(exc, InsufficientPermissionException):
                response = exception_handler(exc, context)
            elif isinstance(exc, RequestProcessingException):
                response = exception_handler(exc, context)
            else:
                # 未知异常
                logger.error(f"未处理的API异常: {str(exc)}", exc_info=True)
                response = {
                    'success': False,
                    'error': {
                        'code': 'INTERNAL_ERROR',
                        'message': '系统繁忙，请稍后重试',
                        'detail': str(exc)  # 开发环境显示详细错误
                    }
                }
                response = Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 统一响应格式
        if response and hasattr(response, 'data'):
            if isinstance(response.data, dict):
                response.data = {
                    'success': not response.status_code >= 400,
                    'data': response.data.get('data') if response.status_code < 400 else None,
                    'error': {
                        'code': response.data.get('code', 'UNKNOWN_ERROR'),
                        'message': response.data.get('detail', str(exc)),
                        'field': response.data.get('field')
                    } if response.status_code >= 400 else None
                }

        return response
```

#### 16.2.2 视图增强错误处理

```python
# apps/portal/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.portal.services.asset_service import UserAssetService
from apps.portal.services.request_service import RequestService
from apps.portal.exceptions import (
    AssetNotAvailableException,
    InsufficientPermissionException,
    RequestProcessingException
)
from apps.portal.serializers import PortalErrorResponseSerializer

class EnhancedAssetViewSet(BaseModelViewSetWithBatch):
    """增强版资产ViewSet - 集成错误处理"""

    def get_exception_handler(self):
        """返回自定义异常处理器"""
        from apps.portal.exceptions import portal_exception_handler
        return portal_exception_handler

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    def get_my_assets(self, request):
        """获取我的资产（增强错误处理）"""
        try:
            user_id = request.user.id
            filters = {
                'status': request.GET.get('status'),
                'category_id': request.GET.get('category_id'),
                'location_id': request.GET.get('location_id')
            }
            # 移除None值
            filters = {k: v for k, v in filters.items() if v}

            service = UserAssetService()
            result = service.get_my_assets(user_id, filters)

            return Response({
                'success': True,
                'data': result
            })

        except AssetNotAvailableException as e:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'ASSET_NOT_AVAILABLE',
                        'message': str(e)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except InsufficientPermissionException as e:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INSUFFICIENT_PERMISSION',
                        'message': str(e)
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            # 捕获所有其他异常
            logger = logging.getLogger(__name__)
            logger.error(f"获取我的资产失败: {str(e)}", exc_info=True)

            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INTERNAL_ERROR',
                        'message': '获取资产列表失败，请重试',
                        'detail': str(e) if settings.DEBUG else None
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def submit_application(self, request):
        """提交申请（增强错误处理）"""
        try:
            # 验证请求参数
            request_type = request.data.get('type')
            application_data = request.data.get('data', {})

            if not request_type:
                raise RequestProcessingException('申请类型不能为空')

            service = RequestService()
            result = service.submit_request(
                user_id=request.user.id,
                request_type=request_type,
                data=application_data
            )

            return Response(result, status=status.HTTP_200_OK)

        except RequestProcessingException as e:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'REQUEST_PROCESSING_ERROR',
                        'message': str(e)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except (AssetNotAvailableException, InsufficientPermissionException) as e:
            # 复用其他异常
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': e.default_code,
                        'message': str(e)
                    }
                },
                status=e.status_code
            )
        except Exception as e:
            logger.error(f"提交申请失败: {str(e)}", exc_info=True)

            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'APPLICATION_SUBMIT_ERROR',
                        'message': '提交申请失败，请重试',
                        'detail': str(e) if settings.DEBUG else None
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### 16.3 Websocket错误处理

#### 16.3.1 实时通知错误处理

```python
# apps/portal/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from apps.common.services.base_crud import BaseCRUDService
import logging

logger = logging.getLogger(__name__)

class PortalNotificationConsumer(AsyncWebsocketConsumer):
    """门户通知WebSocket消费者 - 增强错误处理"""

    async def connect(self):
        """建立连接（增强错误处理）"""
        try:
            # 验证用户认证状态
            if not self.scope.get('user') or not self.scope['user'].is_authenticated:
                await self.close(code=4001, reason="Authentication required")
                return

            user_id = self.scope['user'].id
            self.user_group_name = f'user_{user_id}'

            # 加入用户组
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )

            await self.accept()

            # 发送连接确认
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'WebSocket连接成功'
            }))

            # 启动心跳检测
            self.start_heartbeat()

        except Exception as e:
            logger.error(f"WebSocket连接失败: {str(e)}")
            await self.close(code=4002, reason="Connection failed")

    async def disconnect(self, close_code):
        """断开连接"""
        try:
            if hasattr(self, 'user_group_name'):
                await self.channel_layer.group_discard(
                    self.user_group_name,
                    self.channel_name
                )

            # 停止心跳
            if hasattr(self, 'heartbeat_task'):
                self.heartbeat_task.cancel()

        except Exception as e:
            logger.error(f"WebSocket断开连接失败: {str(e)}")

    async def receive(self, text_data):
        """接收消息（增强错误处理）"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'ping':
                # 心跳响应
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'subscribe':
                # 订阅特定类型的通知
                notification_types = text_data_json.get('types', [])
                await self.handle_subscription(notification_types)
            else:
                logger.warning(f"未知的消息类型: {message_type}")

        except json.JSONDecodeError:
            logger.error("JSON解析失败")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '消息格式错误'
            }))
        except Exception as e:
            logger.error(f"接收WebSocket消息失败: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '处理消息失败'
            }))

    async def notify_application_status(self, event):
        """通知申请状态更新"""
        try:
            message = event['message']

            await self.send(text_data=json.dumps({
                'type': 'application_status',
                'data': message
            }))

        except Exception as e:
            logger.error(f"发送申请状态通知失败: {str(e)}")

    async def notify_asset_reminder(self, event):
        """通知资产提醒"""
        try:
            message = event['message']

            await self.send(text_data=json.dumps({
                'type': 'asset_reminder',
                'data': message
            }))

        except Exception as e:
            logger.error(f"发送资产提醒失败: {str(e)}")

    async def handle_subscription(self, notification_types):
        """处理订阅（增强错误处理）"""
        try:
            valid_types = ['application_status', 'asset_reminder', 'system_notification']
            invalid_types = [t for t in notification_types if t not in valid_types]

            if invalid_types:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'不支持的订阅类型: {invalid_types}'
                }))
                return

            # 存储订阅类型
            if not hasattr(self, 'subscribed_types'):
                self.subscribed_types = set()

            self.subscribed_types.update(notification_types)

            await self.send(text_data=json.dumps({
                'type': 'subscription_confirmed',
                'message': f'已订阅: {notification_types}'
            }))

        except Exception as e:
            logger.error(f"处理订阅失败: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '订阅处理失败'
            }))
```

### 16.4 文件上传错误处理

#### 16.4.1 安全文件上传处理

```python
# apps/portal/utils/file_upload.py

import os
import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
import magic
import logging

logger = logging.getLogger(__name__)

class FileUploadService:
    """文件上传服务 - 增强错误处理"""

    ALLOWED_EXTENSIONS = {
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
        'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'],
        'other': ['zip', 'rar']
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5MB

    def upload_file(self, file_obj, user_id: str, file_type: str = 'other') -> Dict:
        """
        安全文件上传（增强错误处理）

        异常处理场景：
        1. 文件类型不支持
        2. 文件大小超限
        3. 文件内容不安全
        4. 存储空间不足
        5. 并发上传冲突
        """
        try:
            # 1. 验证文件对象
            if not hasattr(file_obj, 'name') or not hasattr(file_obj, 'size'):
                raise ValueError("无效的文件对象")

            # 2. 验证文件大小
            if file_obj.size > self.MAX_FILE_SIZE:
                raise ValueError(f"文件大小不能超过{self.MAX_FILE_SIZE/1024/1024}MB")

            # 3. 验证文件类型
            file_extension = self._get_file_extension(file_obj.name)
            if not self._is_allowed_extension(file_extension, file_type):
                raise ValueError(f"不支持的文件类型: {file_extension}")

            # 4. 验证文件内容（防止伪装）
            file_mime = self._get_file_mime(file_obj)
            if not self._is_valid_mime(file_extension, file_mime):
                raise ValueError("文件类型与内容不匹配")

            # 5. 生成安全的文件名
            safe_filename = self._generate_safe_filename(file_extension, user_id)

            # 6. 创建存储目录
            upload_dir = Path(settings.MEDIA_ROOT) / 'portal_uploads' / str(user_id)
            try:
                upload_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ValueError(f"无法创建存储目录: {str(e)}")

            # 7. 检查磁盘空间
            if not self._check_disk_space(upload_dir, file_obj.size):
                raise ValueError("存储空间不足")

            # 8. 保存文件
            file_path = upload_dir / safe_filename
            try:
                with open(file_path, 'wb') as f:
                    # 分块读取，避免内存溢出
                    for chunk in file_obj.chunks():
                        f.write(chunk)

                # 9. 生成访问URL
                file_url = f'/media/portal_uploads/{user_id}/{safe_filename}'

                return {
                    'success': True,
                    'file_url': file_url,
                    'file_path': str(file_path),
                    'file_name': safe_filename,
                    'file_size': file_obj.size,
                    'mime_type': file_mime
                }

            except OSError as e:
                # 清理已创建的目录
                if upload_dir.exists():
                    try:
                        upload_dir.rmdir()
                    except:
                        pass
                raise ValueError(f"文件保存失败: {str(e)}")

        except ValueError as e:
            raise  # 参数错误直接抛出
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}", exc_info=True)
            raise ValueError("文件上传失败，请重试")

    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        if not filename or '.' not in filename:
            raise ValueError("无效的文件名")

        extension = filename.split('.')[-1].lower()

        # 清理恶意扩展名
        extension = extension.replace('.', '').replace('/', '').replace('\\', '')

        return extension[:10]  # 限制长度

    def _is_allowed_extension(self, extension: str, file_type: str) -> bool:
        """检查扩展名是否允许"""
        allowed_extensions = self.ALLOWED_EXTENSIONS.get(file_type, self.ALLOWED_EXTENSIONS['other'])
        return extension in allowed_extensions

    def _get_file_mime(self, file_obj) -> str:
        """获取文件MIME类型"""
        try:
            # 使用python-magic库检测真实的文件类型
            file_obj.seek(0)  # 重置指针
            mime_type = magic.from_buffer(file_obj.read(1024), mime=True)
            file_obj.seek(0)  # 再次重置
            return mime_type
        except:
            # 如果magic库不可用，使用Django的默认检测
            return file_obj.content_type or 'application/octet-stream'

    def _is_valid_mime(self, extension: str, mime_type: str) -> bool:
        """验证MIME类型与扩展名是否匹配"""
        mime_mapping = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'txt': 'text/plain'
        }

        expected_mime = mime_mapping.get(extension)
        if not expected_mime:
            return True  # 未知类型，允许通过

        return mime_type == expected_mime

    def _generate_safe_filename(self, extension: str, user_id: str) -> str:
        """生成安全的文件名"""
        unique_id = uuid.uuid4().hex[:8]
        return f"{user_id}_{unique_id}.{extension}"

    def _check_disk_space(self, directory: Path, file_size: int) -> bool:
        """检查磁盘空间"""
        try:
            stat = os.statvfs(str(directory.parent))
            available_space = stat.f_frsize * stat.f_bavail
            return available_space > file_size * 2  # 要求剩余空间是文件大小的2倍
        except:
            return True  # 如果无法检查，假设有足够空间
```

### 16.5 日志记录和监控

#### 16.5.1 错误日志记录

```python
# apps/portal/utils/logging.py

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from django.db.models import Model

class PortalAuditLogger:
    """门户审计日志记录器"""

    def __init__(self):
        self.logger = logging.getLogger('portal_audit')

    def log_asset_action(self, user: User, asset: Model, action: str,
                       details: Dict = None, success: bool = True, error: str = None):
        """
        记录资产操作日志

        Args:
            user: 操作用户
            asset: 资产对象
            action: 操作类型
            details: 操作详情
            success: 是否成功
            error: 错误信息
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user.id,
                'user_name': user.username,
                'organization_id': user.organization_id if user.organization else None,
                'action': action,
                'resource_type': asset.__class__.__name__,
                'resource_id': str(asset.id),
                'resource_name': getattr(asset, 'name', str(asset.id)),
                'success': success,
                'details': details or {},
                'error': error,
                'ip_address': getattr(user, 'last_login', None)
            }

            if success:
                self.logger.info(f"资产操作成功: {log_entry}")
            else:
                self.logger.error(f"资产操作失败: {log_entry}")

        except Exception as e:
            self.logger.error(f"记录资产操作日志失败: {str(e)}")

    def log_api_request(self, request, response=None, error=None):
        """记录API请求日志"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'path': request.path,
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self._get_client_ip(request),
                'params': dict(request.GET) if request.method == 'GET' else dict(request.POST),
                'success': error is None,
                'error': str(error) if error else None,
                'response_status': getattr(response, 'status_code', None) if response else None
            }

            if error:
                self.logger.error(f"API请求失败: {log_entry}")
            else:
                self.logger.info(f"API请求: {log_entry}")

        except Exception as e:
            self.logger.error(f"记录API请求日志失败: {str(e)}")

    def log_security_event(self, event_type: str, user: User, details: Dict,
                         severity: str = 'medium'):
        """
        记录安全事件

        Args:
            event_type: 事件类型
            user: 用户
            details: 事件详情
            severity: 严重程度 (low, medium, high, critical)
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'severity': severity,
                'user_id': user.id,
                'user_name': user.username,
                'organization_id': user.organization_id if user.organization else None,
                'ip_address': self._get_client_ip(getattr(user, 'request', None)),
                'details': details
            }

            # 根据严重程度选择日志级别
            if severity == 'critical':
                self.logger.critical(f"安全事件[严重]: {log_entry}")
            elif severity == 'high':
                self.logger.error(f"安全事件[高]: {log_entry}")
            elif severity == 'medium':
                self.logger.warning(f"安全事件[中]: {log_entry}")
            else:
                self.logger.info(f"安全事件[低]: {log_entry}")

        except Exception as e:
            self.logger.error(f"记录安全事件失败: {str(e)}")

    def _get_client_ip(self, request) -> Optional[str]:
        """获取客户端IP地址"""
        if not request:
            return None

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        return ip

# 全局审计日志实例
audit_logger = PortalAuditLogger()
```

### 16.6 数据验证和安全

#### 16.6.1 输入数据验证增强

```python
# apps/portal/validators.py

from rest_framework import serializers
from django.core.validators import validate_email, validate_slug
from django.utils.translation import gettext_lazy as _
import re
from typing import Any, Dict

class SafeInputValidator:
    """安全输入验证器"""

    @staticmethod
    def validate_username(value: str) -> str:
        """验证用户名安全性"""
        if not value:
            raise serializers.ValidationError("用户名不能为空")

        # 长度限制
        if len(value) < 3 or len(value) > 50:
            raise serializers.ValidationError("用户名长度必须在3-50个字符之间")

        # 字符限制（只允许字母、数字、下划线）
        if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$', value):
            raise serializers.ValidationError("用户名只能包含字母、数字、下划线和中文")

        # 检查危险字符
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed'
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise serializers.ValidationError("用户名包含不安全字符")

        return value

    @staticmethod
    def validate_reason(value: str) -> str:
        """验证申请原因"""
        if not value:
            raise serializers.ValidationError("申请原因不能为空")

        # 长度限制
        if len(value) > 500:
            raise serializers.ValidationError("申请原因不能超过500个字符")

        # 检查SQL注入
        sql_patterns = [
            r'(union|select|insert|update|delete|drop|create|alter|exec|execute)',
            r'(\s|--|#|\/\*|\*\/)',
            r'(or\s+1\s*=\s*1)',
            r'(and\s+1\s*=\s*1)',
            r'(waitfor\s+delay)',
            r'(xp_cmdshell|sp_oacreate)'
        ]

        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise serializers.ValidationError("申请原因包含不安全内容")

        return value.strip()

    @staticmethod
    def validate_phone_number(value: str) -> str:
        """验证手机号码"""
        if not value:
            raise serializers.ValidationError("手机号码不能为空")

        # 中国手机号码正则
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError("请输入有效的手机号码")

        return value

    @staticmethod
    def validate_asset_quantity(value: int) -> int:
        """验证资产数量"""
        if value is None:
            raise serializers.ValidationError("数量不能为空")

        if not isinstance(value, int):
            raise serializers.ValidationError("数量必须是整数")

        if value <= 0:
            raise serializers.ValidationError("数量必须大于0")

        if value > 1000:
            raise serializers.ValidationError("单次操作数量不能超过1000")

        return value

class XSSProtectionMiddleware:
    """XSS保护中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 处理POST数据
        if request.method == 'POST':
            self._clean_post_data(request)

        response = self.get_response(request)
        return response

    def _clean_post_data(self, request):
        """清理POST数据"""
        from django.http import QueryDict

        # 清理表单数据
        if hasattr(request, 'POST'):
            cleaned_data = QueryDict('', encoding=request.encoding)
            for key, value in request.POST.items():
                cleaned_data[key] = self._clean_value(value)
            request.POST = cleaned_data

        # 清理JSON数据
        if hasattr(request, 'body'):
            try:
                import json
                data = json.loads(request.body)
                if isinstance(data, dict):
                    cleaned_data = {}
                    for key, value in data.items():
                        cleaned_data[key] = self._clean_value(value)
                    request._body = json.dumps(cleaned_data).encode()
                elif isinstance(data, list):
                    cleaned_data = [self._clean_value(item) for item in data]
                    request._body = json.dumps(cleaned_data).encode()
            except:
                pass  # 如果不是JSON数据，保持原样

    def _clean_value(self, value):
        """清理单个值"""
        if not isinstance(value, str):
            return value

        # 移除危险标签
        value = re.sub(r'<[^>]*>', '', value)

        # HTML实体编码
        value = value.replace('&', '&amp;')
        value = value.replace('<', '&lt;')
        value = value.replace('>', '&gt;')
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#x27;')

        return value
```

---

**文档更新日志**
- 2024-01-15: 更新所有代码示例使用新的公共基类（BaseModelSerializer、BaseModelViewSetWithBatch、BaseCRUDService、BaseModelFilter）
- 2024-01-16: 添加完整的错误处理机制，包括服务层、API层、WebSocket、文件上传和日志记录

