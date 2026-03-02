# Phase 7.1: 资产借用/外借增强 - 后端实现

## 1. 功能概述

### 1.1 业务场景

在现有Phase 1.5资产借用功能基础上，扩展对外借出、押金管理、超期计费、信用管理能力，实现资产借用的全生命周期管理。

| 业务类型 | 场景 | 核心价值 |
|---------|------|----------|
| **内部借用（增强）** | 员工临时借用，增加超期提醒和计费 | 提高资产周转率 |
| **对外借出** | 借给外部单位/个人 | 追踪资产流向，降低流失风险 |
| **押金管理** | 外借时收取押金，归还后退还 | 财务风险控制 |
| **超期计费** | 超期后按天计费 | 促进及时归还 |
| **信用管理** | 记录借用人信用 | 风险评估，决策支持 |

### 1.2 用户角色与权限

| 角色 | 权限 |
|------|------|
| **系统管理员** | 配置外部人员对象、计费规则、信用规则 |
| **资产管理员** | 审批借用、管理押金、查看所有记录、修改信用 |
| **仓库管理员** | 确认借出/归还、验收资产状况 |
| **财务人员** | 查看押金记录、确认退款、查看计费 |
| **普通员工** | 发起内部借用申请、查看自己的记录 |
| **外部人员** | 无系统账号，通过管理员操作 |

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

### 2.2 继承关系示例

```python
# ✅ 所有业务单据模型继承 BaseModel
class LoanDeposit(BaseModel):
    """押金记录 - 自动获得组织隔离、软删除、审计字段"""
    loan = models.ForeignKey('AssetLoan', on_delete=models.PROTECT)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    # ... 其他业务字段

# ✅ 序列化器继承 BaseModelSerializer
class LoanDepositSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = LoanDeposit
        fields = BaseModelSerializer.Meta.fields + ['loan', 'deposit_amount', ...]

# ✅ 服务层继承 BaseCRUDService
class LoanDepositService(BaseCRUDService):
    def __init__(self):
        super().__init__(LoanDeposit)

# ✅ ViewSet继承 BaseModelViewSetWithBatch
class LoanDepositViewSet(BaseModelViewSetWithBatch):
    """自动获得: 组织过滤、软删除、批量操作"""
    queryset = LoanDeposit.objects.all()
    serializer_class = LoanDepositSerializer
```

---

## 3. 数据模型设计

### 3.1 AssetLoan 模型改造

**改造说明**：在现有AssetLoan模型基础上增加字段，保持向后兼容。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **新增字段** |
| borrower_type | string | max_length=20, default='internal' | 借用类型: internal/external |
| borrower_external_id | string | max_length=50, null=True, blank=True | 关联DynamicData.id（外部借用时） |
| borrower_name | string | max_length=200, null=True, blank=True | 借用人姓名（冗余显示） |
| borrower_phone | string | max_length=50, null=True, blank=True | 借用人电话（冗余显示） |
| borrower_company | string | max_length=200, null=True, blank=True | 借用人单位（冗余显示） |
| enable_deposit | boolean | default=False | 是否需要押金 |
| enable_overdue_fee | boolean | default=False | 是否启用超期计费 |
| **现有字段（保持不变）** |
| loan_no | string | max_length=50, unique, db_index | 借用单号 |
| borrower | FK(User) | PROTECT, null=True | 借用人（内部使用） |
| borrow_date | date | - | 借出日期 |
| expected_return_date | date | - | 预计归还日期 |
| actual_return_date | date | null=True | 实际归还日期 |
| loan_reason | text | blank=True | 借用原因 |
| status | string | max_length=20, choices | 状态 |
| approved_by | FK(User) | SET_NULL, null=True | 审批人 |
| lent_by | FK(User) | SET_NULL, null=True | 借出确认人 |
| returned_by | FK(User) | SET_NULL, null=True | 归还确认人（新增字段） |
| returned_at | datetime | null=True | 归还时间 |
| asset_condition | string | max_length=20, choices | 归还时资产状况 |

**状态扩展**：

| 状态值 | 说明 | 适用类型 |
|--------|------|---------|
| draft | 草稿 | 全部 |
| pending | 待审批 | 全部 |
| approved | 已批准 | 全部 |
| borrowed | 借出中 | 全部 |
| returned | 已归还 | 全部 |
| overdue | 已逾期 | 全部 |
| rejected | 已拒绝 | 全部 |
| cancelled | 已取消 | 全部 |

**数据库迁移**：

```python
# migration file
operations = [
    migrations.AddField(
        model_name='assetloan',
        name='borrower_type',
        field=models.CharField(
            max_length=20,
            default='internal',
            choices=[('internal', '内部借用'), ('external', '对外借出')]
        ),
    ),
    migrations.AddField(
        model_name='assetloan',
        name='borrower_external_id',
        field=models.CharField(max_length=50, null=True, blank=True),
    ),
    migrations.AddField(
        model_name='assetloan',
        name='borrower_name',
        field=models.CharField(max_length=200, null=True, blank=True),
    ),
    migrations.AddField(
        model_name='assetloan',
        name='borrower_phone',
        field=models.CharField(max_length=50, null=True, blank=True),
    ),
    migrations.AddField(
        model_name='assetloan',
        name='borrower_company',
        field=models.CharField(max_length=200, null=True, blank=True),
    ),
    migrations.AddField(
        model_name='assetloan',
        name='enable_deposit',
        field=models.BooleanField(default=False),
    ),
    migrations.AddField(
        model_name='assetloan',
        name='enable_overdue_fee',
        field=models.BooleanField(default=False),
    ),
    migrations.AddField(
        model_name='assetloan',
        name='returned_by',
        field=models.ForeignKey(
            'accounts.User',
            on_delete=models.SET_NULL,
            null=True,
            related_name='confirmed_returns'
        ),
    ),
]
```

### 3.2 LoanDeposit（押金记录）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| loan | FK(AssetLoan) | PROTECT, related_name='deposits' | 借用单 |
| **基础信息** |
| deposit_no | string | max_length=50, unique, db_index | 押金单号 (YJ+YYYYMM+序号) |
| deposit_amount | DecimalField | max_digits=12, decimal_places=2 | 押金金额 |
| deposit_date | date | - | 收取日期 |
| payment_method | string | max_length=20, choices | 收取方式: cash/transfer/check/other |
| payment_account | string | max_length=100, blank=True | 收款账户 |
| **状态** |
| deposit_status | string | max_length=20, choices | 状态: collected/refunded/cancelled |
| **退款信息** |
| refunded_date | date | null=True | 退款日期 |
| refunded_amount | DecimalField | max_digits=12, decimal_places=2, null=True | 退款金额 |
| refund_reason | text | blank=True | 退款说明 |
| refund_voucher | FileField | upload_to='deposit_vouchers/', null=True | 退款凭证 |
| refunded_by | FK(User) | SET_NULL, null=True, related_name='refunded_deposits' | 退款操作人 |

**状态说明**：

```
collected (已收取) → refunded (已退还)
                → cancelled (已作废，如借用取消时)
```

**索引**：
- `loan + deposit_status`
- `deposit_date`

### 3.3 LoanFeeRule（计费规则配置）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **基础信息** |
| name | string | max_length=100 | 规则名称 |
| code | string | max_length=50, unique | 规则编码 |
| rule_type | string | max_length=20, choices | 计费类型: daily/tiered |
| is_active | boolean | default=True | 是否启用 |
| **按日计费（daily）** |
| daily_rate | DecimalField | max_digits=12, decimal_places=4 | 每日费率（元/天） |
| **阶梯计费（tiered）** |
| tier_config | JSONField | default=dict | 阶梯配置 |
| **适用范围** |
| apply_to_internal | boolean | default=False | 是否适用于内部借用 |
| apply_to_external | boolean | default=True | 是否适用于对外借用 |
| min_overdue_days | int | default=1 | 最小计费天数 |
| max_fee | DecimalField | max_digits=12, decimal_places=2, null=True | 最高计费限额 |
| **计费币种** |
| currency | string | max_length=10, default='CNY' | 币种 |

**阶梯配置示例**：

```json
{
  "tiers": [
    {"days_start": 1, "days_end": 7, "daily_rate": 10.00},
    {"days_start": 8, "days_end": 30, "daily_rate": 20.00},
    {"days_start": 31, "days_end": null, "daily_rate": 50.00}
  ]
}
```

### 3.4 LoanOverdueFee（超期计费记录）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| loan | FK(AssetLoan) | PROTECT, related_name='overdue_fees' | 借用单 |
| fee_rule | FK(LoanFeeRule) | PROTECT, related_name='fee_records' | 计费规则 |
| **计费信息** |
| calculation_date | date | db_index | 计算日期 |
| overdue_days | int | - | 超期天数 |
| unit_price | DecimalField | max_digits=12, decimal_places=4 | 单价 |
| calculated_fee | DecimalField | max_digits=12, decimal_places=2 | 计算费用 |
| **费用处理** |
| waived_fee | DecimalField | max_digits=12, decimal_places=2, default=0 | 豁免费用 |
| actual_fee | DecimalField | max_digits=12, decimal_places=2 | 实际费用 |
| fee_status | string | max_length=20, choices | 状态: pending/collected/waived/cancelled |
| **收款信息** |
| collected_date | date | null=True | 收款日期 |
| collected_by | FK(User) | SET_NULL, null=True | 收款操作人 |
| waive_reason | text | blank=True | 豁免原因 |
| waive_approved_by | FK(User) | SET_NULL, null=True | 豁免审批人 |

### 3.5 BorrowerCredit（借用人信用）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **借用人关联（二选一）** |
| borrower_type | string | max_length=20, choices | internal/external |
| borrower_user | FK(User) | SET_NULL, null=True, unique=True | 内部用户 |
| borrower_external_id | string | max_length=50, null=True, unique=True | 外部人员ID |
| **信用评分** |
| credit_score | int | default=100 | 信用分（0-100） |
| credit_level | string | max_length=20, choices | 信用等级 |
| **统计信息** |
| total_loan_count | int | default=0 | 总借用次数 |
| normal_return_count | int | default=0 | 正常归还次数 |
| overdue_count | int | default=0 | 超期次数 |
| damage_count | int | default=0 | 损坏次数 |
| lost_count | int | default=0 | 遗失次数 |
| **信用历史** |
| last_overdue_days | int | null=True | 最近一次超期天数 |
| total_overdue_days | int | default=0 | 累计超期天数 |
| **更新信息** |
| last_updated_at | datetime | auto_now=True | 最后更新时间 |
| last_updated_by | FK(User) | SET_NULL, null=True | 最后更新人 |

**信用等级定义**：

| 等级 | 分数范围 | 说明 |
|------|---------|------|
| excellent | 90-100 | 优秀 |
| good | 75-89 | 良好 |
| normal | 60-74 | 一般 |
| poor | 40-59 | 较差 |
| blacklisted | 0-39 | 黑名单 |

**数据库约束**：
- `borrower_user` 和 `borrower_external_id` 二选一必填
- 添加唯一约束：`(borrower_user, organization)` 或 `(borrower_external_id, organization)`

### 3.6 CreditHistory（信用历史记录）

**Model Definition**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| credit | FK(BorrowerCredit) | CASCADE, related_name='histories' | 信用记录 |
| loan | FK(AssetLoan) | SET_NULL, null=True | 关联借用单 |
| **事件信息** |
| event_type | string | max_length=50, choices | 事件类型 |
| event_date | date | db_index | 事件日期 |
| score_change | int | - | 分数变化（正数加分，负数减分） |
| score_after | int | - | 变化后分数 |
| **详情** |
| event_description | text | - | 事件描述 |
| related_asset | FK(Asset) | SET_NULL, null=True | 关联资产 |

**事件类型定义**：

| 事件类型 | 分数变化 | 说明 |
|---------|---------|------|
| loan_created | 0 | 创建借用申请 |
| loan_approved | 0 | 借用批准 |
| returned_normal | +2 | 正常归还（未超期） |
| returned_overdue_short | 0 | 超期1-7天归还 |
| returned_overdue_long | -5 | 超期7-30天归还 |
| returned_overdue_severe | -15 | 超期30天以上归还 |
| asset_damaged_minor | -5 | 资产轻微损坏 |
| asset_damaged_severe | -20 | 资产严重损坏 |
| asset_lost | -50 | 资产遗失 |
| credit_manual_adjust | ±N | 手动调整 |

### 3.7 ExternalPerson 低代码业务对象配置

虽然外部人员通过低代码引擎管理，但需要在PRD中定义预置配置：

**BusinessObject 配置**：

| 字段 | 值 |
|------|---|
| code | ExternalPerson |
| name | 外部人员 |
| enable_workflow | False |
| enable_version | True |
| enable_soft_delete | True |
| table_name | external_person_data |

**FieldDefinition 预置字段**：

| 字段编码 | 字段名称 | 字段类型 | 必填 | 说明 |
|---------|---------|---------|------|------|
| person_name | 姓名/单位名称 | text | ✅ | |
| person_type | 类型 | select | ✅ | 选项: 个人/单位 |
| phone | 联系电话 | text | ✅ | |
| id_card | 身份证号/信用代码 | text | ✅ | 个人为身份证，单位为统一社会信用代码 |
| company_name | 单位名称 | text | ⚪ | 单位类型时必填 |
| credit_code | 统一社会信用代码 | text | ⚪ | |
| bank_account | 银行账号 | text | ⚪ | 退押金用 |
| bank_name | 开户银行 | text | ⚪ | |
| address | 地址 | text | ⚪ | |
| contact_person | 联系人 | text | ⚪ | 单位类型的联系人 |
| contact_phone | 联系人电话 | text | ⚪ | |
| notes | 备注 | textarea | ⚪ | |

**初始化SQL**：

```sql
-- 创建BusinessObject
INSERT INTO business_object (code, name, enable_workflow, organization_id)
VALUES ('ExternalPerson', '外部人员', false, {org_id});

-- 创建FieldDefinition（部分示例）
INSERT INTO field_definition (
    business_object_id, code, name, field_type, is_required, sort_order
)
VALUES
    ({bo_id}, 'person_name', '姓名/单位名称', 'text', true, 1),
    ({bo_id}, 'person_type', '类型', 'select', true, 2),
    ({bo_id}, 'phone', '联系电话', 'text', true, 3),
    ({bo_id}, 'id_card', '身份证号/信用代码', 'text', true, 4);
```

---

## 4. 序列化器设计

### 4.1 AssetLoanSerializer（改造）

```python
from apps.common.serializers.base import BaseModelSerializer
from apps.accounts.serializers import UserSerializer

class AssetLoanSerializer(BaseModelSerializer):
    """资产借用单序列化器（扩展支持对外借出）"""

    # 现有字段
    borrower_detail = UserSerializer(source='borrower', read_only=True)
    approved_by_detail = UserSerializer(source='approved_by', read_only=True)
    lent_by_detail = UserSerializer(source='lent_by', read_only=True)
    returned_by_detail = UserSerializer(source='returned_by', read_only=True)

    # 新增字段
    borrower_external_detail = serializers.SerializerMethodField()
    deposit_status = serializers.SerializerMethodField()
    overdue_fee_total = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    overdue_days = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetLoan
        fields = BaseModelSerializer.Meta.fields + [
            # 现有字段
            'loan_no', 'borrower', 'borrower_detail', 'borrow_date',
            'expected_return_date', 'actual_return_date', 'loan_reason',
            'status', 'approved_by', 'approved_by_detail', 'approved_at',
            'lent_by', 'lent_by_detail', 'lent_at',
            'returned_by', 'returned_by_detail', 'returned_at',
            'asset_condition', 'items',
            # 新增字段
            'borrower_type', 'borrower_external_id', 'borrower_external_detail',
            'borrower_name', 'borrower_phone', 'borrower_company',
            'enable_deposit', 'enable_overdue_fee',
            'deposit_status', 'overdue_fee_total', 'is_overdue', 'overdue_days',
        ]

    def get_borrower_external_detail(self, obj):
        """获取外部借用人详情"""
        if obj.borrower_type == 'external' and obj.borrower_external_id:
            from apps.system.services import DynamicDataService
            service = DynamicDataService()
            external_person = service.get_by_id(obj.borrower_external_id)
            if external_person:
                return {
                    'id': external_person.id,
                    'name': external_person.dynamic_fields.get('person_name'),
                    'type': external_person.dynamic_fields.get('person_type'),
                    'phone': external_person.dynamic_fields.get('phone'),
                    'company': external_person.dynamic_fields.get('company_name'),
                }
        return None

    def get_deposit_status(self, obj):
        """获取押金状态"""
        if not obj.enable_deposit:
            return None
        deposit = obj.deposits.filter(deposit_status='collected').first()
        if deposit:
            return {
                'amount': str(deposit.deposit_amount),
                'date': deposit.deposit_date,
                'status': deposit.deposit_status,
            }
        return None

    def get_overdue_fee_total(self, obj):
        """获取总超期费用"""
        if obj.status not in ['overdue', 'returned']:
            return '0.00'
        total = obj.overdue_fees.filter(fee_status='pending').aggregate(
            total=models.Sum('actual_fee')
        )['total'] or 0
        return str(total)

    def get_is_overdue(self, obj):
        """是否超期"""
        if obj.expected_return_date and obj.status not in ['returned', 'cancelled', 'rejected']:
            return timezone.now().date() > obj.expected_return_date
        return False
```

### 4.2 LoanDepositSerializer

```python
class LoanDepositSerializer(BaseModelSerializer):
    """押金记录序列化器"""

    loan_no = serializers.CharField(source='loan.loan_no', read_only=True)
    borrower_name = serializers.CharField(source='loan.borrower_name', read_only=True)
    refunded_by_detail = UserSerializer(source='refunded_by', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = LoanDeposit
        fields = BaseModelSerializer.Meta.fields + [
            'loan', 'loan_no', 'borrower_name',
            'deposit_no', 'deposit_amount', 'deposit_date',
            'payment_method', 'payment_account',
            'deposit_status',
            'refunded_date', 'refunded_amount', 'refund_reason',
            'refund_voucher', 'refunded_by', 'refunded_by_detail',
        ]

class LoanDepositCreateSerializer(serializers.Serializer):
    """押金收取创建序列化器"""

    loan_id = serializers.UUIDField(required=True)
    deposit_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    payment_method = serializers.ChoiceField(
        choices=['cash', 'transfer', 'check', 'other'],
        required=True
    )
    payment_account = serializers.CharField(max_length=100, required=False, allow_blank=True)
    deposit_date = serializers.DateField(required=False)
    voucher = serializers.FileField(required=False, allow_null=True)

    def validate_loan_id(self, value):
        """验证借用单"""
        loan = AssetLoan.objects.filter(id=value).first()
        if not loan:
            raise serializers.ValidationError("借用单不存在")
        if not loan.enable_deposit:
            raise serializers.ValidationError("该借用单未启用押金")
        if loan.deposits.filter(deposit_status='collected').exists():
            raise serializers.ValidationError("该借用单已收取押金")
        return value

    def validate_deposit_amount(self, value):
        """验证押金金额"""
        if value <= 0:
            raise serializers.ValidationError("押金金额必须大于0")
        return value
```

### 4.3 LoanOverdueFeeSerializer

```python
class LoanOverdueFeeSerializer(BaseModelSerializer):
    """超期计费记录序列化器"""

    loan_no = serializers.CharField(source='loan.loan_no', read_only=True)
    fee_rule_name = serializers.CharField(source='fee_rule.name', read_only=True)
    collected_by_detail = UserSerializer(source='collected_by', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = LoanOverdueFee
        fields = BaseModelSerializer.Meta.fields + [
            'loan', 'loan_no', 'fee_rule', 'fee_rule_name',
            'calculation_date', 'overdue_days', 'unit_price',
            'calculated_fee', 'waived_fee', 'actual_fee', 'fee_status',
            'collected_date', 'collected_by', 'collected_by_detail',
            'waive_reason', 'waive_approved_by',
        ]
```

### 4.4 BorrowerCreditSerializer

```python
class BorrowerCreditSerializer(BaseModelSerializer):
    """借用人信用序列化器"""

    borrower_name = serializers.SerializerMethodField()
    borrower_info = serializers.SerializerMethodField()
    credit_level_display = serializers.CharField(source='get_credit_level_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = BorrowerCredit
        fields = BaseModelSerializer.Meta.fields + [
            'borrower_type', 'borrower_user', 'borrower_external_id',
            'borrower_name', 'borrower_info',
            'credit_score', 'credit_level', 'credit_level_display',
            'total_loan_count', 'normal_return_count', 'overdue_count',
            'damage_count', 'lost_count',
            'last_overdue_days', 'total_overdue_days',
            'last_updated_at', 'last_updated_by',
        ]

    def get_borrower_name(self, obj):
        """获取借用人姓名"""
        if obj.borrower_type == 'internal' and obj.borrower_user:
            return obj.borrower_user.get_full_name() or obj.borrower_user.username
        elif obj.borrower_type == 'external' and obj.borrower_external_id:
            from apps.system.services import DynamicDataService
            service = DynamicDataService()
            external_person = service.get_by_id(obj.borrower_external_id)
            if external_person:
                return external_person.dynamic_fields.get('person_name')
        return None

    def get_borrower_info(self, obj):
        """获取借用人详细信息"""
        if obj.borrower_type == 'internal' and obj.borrower_user:
            return {
                'type': 'internal',
                'user_id': obj.borrower_user.id,
                'username': obj.borrower_user.username,
                'full_name': obj.borrower_user.get_full_name(),
                'email': obj.borrower_user.email,
                'department': obj.borrower_user.get_department_name(),
            }
        elif obj.borrower_type == 'external' and obj.borrower_external_id:
            from apps.system.services import DynamicDataService
            service = DynamicDataService()
            external_person = service.get_by_id(obj.borrower_external_id)
            if external_person:
                return {
                    'type': 'external',
                    'external_id': obj.borrower_external_id,
                    'name': external_person.dynamic_fields.get('person_name'),
                    'person_type': external_person.dynamic_fields.get('person_type'),
                    'phone': external_person.dynamic_fields.get('phone'),
                    'company': external_person.dynamic_fields.get('company_name'),
                }
        return None

class CreditHistorySerializer(BaseModelSerializer):
    """信用历史序列化器"""

    loan_no = serializers.CharField(source='loan.loan_no', read_only=True)
    asset_name = serializers.CharField(source='related_asset.name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = CreditHistory
        fields = BaseModelSerializer.Meta.fields + [
            'credit', 'loan', 'loan_no', 'related_asset', 'asset_name',
            'event_type', 'event_type_display', 'event_date',
            'score_change', 'score_after', 'event_description',
        ]
```

---

## 5. ViewSet 设计

### 5.1 AssetLoanViewSet（扩展）

```python
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.loans.services import AssetLoanService, LoanDepositService

class AssetLoanViewSet(BaseModelViewSetWithBatch):
    """资产借用单ViewSet（扩展支持对外借出）"""

    queryset = AssetLoan.objects.select_related(
        'borrower', 'approved_by', 'lent_by', 'returned_by'
    ).prefetch_related('items__asset', 'deposits', 'overdue_fees')
    serializer_class = AssetLoanSerializer
    filterset_class = AssetLoanFilter
    service = AssetLoanService()

    def get_queryset(self):
        """获取查询集（自动过滤组织）"""
        queryset = super().get_queryset()

        # 根据borrower_type过滤
        borrower_type = self.request.query_params.get('borrower_type')
        if borrower_type:
            queryset = queryset.filter(borrower_type=borrower_type)

        # 超期筛选
        is_overdue = self.request.query_params.get('is_overdue')
        if is_overdue == 'true':
            from django.utils import timezone
            today = timezone.now().date()
            queryset = queryset.filter(
                expected_return_date__lt=today,
                status__in=['borrowed', 'overdue']
            )

        return queryset

    @action(detail=True, methods=['post'])
    def collect_deposit(self, request, pk=None):
        """收取押金"""
        loan = self.get_object()
        serializer = LoanDepositCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        deposit = self.service.collect_deposit(
            loan=loan,
            amount=serializer.validated_data['deposit_amount'],
            payment_method=serializer.validated_data['payment_method'],
            payment_account=serializer.validated_data.get('payment_account', ''),
            operator=request.user
        )

        return Response({
            'success': True,
            'message': '押金收取成功',
            'data': LoanDepositSerializer(deposit).data
        })

    @action(detail=True, methods=['post'])
    def refund_deposit(self, request, pk=None):
        """退还押金"""
        loan = self.get_object()
        amount = request.data.get('amount')
        reason = request.data.get('reason', '')
        voucher = request.files.get('voucher')

        if not amount:
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': '请输入退款金额'}
            }, status=400)

        deposit = self.service.refund_deposit(
            loan=loan,
            amount=Decimal(amount),
            reason=reason,
            voucher=voucher,
            operator=request.user
        )

        return Response({
            'success': True,
            'message': '押金退还成功',
            'data': LoanDepositSerializer(deposit).data
        })

    @action(detail=True, methods=['post'])
    def calculate_overdue_fee(self, request, pk=None):
        """计算超期费用"""
        loan = self.get_object()
        fees = self.service.calculate_overdue_fee(loan)

        return Response({
            'success': True,
            'message': '费用计算完成',
            'data': {
                'overdue_days': fees.get('overdue_days', 0),
                'total_fee': str(fees.get('total_fee', 0)),
                'fee_details': LoanOverdueFeeSerializer(
                    fees.get('records', []), many=True
                ).data
            }
        })

    @action(detail=True, methods=['get'])
    def borrower_credit(self, request, pk=None):
        """获取借用人信用"""
        loan = self.get_object()
        credit = self.service.get_borrower_credit(loan)

        if not credit:
            return Response({
                'success': True,
                'data': None,
                'message': '借用人信用记录不存在'
            })

        return Response({
            'success': True,
            'data': BorrowerCreditSerializer(credit).data
        })

    @action(detail=True, methods=['post'])
    def update_credit(self, request, pk=None):
        """手动更新信用分"""
        loan = self.get_object()
        score_change = request.data.get('score_change')
        reason = request.data.get('reason', '')

        if score_change is None:
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': '请输入分数变化'}
            }, status=400)

        credit = self.service.update_credit_score(
            loan=loan,
            score_change=int(score_change),
            reason=reason,
            event_type='credit_manual_adjust',
            operator=request.user
        )

        return Response({
            'success': True,
            'message': '信用分更新成功',
            'data': BorrowerCreditSerializer(credit).data
        })
```

### 5.2 LoanDepositViewSet

```python
class LoanDepositViewSet(BaseModelViewSetWithBatch):
    """押金记录ViewSet"""

    queryset = LoanDeposit.objects.select_related('loan', 'refunded_by')
    serializer_class = LoanDepositSerializer
    filterset_class = LoanDepositFilter

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """押金汇总"""
        from django.db.models import Sum, Q

        org = request.user.organization
        base_qs = self.get_queryset()

        # 待退还押金
        pending_refund = base_qs.filter(
            deposit_status='collected',
            loan__status__in=['returned', 'cancelled']
        ).aggregate(
            total=Sum('deposit_amount'),
            count=models.Count('id')
        )

        # 已收取押金
        collected = base_qs.filter(deposit_status='collected').aggregate(
            total=Sum('deposit_amount'),
            count=models.Count('id')
        )

        # 已退还押金
        refunded = base_qs.filter(deposit_status='refunded').aggregate(
            total=Sum('refunded_amount'),
            count=models.Count('id')
        )

        return Response({
            'success': True,
            'data': {
                'collected': {
                    'total': str(collected['total'] or 0),
                    'count': collected['count']
                },
                'refunded': {
                    'total': str(refunded['total'] or 0),
                    'count': refunded['count']
                },
                'pending_refund': {
                    'total': str(pending_refund['total'] or 0),
                    'count': pending_refund['count']
                }
            }
        })
```

### 5.3 BorrowerCreditViewSet

```python
class BorrowerCreditViewSet(BaseModelViewSetWithBatch):
    """借用人信用ViewSet"""

    queryset = BorrowerCredit.objects.all()
    serializer_class = BorrowerCreditSerializer
    filterset_class = BorrowerCreditFilter

    @action(detail=False, methods=['get'])
    def my_credit(self, request):
        """获取我的信用（内部用户）"""
        credit = self.get_queryset().filter(
            borrower_type='internal',
            borrower_user=request.user
        ).first()

        if not credit:
            return Response({
                'success': True,
                'data': None,
                'message': '信用记录不存在'
            })

        return Response({
            'success': True,
            'data': BorrowerCreditSerializer(credit).data
        })

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """获取信用历史"""
        credit = self.get_object()
        histories = credit.histories.select_related(
            'loan', 'related_asset'
        ).order_by('-event_date')

        page = self.paginate_queryset(histories)
        if page is not None:
            serializer = CreditHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CreditHistorySerializer(histories, many=True)
        return Response({'success': True, 'data': serializer.data})
```

---

## 6. Service 设计

### 6.1 AssetLoanService（扩展）

```python
from apps.common.services.base_crud import BaseCRUDService
from django.db import transaction
from decimal import Decimal

class AssetLoanService(BaseCRUDService):
    """资产借用服务（扩展）"""

    def __init__(self):
        super().__init__(AssetLoan)

    @transaction.atomic
    def create_external_loan(self, data, user):
        """创建对外借用单"""
        from apps.system.services import DynamicDataService

        external_id = data.get('borrower_external_id')
        if not external_id:
            raise ValueError('必须指定外部借用人')

        # 获取外部人员信息
        dynamic_service = DynamicDataService()
        external_person = dynamic_service.get_by_id(external_id)
        if not external_person:
            raise ValueError('外部人员不存在')

        # 创建借用单
        loan_data = {
            **data,
            'borrower_type': 'external',
            'borrower_external_id': external_id,
            'borrower_name': external_person.dynamic_fields.get('person_name'),
            'borrower_phone': external_person.dynamic_fields.get('phone'),
            'borrower_company': external_person.dynamic_fields.get('company_name'),
            'status': 'pending',
            'created_by': user,
            'organization_id': user.organization_id,
        }

        loan = self.create(loan_data)

        # 创建借用明细
        items_data = data.get('items', [])
        for item_data in items_data:
            LoanItem.objects.create(
                loan=loan,
                asset_id=item_data['asset_id'],
                quantity=item_data.get('quantity', 1),
                remark=item_data.get('remark', '')
            )

        # 更新信用记录
        self._update_credit_on_loan_create(loan, user)

        return loan

    def collect_deposit(self, loan, amount, payment_method, payment_account, operator):
        """收取押金"""
        if not loan.enable_deposit:
            raise ValueError('该借用单未启用押金')

        if loan.deposits.filter(deposit_status='collected').exists():
            raise ValueError('该借用单已收取押金')

        deposit = LoanDeposit.objects.create(
            loan=loan,
            deposit_no=self._generate_deposit_no(),
            deposit_amount=amount,
            deposit_date=timezone.now().date(),
            payment_method=payment_method,
            payment_account=payment_account,
            deposit_status='collected',
            created_by=operator,
            organization_id=loan.organization_id
        )

        return deposit

    def refund_deposit(self, loan, amount, reason, voucher, operator):
        """退还押金"""
        deposit = loan.deposits.filter(deposit_status='collected').first()
        if not deposit:
            raise ValueError('未找到有效的押金记录')

        if amount > deposit.deposit_amount:
            raise ValueError('退款金额不能超过押金金额')

        # 扣除超期费用
        overdue_fees = loan.overdue_fees.filter(fee_status='pending')
        total_fee = sum(f.actual_fee for f in overdue_fees)

        refund_amount = min(Decimal(amount), deposit.deposit_amount - total_fee)

        deposit.deposit_status = 'refunded'
        deposit.refunded_amount = refund_amount
        deposit.refunded_date = timezone.now().date()
        deposit.refund_reason = reason
        if voucher:
            deposit.refund_voucher.save(voucher.name, voucher)
        deposit.refunded_by = operator
        deposit.save()

        # 标记费用为已收取
        if total_fee > 0:
            overdue_fees.update(
                fee_status='collected',
                collected_date=timezone.now().date(),
                collected_by=operator
            )

        return deposit

    def calculate_overdue_fee(self, loan):
        """计算超期费用"""
        if not loan.enable_overdue_fee:
            return {'overdue_days': 0, 'total_fee': Decimal('0'), 'records': []}

        if loan.expected_return_date is None:
            return {'overdue_days': 0, 'total_fee': Decimal('0'), 'records': []}

        today = timezone.now().date()
        if today <= loan.expected_return_date:
            return {'overdue_days': 0, 'total_fee': Decimal('0'), 'records': []}

        overdue_days = (today - loan.expected_return_date).days

        # 获取适用规则
        rule = self._get_applicable_fee_rule(loan)
        if not rule:
            return {'overdue_days': overdue_days, 'total_fee': Decimal('0'), 'records': []}

        # 计算费用
        if rule.rule_type == 'daily':
            fee = overdue_days * rule.daily_rate
        elif rule.rule_type == 'tiered':
            fee = self._calculate_tiered_fee(overdue_days, rule.tier_config)

        # 检查是否已存在今日的计算记录
        existing = loan.overdue_fees.filter(
            calculation_date=today,
            fee_rule=rule
        ).first()

        if existing:
            return {
                'overdue_days': overdue_days,
                'total_fee': existing.actual_fee,
                'records': [existing]
            }

        # 创建计费记录
        fee_record = LoanOverdueFee.objects.create(
            loan=loan,
            fee_rule=rule,
            calculation_date=today,
            overdue_days=overdue_days,
            unit_price=rule.daily_rate if rule.rule_type == 'daily' else Decimal('0'),
            calculated_fee=fee,
            actual_fee=min(fee, rule.max_fee) if rule.max_fee else fee,
            fee_status='pending',
            created_by=operator if operator else None,
            organization_id=loan.organization_id
        )

        return {
            'overdue_days': overdue_days,
            'total_fee': fee_record.actual_fee,
            'records': [fee_record]
        }

    def get_borrower_credit(self, loan):
        """获取借用人信用"""
        if loan.borrower_type == 'internal':
            credit, _ = BorrowerCredit.objects.get_or_create(
                borrower_type='internal',
                borrower_user=loan.borrower,
                organization_id=loan.organization_id,
                defaults={'credit_score': 100}
            )
        else:
            credit, _ = BorrowerCredit.objects.get_or_create(
                borrower_type='external',
                borrower_external_id=loan.borrower_external_id,
                organization_id=loan.organization_id,
                defaults={'credit_score': 100}
            )
        return credit

    def update_credit_score(self, loan, score_change, reason, event_type, operator):
        """更新信用分"""
        credit = self.get_borrower_credit(loan)
        old_score = credit.credit_score
        new_score = max(0, min(100, old_score + score_change))

        # 更新信用等级
        credit.credit_score = new_score
        credit.credit_level = self._calculate_credit_level(new_score)
        credit.last_updated_by = operator
        credit.save()

        # 创建历史记录
        CreditHistory.objects.create(
            credit=credit,
            loan=loan,
            event_type=event_type,
            event_date=timezone.now().date(),
            score_change=score_change,
            score_after=new_score,
            event_description=reason or f'分数从 {old_score} 变更为 {new_score}',
            created_by=operator,
            organization_id=loan.organization_id
        )

        return credit

    def _calculate_tiered_fee(self, days, tier_config):
        """计算阶梯费用"""
        total_fee = Decimal('0')
        remaining_days = days

        for tier in tier_config.get('tiers', []):
            if remaining_days <= 0:
                break

            start = tier['days_start']
            end = tier['days_end'] or float('inf')

            tier_days = min(remaining_days, end - start + 1)
            if tier_days > 0:
                total_fee += Decimal(str(tier_days)) * Decimal(str(tier['daily_rate']))
                remaining_days -= tier_days

        return total_fee

    def _calculate_credit_level(self, score):
        """计算信用等级"""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'normal'
        elif score >= 40:
            return 'poor'
        else:
            return 'blacklisted'

    def _get_applicable_fee_rule(self, loan):
        """获取适用的计费规则"""
        from django.db.models import Q

        qs = LoanFeeRule.objects.filter(
            is_active=True,
            organization_id=loan.organization_id
        )

        if loan.borrower_type == 'internal':
            qs = qs.filter(apply_to_internal=True)
        else:
            qs = qs.filter(apply_to_external=True)

        return qs.first()

    def _generate_deposit_no(self):
        """生成押金单号"""
        today = timezone.now().strftime('%Y%m')
        prefix = f'YJ{today}'
        count = LoanDeposit.objects.filter(
            deposit_no__startswith=prefix
        ).count()
        return f'{prefix}{(count + 1):04d}'
```

### 6.2 BorrowerCreditService

```python
class BorrowerCreditService(BaseCRUDService):
    """借用人信用服务"""

    def __init__(self):
        super().__init__(BorrowerCredit)

    def record_return_event(self, loan, asset_condition):
        """记录归还事件，更新信用"""
        score_change = 0
        event_type = 'returned_normal'
        description = '正常归还'

        # 计算超期天数
        if loan.expected_return_date and loan.actual_return_date:
            overdue_days = (loan.actual_return_date - loan.expected_return_date).days
            if overdue_days > 0:
                if overdue_days <= 7:
                    event_type = 'returned_overdue_short'
                    description = f'超期{overdue_days}天归还'
                    score_change = 0
                elif overdue_days <= 30:
                    event_type = 'returned_overdue_long'
                    description = f'超期{overdue_days}天归还'
                    score_change = -5
                else:
                    event_type = 'returned_overdue_severe'
                    description = f'超期{overdue_days}天归还'
                    score_change = -15

        # 根据资产状况调整
        if asset_condition == 'minor_damage':
            score_change -= 5
            event_type = 'asset_damaged_minor'
            description = '归还时资产轻微损坏'
        elif asset_condition == 'major_damage':
            score_change -= 20
            event_type = 'asset_damaged_severe'
            description = '归还时资产严重损坏'
        elif asset_condition == 'lost':
            score_change -= 50
            event_type = 'asset_lost'
            description = '资产遗失'

        # 更新信用
        loan_service = AssetLoanService()
        loan_service.update_credit_score(
            loan=loan,
            score_change=score_change,
            reason=description,
            event_type=event_type,
            operator=None
        )

        # 更新统计
        credit = loan_service.get_borrower_credit(loan)
        if asset_condition == 'good' and score_change >= 0:
            credit.normal_return_count += 1
        elif score_change < 0:
            if asset_condition in ['minor_damage', 'major_damage']:
                credit.damage_count += 1
            elif asset_condition == 'lost':
                credit.lost_count += 1
        credit.total_loan_count += 1
        credit.last_overdue_days = overdue_days if overdue_days > 0 else 0
        credit.total_overdue_days += max(0, overdue_days)
        credit.save()

    def check_credit_eligibility(self, borrower_type, borrower_id, organization_id):
        """检查借用资格"""
        credit = BorrowerCredit.objects.filter(
            organization_id=organization_id,
            borrower_type=borrower_type,
            **{'borrower_user': borrower_id} if borrower_type == 'internal' else {'borrower_external_id': borrower_id}
        ).first()

        if not credit:
            return {'eligible': True, 'reason': '新用户'}

        # 黑名单检查
        if credit.credit_level == 'blacklisted':
            return {
                'eligible': False,
                'reason': '信用等级过低（黑名单）',
                'credit_score': credit.credit_score
            }

        # 严重超期检查
        if credit.lost_count > 0:
            return {
                'eligible': False,
                'reason': '存在资产遗失记录',
                'credit_score': credit.credit_score
            }

        # 连续超期检查
        if credit.overdue_count >= 3:
            return {
                'eligible': False,
                'reason': '超期次数过多',
                'credit_score': credit.credit_score
            }

        return {
            'eligible': True,
            'credit_score': credit.credit_score,
            'credit_level': credit.credit_level
        }
```

---

## 7. 定时任务

### 7.1 超期检测与计费任务

```python
# apps/loans/tasks.py

from celery import shared_task
from django.utils import timezone
from django.db.models import Q

@shared_task
def check_overdue_loans():
    """检查超期借用单并计费"""
    from apps.loans.models import AssetLoan
    from apps.loans.services import AssetLoanService

    today = timezone.now().date()
    service = AssetLoanService()

    # 查找启用计费的超期借用单
    overdue_loans = AssetLoan.objects.filter(
        enable_overdue_fee=True,
        expected_return_date__lt=today,
        status__in=['borrowed', 'overdue']
    ).select_related('organization')

    results = {
        'processed': 0,
        'fees_created': 0,
        'errors': []
    }

    for loan in overdue_loans:
        try:
            # 更新状态为超期
            if loan.status == 'borrowed':
                loan.status = 'overdue'
                loan.save()

            # 计算费用
            fee_result = service.calculate_overdue_fee(loan)
            if fee_result.get('records'):
                results['fees_created'] += len(fee_result['records'])

            # 发送超期提醒
            if fee_result.get('overdue_days', 0) in [1, 7, 30]:  # 关键天数提醒
                _send_overdue_notification(loan, fee_result['overdue_days'])

            results['processed'] += 1

        except Exception as e:
            results['errors'].append({
                'loan_id': str(loan.id),
                'error': str(e)
            })

    return results


@shared_task
def update_loan_status_daily():
    """每日更新借用状态"""
    from apps.loans.models import AssetLoan

    today = timezone.now().date()

    # 将超期的借用单状态更新为overdue
    AssetLoan.objects.filter(
        expected_return_date__lt=today,
        status='borrowed'
    ).update(status='overdue')

    return {'updated': AssetLoan.objects.filter(status='overdue').count()}


def _send_overdue_notification(loan, overdue_days):
    """发送超期提醒"""
    from apps.notifications.services import NotificationService

    notify_service = NotificationService()

    # 内部借用：通知借用人
    if loan.borrower_type == 'internal' and loan.borrower:
        notify_service.send_template_notification(
            template_code='loan_overdue_reminder',
            recipients=[{'user_id': loan.borrower.id}],
            context={
                'borrower_name': loan.borrower.get_full_name(),
                'loan_no': loan.loan_no,
                'overdue_days': overdue_days,
                'expected_return_date': loan.expected_return_date,
            }
        )

    # 通知管理员
    admins = User.objects.filter(
        organization=loan.organization,
        groups__name__in=['asset_admin', 'warehouse_admin']
    )

    notify_service.send_template_notification(
        template_code='loan_overdue_admin_notice',
        recipients=[{'user_id': u.id} for u in admins],
        context={
            'loan_no': loan.loan_no,
            'borrower_name': loan.borrower_name,
            'overdue_days': overdue_days,
        }
    )

# Celery Beat 配置
CELERY_BEAT_SCHEDULE = {
    'check-overdue-loans': {
        'task': 'apps.loans.tasks.check_overdue_loans',
        'schedule': crontab(hour=1, minute=0),  # 每天凌晨1点执行
    },
    'update-loan-status': {
        'task': 'apps.loans.tasks.update_loan_status_daily',
        'schedule': crontab(hour=0, minute=0),  # 每天凌晨0点执行
    },
}
```

---

## 8. 数据库迁移

### 8.1 Migration 文件

```python
# Generated by Django 5.0 on 2025-01-20

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('assets', '0001_initial'),
        ('loans', '0001_initial'),  # 假设已有AssetLoan
    ]

    operations = [
        # ========== AssetLoan 模型改造 ==========
        migrations.AddField(
            model_name='assetloan',
            name='borrower_type',
            field=models.CharField(
                max_length=20,
                default='internal',
                choices=[('internal', '内部借用'), ('external', '对外借出')]
            ),
        ),
        migrations.AddField(
            model_name='assetloan',
            name='borrower_external_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='assetloan',
            name='borrower_name',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='assetloan',
            name='borrower_phone',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='assetloan',
            name='borrower_company',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='assetloan',
            name='enable_deposit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='assetloan',
            name='enable_overdue_fee',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='assetloan',
            name='returned_by',
            field=models.ForeignKey(
                'accounts.User',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                related_name='confirmed_returns'
            ),
        ),

        # ========== 创建 LoanDeposit 模型 ==========
        migrations.CreateModel(
            name='LoanDeposit',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('deposit_no', models.CharField(max_length=50, unique=True, db_index=True)),
                ('deposit_amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('deposit_date', models.DateField()),
                ('payment_method', models.CharField(
                    max_length=20,
                    choices=[('cash', '现金'), ('transfer', '转账'), ('check', '支票'), ('other', '其他')]
                )),
                ('payment_account', models.CharField(max_length=100, blank=True)),
                ('deposit_status', models.CharField(
                    max_length=20,
                    choices=[('collected', '已收取'), ('refunded', '已退还'), ('cancelled', '已作废')],
                    default='collected'
                )),
                ('refunded_date', models.DateField(null=True, blank=True)),
                ('refunded_amount', models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ('refund_reason', models.TextField(blank=True)),
                ('refund_voucher', models.FileField(upload_to='deposit_vouchers/', null=True, blank=True)),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT)),
                ('custom_fields', models.JSONField(default=dict)),
                # Foreign keys
                ('loan', models.ForeignKey('loans.AssetLoan', on_delete=models.PROTECT, related_name='deposits')),
                ('refunded_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    related_name='refunded_deposits'
                )),
            ],
            options={
                'db_table': 'loan_deposit',
                'indexes': [
                    models.Index(fields=['loan', 'deposit_status']),
                    models.Index(fields=['deposit_date']),
                ],
            },
        ),

        # ========== 创建 LoanFeeRule 模型 ==========
        migrations.CreateModel(
            name='LoanFeeRule',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('rule_type', models.CharField(
                    max_length=20,
                    choices=[('daily', '按日计费'), ('tiered', '阶梯计费')],
                    default='daily'
                )),
                ('is_active', models.BooleanField(default=True)),
                ('daily_rate', models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)),
                ('tier_config', models.JSONField(default=dict, blank=True)),
                ('apply_to_internal', models.BooleanField(default=False)),
                ('apply_to_external', models.BooleanField(default=True)),
                ('min_overdue_days', models.IntegerField(default=1)),
                ('max_fee', models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)),
                ('currency', models.CharField(max_length=10, default='CNY')),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT)),
                ('custom_fields', models.JSONField(default=dict)),
            ],
            options={
                'db_table': 'loan_fee_rule',
            },
        ),

        # ========== 创建 LoanOverdueFee 模型 ==========
        migrations.CreateModel(
            name='LoanOverdueFee',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('calculation_date', models.DateField(db_index=True)),
                ('overdue_days', models.IntegerField()),
                ('unit_price', models.DecimalField(max_digits=12, decimal_places=4)),
                ('calculated_fee', models.DecimalField(max_digits=12, decimal_places=2)),
                ('waived_fee', models.DecimalField(max_digits=12, decimal_places=2, default=0)),
                ('actual_fee', models.DecimalField(max_digits=12, decimal_places=2)),
                ('fee_status', models.CharField(
                    max_length=20,
                    choices=[('pending', '待收取'), ('collected', '已收取'), ('waived', '已豁免'), ('cancelled', '已取消')],
                    default='pending'
                )),
                ('collected_date', models.DateField(null=True, blank=True)),
                ('waive_reason', models.TextField(blank=True)),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT, null=True)),
                ('custom_fields', models.JSONField(default=dict)),
                # Foreign keys
                ('loan', models.ForeignKey('loans.AssetLoan', on_delete=models.PROTECT, related_name='overdue_fees')),
                ('fee_rule', models.ForeignKey('loans.LoanFeeRule', on_delete=models.PROTECT, related_name='fee_records')),
                ('collected_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    related_name='collected_fees'
                )),
                ('waive_approved_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    related_name='approved_waived_fees'
                )),
            ],
            options={
                'db_table': 'loan_overdue_fee',
            },
        ),

        # ========== 创建 BorrowerCredit 模型 ==========
        migrations.CreateModel(
            name='BorrowerCredit',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('borrower_type', models.CharField(
                    max_length=20,
                    choices=[('internal', '内部'), ('external', '外部')]
                )),
                ('borrower_external_id', models.CharField(max_length=50, null=True, blank=True, unique=True)),
                ('credit_score', models.IntegerField(default=100)),
                ('credit_level', models.CharField(
                    max_length=20,
                    choices=[
                        ('excellent', '优秀'),
                        ('good', '良好'),
                        ('normal', '一般'),
                        ('poor', '较差'),
                        ('blacklisted', '黑名单')
                    ],
                    default='excellent'
                )),
                ('total_loan_count', models.IntegerField(default=0)),
                ('normal_return_count', models.IntegerField(default=0)),
                ('overdue_count', models.IntegerField(default=0)),
                ('damage_count', models.IntegerField(default=0)),
                ('lost_count', models.IntegerField(default=0)),
                ('last_overdue_days', models.IntegerField(null=True, blank=True)),
                ('total_overdue_days', models.IntegerField(default=0)),
                ('last_updated_at', models.DateTimeField(auto_now=True)),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT)),
                ('custom_fields', models.JSONField(default=dict)),
                # Foreign keys
                ('borrower_user', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    unique=True,
                    related_name='credit_record'
                )),
                ('last_updated_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True
                )),
            ],
            options={
                'db_table': 'borrower_credit',
            },
        ),

        # ========== 创建 CreditHistory 模型 ==========
        migrations.CreateModel(
            name='CreditHistory',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('event_type', models.CharField(max_length=50)),
                ('event_date', models.DateField(db_index=True)),
                ('score_change', models.IntegerField()),
                ('score_after', models.IntegerField()),
                ('event_description', models.TextField()),
                # BaseModel fields
                ('organization', models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=models.PROTECT')),
                ('custom_fields', models.JSONField(default=dict)),
                # Foreign keys
                ('credit', models.ForeignKey('loans.BorrowerCredit', on_delete=models.CASCADE, related_name='histories')),
                ('loan', models.ForeignKey('loans.AssetLoan', on_delete=models.SET_NULL, null=True)),
                ('related_asset', models.ForeignKey('assets.Asset', on_delete=models.SET_NULL, null=True)),
            ],
            options={
                'db_table': 'credit_history',
            },
        ),
    ]
```

---

## 9. 测试用例

### 9.1 模型测试

```python
# apps/loans/tests/test_models.py

from django.test import TestCase
from apps.loans.models import AssetLoan, LoanDeposit, BorrowerCredit
from apps.accounts.models import User
from apps.organizations.models import Organization
from decimal import Decimal

class AssetLoanModelTest(TestCase):
    """AssetLoan模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

    def test_external_loan_creation(self):
        """测试对外借用创建"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010001',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrower_phone='13800138000',
            borrow_date='2025-01-01',
            expected_return_date='2025-01-15',
            status='pending',
            created_by=self.user,
            enable_deposit=True,
            enable_overdue_fee=True,
        )

        self.assertEqual(loan.borrower_type, 'external')
        self.assertIsNone(loan.borrower)
        self.assertEqual(loan.borrower_external_id, 'EXT001')
        self.assertTrue(loan.enable_deposit)

    def test_deposit_status_collected(self):
        """测试押金已收取状态"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010002',
            borrower_type='internal',
            borrower=self.user,
            borrow_date='2025-01-01',
            expected_return_date='2025-01-15',
            status='approved',
            created_by=self.user,
            enable_deposit=True,
        )

        deposit = LoanDeposit.objects.create(
            organization=self.org,
            loan=loan,
            deposit_no='YJ2025010001',
            deposit_amount=Decimal('5000.00'),
            deposit_date='2025-01-01',
            payment_method='transfer',
            deposit_status='collected',
            created_by=self.user,
        )

        self.assertEqual(loan.deposits.count(), 1)
        self.assertEqual(loan.deposits.first().deposit_status, 'collected')
        self.assertEqual(loan.deposits.first().deposit_amount, Decimal('5000.00'))

class BorrowerCreditModelTest(TestCase):
    """BorrowerCredit模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

    def test_credit_level_calculation(self):
        """测试信用等级计算"""
        credit = BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=85,
        )

        self.assertEqual(credit.credit_level, 'good')

        credit.credit_score = 40
        credit.save()
        self.assertEqual(credit.credit_level, 'poor')

    def test_external_borrower_credit(self):
        """测试外部借用人信用"""
        credit = BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='external',
            borrower_external_id='EXT001',
            credit_score=95,
        )

        self.assertEqual(credit.borrower_type, 'external')
        self.assertIsNone(credit.borrower_user)
        self.assertEqual(credit.credit_level, 'excellent')
```

### 9.2 Service测试

```python
# apps/loans/tests/test_services.py

from django.test import TestCase
from apps.loans.services import AssetLoanService, BorrowerCreditService
from apps.loans.models import AssetLoan, BorrowerCredit, LoanDeposit
from apps.accounts.models import User
from apps.organizations.models import Organization
from decimal import Decimal
from unittest.mock import Mock, patch

class AssetLoanServiceTest(TestCase):
    """AssetLoanService测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)
        self.service = AssetLoanService()

    def test_collect_deposit(self):
        """测试收取押金"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010001',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date='2025-01-01',
            expected_return_date='2025-01-15',
            status='approved',
            created_by=self.user,
            enable_deposit=True,
        )

        deposit = self.service.collect_deposit(
            loan=loan,
            amount=Decimal('5000.00'),
            payment_method='transfer',
            payment_account='6222 0000 0000 0000',
            operator=self.user
        )

        self.assertIsNotNone(deposit)
        self.assertEqual(deposit.deposit_status, 'collected')
        self.assertEqual(deposit.deposit_amount, Decimal('5000.00'))
        self.assertTrue(deposit.deposit_no.startswith('YJ'))

    def test_refund_deposit_with_overdue_fee(self):
        """测试退还押金（扣除超期费用）"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010002',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date='2025-01-01',
            expected_return_date='2025-01-15',
            status='returned',
            created_by=self.user,
            enable_deposit=True,
            enable_overdue_fee=True,
        )

        # 收取押金
        deposit = self.service.collect_deposit(
            loan=loan,
            amount=Decimal('5000.00'),
            payment_method='transfer',
            payment_account='',
            operator=self.user
        )

        # 创建超期费用记录
        from apps.loans.models import LoanOverdueFee, LoanFeeRule
        fee_rule = LoanFeeRule.objects.create(
            organization=self.org,
            name='测试规则',
            code='TEST_RULE',
            daily_rate=Decimal('50.00'),
            created_by=self.user
        )

        overdue_fee = LoanOverdueFee.objects.create(
            organization=self.org,
            loan=loan,
            fee_rule=fee_rule,
            calculation_date='2025-01-20',
            overdue_days=5,
            unit_price=Decimal('50.00'),
            calculated_fee=Decimal('250.00'),
            actual_fee=Decimal('250.00'),
            fee_status='pending',
            created_by=self.user
        )

        # 退还押金（应扣除250元费用）
        refunded_deposit = self.service.refund_deposit(
            loan=loan,
            amount=Decimal('5000.00'),
            reason='正常归还',
            voucher=None,
            operator=self.user
        )

        self.assertEqual(refunded_deposit.refunded_amount, Decimal('4750.00'))

        # 刷新费用记录状态
        overdue_fee.refresh_from_db()
        self.assertEqual(overdue_fee.fee_status, 'collected')

    def test_calculate_overdue_fee(self):
        """测试超期费用计算"""
        from datetime import date, timedelta
        from apps.loans.models import LoanFeeRule

        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010003',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today() - timedelta(days=20),
            expected_return_date=date.today() - timedelta(days=5),
            status='borrowed',
            created_by=self.user,
            enable_overdue_fee=True,
        )

        # 创建计费规则
        fee_rule = LoanFeeRule.objects.create(
            organization=self.org,
            name='每日50元',
            code='DAILY_50',
            rule_type='daily',
            daily_rate=Decimal('50.00'),
            apply_to_external=True,
            created_by=self.user
        )

        result = self.service.calculate_overdue_fee(loan)

        self.assertGreater(result['overdue_days'], 0)
        self.assertGreater(result['total_fee'], 0)
        self.assertEqual(len(result['records']), 1)

class BorrowerCreditServiceTest(TestCase):
    """BorrowerCreditService测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)
        self.service = BorrowerCreditService()

    def test_record_normal_return(self):
        """测试记录正常归还"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010001',
            borrower_type='internal',
            borrower=self.user,
            borrow_date='2025-01-01',
            expected_return_date='2025-01-15',
            actual_return_date='2025-01-14',
            status='returned',
            created_by=self.user,
        )

        # 模拟记录归还事件
        with patch('apps.loans.services.AssetLoanService.get_borrower_credit') as mock_get_credit:
            mock_credit = BorrowerCredit.objects.create(
                organization=self.org,
                borrower_type='internal',
                borrower_user=self.user,
                credit_score=100,
            )
            mock_get_credit.return_value = mock_credit

            self.service.record_return_event(loan, 'good')

            mock_credit.refresh_from_db()
            self.assertEqual(mock_credit.normal_return_count, 1)
            self.assertEqual(mock_credit.credit_score, 102)  # +2分

    def test_check_credit_eligibility_blacklisted(self):
        """测试黑名单用户借用资格检查"""
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=20,
            credit_level='blacklisted',
        )

        result = self.service.check_credit_eligibility('internal', self.user.id, self.org.id)

        self.assertFalse(result['eligible'])
        self.assertIn('黑名单', result['reason'])

    def test_check_credit_eligibility_good(self):
        """测试良好信用用户借用资格检查"""
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=85,
            credit_level='good',
        )

        result = self.service.check_credit_eligibility('internal', self.user.id, self.org.id)

        self.assertTrue(result['eligible'])
        self.assertEqual(result['credit_score'], 85)
```

---

## 10. API错误码扩展

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| `DEPOSIT_ALREADY_COLLECTED` | 400 | 该借用单已收取押金 |
| `DEPOSIT_NOT_FOUND` | 404 | 未找到有效的押金记录 |
| `REFUND_AMOUNT_EXCEEDS` | 400 | 退款金额超过押金金额 |
| `CREDIT_BLACKLISTED` | 403 | 借用人信用等级过低（黑名单） |
| `CREDIT_ASSET_LOST` | 403 | 存在资产遗失记录 |
| `OVERDUE_FEE_NOT_ENABLED` | 400 | 该借用单未启用超期计费 |
| `EXTERNAL_PERSON_NOT_FOUND` | 404 | 外部人员不存在 |
| `LOAN_NOT_APPROVED` | 400 | 借用单未批准，无法操作 |

---

## 11. 与其他模块集成

### 11.1 与低代码引擎集成

```python
# 获取ExternalPerson业务对象
from apps.system.models import BusinessObject
from apps.system.services import DynamicDataService

def get_external_person(external_id):
    bo = BusinessObject.objects.get(code='ExternalPerson')
    service = DynamicDataService()
    return service.get_by_id(external_id)

# 创建外部人员
def create_external_person(data, organization, user):
    bo = BusinessObject.objects.get(code='ExternalPerson')
    service = DynamicDataService()

    # 验证必填字段
    field_definitions = bo.field_definitions.filter(is_required=True)
    for fd in field_definitions:
        if fd.code not in data or not data[fd.code]:
            raise ValueError(f'{fd.name}为必填字段')

    return service.create(
        business_object_code='ExternalPerson',
        data=data,
        created_by=user,
        organization_id=organization.id
    )
```

### 11.2 与工作流引擎集成

对外借用可配置独立的审批流程：

```python
# 借用类型 -> 工作流定义映射
WORKFLOW_MAPPING = {
    'internal': 'asset_loan_internal_workflow',
    'external': 'asset_loan_external_workflow',  # 更严格的审批流程
}

def get_workflow_for_loan(borrower_type, organization):
    from apps.workflows.models import WorkflowDefinition
    code = WORKFLOW_MAPPING.get(borrower_type, 'asset_loan_default_workflow')
    return WorkflowDefinition.objects.filter(
        code=code,
        organization=organization,
        is_published=True
    ).first()
```

### 11.3 与通知系统集成

```python
# 通知模板配置
NOTIFICATION_TEMPLATES = [
    {
        'code': 'loan_overdue_reminder',
        'title': '资产借用超期提醒',
        'content': '您借用的资产{{loan_no}}已超期{{overdue_days}}天，请尽快归还。',
    },
    {
        'code': 'loan_overdue_admin_notice',
        'title': '资产借用超期通知',
        'content': '借用单{{loan_no}}（借用人：{{borrower_name}}）已超期{{overdue_days}}天。',
    },
    {
        'code': 'deposit_collected',
        'title': '押金收取通知',
        'content': '借用单{{loan_no}}的押金{{amount}}元已收取。',
    },
    {
        'code': 'deposit_refunded',
        'title': '押金退还通知',
        'content': '借用单{{loan_no}}的押金{{amount}}元已退还。',
    },
]
```
