import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, UserOrganization
from apps.organizations.models import Organization
from apps.system.services.object_registry import ObjectRegistry


def _build_authed_client():
    ObjectRegistry.auto_register_standard_objects()

    client = APIClient()
    suffix = uuid.uuid4().hex[:8]
    org = Organization.objects.create(
        name=f'Router Smoke Org {suffix}',
        code=f'ROUTER_SMOKE_{suffix}',
    )
    user = User.objects.create_user(
        username=f'router_smoke_{suffix}',
        password='pass123456',
        organization=org,
    )
    UserOrganization.objects.create(
        user=user,
        organization=org,
        role='admin',
        is_active=True,
        is_primary=True,
    )
    user.current_organization = org
    user.save(update_fields=['current_organization'])

    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    return client


@pytest.mark.django_db
def test_list_endpoints_for_migrated_modules():
    client = _build_authed_client()
    for code in [
        'FinanceVoucher',
        'WorkflowDefinition',
        'WorkflowInstance',
        'WorkflowTemplate',
        'WorkflowTask',
        'WorkflowApproval',
        'WorkflowOperationLog',
        'DepreciationRecord',
        'InventoryReconciliation',
        'InventoryReport',
        'ITAsset',
        'ITMaintenanceRecord',
        'ConfigurationChange',
        'Software',
        'SoftwareLicense',
        'LicenseAllocation',
        'ITSoftware',
        'ITSoftwareLicense',
        'ITLicenseAllocation',
        'LeasingContract',
        'LeaseItem',
        'RentPayment',
        'LeaseReturn',
        'LeaseExtension',
        'InsuranceCompany',
        'InsurancePolicy',
        'InsuredAsset',
        'PremiumPayment',
        'ClaimRecord',
        'PolicyRenewal',
    ]:
        response = client.get(f'/api/system/objects/{code}/')
        assert response.status_code == status.HTTP_200_OK, (
            f'Expected 200 for object code {code}, got {response.status_code}'
        )
        assert response.data.get('success', False) is True


@pytest.mark.django_db
def test_collection_custom_actions_for_migrated_modules():
    client = _build_authed_client()

    compliance = client.get('/api/system/objects/SoftwareLicense/compliance_report/')
    assert compliance.status_code == status.HTTP_200_OK
    assert compliance.data.get('success', False) is True

    global_config = client.get('/api/system/objects/DepreciationConfig/global/')
    assert global_config.status_code == status.HTTP_200_OK
    assert global_config.data.get('success', False) is True


@pytest.mark.django_db
def test_metadata_endpoint_for_hardcoded_asset_object():
    client = _build_authed_client()
    response = client.get('/api/system/objects/Asset/metadata/')
    assert response.status_code == status.HTTP_200_OK
    assert response.data.get('success', False) is True
    assert response.data.get('data', {}).get('code') == 'Asset'


@pytest.mark.django_db
def test_legacy_routes_remain_available_for_backwards_compatibility():
    client = _build_authed_client()
    legacy_urls = [
        '/api/finance/vouchers/',
        '/api/depreciation/records/',
        '/api/it-assets/it-assets/',
        '/api/software-licenses/software/',
        '/api/leasing/lease-contracts/',
        '/api/insurance/policies/',
    ]
    for url in legacy_urls:
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK, (
            f'Expected 200 for backwards-compatible legacy route: {url}'
        )
