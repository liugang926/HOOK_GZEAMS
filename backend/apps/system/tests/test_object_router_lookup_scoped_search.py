import pytest

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject, DynamicData
from apps.system.viewsets.object_router import ObjectRouterViewSet


@pytest.mark.django_db
def test_apply_lookup_scoped_search_for_dynamic_fields():
    org = Organization.objects.create(name='Lookup Unit Org', code='lookup-unit-org')
    user = User.objects.create_user(username='lookup-unit-user', password='pass123456', organization=org)
    bo = BusinessObject.objects.create(code='LOOKUPUNITOBJ', name='Lookup Unit Object', is_hardcoded=False)

    primary_match = DynamicData.objects.create(
        business_object=bo,
        organization=org,
        data_no='UNIT0001',
        dynamic_fields={'name': 'Alpha Laptop', 'code': 'LTP-001'},
        custom_fields={},
        created_by=user,
    )
    secondary_match = DynamicData.objects.create(
        business_object=bo,
        organization=org,
        data_no='UNIT0002',
        dynamic_fields={'name': 'Monitor B', 'code': 'ALPHA-CODE'},
        custom_fields={},
        created_by=user,
    )

    viewset = ObjectRouterViewSet()
    base_qs = DynamicData.objects.filter(business_object=bo, organization=org, is_deleted=False)

    primary_qs = viewset._apply_lookup_scoped_search(
        base_qs,
        {
            'search': 'Alpha',
            'scope': 'primary',
            'display_field': 'name',
            'secondary_field': 'code',
        }
    )
    assert list(primary_qs.values_list('id', flat=True)) == [primary_match.id]

    secondary_qs = viewset._apply_lookup_scoped_search(
        base_qs,
        {
            'search': 'Alpha',
            'scope': 'secondary',
            'display_field': 'name',
            'secondary_field': 'code',
        }
    )
    assert list(secondary_qs.values_list('id', flat=True)) == [secondary_match.id]

    all_qs = viewset._apply_lookup_scoped_search(
        base_qs,
        {
            'search': 'Alpha',
            'scope': 'all',
            'display_field': 'name',
            'secondary_field': 'code',
        }
    )
    assert set(all_qs.values_list('id', flat=True)) == {primary_match.id, secondary_match.id}


@pytest.mark.django_db
def test_apply_lookup_scoped_search_for_uuid_id_prefix():
    org_a = Organization.objects.create(name='Lookup ID A', code='lookup-id-a')
    Organization.objects.create(name='Lookup ID B', code='lookup-id-b')

    viewset = ObjectRouterViewSet()
    base_qs = Organization.objects.filter(is_deleted=False)
    search_prefix = str(org_a.id).split('-')[0]

    id_qs = viewset._apply_lookup_scoped_search(
        base_qs,
        {
            'search': search_prefix,
            'scope': 'id',
            'display_field': 'name',
            'secondary_field': 'code',
        }
    )
    assert list(id_qs.values_list('id', flat=True)) == [org_a.id]
