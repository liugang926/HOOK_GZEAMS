import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory, AssetLoan, AssetReturn, LoanItem, Location, ReturnItem
from apps.depreciation.models import DepreciationRecord
from apps.finance.models import FinanceVoucher, VoucherEntry
from apps.inventory.models import InventoryDifference, InventoryFollowUp, InventoryTask
from apps.insurance.models import ClaimRecord, InsuranceCompany, InsurancePolicy, PremiumPayment
from apps.integration.models import IntegrationLog
from apps.leasing.models import LeaseContract, LeaseItem, RentPayment
from apps.lifecycle.models import AssetReceipt, AssetReceiptItem, PurchaseRequest, PurchaseRequestItem
from apps.organizations.models import Department, Organization
from apps.projects.models import AssetProject, ProjectAsset
from apps.system.services.object_closure_binding_service import ObjectClosureBindingService


def _build_org_and_user(suffix: str):
    organization = Organization.objects.create(
        name=f'Closure Org {suffix}',
        code=f'CLOSURE_ORG_{suffix}',
    )
    user = User.objects.create_user(
        username=f'closure_user_{suffix}',
        email=f'closure_{suffix}@example.com',
        password='pass123456',
        organization=organization,
    )
    return organization, user


def _build_department(organization, suffix: str):
    return Department.objects.create(
        organization=organization,
        code=f'DEPT_{suffix}',
        name=f'Department {suffix}',
    )


@pytest.mark.django_db
def test_finance_voucher_summary_exposes_sync_blocker_metrics():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    voucher = FinanceVoucher.objects.create(
        organization=organization,
        voucher_no=f'FV-{suffix}',
        voucher_date=date.today(),
        business_type='purchase',
        summary='Finance voucher closure test',
        total_amount=Decimal('100.00'),
        status='approved',
        created_by=user,
    )
    VoucherEntry.objects.create(
        organization=organization,
        voucher=voucher,
        account_code='1001',
        account_name='Cash',
        debit_amount=Decimal('100.00'),
        credit_amount=Decimal('0.00'),
        description='Debit line',
        line_no=1,
        created_by=user,
    )
    VoucherEntry.objects.create(
        organization=organization,
        voucher=voucher,
        account_code='2001',
        account_name='Payable',
        debit_amount=Decimal('0.00'),
        credit_amount=Decimal('100.00'),
        description='Credit line',
        line_no=2,
        created_by=user,
    )
    IntegrationLog.objects.create(
        organization=organization,
        system_type='m18',
        integration_type='m18_finance_voucher',
        action='push',
        request_method='POST',
        request_url='/external/m18/finance/vouchers',
        request_body={'voucher_id': str(voucher.id)},
        response_body={'error': 'timeout'},
        status_code=500,
        success=False,
        error_message='timeout',
        business_type='voucher',
        business_id=str(voucher.id),
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='FinanceVoucher',
        business_id=str(voucher.id),
        instance=voucher,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Ready for ERP posting'
    assert summary['blocker'] == 'Review ERP integration errors and retry the push.'
    assert summary['owner'] == user.username
    assert summary['completionDisplay'] == '75%'
    assert summary['metrics']['failedSyncCount'] == 1
    assert summary['metrics']['entryCount'] == 2


@pytest.mark.django_db
def test_insurance_policy_summary_surfaces_pending_premiums_and_open_claims():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    company = InsuranceCompany.objects.create(
        organization=organization,
        code=f'INS-{suffix}',
        name='Closure Insurance',
        created_by=user,
    )
    policy = InsurancePolicy.objects.create(
        organization=organization,
        policy_no=f'POL-{suffix}',
        company=company,
        insurance_type='property',
        start_date=date.today() - timedelta(days=10),
        end_date=date.today() + timedelta(days=15),
        total_insured_amount=Decimal('100000.00'),
        total_premium=Decimal('5000.00'),
        status='active',
        created_by=user,
    )
    PremiumPayment.objects.create(
        organization=organization,
        policy=policy,
        payment_no=f'PAY-{suffix}',
        due_date=date.today(),
        amount=Decimal('2500.00'),
        paid_amount=Decimal('0.00'),
        status='pending',
        created_by=user,
    )
    ClaimRecord.objects.create(
        organization=organization,
        policy=policy,
        incident_date=date.today() - timedelta(days=3),
        incident_type='damage',
        incident_description='Damage incident',
        claim_date=date.today() - timedelta(days=2),
        claimed_amount=Decimal('1800.00'),
        status='reported',
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='InsurancePolicy',
        business_id=str(policy.id),
        instance=policy,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Active coverage'
    assert summary['blocker'] == 'Resolve outstanding premiums and open claims before closing the policy.'
    assert summary['completionDisplay'] == '55%'
    assert summary['metrics']['pendingPaymentCount'] == 1
    assert summary['metrics']['openClaimCount'] == 1
    assert summary['metrics']['isExpiringSoon'] is True


@pytest.mark.django_db
def test_claim_record_summary_tracks_settlement_stage():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    company = InsuranceCompany.objects.create(
        organization=organization,
        code=f'CLAIM-{suffix}',
        name='Claim Insurance',
        created_by=user,
    )
    policy = InsurancePolicy.objects.create(
        organization=organization,
        policy_no=f'POL-C-{suffix}',
        company=company,
        insurance_type='property',
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=30),
        total_insured_amount=Decimal('200000.00'),
        total_premium=Decimal('8000.00'),
        status='active',
        created_by=user,
    )
    claim = ClaimRecord.objects.create(
        organization=organization,
        policy=policy,
        incident_date=date.today() - timedelta(days=5),
        incident_type='damage',
        incident_description='Major device damage',
        claim_date=date.today() - timedelta(days=4),
        claimed_amount=Decimal('3000.00'),
        approved_amount=Decimal('2400.00'),
        status='approved',
        adjuster_name='Adjuster Lee',
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='ClaimRecord',
        business_id=str(claim.id),
        instance=claim,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Approved for settlement'
    assert summary['approvalStatus'] == 'approved'
    assert summary['owner'] == 'Adjuster Lee'
    assert summary['blocker'] == 'Record settlement payment to continue closure.'
    assert summary['metrics']['claimedAmount'] == 3000.0
    assert summary['metrics']['approvedAmount'] == 2400.0
    assert summary['metrics']['payoutRatio'] == 80.0


@pytest.mark.django_db
def test_leasing_contract_summary_counts_pending_returns_and_open_payments():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    category = AssetCategory.objects.create(
        organization=organization,
        code=f'CAT-{suffix}',
        name='Closure Category',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        asset_code=f'ASSET-{suffix}',
        asset_name='Leased Asset',
        asset_category=category,
        purchase_price=Decimal('1200.00'),
        current_value=Decimal('1200.00'),
        purchase_date=date.today() - timedelta(days=90),
        created_by=user,
    )
    contract = LeaseContract.objects.create(
        organization=organization,
        contract_no=f'LC-{suffix}',
        lessee_name='Closure Customer',
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=5),
        total_rent=Decimal('900.00'),
        status='active',
        actual_start_date=date.today() - timedelta(days=30),
        approved_by=user,
        created_by=user,
    )
    LeaseItem.objects.create(
        organization=organization,
        contract=contract,
        asset=asset,
        daily_rate=Decimal('30.00'),
        actual_start_date=date.today() - timedelta(days=30),
        created_by=user,
    )
    RentPayment.objects.create(
        organization=organization,
        contract=contract,
        payment_no=f'RENT-{suffix}',
        due_date=date.today() - timedelta(days=3),
        amount=Decimal('450.00'),
        paid_amount=Decimal('0.00'),
        status='pending',
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='LeasingContract',
        business_id=str(contract.id),
        instance=contract,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Active lease'
    assert summary['blocker'] == 'Record all asset returns before completing the contract.'
    assert summary['completionDisplay'] == '45%'
    assert summary['metrics']['leasedAssetCount'] == 1
    assert summary['metrics']['returnedAssetCount'] == 0
    assert summary['metrics']['pendingReturnCount'] == 1
    assert summary['metrics']['openPaymentCount'] == 1


@pytest.mark.django_db
def test_asset_summary_surfaces_cross_object_blockers_and_source_traceability():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    department = _build_department(organization, suffix)
    category = AssetCategory.objects.create(
        organization=organization,
        code=f'ASSET-CAT-{suffix}',
        name='Asset Closure Category',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        asset_code=f'ASSET-CLOSURE-{suffix}',
        asset_name='Closure Asset',
        asset_category=category,
        purchase_price=Decimal('8600.00'),
        current_value=Decimal('5200.00'),
        purchase_date=date.today() - timedelta(days=120),
        asset_status='idle',
        created_by=user,
    )
    task = InventoryTask.objects.create(
        organization=organization,
        task_code=f'INV-{suffix}',
        task_name='Asset Closure Inventory',
        inventory_type=InventoryTask.TYPE_FULL,
        planned_date=date.today(),
        created_by=user,
    )
    difference = InventoryDifference.objects.create(
        organization=organization,
        task=task,
        asset=asset,
        difference_type=InventoryDifference.TYPE_MISSING,
        description='Asset not found during inventory',
        status=InventoryDifference.STATUS_APPROVED,
        created_by=user,
    )
    InventoryFollowUp.objects.create(
        organization=organization,
        task=task,
        difference=difference,
        asset=asset,
        title='Manual finance follow-up',
        closure_type=InventoryDifference.CLOSURE_TYPE_FINANCIAL_ADJUSTMENT,
        linked_action_code='finance.adjustment',
        status=InventoryFollowUp.STATUS_PENDING,
        assignee=user,
        created_by=user,
    )
    project = AssetProject.objects.create(
        organization=organization,
        project_name='Asset Closure Project',
        project_manager=user,
        department=department,
        start_date=date.today() - timedelta(days=10),
        status='active',
        created_by=user,
    )
    ProjectAsset.objects.create(
        organization=organization,
        project=project,
        asset=asset,
        allocation_date=date.today() - timedelta(days=5),
        allocated_by=user,
        return_status='in_use',
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='Asset',
        business_id=str(asset.id),
        instance=asset,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Inventory exception pending'
    assert summary['blocker'] == 'Resolve inventory differences and manual follow-up tasks before closure.'
    assert summary['owner'] == user.username
    assert summary['completionDisplay'] == '65%'
    assert summary['metrics']['activeProjectAllocationCount'] == 1
    assert summary['metrics']['pendingInventoryDifferenceCount'] == 1
    assert summary['metrics']['pendingInventoryFollowUpCount'] == 1
    assert summary['metrics']['sourceReceiptNo'] == ''
    assert summary['metrics']['sourcePurchaseRequestNo'] == ''


@pytest.mark.django_db
def test_asset_summary_tracks_open_finance_vouchers_after_operational_blockers_clear():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    category = AssetCategory.objects.create(
        organization=organization,
        code=f'FIN-CAT-{suffix}',
        name='Finance Closure Category',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        asset_code=f'ASSET-FIN-{suffix}',
        asset_name='Finance Linked Asset',
        asset_category=category,
        purchase_price=Decimal('3200.00'),
        current_value=Decimal('2800.00'),
        purchase_date=date.today() - timedelta(days=20),
        asset_status='idle',
        created_by=user,
    )
    FinanceVoucher.objects.create(
        organization=organization,
        voucher_no=f'FV-ASSET-{suffix}',
        voucher_date=date.today(),
        business_type='purchase',
        summary='Asset purchase voucher',
        total_amount=Decimal('3200.00'),
        status='approved',
        custom_fields={
            'source_object_code': 'Asset',
            'source_id': str(asset.id),
            'source_record_no': asset.asset_code,
            'asset_ids': [str(asset.id)],
            'asset_id_index': f'|{asset.id}|',
            'source_trace': {
                'source_object_code': 'Asset',
                'source_object_label': 'Asset',
                'source_id': str(asset.id),
                'source_record_no': asset.asset_code,
                'asset_ids': [str(asset.id)],
                'asset_codes': [asset.asset_code],
                'asset_id_index': f'|{asset.id}|',
            },
        },
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='Asset',
        business_id=str(asset.id),
        instance=asset,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Finance posting pending'
    assert summary['blocker'] == 'Submit, approve, and post linked finance vouchers to complete financial closure.'
    assert summary['completionDisplay'] == '85%'
    assert summary['metrics']['linkedFinanceVoucherCount'] == 1
    assert summary['metrics']['openFinanceVoucherCount'] == 1
    assert summary['metrics']['latestFinanceVoucherNo'] == f'FV-ASSET-{suffix}'
    assert summary['metrics']['latestFinanceVoucherStatus'] == 'approved'


@pytest.mark.django_db
def test_asset_summary_tracks_open_loans_before_finance_closure():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    category = AssetCategory.objects.create(
        organization=organization,
        code=f'LOAN-CAT-{suffix}',
        name='Loan Closure Category',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        asset_code=f'ASSET-LOAN-{suffix}',
        asset_name='Loaned Asset',
        asset_category=category,
        purchase_price=Decimal('4200.00'),
        current_value=Decimal('4200.00'),
        purchase_date=date.today() - timedelta(days=14),
        asset_status='lent',
        created_by=user,
    )
    loan = AssetLoan.objects.create(
        organization=organization,
        borrower=user,
        borrow_date=date.today() - timedelta(days=2),
        expected_return_date=date.today() + timedelta(days=7),
        status='borrowed',
        created_by=user,
    )
    LoanItem.objects.create(
        organization=organization,
        loan=loan,
        asset=asset,
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='Asset',
        business_id=str(asset.id),
        instance=asset,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Loan in progress'
    assert summary['blocker'] == 'Complete the loan return flow before closing the asset lifecycle.'
    assert summary['metrics']['openLoanCount'] == 1


@pytest.mark.django_db
def test_asset_summary_tracks_pending_depreciation_after_operational_blockers_clear():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    category = AssetCategory.objects.create(
        organization=organization,
        code=f'DEP-CAT-{suffix}',
        name='Depreciation Closure Category',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        asset_code=f'ASSET-DEP-{suffix}',
        asset_name='Depreciating Asset',
        asset_category=category,
        purchase_price=Decimal('9800.00'),
        current_value=Decimal('9100.00'),
        purchase_date=date.today() - timedelta(days=45),
        asset_status='idle',
        created_by=user,
    )
    DepreciationRecord.objects.create(
        organization=organization,
        asset=asset,
        period=date.today().strftime('%Y-%m'),
        depreciation_amount=Decimal('700.00'),
        accumulated_amount=Decimal('700.00'),
        net_value=Decimal('9100.00'),
        status='calculated',
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='Asset',
        business_id=str(asset.id),
        instance=asset,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Depreciation posting pending'
    assert summary['blocker'] == 'Post or resolve outstanding depreciation records before accounting closure.'
    assert summary['metrics']['pendingDepreciationCount'] == 1


@pytest.mark.django_db
def test_purchase_request_summary_tracks_finance_posting_after_assets_are_generated():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    department_org = Organization.objects.create(
        name=f'Lifecycle Department {suffix}',
        code=f'LIFECYCLE_DEPT_{suffix}',
        org_type='department',
        parent=organization,
    )
    category = AssetCategory.objects.create(
        organization=organization,
        code=f'PR-CAT-{suffix}',
        name='Purchase Request Category',
        created_by=user,
    )
    purchase_request = PurchaseRequest.objects.create(
        organization=organization,
        applicant=user,
        department=department_org,
        request_date=date.today() - timedelta(days=7),
        expected_date=date.today() + timedelta(days=3),
        reason='Need a tracked workstation',
        status='processing',
        created_by=user,
    )
    PurchaseRequestItem.objects.create(
        organization=organization,
        purchase_request=purchase_request,
        asset_category=category,
        sequence=1,
        item_name='Tracked Workstation',
        specification='16-inch',
        brand='OpenAI',
        quantity=1,
        unit='pcs',
        unit_price=Decimal('8800.00'),
        total_amount=Decimal('8800.00'),
        created_by=user,
    )
    receipt = AssetReceipt.objects.create(
        organization=organization,
        purchase_request=purchase_request,
        receipt_date=date.today() - timedelta(days=2),
        receiver=user,
        status='passed',
        supplier='Closure Supplier',
        created_by=user,
    )
    receipt_item = AssetReceiptItem.objects.create(
        organization=organization,
        asset_receipt=receipt,
        asset_category=category,
        sequence=1,
        item_name='Tracked Workstation',
        specification='16-inch',
        brand='OpenAI',
        ordered_quantity=1,
        received_quantity=1,
        qualified_quantity=1,
        defective_quantity=0,
        unit_price=Decimal('8800.00'),
        total_amount=Decimal('8800.00'),
        asset_generated=True,
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        asset_code=f'ASSET-PR-{suffix}',
        asset_name='Tracked Workstation',
        asset_category=category,
        purchase_price=Decimal('8800.00'),
        current_value=Decimal('8800.00'),
        purchase_date=date.today() - timedelta(days=2),
        source_purchase_request=purchase_request,
        source_receipt=receipt,
        source_receipt_item=receipt_item,
        created_by=user,
    )
    FinanceVoucher.objects.create(
        organization=organization,
        voucher_no=f'FV-PR-{suffix}',
        voucher_date=date.today(),
        business_type='purchase',
        summary='Purchase request voucher',
        total_amount=Decimal('8800.00'),
        status='approved',
        custom_fields={
            'source_object_code': 'PurchaseRequest',
            'source_id': str(purchase_request.id),
            'source_record_no': purchase_request.request_no,
            'source_purchase_request_id': str(purchase_request.id),
            'source_purchase_request_no': purchase_request.request_no,
            'source_receipt_id': str(receipt.id),
            'source_receipt_no': receipt.receipt_no,
            'asset_ids': [str(asset.id)],
            'asset_id_index': f'|{asset.id}|',
        },
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='PurchaseRequest',
        business_id=str(purchase_request.id),
        instance=purchase_request,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Finance posting pending'
    assert summary['blocker'] == 'Submit, approve, and post linked finance vouchers to complete financial closure.'
    assert summary['completionDisplay'] == '90%'
    assert summary['owner'] == user.username
    assert summary['metrics']['linkedReceiptCount'] == 1
    assert summary['metrics']['generatedAssetCount'] == 1
    assert summary['metrics']['pendingGenerationCount'] == 0
    assert summary['metrics']['linkedFinanceVoucherCount'] == 1
    assert summary['metrics']['openFinanceVoucherCount'] == 1
    assert summary['metrics']['latestReceiptNo'] == receipt.receipt_no


@pytest.mark.django_db
def test_asset_receipt_summary_tracks_pending_generation_before_finance_closure():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    department_org = Organization.objects.create(
        name=f'Receipt Department {suffix}',
        code=f'RECEIPT_DEPT_{suffix}',
        org_type='department',
        parent=organization,
    )
    category = AssetCategory.objects.create(
        organization=organization,
        code=f'RC-CAT-{suffix}',
        name='Receipt Category',
        created_by=user,
    )
    purchase_request = PurchaseRequest.objects.create(
        organization=organization,
        applicant=user,
        department=department_org,
        request_date=date.today() - timedelta(days=5),
        expected_date=date.today() + timedelta(days=2),
        reason='Need receipt closure coverage',
        status='processing',
        created_by=user,
    )
    receipt = AssetReceipt.objects.create(
        organization=organization,
        purchase_request=purchase_request,
        receipt_date=date.today() - timedelta(days=1),
        receiver=user,
        status='passed',
        supplier='Receipt Supplier',
        created_by=user,
    )
    AssetReceiptItem.objects.create(
        organization=organization,
        asset_receipt=receipt,
        asset_category=category,
        sequence=1,
        item_name='Receipt Device',
        specification='13-inch',
        brand='OpenAI',
        ordered_quantity=2,
        received_quantity=2,
        qualified_quantity=2,
        defective_quantity=0,
        unit_price=Decimal('2600.00'),
        total_amount=Decimal('5200.00'),
        asset_generated=False,
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='AssetReceipt',
        business_id=str(receipt.id),
        instance=receipt,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Asset generation pending'
    assert summary['blocker'] == 'Generate asset cards for qualified receipt items.'
    assert summary['completionDisplay'] == '75%'
    assert summary['owner'] == user.username
    assert summary['metrics']['totalItems'] == 1
    assert summary['metrics']['totalQualifiedCount'] == 2
    assert summary['metrics']['generatedAssetCount'] == 0
    assert summary['metrics']['pendingGenerationCount'] == 2
    assert summary['metrics']['sourcePurchaseRequestNo'] == purchase_request.request_no


@pytest.mark.django_db
def test_asset_receipt_summary_tracks_finance_posting_after_assets_are_generated():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    department_org = Organization.objects.create(
        name=f'Receipt Finance Department {suffix}',
        code=f'RECEIPT_FIN_DEPT_{suffix}',
        org_type='department',
        parent=organization,
    )
    category = AssetCategory.objects.create(
        organization=organization,
        code=f'RC-FIN-CAT-{suffix}',
        name='Receipt Finance Category',
        created_by=user,
    )
    purchase_request = PurchaseRequest.objects.create(
        organization=organization,
        applicant=user,
        department=department_org,
        request_date=date.today() - timedelta(days=6),
        expected_date=date.today() + timedelta(days=1),
        reason='Need receipt finance closure',
        status='completed',
        created_by=user,
    )
    receipt = AssetReceipt.objects.create(
        organization=organization,
        purchase_request=purchase_request,
        receipt_date=date.today() - timedelta(days=2),
        receiver=user,
        inspector=user,
        status='passed',
        supplier='Receipt Finance Supplier',
        created_by=user,
    )
    receipt_item = AssetReceiptItem.objects.create(
        organization=organization,
        asset_receipt=receipt,
        asset_category=category,
        sequence=1,
        item_name='Receipt Finance Device',
        specification='15-inch',
        brand='OpenAI',
        ordered_quantity=1,
        received_quantity=1,
        qualified_quantity=1,
        defective_quantity=0,
        unit_price=Decimal('4100.00'),
        total_amount=Decimal('4100.00'),
        asset_generated=True,
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        asset_code=f'ASSET-RC-{suffix}',
        asset_name='Receipt Finance Device',
        asset_category=category,
        purchase_price=Decimal('4100.00'),
        current_value=Decimal('4100.00'),
        purchase_date=date.today() - timedelta(days=2),
        source_purchase_request=purchase_request,
        source_receipt=receipt,
        source_receipt_item=receipt_item,
        created_by=user,
    )
    FinanceVoucher.objects.create(
        organization=organization,
        voucher_no=f'FV-RC-{suffix}',
        voucher_date=date.today(),
        business_type='purchase',
        summary='Receipt voucher',
        total_amount=Decimal('4100.00'),
        status='approved',
        custom_fields={
            'source_object_code': 'AssetReceipt',
            'source_id': str(receipt.id),
            'source_record_no': receipt.receipt_no,
            'source_purchase_request_id': str(purchase_request.id),
            'source_purchase_request_no': purchase_request.request_no,
            'source_receipt_id': str(receipt.id),
            'source_receipt_no': receipt.receipt_no,
            'asset_ids': [str(asset.id)],
            'asset_id_index': f'|{asset.id}|',
        },
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='AssetReceipt',
        business_id=str(receipt.id),
        instance=receipt,
        organization_id=str(organization.id),
    )

    assert summary['stage'] == 'Finance posting pending'
    assert summary['blocker'] == 'Submit, approve, and post linked finance vouchers to complete financial closure.'
    assert summary['completionDisplay'] == '90%'
    assert summary['metrics']['generatedAssetCount'] == 1
    assert summary['metrics']['pendingGenerationCount'] == 0
    assert summary['metrics']['linkedFinanceVoucherCount'] == 1
    assert summary['metrics']['openFinanceVoucherCount'] == 1


@pytest.mark.django_db
def test_asset_project_summary_blocks_closure_until_allocations_are_returned():
    suffix = uuid.uuid4().hex[:8]
    organization, user = _build_org_and_user(suffix)
    department = _build_department(organization, suffix)
    category = AssetCategory.objects.create(
        organization=organization,
        code=f'PROJ-CAT-{suffix}',
        name='Project Closure Category',
        created_by=user,
    )
    location = Location.objects.create(
        organization=organization,
        name=f'Project Return Location {suffix}',
        path=f'Project Return Location {suffix}',
        location_type='area',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        asset_code=f'ASSET-PROJ-{suffix}',
        asset_name='Project Asset',
        asset_category=category,
        purchase_price=Decimal('4200.00'),
        current_value=Decimal('3600.00'),
        purchase_date=date.today() - timedelta(days=60),
        created_by=user,
    )
    project = AssetProject.objects.create(
        organization=organization,
        project_name='Closure Project',
        project_manager=user,
        department=department,
        start_date=date.today() - timedelta(days=20),
        status='active',
        completed_milestones=2,
        total_milestones=4,
        created_by=user,
    )
    allocation = ProjectAsset.objects.create(
        organization=organization,
        project=project,
        asset=asset,
        allocation_date=date.today() - timedelta(days=7),
        allocated_by=user,
        return_status='in_use',
        created_by=user,
    )
    return_order = AssetReturn.objects.create(
        organization=organization,
        returner=user,
        return_date=date.today(),
        return_location=location,
        status='pending',
        created_by=user,
    )
    ReturnItem.objects.create(
        organization=organization,
        asset_return=return_order,
        asset=asset,
        project_allocation=allocation,
        asset_status='idle',
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='AssetProject',
        business_id=str(project.id),
        instance=project,
        organization_id=str(organization.id),
    )

    assert summary['hasSummary'] is True
    assert summary['stage'] == 'Active asset allocations'
    assert summary['blocker'] == 'Return or transfer active project assets before closing the project.'
    assert summary['owner'] == user.username
    assert summary['completionDisplay'] == '70%'
    assert summary['metrics']['totalAssets'] == 1
    assert summary['metrics']['activeAssets'] == 1
    assert summary['metrics']['memberCount'] == 0
    assert summary['metrics']['pendingReturnCount'] == 1
    assert summary['metrics']['progress'] == 50.0


def test_asset_project_summary_blocks_closure_for_pending_returns_without_active_assets(db):
    organization = Organization.objects.create(code='ORG-PROJECT-RET', name='Project Return Org')
    department = Department.objects.create(
        organization=organization,
        code='OPS',
        name='Operations',
    )
    user = User.objects.create_user(
        username='project_return_owner',
        password='pass123456',
        organization=organization,
    )
    category = AssetCategory.objects.create(
        organization=organization,
        code='DEVICE',
        name='Device',
        created_by=user,
    )
    location = Location.objects.create(
        organization=organization,
        name='Project Return Storage',
        path='Project Return Storage',
        location_type='area',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=organization,
        asset_code='ASSET-PROJECT-RET-001',
        asset_name='Tracked Tablet',
        asset_category=category,
        purchase_price=Decimal('2200.00'),
        purchase_date=date.today() - timedelta(days=30),
        created_by=user,
    )
    project = AssetProject.objects.create(
        organization=organization,
        project_name='Pending Return Project',
        project_manager=user,
        department=department,
        start_date=date.today() - timedelta(days=10),
        status='active',
        completed_milestones=3,
        total_milestones=4,
        created_by=user,
    )
    allocation = ProjectAsset.objects.create(
        organization=organization,
        project=project,
        asset=asset,
        allocation_date=date.today() - timedelta(days=5),
        allocated_by=user,
        return_status='transferred',
        created_by=user,
    )
    return_order = AssetReturn.objects.create(
        organization=organization,
        returner=user,
        return_date=date.today(),
        return_location=location,
        status='pending',
        created_by=user,
    )
    ReturnItem.objects.create(
        organization=organization,
        asset_return=return_order,
        asset=asset,
        project_allocation=allocation,
        asset_status='idle',
        created_by=user,
    )

    summary = ObjectClosureBindingService().get_object_closure_summary(
        object_code='AssetProject',
        business_id=str(project.id),
        instance=project,
        organization_id=str(organization.id),
    )

    assert summary['stage'] == 'Pending asset returns'
    assert summary['blocker'] == 'Complete or cancel pending return orders before closing the project.'
    assert summary['completionDisplay'] == '85%'
    assert summary['metrics']['activeAssets'] == 0
    assert summary['metrics']['pendingReturnCount'] == 1
