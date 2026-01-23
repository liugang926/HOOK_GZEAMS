"""
Tests for Department API endpoints.

Tests DepartmentViewSet actions including:
- tree endpoint
- path endpoint (breadcrumbs)
- select_options endpoint (for dropdowns)
"""
import pytest
from django.urls import reverse
from apps.organizations.models import Department
from apps.accounts.models import UserOrganization


@pytest.mark.django_db
class TestDepartmentViewSet:
    """Test DepartmentViewSet endpoints."""

    def test_tree_endpoint(self, auth_client, organization):
        """Test department tree retrieval."""
        # Create hierarchical departments
        parent = Department.objects.create(
            code='HQ',
            name='Headquarters',
            organization=organization,
            level=1,
            order=1
        )
        child = Department.objects.create(
            code='IT',
            name='IT Department',
            organization=organization,
            parent=parent,
            level=2,
            order=1
        )
        grandchild = Department.objects.create(
            code='DEV',
            name='Development Team',
            organization=organization,
            parent=child,
            level=3,
            order=1
        )

        url = '/api/organizations/departments/tree/'
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'data' in data
        assert 'tree' in data['data']
        assert 'count' in data['data']
        assert data['data']['count'] == 3

        # Verify tree structure
        tree = data['data']['tree']
        assert len(tree) == 1
        assert tree[0]['code'] == 'HQ'
        assert tree[0]['name'] == 'Headquarters'
        assert len(tree[0]['children']) == 1
        assert tree[0]['children'][0]['code'] == 'IT'
        assert tree[0]['children'][0]['children'][0]['code'] == 'DEV'

    def test_tree_endpoint_empty(self, auth_client, organization):
        """Test tree endpoint with no departments."""
        url = '/api/organizations/departments/tree/'
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['count'] == 0
        assert data['data']['tree'] == []

    def test_path_endpoint_root(self, auth_client, organization):
        """Test path endpoint for root department."""
        root_dept = Department.objects.create(
            code='HQ',
            name='Headquarters',
            organization=organization,
            level=1
        )

        url = f'/api/organizations/departments/{root_dept.id}/path/'
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['code'] == 'HQ'
        assert data['data'][0]['name'] == 'Headquarters'
        assert data['data'][0]['level'] == 1

    def test_path_endpoint_nested(self, auth_client, organization):
        """Test path endpoint for nested department."""
        parent = Department.objects.create(
            code='HQ',
            name='Headquarters',
            organization=organization,
            level=1
        )
        child = Department.objects.create(
            code='IT',
            name='IT Department',
            organization=organization,
            parent=parent,
            level=2
        )
        grandchild = Department.objects.create(
            code='DEV',
            name='Development Team',
            organization=organization,
            parent=child,
            level=3
        )

        url = f'/api/organizations/departments/{grandchild.id}/path/'
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) == 3

        # Verify path order (root to leaf)
        assert data['data'][0]['code'] == 'HQ'
        assert data['data'][1]['code'] == 'IT'
        assert data['data'][2]['code'] == 'DEV'

        # Verify full_path_name is populated
        assert data['data'][0]['full_path_name'] == 'Headquarters'
        assert data['data'][1]['full_path_name'] == 'Headquarters / IT Department'
        assert data['data'][2]['full_path_name'] == 'Headquarters / IT Department / Development Team'

    def test_select_options_flat(self, auth_client, organization):
        """Test select options endpoint with flat departments."""
        Department.objects.create(
            code='HQ',
            name='Headquarters',
            organization=organization,
            level=1
        )
        Department.objects.create(
            code='IT',
            name='IT Department',
            organization=organization,
            level=1
        )

        url = '/api/organizations/departments/select-options/'
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) == 2

        # Verify option structure
        option = data['data'][0]
        assert 'value' in option
        assert 'label' in option
        assert 'code' in option
        assert 'level' in option

    def test_select_options_hierarchical(self, auth_client, organization):
        """Test select options endpoint with hierarchical departments."""
        parent = Department.objects.create(
            code='HQ',
            name='Headquarters',
            organization=organization,
            level=1
        )
        child = Department.objects.create(
            code='IT',
            name='IT Department',
            organization=organization,
            parent=parent,
            level=2
        )

        url = '/api/organizations/departments/select-options/'
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) == 2

        # Find child option and verify label shows full path
        child_option = next(opt for opt in data['data'] if opt['code'] == 'IT')
        assert 'Headquarters / IT Department' in child_option['label']

    def test_select_options_empty(self, auth_client, organization):
        """Test select options endpoint with no departments."""
        url = '/api/organizations/departments/select-options/'
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data'] == []

    def test_select_options_only_active(self, auth_client, organization):
        """Test select options only returns active departments."""
        Department.objects.create(
            code='ACTIVE',
            name='Active Dept',
            organization=organization,
            level=1,
            is_active=True
        )
        Department.objects.create(
            code='INACTIVE',
            name='Inactive Dept',
            organization=organization,
            level=1,
            is_active=False
        )

        url = '/api/organizations/departments/select-options/'
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['code'] == 'ACTIVE'

    def test_tree_endpoint_isolated_by_organization(self, auth_client, organization, second_organization):
        """Test tree endpoint isolates departments by organization."""
        # Create department in first organization
        dept1 = Department.objects.create(
            code='DEPT1',
            name='Department 1',
            organization=organization,
            level=1
        )

        # Create department in second organization
        dept2 = Department.objects.create(
            code='DEPT2',
            name='Department 2',
            organization=second_organization,
            level=1
        )

        # User belongs to first organization
        url = '/api/organizations/departments/tree/'
        response = auth_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['count'] == 1
        assert data['data']['tree'][0]['code'] == 'DEPT1'

    def test_path_endpoint_not_found(self, auth_client, organization):
        """Test path endpoint with non-existent department."""
        import uuid
        fake_id = uuid.uuid4()

        url = f'/api/organizations/departments/{fake_id}/path/'
        response = auth_client.get(url)

        assert response.status_code == 404
