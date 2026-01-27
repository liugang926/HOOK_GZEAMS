"""
Permissions app - Field-level and data-level permission management.

This app provides comprehensive permission control including:
- Field-level permissions (read/write/hidden/masked)
- Data-level permissions (all/self_dept/self_and_sub/specified/custom)
- Permission inheritance (roles and departments)
- Permission audit logging
"""
default_app_config = 'apps.permissions.apps.PermissionsConfig'
