import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.serializers import PageLayoutSerializer
from apps.system.models import BusinessObject, PageLayout, LayoutHistory, ImportStrategy
from apps.system.services.config_package_service import ConfigPackageService
from apps.system.viewsets import PageLayoutViewSet


def _create_default_form_layout(bo: BusinessObject) -> PageLayout:
    return PageLayout.objects.create(
        business_object=bo,
        layout_code=f'{bo.code}_form_default',
        layout_name='Default Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 'section-basic',
                    'type': 'section',
                    'title': 'Basic',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name', 'span': 12},
                    ],
                }
            ]
        },
    )


@pytest.mark.django_db
def test_get_default_endpoint_normalizes_readonly_to_form_type():
    org = Organization.objects.create(name='Test Org', code='test-org-layout-default')
    user = User.objects.create(username='layout_default_user', organization=org)
    bo = BusinessObject.objects.create(code='LAYOUTDEFAULTOBJ', name='Layout Default Object', is_hardcoded=False)
    _create_default_form_layout(bo)

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/page-layouts/default/LAYOUTDEFAULTOBJ/readonly/')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get('success') is True
    data = payload.get('data', {})
    assert (data.get('layoutType') or data.get('layout_type')) == 'form'


@pytest.mark.django_db
def test_by_object_and_type_endpoint_normalizes_readonly_to_form_type():
    org = Organization.objects.create(name='Test Org', code='test-org-layout-by-type')
    user = User.objects.create(username='layout_by_type_user', organization=org)
    bo = BusinessObject.objects.create(code='LAYOUTBYTYPEOBJ', name='Layout By Type Object', is_hardcoded=False)
    _create_default_form_layout(bo)

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/page-layouts/by-object/LAYOUTBYTYPEOBJ/readonly/')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get('success') is True
    data = payload.get('data', {})
    assert (data.get('layoutType') or data.get('layout_type')) == 'form'


@pytest.mark.django_db
def test_get_default_endpoint_normalizes_search_to_form_type():
    org = Organization.objects.create(name='Test Org', code='test-org-layout-default-search')
    user = User.objects.create(username='layout_default_search_user', organization=org)
    bo = BusinessObject.objects.create(code='LAYOUTDEFAULTSEARCH', name='Layout Default Search Object', is_hardcoded=False)
    _create_default_form_layout(bo)

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/page-layouts/default/LAYOUTDEFAULTSEARCH/search/')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get('success') is True
    data = payload.get('data', {})
    assert (data.get('layoutType') or data.get('layout_type')) == 'form'


@pytest.mark.django_db
def test_by_object_and_type_prefers_published_over_draft_custom():
    org = Organization.objects.create(name='Test Org', code='test-org-layout-priority')
    user = User.objects.create(username='layout_priority_user', organization=org)
    bo = BusinessObject.objects.create(code='LAYOUTPRIOBJ', name='Layout Priority Object', is_hardcoded=False)

    draft_custom = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code=f'{bo.code}_form_custom_draft',
        layout_name='Draft Custom Form',
        layout_type='form',
        mode='edit',
        status='draft',
        is_default=False,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 'section-draft',
                    'type': 'section',
                    'title': 'Draft',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Draft)', 'span': 12},
                    ],
                }
            ]
        },
    )
    published_default = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code=f'{bo.code}_form_default',
        layout_name='Published Default Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 'section-published',
                    'type': 'section',
                    'title': 'Published',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Published)', 'span': 12},
                    ],
                }
            ]
        },
    )
    # Legacy detail row should be ignored by readonly lookup under single-layout model.
    PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code=f'{bo.code}_detail_legacy_default',
        layout_name='Legacy Detail',
        layout_type='detail',
        mode='readonly',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={'sections': []},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/page-layouts/by-object/LAYOUTPRIOBJ/readonly/')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get('success') is True
    data = payload.get('data', {})
    assert str(data.get('id')) == str(published_default.id)
    assert str(data.get('id')) != str(draft_custom.id)
    assert (data.get('layoutType') or data.get('layout_type')) == 'form'


@pytest.mark.django_db
def test_by_object_list_only_returns_form_layouts_for_unified_management():
    org = Organization.objects.create(name='Test Org', code='test-org-layout-by-object-only-form')
    user = User.objects.create(username='layout_by_object_form_user', organization=org)
    bo = BusinessObject.objects.create(code='LAYOUTLISTOBJ', name='Layout List Object', is_hardcoded=False)

    default_form = PageLayout.objects.create(
        business_object=bo,
        layout_code=f'{bo.code.lower()}_default_form',
        layout_name='Default Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={'sections': []},
    )
    custom_form = PageLayout.objects.create(
        business_object=bo,
        layout_code=f'{bo.code.lower()}_custom_form',
        layout_name='Custom Form',
        layout_type='form',
        mode='edit',
        status='draft',
        is_default=False,
        is_active=True,
        layout_config={'sections': []},
    )
    # Legacy rows that should be hidden from unified designer list.
    PageLayout.objects.create(
        business_object=bo,
        layout_code=f'{bo.code.lower()}_default_list',
        layout_name='Legacy List',
        layout_type='list',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={'columns': []},
    )
    PageLayout.objects.create(
        business_object=bo,
        layout_code=f'{bo.code.lower()}_default_detail',
        layout_name='Legacy Detail',
        layout_type='detail',
        mode='readonly',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={'sections': []},
    )
    # Stale demoted generated form layout that should not appear as custom row.
    PageLayout.objects.create(
        business_object=bo,
        layout_code=f'{bo.code.lower()}_default_form',
        layout_name='Stale Generated Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=False,
        is_active=True,
        layout_config={'sections': []},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/page-layouts/by-object/LAYOUTLISTOBJ/')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get('success') is True
    rows = payload.get('data', [])
    returned_ids = {str(item.get('id')) for item in rows}

    assert str(default_form.id) in returned_ids
    assert str(custom_form.id) in returned_ids
    assert len(rows) == 2

    returned_types = {item.get('layoutType') or item.get('layout_type') for item in rows}
    assert returned_types == {'form'}


@pytest.mark.django_db
def test_by_object_list_keeps_single_default_row_when_duplicates_exist():
    org = Organization.objects.create(name='Test Org', code='test-org-layout-single-default')
    user = User.objects.create(username='layout_by_object_single_default_user', organization=org)
    bo = BusinessObject.objects.create(code='LAYOUTSINGLEDEF', name='Layout Single Default', is_hardcoded=False)

    older_default = PageLayout.objects.create(
        business_object=bo,
        layout_code=f'{bo.code.lower()}_default_form',
        layout_name='Older Default',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={'sections': [{'id': 'old', 'type': 'section', 'fields': []}]},
    )
    latest_default = PageLayout.objects.create(
        business_object=bo,
        layout_code=f'{bo.code.lower()}_default_form_v2',
        layout_name='Latest Default',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={'sections': [{'id': 'new', 'type': 'section', 'fields': []}]},
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/page-layouts/by-object/LAYOUTSINGLEDEF/')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get('success') is True
    rows = payload.get('data', [])
    defaults = [row for row in rows if row.get('isDefault')]

    assert len(defaults) == 1
    assert str(defaults[0].get('id')) == str(latest_default.id)
    assert str(defaults[0].get('id')) != str(older_default.id)


@pytest.mark.django_db
def test_serializer_normalizes_readonly_detail_payload_to_shared_form_layout():
    bo = BusinessObject.objects.create(code='LAYOUTSERREAD', name='Layout Serializer Readonly', is_hardcoded=False)

    serializer = PageLayoutSerializer(data={
        'business_object': str(bo.id),
        'layout_code': 'layoutserread_legacy_detail',
        'layout_name': 'Legacy Detail Payload',
        'mode': 'readonly',
        'layout_type': 'detail',
        'status': 'draft',
        'version': '0.1.0',
        'layout_config': {
            'sections': [
                {
                    'id': 'section-basic',
                    'type': 'section',
                    'title': 'Basic',
                    'fields': [
                        {'id': 'field-name', 'fieldCode': 'name', 'label': 'Name', 'span': 12},
                    ],
                }
            ]
        },
    })

    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.layout_type == 'form'
    assert instance.mode == 'edit'


@pytest.mark.django_db
def test_serializer_normalizes_search_payload_to_shared_form_layout():
    bo = BusinessObject.objects.create(code='LAYOUTSERSEARCH', name='Layout Serializer Search', is_hardcoded=False)

    serializer = PageLayoutSerializer(data={
        'business_object': str(bo.id),
        'layout_code': 'layoutsersearch_legacy_search',
        'layout_name': 'Legacy Search Payload',
        'mode': 'search',
        'layout_type': 'search',
        'status': 'draft',
        'version': '0.1.0',
        'layout_config': {
            'sections': [
                {
                    'id': 'section-basic',
                    'type': 'section',
                    'title': 'Basic',
                    'fields': [
                        {'id': 'field-name', 'fieldCode': 'name', 'label': 'Name', 'span': 12},
                    ],
                }
            ]
        },
    })

    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.layout_type == 'form'
    assert instance.mode == 'edit'


@pytest.mark.django_db
def test_serializer_fills_missing_section_and_field_ids():
    bo = BusinessObject.objects.create(code='LAYOUTSERIDS', name='Layout Serializer Ids', is_hardcoded=False)

    serializer = PageLayoutSerializer(data={
        'business_object': str(bo.id),
        'layout_code': 'layoutserids_form',
        'layout_name': 'Layout Missing Ids',
        'mode': 'edit',
        'layout_type': 'form',
        'status': 'draft',
        'version': '0.1.0',
        'layout_config': {
            'sections': [
                {
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name'},
                    ],
                }
            ]
        },
    })

    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    sections = (instance.layout_config or {}).get('sections') or []
    assert len(sections) == 1
    assert sections[0].get('id')
    assert sections[0].get('type') == 'section'
    fields = sections[0].get('fields') or []
    assert len(fields) == 1
    assert fields[0].get('id')
    assert fields[0].get('fieldCode') == 'name'


@pytest.mark.django_db
def test_duplicate_endpoint_uses_serializer_normalization_and_keeps_org_scope():
    org = Organization.objects.create(name='Test Org', code='test-org-layout-duplicate-normalization')
    user = User.objects.create(username='layout_duplicate_normalize_user', organization=org)
    bo = BusinessObject.objects.create(code='LAYOUTDUPNORM', name='Layout Duplicate Normalize', is_hardcoded=False)
    source = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='layoutdupnorm_default_form',
        layout_name='Source Layout',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    # Missing id/type on purpose; duplicate should normalize.
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name'},
                    ],
                }
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post(f'/api/system/page-layouts/{source.id}/duplicate/', {}, format='json')
    assert resp.status_code == 201

    payload = resp.json()
    assert payload.get('success') is True
    data = payload.get('data', {})

    duplicated = PageLayout.objects.get(id=data.get('id'))
    assert duplicated.organization_id == org.id
    assert duplicated.created_by_id == user.id
    sections = (duplicated.layout_config or {}).get('sections') or []
    assert len(sections) == 1
    assert sections[0].get('id')
    assert sections[0].get('type') == 'section'


@pytest.mark.django_db
def test_rollback_endpoint_normalizes_history_snapshot_before_persist():
    org = Organization.objects.create(name='Test Org', code='test-org-layout-rollback-normalization')
    user = User.objects.create(username='layout_rollback_normalize_user', organization=org)
    bo = BusinessObject.objects.create(code='LAYOUTRBNORM', name='Layout Rollback Normalize', is_hardcoded=False)
    layout = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='layoutrbnorm_form',
        layout_name='Rollback Source',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=False,
        is_active=True,
        version='1.0.0',
        layout_config={
            'sections': [
                {
                    'id': 'section-stable',
                    'type': 'section',
                    'fields': [
                        {'id': 'field-stable', 'fieldCode': 'name', 'label': 'Name'},
                    ],
                }
            ]
        },
    )
    LayoutHistory.objects.create(
        layout=layout,
        version='1.0.1',
        config_snapshot={
            'sections': [
                {
                    # Missing id/type on purpose.
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name from History'},
                    ],
                }
            ]
        },
        published_by=user,
        action='publish',
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post(f'/api/system/page-layouts/{layout.id}/rollback/1.0.1/', {}, format='json')
    assert resp.status_code == 200

    layout.refresh_from_db()
    assert layout.status == 'draft'
    assert layout.parent_version == '1.0.1'
    sections = (layout.layout_config or {}).get('sections') or []
    assert len(sections) == 1
    assert sections[0].get('id')
    assert sections[0].get('type') == 'section'


@pytest.mark.django_db
def test_save_diff_config_normalizes_layout_type_and_section_ids():
    org = Organization.objects.create(name='Test Org', code='test-org-diff-normalize')
    user = User.objects.create(username='layout_diff_normalize_user', organization=org)
    bo = BusinessObject.objects.create(
        code='LAYOUTDIFFNORM',
        name='Layout Diff Normalize',
        organization=org,
        is_hardcoded=False,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post('/api/system/page-layouts/save-diff-config/', {
        'object_code': bo.code,
        'layout_type': 'detail',
        'priority': 'org',
        'diff_config': {
            'sections': [
                {
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name Override'}
                    ]
                }
            ]
        }
    }, format='json')
    assert resp.status_code == 201

    payload = resp.json()
    assert payload.get('success') is True
    data = payload.get('data', {})

    assert (data.get('layoutType') or data.get('layout_type')) == 'form'
    layout = PageLayout.objects.get(id=data.get('id'))
    assert layout.layout_type == 'form'
    sections = (layout.diff_config or {}).get('sections') or []
    assert len(sections) == 1
    assert sections[0].get('id')
    assert sections[0].get('type') == 'section'
    fields = sections[0].get('fields') or []
    assert len(fields) == 1
    assert fields[0].get('id')


@pytest.mark.django_db
def test_config_package_import_layout_uses_serializer_normalization():
    org = Organization.objects.create(name='Test Org', code='test-org-package-layout-normalize')
    user = User.objects.create(username='layout_package_normalize_user', organization=org)
    bo = BusinessObject.objects.create(
        code='LAYOUTPKGNORM',
        name='Layout Package Normalize',
        organization=org,
        is_hardcoded=False,
    )
    service = ConfigPackageService(organization=org, user=user)

    result, err = service._import_layout(
        data={
            'business_object_code': bo.code,
            'layout_code': 'layoutpkgnorm_imported_detail',
            'layout_name': 'Imported Legacy Detail',
            'layout_type': 'detail',
            'mode': 'readonly',
            'status': 'draft',
            'version': '0.1.0',
            'is_default': False,
            'is_active': True,
            'layout_config': {
                'sections': [
                    {
                        'fields': [
                            {'fieldCode': 'name', 'label': 'Imported Name'}
                        ]
                    }
                ]
            }
        },
        strategy=ImportStrategy.MERGE,
        rollback_data={}
    )

    assert err is None
    assert result == 'created'

    layout = PageLayout.objects.get(
        organization=org,
        business_object=bo,
        layout_code='layoutpkgnorm_imported_detail',
        is_deleted=False
    )
    assert layout.layout_type == 'form'
    assert layout.mode == 'edit'
    sections = (layout.layout_config or {}).get('sections') or []
    assert len(sections) == 1
    assert sections[0].get('id')
    assert sections[0].get('type') == 'section'


@pytest.mark.django_db
def test_get_merged_layout_normalizes_type_and_merges_section_without_ids():
    org = Organization.objects.create(name='Test Org', code='test-org-merged-layout-normalize')
    user = User.objects.create(username='layout_merged_normalize_user', organization=org)
    bo = BusinessObject.objects.create(
        code='LAYOUTMERGENORM',
        name='Layout Merge Normalize',
        organization=org,
        is_hardcoded=False,
    )

    PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='layoutmergenorm_default_form',
        layout_name='Default Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 'section-basic',
                    'type': 'section',
                    'title': 'Basic',
                    'fields': [
                        {
                            'id': 'field-name',
                            'fieldCode': 'name',
                            'label': 'Name',
                            'span': 12,
                        }
                    ],
                }
            ]
        },
    )
    PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='layoutmergenorm_diff_org',
        layout_name='Diff Org',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=False,
        is_active=True,
        priority='global',
        context_type='',
        layout_config={},
        diff_config={
            'sections': [
                {
                    # Missing id/type by design; merge should still apply to first section.
                    'title': 'Basic Override',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name Override'}
                    ]
                }
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post('/api/system/page-layouts/get-merged-layout/', {
        'object_code': bo.code,
        'layout_type': 'detail',
    }, format='json')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get('success') is True
    data = payload.get('data', {})
    assert data.get('source') == 'global'
    assert data.get('hasDiffConfig') is True or data.get('has_diff_config') is True

    config = data.get('layoutConfig') or data.get('layout_config') or {}
    sections = config.get('sections') or []
    assert len(sections) >= 1
    assert sections[0].get('id')
    assert sections[0].get('type') == 'section'
    assert sections[0].get('title') == 'Basic Override'
    fields = sections[0].get('fields') or []
    assert len(fields) >= 1
    assert fields[0].get('fieldCode') == 'name'
    assert fields[0].get('label') == 'Name Override'


@pytest.mark.django_db
def test_get_merged_layout_does_not_use_other_org_diff_config():
    org_a = Organization.objects.create(name='Org A', code='test-org-merge-scope-a')
    org_b = Organization.objects.create(name='Org B', code='test-org-merge-scope-b')
    user_a = User.objects.create(username='layout_merge_scope_user_a', organization=org_a)
    bo = BusinessObject.objects.create(
        code='LAYOUTMERGESCOPE',
        name='Layout Merge Scope',
        organization=org_a,
        is_hardcoded=False,
    )

    PageLayout.objects.create(
        organization=org_a,
        business_object=bo,
        layout_code='layoutmergescope_default_form',
        layout_name='Default Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 'section-basic',
                    'type': 'section',
                    'title': 'Base Title',
                    'fields': [
                        {'id': 'field-name', 'fieldCode': 'name', 'label': 'Name', 'span': 12}
                    ],
                }
            ]
        },
    )
    # Diff config exists only in another organization and must not leak.
    PageLayout.objects.create(
        organization=org_b,
        business_object=bo,
        layout_code='layoutmergescope_org_b_diff',
        layout_name='Org B Diff',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=False,
        is_active=True,
        priority='org',
        context_type='',
        layout_config={},
        diff_config={
            'sections': [
                {
                    'title': 'Org B Title',
                    'fields': [{'fieldCode': 'name', 'label': 'Org B Name'}],
                }
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user_a)

    resp = client.post('/api/system/page-layouts/get-merged-layout/', {
        'object_code': bo.code,
        'layout_type': 'detail',
    }, format='json')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload.get('success') is True
    data = payload.get('data', {})
    assert data.get('source') == 'default'
    config = data.get('layoutConfig') or data.get('layout_config') or {}
    sections = config.get('sections') or []
    assert len(sections) >= 1
    assert sections[0].get('title') == 'Base Title'
    fields = sections[0].get('fields') or []
    assert len(fields) >= 1
    assert fields[0].get('label') == 'Name'


@pytest.mark.django_db
def test_object_router_runtime_normalizes_layout_config_structure():
    org = Organization.objects.create(name='Test Org', code='test-org-runtime-layout-normalize')
    user = User.objects.create(username='runtime_layout_normalize_user', organization=org)
    bo = BusinessObject.objects.create(
        code='LAYOUTRUNTIMENORM',
        name='Layout Runtime Normalize',
        organization=org,
        is_hardcoded=False,
    )
    PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='layoutruntimenorm_custom_form',
        layout_name='Runtime Legacy Layout',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=False,
        is_active=True,
        layout_config={
            'sections': [
                {
                    # Missing id/type to simulate legacy dirty data.
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name'}
                    ],
                }
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/objects/LAYOUTRUNTIMENORM/runtime/?mode=readonly')
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get('success') is True
    layout = payload.get('data', {}).get('layout', {})
    config = layout.get('layoutConfig') or layout.get('layout_config') or {}
    sections = config.get('sections') or []
    assert len(sections) == 1
    assert sections[0].get('id')
    assert sections[0].get('type') == 'section'
    fields = sections[0].get('fields') or []
    assert len(fields) == 1
    assert fields[0].get('id')
    assert fields[0].get('fieldCode') == 'name'


@pytest.mark.django_db
def test_diff_scope_helper_filters_org_priority_by_org_id():
    org_a = Organization.objects.create(name='Org A', code='test-org-diff-scope-a')
    org_b = Organization.objects.create(name='Org B', code='test-org-diff-scope-b')
    user_a = User.objects.create(username='layout_diff_scope_user_a', organization=org_a)
    bo = BusinessObject.objects.create(
        code='LAYOUTDIFFSCOPE',
        name='Layout Diff Scope',
        organization=org_a,
        is_hardcoded=False,
    )
    layout_a = PageLayout.objects.create(
        organization=org_a,
        business_object=bo,
        layout_code='layoutdiffscope_org_a',
        layout_name='Org A Diff',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=False,
        is_active=True,
        priority='org',
        context_type='',
        layout_config={},
        diff_config={'sections': []},
    )
    PageLayout.objects.create(
        organization=org_b,
        business_object=bo,
        layout_code='layoutdiffscope_org_b',
        layout_name='Org B Diff',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=False,
        is_active=True,
        priority='org',
        context_type='',
        layout_config={},
        diff_config={'sections': []},
    )

    base_qs = PageLayout.objects.filter(
        business_object=bo,
        layout_type='form',
        is_deleted=False,
        is_active=True,
    )
    scoped = PageLayoutViewSet._scope_diff_layout_queryset(
        base_qs,
        'org',
        org_id=org_a.id,
        user=user_a
    )

    ids = list(scoped.values_list('id', flat=True))
    assert ids == [layout_a.id]
