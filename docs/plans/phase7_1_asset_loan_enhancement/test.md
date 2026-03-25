# Phase 7.1: 资产借用/外借增强 - 测试验证

## 测试策略

采用**TDD（测试驱动开发）**思路，确保借用/外借、押金管理、超期计费、信用管理功能的可靠性。

---

## 单元测试

### 后端模型测试

```python
# apps/loans/tests/test_models.py

from django.test import TestCase
from django.utils import timezone
from apps.loans.models import AssetLoan, LoanDeposit, LoanFeeRule, LoanOverdueFee, BorrowerCredit, CreditHistory
from apps.accounts.models import User
from apps.organizations.models import Organization
from decimal import Decimal
from datetime import date, timedelta


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
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='pending',
            created_by=self.user,
            enable_deposit=True,
            enable_overdue_fee=True,
        )

        self.assertEqual(loan.borrower_type, 'external')
        self.assertIsNone(loan.borrower)
        self.assertEqual(loan.borrower_external_id, 'EXT001')
        self.assertTrue(loan.enable_deposit)
        self.assertTrue(loan.enable_overdue_fee)

    def test_internal_loan_creation(self):
        """测试内部借用创建"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010002',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='pending',
            created_by=self.user,
        )

        self.assertEqual(loan.borrower_type, 'internal')
        self.assertEqual(loan.borrower, self.user)
        self.assertIsNone(loan.borrower_external_id)

    def test_soft_delete(self):
        """测试软删除功能"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010003',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='pending',
            created_by=self.user,
        )

        # 软删除
        loan.soft_delete()

        # 验证软删除
        self.assertTrue(loan.is_deleted)
        self.assertIsNotNone(loan.deleted_at)

        # 正常查询无法获取
        active_loans = AssetLoan.objects.filter(loan_no='LN2025010003')
        self.assertEqual(active_loans.count(), 0)

    def test_organization_isolation(self):
        """测试组织隔离"""
        org2 = Organization.objects.create(code='TEST2', name='Test Org 2')

        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010004',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='pending',
            created_by=self.user,
        )

        # 同组织可以查询
        loans = AssetLoan.objects.filter(organization=self.org)
        self.assertEqual(loans.count(), 1)

        # 不同组织无法查询
        loans_org2 = AssetLoan.objects.filter(organization=org2)
        self.assertEqual(loans_org2.count(), 0)


class LoanDepositModelTest(TestCase):
    """LoanDeposit模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

        self.loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010001',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='approved',
            created_by=self.user,
            enable_deposit=True,
        )

    def test_deposit_creation(self):
        """测试押金创建"""
        deposit = LoanDeposit.objects.create(
            organization=self.org,
            loan=self.loan,
            deposit_no='YJ2025010001',
            deposit_amount=Decimal('5000.00'),
            deposit_date=date.today(),
            payment_method='transfer',
            payment_account='6222 0000 0000 0000',
            deposit_status='collected',
            created_by=self.user,
        )

        self.assertEqual(deposit.loan, self.loan)
        self.assertEqual(deposit.deposit_status, 'collected')
        self.assertEqual(deposit.deposit_amount, Decimal('5000.00'))
        self.assertTrue(deposit.deposit_no.startswith('YJ'))

    def test_deposit_refund(self):
        """测试押金退还"""
        deposit = LoanDeposit.objects.create(
            organization=self.org,
            loan=self.loan,
            deposit_no='YJ2025010002',
            deposit_amount=Decimal('5000.00'),
            deposit_date=date.today(),
            payment_method='transfer',
            deposit_status='collected',
            created_by=self.user,
        )

        # 退还押金
        deposit.deposit_status = 'refunded'
        deposit.refunded_amount = Decimal('4750.00')
        deposit.refunded_date = date.today()
        deposit.refund_reason = '正常归还，扣除超期费用250元'
        deposit.refunded_by = self.user
        deposit.save()

        self.assertEqual(deposit.deposit_status, 'refunded')
        self.assertEqual(deposit.refunded_amount, Decimal('4750.00'))

    def test_deposit_to_loan_relationship(self):
        """测试押金与借用单关联"""
        deposit = LoanDeposit.objects.create(
            organization=self.org,
            loan=self.loan,
            deposit_no='YJ2025010003',
            deposit_amount=Decimal('5000.00'),
            deposit_date=date.today(),
            payment_method='cash',
            deposit_status='collected',
            created_by=self.user,
        )

        # 从loan查询deposits
        deposits = self.loan.deposits.all()
        self.assertEqual(deposits.count(), 1)
        self.assertEqual(deposits.first(), deposit)


class LoanFeeRuleModelTest(TestCase):
    """LoanFeeRule模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

    def test_daily_fee_rule_creation(self):
        """测试按日计费规则创建"""
        rule = LoanFeeRule.objects.create(
            organization=self.org,
            name='每日50元',
            code='DAILY_50',
            rule_type='daily',
            daily_rate=Decimal('50.0000'),
            apply_to_external=True,
            apply_to_internal=False,
            min_overdue_days=1,
            created_by=self.user,
        )

        self.assertEqual(rule.rule_type, 'daily')
        self.assertEqual(rule.daily_rate, Decimal('50.0000'))
        self.assertTrue(rule.apply_to_external)
        self.assertFalse(rule.apply_to_internal)

    def test_tiered_fee_rule_creation(self):
        """测试阶梯计费规则创建"""
        tier_config = {
            "tiers": [
                {"days_start": 1, "days_end": 7, "daily_rate": "10.00"},
                {"days_start": 8, "days_end": 30, "daily_rate": "20.00"},
                {"days_start": 31, "days_end": None, "daily_rate": "50.00"}
            ]
        }

        rule = LoanFeeRule.objects.create(
            organization=self.org,
            name='阶梯计费',
            code='TIERED_FEE',
            rule_type='tiered',
            tier_config=tier_config,
            apply_to_external=True,
            max_fee=Decimal('5000.00'),
            created_by=self.user,
        )

        self.assertEqual(rule.rule_type, 'tiered')
        self.assertEqual(len(rule.tier_config['tiers']), 3)
        self.assertEqual(rule.max_fee, Decimal('5000.00'))


class BorrowerCreditModelTest(TestCase):
    """BorrowerCredit模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

    def test_credit_level_calculation(self):
        """测试信用等级计算"""
        # excellent (90-100)
        credit = BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=95,
            created_by=self.user,
        )
        self.assertEqual(credit.credit_level, 'excellent')

        # good (75-89)
        credit.credit_score = 85
        credit.save()
        self.assertEqual(credit.credit_level, 'good')

        # normal (60-74)
        credit.credit_score = 70
        credit.save()
        self.assertEqual(credit.credit_level, 'normal')

        # poor (40-59)
        credit.credit_score = 50
        credit.save()
        self.assertEqual(credit.credit_level, 'poor')

        # blacklisted (0-39)
        credit.credit_score = 20
        credit.save()
        self.assertEqual(credit.credit_level, 'blacklisted')

    def test_external_borrower_credit(self):
        """测试外部借用人信用"""
        credit = BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='external',
            borrower_external_id='EXT001',
            credit_score=90,
            created_by=self.user,
        )

        self.assertEqual(credit.borrower_type, 'external')
        self.assertIsNone(credit.borrower_user)
        self.assertEqual(credit.credit_level, 'excellent')

    def test_credit_statistics_update(self):
        """测试信用统计更新"""
        credit = BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=80,
            total_loan_count=5,
            normal_return_count=4,
            overdue_count=1,
            damage_count=0,
            lost_count=0,
            created_by=self.user,
        )

        # 更新统计
        credit.total_loan_count = 6
        credit.normal_return_count = 5
        credit.overdue_count = 1
        credit.last_overdue_days = 3
        credit.total_overdue_days = 3
        credit.save()

        self.assertEqual(credit.total_loan_count, 6)
        self.assertEqual(credit.normal_return_count, 5)


class CreditHistoryModelTest(TestCase):
    """CreditHistory模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

        self.credit = BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=95,
            created_by=self.user,
        )

    def test_credit_history_creation(self):
        """测试信用历史创建"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010001',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today() - timedelta(days=20),
            expected_return_date=date.today() - timedelta(days=5),
            actual_return_date=date.today() - timedelta(days=2),
            status='returned',
            created_by=self.user,
        )

        history = CreditHistory.objects.create(
            organization=self.org,
            credit=self.credit,
            loan=loan,
            event_type='returned_normal',
            event_date=date.today() - timedelta(days=2),
            score_change=2,
            score_after=97,
            event_description='正常归还',
            created_by=self.user,
        )

        self.assertEqual(history.credit, self.credit)
        self.assertEqual(history.loan, loan)
        self.assertEqual(history.score_change, 2)
        self.assertEqual(history.score_after, 97)

    def test_event_types(self):
        """测试各种事件类型"""
        event_types = [
            'loan_created', 'loan_approved',
            'returned_normal', 'returned_overdue_short',
            'returned_overdue_long', 'returned_overdue_severe',
            'asset_damaged_minor', 'asset_damaged_severe',
            'asset_lost', 'credit_manual_adjust'
        ]

        for event_type in event_types:
            history = CreditHistory.objects.create(
                organization=self.org,
                credit=self.credit,
                event_type=event_type,
                event_date=date.today(),
                score_change=0,
                score_after=95,
                event_description=f'Test {event_type}',
                created_by=self.user,
            )
            self.assertEqual(history.event_type, event_type)
```

### 后端服务测试

```python
# apps/loans/tests/test_services.py

from django.test import TestCase
from django.utils import timezone
from apps.loans.services import AssetLoanService, LoanDepositService, BorrowerCreditService
from apps.loans.models import AssetLoan, LoanDeposit, LoanFeeRule, LoanOverdueFee, BorrowerCredit
from apps.accounts.models import User
from apps.organizations.models import Organization
from decimal import Decimal
from datetime import date, timedelta
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
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
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
        self.assertEqual(deposit.payment_method, 'transfer')

    def test_collect_deposit_already_collected(self):
        """测试重复收取押金"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010002',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='approved',
            created_by=self.user,
            enable_deposit=True,
        )

        # 第一次收取
        self.service.collect_deposit(
            loan=loan,
            amount=Decimal('5000.00'),
            payment_method='transfer',
            payment_account='',
            operator=self.user
        )

        # 第二次收取应该失败
        with self.assertRaises(ValueError) as ctx:
            self.service.collect_deposit(
                loan=loan,
                amount=Decimal('5000.00'),
                payment_method='transfer',
                payment_account='',
                operator=self.user
            )

        self.assertIn('已收取押金', str(ctx.exception))

    def test_refund_deposit(self):
        """测试退还押金"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010003',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            actual_return_date=date.today(),
            status='returned',
            created_by=self.user,
            enable_deposit=True,
        )

        # 收取押金
        self.service.collect_deposit(
            loan=loan,
            amount=Decimal('5000.00'),
            payment_method='transfer',
            payment_account='',
            operator=self.user
        )

        # 退还押金
        refunded_deposit = self.service.refund_deposit(
            loan=loan,
            amount=Decimal('5000.00'),
            reason='正常归还',
            voucher=None,
            operator=self.user
        )

        self.assertEqual(refunded_deposit.deposit_status, 'refunded')
        self.assertEqual(refunded_deposit.refunded_amount, Decimal('5000.00'))

    def test_refund_deposit_with_overdue_fee(self):
        """测试退还押金（扣除超期费用）"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010004',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today() - timedelta(days=20),
            expected_return_date=date.today() - timedelta(days=5),
            actual_return_date=date.today(),
            status='returned',
            created_by=self.user,
            enable_deposit=True,
            enable_overdue_fee=True,
        )

        # 收取押金
        self.service.collect_deposit(
            loan=loan,
            amount=Decimal('5000.00'),
            payment_method='transfer',
            payment_account='',
            operator=self.user
        )

        # 创建计费规则
        fee_rule = LoanFeeRule.objects.create(
            organization=self.org,
            name='每日50元',
            code='DAILY_50',
            daily_rate=Decimal('50.00'),
            apply_to_external=True,
            created_by=self.user
        )

        # 创建超期费用
        overdue_fee = LoanOverdueFee.objects.create(
            organization=self.org,
            loan=loan,
            fee_rule=fee_rule,
            calculation_date=date.today(),
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
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010005',
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

    def test_calculate_tiered_overdue_fee(self):
        """测试阶梯超期费用计算"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010006',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today() - timedelta(days=40),
            expected_return_date=date.today() - timedelta(days=20),
            status='borrowed',
            created_by=self.user,
            enable_overdue_fee=True,
        )

        # 创建阶梯计费规则
        tier_config = {
            "tiers": [
                {"days_start": 1, "days_end": 7, "daily_rate": "10.00"},
                {"days_start": 8, "days_end": 30, "daily_rate": "20.00"},
                {"days_start": 31, "days_end": None, "daily_rate": "50.00"}
            ]
        }

        fee_rule = LoanFeeRule.objects.create(
            organization=self.org,
            name='阶梯计费',
            code='TIERED',
            rule_type='tiered',
            tier_config=tier_config,
            apply_to_external=True,
            max_fee=Decimal('5000.00'),
            created_by=self.user
        )

        result = self.service.calculate_overdue_fee(loan)

        # 20天超期：7天*10 + 13天*20 = 70 + 260 = 330
        self.assertEqual(result['overdue_days'], 20)
        self.assertEqual(str(result['total_fee']), '330.00')

    def test_get_borrower_credit(self):
        """测试获取借用人信用"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010007',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='pending',
            created_by=self.user,
        )

        credit = self.service.get_borrower_credit(loan)

        self.assertIsNotNone(credit)
        self.assertEqual(credit.borrower_type, 'internal')
        self.assertEqual(credit.borrower_user, self.user)
        self.assertEqual(credit.credit_score, 100)  # 初始分数

    def test_update_credit_score(self):
        """测试更新信用分"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010008',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='returned',
            actual_return_date=date.today(),
            created_by=self.user,
        )

        credit = self.service.get_borrower_credit(loan)
        old_score = credit.credit_score

        # 更新信用分
        updated_credit = self.service.update_credit_score(
            loan=loan,
            score_change=5,
            reason='测试加分',
            event_type='credit_manual_adjust',
            operator=self.user
        )

        self.assertEqual(updated_credit.credit_score, old_score + 5)

        # 验证历史记录
        history = credit.histories.first()
        self.assertIsNotNone(history)
        self.assertEqual(history.score_change, 5)

    def test_credit_score_boundary(self):
        """测试信用分边界"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010009',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='returned',
            actual_return_date=date.today(),
            created_by=self.user,
        )

        credit = self.service.get_borrower_credit(loan)

        # 测试上限100
        credit = self.service.update_credit_score(
            loan=loan,
            score_change=50,
            reason='测试上限',
            event_type='credit_manual_adjust',
            operator=self.user
        )
        self.assertEqual(credit.credit_score, 100)

        # 测试下限0
        credit = self.service.update_credit_score(
            loan=loan,
            score_change=-200,
            reason='测试下限',
            event_type='credit_manual_adjust',
            operator=self.user
        )
        self.assertEqual(credit.credit_score, 0)


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
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=1),
            actual_return_date=date.today() - timedelta(days=2),
            status='returned',
            created_by=self.user,
        )

        # 获取或创建信用记录
        from apps.loans.services import AssetLoanService
        loan_service = AssetLoanService()
        credit = loan_service.get_borrower_credit(loan)

        # 记录归还事件
        self.service.record_return_event(loan, 'good')

        credit.refresh_from_db()
        self.assertEqual(credit.normal_return_count, 1)
        self.assertEqual(credit.credit_score, 102)  # +2分

    def test_record_overdue_return(self):
        """测试记录超期归还"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010002',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today() - timedelta(days=30),
            expected_return_date=date.today() - timedelta(days=20),
            actual_return_date=date.today() - timedelta(days=10),
            status='returned',
            created_by=self.user,
        )

        from apps.loans.services import AssetLoanService
        loan_service = AssetLoanService()
        credit = loan_service.get_borrower_credit(loan)

        # 记录超期归还（10天）
        self.service.record_return_event(loan, 'good')

        credit.refresh_from_db()
        self.assertEqual(credit.overdue_count, 1)
        self.assertEqual(credit.credit_score, 95)  # -5分（超期8-30天）

    def test_record_damaged_return(self):
        """测试记录损坏归还"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010003',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=1),
            actual_return_date=date.today() - timedelta(days=2),
            status='returned',
            created_by=self.user,
        )

        from apps.loans.services import AssetLoanService
        loan_service = AssetLoanService()
        credit = loan_service.get_borrower_credit(loan)

        # 记录轻微损坏归还
        self.service.record_return_event(loan, 'minor_damage')

        credit.refresh_from_db()
        self.assertEqual(credit.damage_count, 1)
        self.assertEqual(credit.credit_score, 95)  # +2 -5 = -3

    def test_record_lost_asset(self):
        """测试记录资产遗失"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010004',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=1),
            actual_return_date=date.today(),
            status='returned',
            created_by=self.user,
        )

        from apps.loans.services import AssetLoanService
        loan_service = AssetLoanService()
        credit = loan_service.get_borrower_credit(loan)

        # 记录资产遗失
        self.service.record_return_event(loan, 'lost')

        credit.refresh_from_db()
        self.assertEqual(credit.lost_count, 1)
        self.assertEqual(credit.credit_score, 50)  # -50分

    def test_check_credit_eligibility_blacklisted(self):
        """测试黑名单用户借用资格检查"""
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=20,
            credit_level='blacklisted',
            created_by=self.user,
        )

        result = self.service.check_credit_eligibility(
            borrower_type='internal',
            borrower_id=self.user.id,
            organization_id=self.org.id
        )

        self.assertFalse(result['eligible'])
        self.assertIn('黑名单', result['reason'])
        self.assertEqual(result['credit_score'], 20)

    def test_check_credit_eligibility_asset_lost(self):
        """测试有遗失记录用户借用资格检查"""
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=50,
            credit_level='poor',
            lost_count=1,
            created_by=self.user,
        )

        result = self.service.check_credit_eligibility(
            borrower_type='internal',
            borrower_id=self.user.id,
            organization_id=self.org.id
        )

        self.assertFalse(result['eligible'])
        self.assertIn('资产遗失', result['reason'])

    def test_check_credit_eligibility_too_many_overdue(self):
        """测试超期次数过多用户借用资格检查"""
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=60,
            credit_level='normal',
            overdue_count=3,
            lost_count=0,
            created_by=self.user,
        )

        result = self.service.check_credit_eligibility(
            borrower_type='internal',
            borrower_id=self.user.id,
            organization_id=self.org.id
        )

        self.assertFalse(result['eligible'])
        self.assertIn('超期次数过多', result['reason'])

    def test_check_credit_eligibility_good(self):
        """测试良好信用用户借用资格检查"""
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=85,
            credit_level='good',
            overdue_count=0,
            lost_count=0,
            created_by=self.user,
        )

        result = self.service.check_credit_eligibility(
            borrower_type='internal',
            borrower_id=self.user.id,
            organization_id=self.org.id
        )

        self.assertTrue(result['eligible'])
        self.assertEqual(result['credit_score'], 85)
        self.assertEqual(result['credit_level'], 'good')

    def test_check_credit_eligibility_new_user(self):
        """测试新用户借用资格检查"""
        result = self.service.check_credit_eligibility(
            borrower_type='internal',
            borrower_id=self.user.id,
            organization_id=self.org.id
        )

        self.assertTrue(result['eligible'])
        self.assertEqual(result['reason'], '新用户')
```

---

## API集成测试

```python
# apps/loans/tests/test_api.py

from django.test import TestCase
from rest_framework.test import APIClient
from apps.loans.models import AssetLoan, LoanDeposit, LoanFeeRule, BorrowerCredit
from apps.accounts.models import User
from apps.organizations.models import Organization
from decimal import Decimal
from datetime import date, timedelta


class AssetLoanAPITest(TestCase):
    """资产借用API集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            organization=self.org,
            is_staff=True
        )

    def test_create_internal_loan(self):
        """测试创建内部借用"""
        response = self.client.post(
            '/api/loans/asset-loans/',
            {
                'borrower_type': 'internal',
                'borrower': str(self.user.id),
                'borrow_date': str(date.today()),
                'expected_return_date': str(date.today() + timedelta(days=15)),
                'loan_reason': '项目需要',
                'enable_deposit': False,
                'enable_overdue_fee': False,
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data']['borrower_type'], 'internal')

    def test_create_external_loan(self):
        """测试创建对外借用"""
        response = self.client.post(
            '/api/loans/asset-loans/external/',
            {
                'borrower_external_id': 'EXT001',
                'borrow_date': str(date.today()),
                'expected_return_date': str(date.today() + timedelta(days=15)),
                'loan_reason': '合作单位展示',
                'enable_deposit': True,
                'enable_overdue_fee': True,
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['borrower_type'], 'external')

    def test_get_loan_list(self):
        """测试获取借用单列表"""
        # 创建测试数据
        AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010001',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='pending',
            created_by=self.user,
        )

        response = self.client.get('/api/loans/asset-loans/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data['data'])

    def test_filter_by_borrower_type(self):
        """测试按借用类型筛选"""
        # 创建内部借用
        AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010002',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='pending',
            created_by=self.user,
        )

        # 创建对外借用
        AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010003',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='pending',
            created_by=self.user,
        )

        # 筛选内部借用
        response = self.client.get('/api/loans/asset-loans/?borrower_type=internal')
        data = response.json()
        self.assertEqual(len(data['data']['results']), 1)
        self.assertEqual(data['data']['results'][0]['borrower_type'], 'internal')

        # 筛选对外借用
        response = self.client.get('/api/loans/asset-loans/?borrower_type=external')
        data = response.json()
        self.assertEqual(len(data['data']['results']), 1)
        self.assertEqual(data['data']['results'][0]['borrower_type'], 'external')

    def test_collect_deposit_api(self):
        """测试收取押金API"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010004',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='approved',
            created_by=self.user,
            enable_deposit=True,
        )

        response = self.client.post(
            f'/api/loans/asset-loans/{loan.id}/collect-deposit/',
            {
                'deposit_amount': '5000.00',
                'payment_method': 'transfer',
                'payment_account': '6222 0000 0000 0000',
                'deposit_date': str(date.today()),
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['deposit_status'], 'collected')

    def test_collect_deposit_already_collected(self):
        """测试重复收取押金API"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010005',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='approved',
            created_by=self.user,
            enable_deposit=True,
        )

        # 第一次收取
        LoanDeposit.objects.create(
            organization=self.org,
            loan=loan,
            deposit_no='YJ2025010001',
            deposit_amount=Decimal('5000.00'),
            deposit_date=date.today(),
            payment_method='transfer',
            deposit_status='collected',
            created_by=self.user,
        )

        # 第二次收取应该失败
        response = self.client.post(
            f'/api/loans/asset-loans/{loan.id}/collect-deposit/',
            {
                'deposit_amount': '5000.00',
                'payment_method': 'transfer',
            },
            format='json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_calculate_overdue_fee_api(self):
        """测试计算超期费用API"""
        fee_rule = LoanFeeRule.objects.create(
            organization=self.org,
            name='每日50元',
            code='DAILY_50',
            daily_rate=Decimal('50.00'),
            apply_to_external=True,
            created_by=self.user,
        )

        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010006',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today() - timedelta(days=20),
            expected_return_date=date.today() - timedelta(days=5),
            status='borrowed',
            created_by=self.user,
            enable_overdue_fee=True,
        )

        response = self.client.post(
            f'/api/loans/asset-loans/{loan.id}/calculate-overdue-fee/'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertGreater(data['data']['overdue_days'], 0)
        self.assertGreater(float(data['data']['total_fee']), 0)

    def test_get_borrower_credit_api(self):
        """测试获取借用人信用API"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010007',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='pending',
            created_by=self.user,
        )

        response = self.client.get(f'/api/loans/asset-loans/{loan.id}/borrower-credit/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('data', data)

    def test_update_credit_score_api(self):
        """测试手动更新信用分API"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010008',
            borrower_type='internal',
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='returned',
            actual_return_date=date.today(),
            created_by=self.user,
        )

        response = self.client.post(
            f'/api/loans/asset-loans/{loan.id}/update-credit/',
            {
                'score_change': -5,
                'reason': '测试减分',
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['credit_score'], 95)


class LoanDepositAPITest(TestCase):
    """押金管理API测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_get_deposits_list(self):
        """测试获取押金记录列表"""
        loan = AssetLoan.objects.create(
            organization=self.org,
            loan_no='LN2025010001',
            borrower_type='external',
            borrower_external_id='EXT001',
            borrower_name='张三',
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=15),
            status='approved',
            created_by=self.user,
            enable_deposit=True,
        )

        LoanDeposit.objects.create(
            organization=self.org,
            loan=loan,
            deposit_no='YJ2025010001',
            deposit_amount=Decimal('5000.00'),
            deposit_date=date.today(),
            payment_method='transfer',
            deposit_status='collected',
            created_by=self.user,
        )

        response = self.client.get('/api/loans/deposits/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['count'], 1)

    def test_get_deposits_summary(self):
        """测试获取押金汇总"""
        response = self.client.get('/api/loans/deposits/summary/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('collected', data['data'])
        self.assertIn('refunded', data['data'])


class LoanFeeRuleAPITest(TestCase):
    """计费规则API测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_create_daily_fee_rule(self):
        """测试创建按日计费规则"""
        response = self.client.post(
            '/api/loans/fee-rules/',
            {
                'name': '每日50元',
                'code': 'DAILY_50',
                'rule_type': 'daily',
                'daily_rate': '50.00',
                'apply_to_external': True,
                'apply_to_internal': False,
                'min_overdue_days': 1,
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['rule_type'], 'daily')

    def test_create_tiered_fee_rule(self):
        """测试创建阶梯计费规则"""
        tier_config = {
            "tiers": [
                {"days_start": 1, "days_end": 7, "daily_rate": "10.00"},
                {"days_start": 8, "days_end": 30, "daily_rate": "20.00"},
            ]
        }

        response = self.client.post(
            '/api/loans/fee-rules/',
            {
                'name': '阶梯计费',
                'code': 'TIERED',
                'rule_type': 'tiered',
                'tier_config': tier_config,
                'apply_to_external': True,
                'max_fee': '5000.00',
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['rule_type'], 'tiered')

    def test_get_fee_rules(self):
        """测试获取计费规则列表"""
        LoanFeeRule.objects.create(
            organization=self.org,
            name='每日50元',
            code='DAILY_50',
            rule_type='daily',
            daily_rate=Decimal('50.00'),
            apply_to_external=True,
            created_by=self.user,
        )

        response = self.client.get('/api/loans/fee-rules/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['data']['count'], 0)


class BorrowerCreditAPITest(TestCase):
    """信用管理API测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_get_credits_list(self):
        """测试获取信用记录列表"""
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=85,
            created_by=self.user,
        )

        response = self.client.get('/api/loans/credits/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data['data']['count'], 0)

    def test_get_my_credit(self):
        """测试获取我的信用"""
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=85,
            created_by=self.user,
        )

        response = self.client.get('/api/loans/credits/my-credit/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['borrower_type'], 'internal')

    def test_check_eligibility(self):
        """测试检查借用资格"""
        # 创建良好信用记录
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=85,
            credit_level='good',
            created_by=self.user,
        )

        response = self.client.post(
            '/api/loans/credits/check-eligibility/',
            {
                'borrower_type': 'internal',
                'borrower_user_id': str(self.user.id),
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['data']['eligible'])

    def test_check_eligibility_blacklisted(self):
        """测试检查黑名单用户资格"""
        BorrowerCredit.objects.create(
            organization=self.org,
            borrower_type='internal',
            borrower_user=self.user,
            credit_score=20,
            credit_level='blacklisted',
            created_by=self.user,
        )

        response = self.client.post(
            '/api/loans/credits/check-eligibility/',
            {
                'borrower_type': 'internal',
                'borrower_user_id': str(self.user.id),
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['data']['eligible'])
        self.assertIn('黑名单', data['data']['reason'])
```

---

## 前端组件测试

```vue
<!-- src/views/loans/__tests__/LoanForm.spec.vue -->
<script setup>
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LoanForm from '../LoanForm.vue'
import { createPinia, setActivePinia } from 'pinia'
import ElMessage from 'element-plus'

// Mock API
vi.mock('@/api/loans', () => ({
  createLoan: vi.fn(() => Promise.resolve({
    success: true,
    data: { id: 'loan-uuid', loan_no: 'LN2025010001' }
  })),
  updateLoan: vi.fn(() => Promise.resolve({ success: true })),
  getLoan: vi.fn(() => Promise.resolve({
    success: true,
    data: {
      id: 'loan-uuid',
      loan_no: 'LN2025010001',
      borrower_type: 'internal',
      status: 'pending'
    }
  })),
  checkCreditEligibility: vi.fn(() => Promise.resolve({
    success: true,
    data: { eligible: true, credit_score: 85 }
  }))
}))

describe('LoanForm.vue', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)

    wrapper = mount(LoanForm, {
      props: {
        loanId: null
      },
      global: {
        stubs: {
          ElForm: true,
          ElFormItem: true,
          ElInput: true,
          ElSelect: true,
          ElOption: true,
          ElDatePicker: true,
          ElSwitch: true,
          ElButton: true,
          ElDialog: true
        },
        mocks: {
          $router: { push: vi.fn() }
        }
      }
    })
  })

  it('初始化表单', () => {
    expect(wrapper.vm.form.borrower_type).toBe('internal')
    expect(wrapper.vm.form.enable_deposit).toBe(false)
    expect(wrapper.vm.form.enable_overdue_fee).toBe(false)
  })

  it('切换借用类型', async () => {
    await wrapper.vm.handleBorrowerTypeChange('external')

    expect(wrapper.vm.form.borrower_type).toBe('external')
    expect(wrapper.vm.form.borrower).toBeNull()
  })

  it('启用押金时显示金额输入', async () => {
    wrapper.vm.form.enable_deposit = true
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.showDepositAmount).toBe(true)
  })

  it('提交借用单', async () => {
    wrapper.vm.form = {
      borrower_type: 'internal',
      borrower: 'user-uuid',
      borrow_date: new Date(),
      expected_return_date: new Date(),
      loan_reason: '测试',
      enable_deposit: false,
      enable_overdue_fee: false
    }

    await wrapper.vm.handleSubmit()

    // 验证API被调用
    const { createLoan } = await import('@/api/loans')
    expect(createLoan).toHaveBeenCalled()
  })
})
</script>
```

```vue
<!-- src/views/loans/__tests__/DepositManager.spec.vue -->
<script setup>
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DepositManager from '../DepositManager.vue'

vi.mock('@/api/loans', () => ({
  collectDeposit: vi.fn(() => Promise.resolve({
    success: true,
    data: {
      id: 'deposit-uuid',
      deposit_no: 'YJ2025010001',
      deposit_status: 'collected'
    }
  })),
  refundDeposit: vi.fn(() => Promise.resolve({
    success: true,
    data: {
      deposit_status: 'refunded',
      refunded_amount: '4750.00'
    }
  }))
}))

describe('DepositManager.vue', () => {
  it('显示收取押金对话框', async () => {
    const wrapper = mount(DepositManager, {
      props: {
        loan: {
          id: 'loan-uuid',
          enable_deposit: true,
          loan_no: 'LN2025010001'
        }
      },
      global: {
        stubs: {
          ElDialog: true,
          ElForm: true,
          ElInput: true,
          ElButton: true
        }
      }
    })

    wrapper.vm.openCollectDialog()
    expect(wrapper.vm.collectDialogVisible).toBe(true)
  })

  it('提交收取押金', async () => {
    const wrapper = mount(DepositManager, {
      props: {
        loan: {
          id: 'loan-uuid',
          enable_deposit: true
        }
      },
      global: { stubs: { ElDialog: true, ElForm: true, ElButton: true } }
    })

    wrapper.vm.collectForm = {
      deposit_amount: '5000.00',
      payment_method: 'transfer',
      payment_account: '6222 0000 0000 0000'
    }

    await wrapper.vm.handleCollectDeposit()

    const { collectDeposit } = await import('@/api/loans')
    expect(collectDeposit).toHaveBeenCalled()
  })

  it('退还押金验证', async () => {
    const wrapper = mount(DepositManager, {
      props: {
        loan: {
          id: 'loan-uuid',
          enable_deposit: true
        },
        deposit: {
          id: 'deposit-uuid',
          deposit_amount: '5000.00',
          deposit_status: 'collected'
        }
      },
      global: { stubs: { ElDialog: true, ElForm: true, ElButton: true } }
    })

    wrapper.vm.refundForm = {
      amount: '6000.00',  // 超过押金金额
      reason: '测试'
    }

    const valid = await wrapper.vm.validateRefundAmount()
    expect(valid).toBe(false)
  })
})
</script>
```

```vue
<!-- src/views/loans/__tests__/CreditScoreDisplay.spec.vue -->
<script setup>
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import CreditScoreDisplay from '../CreditScoreDisplay.vue'

describe('CreditScoreDisplay.vue', () => {
  it('显示信用分数', () => {
    const wrapper = mount(CreditScoreDisplay, {
      props: {
        creditScore: 85,
        creditLevel: 'good'
      }
    })

    expect(wrapper.text()).toContain('85')
    expect(wrapper.find('.credit-level-good').exists()).toBe(true)
  })

  it('信用等级颜色映射', () => {
    const wrapper = mount(CreditScoreDisplay, {
      props: {
        creditScore: 95,
        creditLevel: 'excellent'
      }
    })

    expect(wrapper.vm.levelColor).toBe('#67C23A')
  })

  it('显示信用历史', async () => {
    const wrapper = mount(CreditScoreDisplay, {
      props: {
        creditScore: 85,
        creditLevel: 'good'
      },
      global: {
        stubs: {
          ElTimeline: true,
          ElTimelineItem: true
        }
      }
    })

    wrapper.vm.histories = [
      {
        id: '1',
        event_type: 'returned_normal',
        event_date: '2025-01-15',
        score_change: 2,
        score_after: 87,
        event_description: '正常归还'
      }
    ]

    await wrapper.vm.$nextTick()
    expect(wrapper.vm.histories.length).toBe(1)
  })
})
</script>
```

---

## E2E测试

```python
# tests/e2e/test_loan_e2e.py

from playwright.sync_api import Page, expect


class TestLoanE2E:
    """借用流程端到端测试"""

    def setup_method(self):
        self.page = self.browser.new_page()
        self.page.goto('http://localhost:5173/login')
        # 登录
        self.page.fill('input[name="username"]', 'admin')
        self.page.fill('input[name="password"]', 'admin123')
        self.page.click('button:has-text("登录")')

    def test_create_external_loan_flow(self):
        """测试创建对外借用完整流程"""
        # 进入借用管理页面
        self.page.goto('http://localhost:5173/loans')
        self.page.click('button:has-text("新建借用")')

        # 选择借用类型
        self.page.click('input[value="external"]')

        # 选择外部人员
        self.page.click('.external-person-selector')
        self.page.click('text=张三')

        # 填写借用信息
        self.page.fill('[name="borrow_date"]', '2025-01-01')
        self.page.fill('[name="expected_return_date"]', '2025-01-15')
        self.page.fill('[name="loan_reason"]', '合作单位展示使用')

        # 启用押金
        self.page.click('[name="enable_deposit"]')
        self.page.fill('[name="deposit_amount"]', '5000')

        # 启用超期计费
        self.page.click('[name="enable_overdue_fee"]')

        # 添加借用明细
        self.page.click('button:has-text("添加资产")')
        self.page.fill('.asset-selector input', 'ZC001')
        self.page.click('text=MacBook Pro')
        self.page.fill('[name="quantity"]', '1')

        # 提交
        self.page.click('button:has-text("提交")')

        # 验证成功提示
        self.page.wait_for_selector('.el-message--success')
        expect(self.page).to_have_url('http://localhost:5173/loans')

    def test_collect_deposit_flow(self):
        """测试收取押金流程"""
        # 进入借用单详情
        self.page.goto('http://localhost:5173/loans/loan-uuid')

        # 点击收取押金
        self.page.click('button:has-text("收取押金")')

        # 等待对话框
        self.page.wait_for_selector('.deposit-dialog')

        # 填写押金信息
        self.page.fill('[name="deposit_amount"]', '5000')
        self.page.select_option('[name="payment_method"]', 'transfer')
        self.page.fill('[name="payment_account"]', '6222 0000 0000 0000')

        # 确认收取
        self.page.click('button:has-text("确认收取")')

        # 验证成功
        self.page.wait_for_selector('.el-message--success')
        expect(self.page.locator('.deposit-status')).to_have_text('已收取')

    def test_refund_deposit_flow(self):
        """测试退还押金流程"""
        # 进入已归还的借用单
        self.page.goto('http://localhost:5173/loans/loan-uuid')

        # 点击退还押金
        self.page.click('button:has-text("退还押金")')

        # 填写退款信息
        self.page.fill('[name="amount"]', '4750')
        self.page.fill('[name="reason"]', '正常归还，扣除超期费用250元')

        # 确认退还
        self.page.click('button:has-text("确认退还")')

        # 验证成功
        self.page.wait_for_selector('.el-message--success')

    def test_check_credit_before_loan(self):
        """测试借用前检查信用"""
        # 进入创建借用页面
        self.page.goto('http://localhost:5173/loans/new')

        # 选择外部人员
        self.page.click('.external-person-selector')
        self.page.click('text=张三')

        # 等待信用检查完成
        self.page.wait_for_selector('.credit-check-result')

        # 验证信用显示
        credit_score = self.page.locator('.credit-score')
        expect(credit_score).to_be_visible()

    def test_overdue_fee_calculation(self):
        """测试超期费用计算"""
        # 进入超期借用单
        self.page.goto('http://localhost:5173/loans/overdue-loan-uuid')

        # 点击计算费用
        self.page.click('button:has-text("计算超期费用")')

        # 等待计算完成
        self.page.wait_for_selector('.fee-calculation-result')

        # 验证费用显示
        overdue_days = self.page.locator('.overdue-days')
        expect(overdue_days).to_be_visible()

        total_fee = self.page.locator('.total-fee')
        expect(total_fee).to_be_visible()
```

---

## 验收标准检查清单

### 后端验收

- [ ] AssetLoan模型支持内部/外部借用类型
- [ ] LoanDeposit押金记录正常创建和更新
- [ ] LoanFeeRule计费规则（按日/阶梯）正常工作
- [ ] LoanOverdueFee超期费用计算正确
- [ ] BorrowerCredit信用评分和等级计算正确
- [ ] CreditHistory历史记录完整
- [ ] 软删除功能正常
- [ ] 组织隔离正常
- [ ] 审计字段自动填充

### API验收

- [ ] 借用单CRUD接口正常
- [ ] 收取/退还押金接口正常
- [ ] 超期费用计算接口正常
- [ ] 信用查询和更新接口正常
- [ ] 借用资格检查接口正常
- [ ] 批量操作接口正常
- [ ] 错误码和错误消息正确

### 前端验收

- [ ] LoanForm组件正常提交
- [ ] DepositManager组件正常收取/退还
- [ ] CreditScoreDisplay组件正确显示
- [ ] 借用单列表和详情页正常
- [ ] 外部人员选择器正常
- [ ] 押金管理界面正常
- [ ] 信用历史展示正常

---

## 运行测试命令

```bash
# 后端单元测试
docker-compose exec backend python manage.py test apps.loans.tests

# 运行特定测试
docker-compose exec backend python manage.py test apps.loans.tests.test_models
docker-compose exec backend python manage.py test apps.loans.tests.test_services
docker-compose exec backend python manage.py test apps.loans.tests.test_api

# 带覆盖率报告
docker-compose exec backend coverage run --source='apps.loans' manage.py test apps.loans.tests
docker-compose exec backend coverage report

# 前端测试
npm run test

# E2E测试
npm run test:e2e
```

---

## 性能测试

```python
# apps/loans/tests/test_performance.py

from django.test import TestCase
from apps.loans.models import AssetLoan, LoanDeposit
from apps.accounts.models import User
from apps.organizations.models import Organization
from datetime import date, timedelta
import time


class LoanPerformanceTest(TestCase):
    """借用模块性能测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

    def test_large_loan_list_query_performance(self):
        """测试大数据量借用单列表查询性能"""
        # 创建1000条借用记录
        for i in range(1000):
            AssetLoan.objects.create(
                organization=self.org,
                loan_no=f'LN{i:06d}',
                borrower_type='internal',
                borrower=self.user,
                borrow_date=date.today() - timedelta(days=i % 365),
                expected_return_date=date.today() - timedelta(days=i % 365) + timedelta(days=15),
                status='pending',
                created_by=self.user,
            )

        # 测试查询性能
        start = time.time()
        loans = AssetLoan.objects.filter(organization=self.org)
        count = loans.count()
        elapsed = time.time() - start

        self.assertEqual(count, 1000)
        self.assertLess(elapsed, 0.5)  # 应在500ms内完成

    def test_deposit_query_performance(self):
        """测试押金查询性能"""
        # 创建借用单和押金
        for i in range(500):
            loan = AssetLoan.objects.create(
                organization=self.org,
                loan_no=f'LN{i:06d}',
                borrower_type='external',
                borrower_external_id=f'EXT{i}',
                borrower_name=f'借用人{i}',
                borrow_date=date.today(),
                expected_return_date=date.today() + timedelta(days=15),
                status='approved',
                created_by=self.user,
                enable_deposit=True,
            )

            LoanDeposit.objects.create(
                organization=self.org,
                loan=loan,
                deposit_no=f'YJ{i:06d}',
                deposit_amount=5000.00,
                deposit_date=date.today(),
                payment_method='transfer',
                deposit_status='collected',
                created_by=self.user,
            )

        # 测试关联查询性能
        start = time.time()
        loans_with_deposits = AssetLoan.objects.select_related('organization').prefetch_related('deposits')
        result = list(loans_with_deposits[:100])
        elapsed = time.time() - start

        self.assertEqual(len(result), 100)
        self.assertLess(elapsed, 0.3)  # 应在300ms内完成
```
