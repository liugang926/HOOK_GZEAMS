"""
Workflow Import/Export Service.

Handles importing and exporting workflow definitions and templates.
Supports JSON format for workflow portability between organizations.
"""
import json
import zipfile
import io
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction

from apps.workflows.models.workflow_definition import WorkflowDefinition
from apps.workflows.models.workflow_template import WorkflowTemplate
from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
from apps.workflows.services.workflow_validation import WorkflowValidationService


class WorkflowImportExportService:
    """
    Service for importing and exporting workflow definitions.

    Features:
    - Export single workflow or multiple workflows
    - Export as JSON or ZIP package
    - Import workflow with conflict resolution
    - Template export/import
    - Version-aware import/export
    """

    # Export format versions
    FORMAT_VERSION = "1.0"

    def __init__(self):
        """Initialize the import/export service."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.validator = WorkflowValidationService()

    def export_workflow(
        self,
        workflow: WorkflowDefinition,
        include_metadata: bool = True,
        format_type: str = 'json'
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Export a single workflow definition.

        Args:
            workflow: The WorkflowDefinition to export
            include_metadata: Include audit metadata (created_at, updated_at, etc.)
            format_type: Export format ('json' or 'zip')

        Returns:
            Tuple of (success, data/error_message, metadata_dict)
        """
        try:
            export_data = {
                'format_version': self.FORMAT_VERSION,
                'export_type': 'workflow_definition',
                'exported_at': timezone.now().isoformat(),
                'workflow': self._serialize_workflow(workflow, include_metadata)
            }

            if format_type == 'json':
                json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
                metadata = {
                    'filename': f"{workflow.code}_v{workflow.version}.json",
                    'content_type': 'application/json',
                    'size': len(json_data.encode('utf-8'))
                }
                return True, json_data, metadata

            elif format_type == 'zip':
                # Create ZIP in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add workflow JSON
                    json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
                    zip_file.writestr(f"{workflow.code}.json", json_data)

                    # Add preview image if exists
                    if workflow.preview_image:
                        zip_file.writestr(f"{workflow.code}_preview.png", workflow.preview_image)

                zip_buffer.seek(0)
                metadata = {
                    'filename': f"{workflow.code}_v{workflow.version}.zip",
                    'content_type': 'application/zip',
                    'size': len(zip_buffer.getvalue())
                }
                return True, zip_buffer.getvalue(), metadata

            else:
                return False, f"Unsupported format type: {format_type}", None

        except Exception as e:
            return False, f"Export failed: {str(e)}", None

    def export_workflows(
        self,
        workflows: List[WorkflowDefinition],
        include_metadata: bool = True
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Export multiple workflow definitions as a ZIP package.

        Args:
            workflows: List of WorkflowDefinition objects to export
            include_metadata: Include audit metadata

        Returns:
            Tuple of (success, data/error_message, metadata_dict)
        """
        if not workflows:
            return False, "No workflows to export", None

        try:
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Create manifest
                manifest = {
                    'format_version': self.FORMAT_VERSION,
                    'export_type': 'workflow_bundle',
                    'exported_at': timezone.now().isoformat(),
                    'workflow_count': len(workflows),
                    'workflows': []
                }

                for workflow in workflows:
                    # Export individual workflow
                    workflow_data = self._serialize_workflow(workflow, include_metadata)

                    # Add to ZIP
                    filename = f"{workflow.code}.json"
                    zip_file.writestr(filename, json.dumps(workflow_data, indent=2, ensure_ascii=False))

                    # Add to manifest
                    manifest['workflows'].append({
                        'code': workflow.code,
                        'name': workflow.name,
                        'version': workflow.version,
                        'file': filename
                    })

                    # Add preview if exists
                    if workflow.preview_image:
                        zip_file.writestr(f"{workflow.code}_preview.png", workflow.preview_image)

                # Add manifest to ZIP
                zip_file.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

            zip_buffer.seek(0)
            metadata = {
                'filename': f"workflows_bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                'content_type': 'application/zip',
                'size': len(zip_buffer.getvalue())
            }
            return True, zip_buffer.getvalue(), metadata

        except Exception as e:
            return False, f"Bundle export failed: {str(e)}", None

    def export_template(
        self,
        template: WorkflowTemplate,
        include_usage_stats: bool = False
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Export a workflow template.

        Args:
            template: The WorkflowTemplate to export
            include_usage_stats: Include usage_count and statistics

        Returns:
            Tuple of (success, data/error_message, metadata_dict)
        """
        try:
            export_data = {
                'format_version': self.FORMAT_VERSION,
                'export_type': 'workflow_template',
                'exported_at': timezone.now().isoformat(),
                'template': self._serialize_template(template, include_usage_stats)
            }

            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            metadata = {
                'filename': f"template_{template.code}.json",
                'content_type': 'application/json',
                'size': len(json_data.encode('utf-8'))
            }
            return True, json_data, metadata

        except Exception as e:
            return False, f"Template export failed: {str(e)}", None

    def import_workflow(
        self,
        data: str,
        organization,
        user,
        conflict_resolution: str = 'skip',
        validate_before_import: bool = True
    ) -> Tuple[bool, Optional[WorkflowDefinition], List[str]]:
        """
        Import a workflow definition.

        Args:
            data: JSON string containing workflow export data
            organization: Organization to assign to the workflow
            user: User performing the import
            conflict_resolution: How to handle code conflicts ('skip', 'overwrite', 'rename')
            validate_before_import: Validate workflow before importing

        Returns:
            Tuple of (success, workflow_instance, messages)
        """
        self.errors = []
        self.warnings = []
        messages = []

        try:
            # Parse JSON
            export_data = json.loads(data)

            # Validate format
            if export_data.get('export_type') != 'workflow_definition':
                self.errors.append(_('Invalid export format: expected workflow_definition.'))
                return False, None, self.errors

            workflow_data = export_data.get('workflow', {})
            if not workflow_data:
                self.errors.append(_('No workflow data found in export.'))
                return False, None, self.errors

            # Check for existing workflow with same code
            existing_code = workflow_data.get('code')
            existing = WorkflowDefinition.objects.filter(
                code=existing_code,
                organization=organization,
                is_deleted=False
            ).first()

            if existing:
                if conflict_resolution == 'skip':
                    self.warnings.append(_(f'Workflow with code "{existing_code}" already exists. Skipping.'))
                    return False, None, self.warnings
                elif conflict_resolution == 'overwrite':
                    existing.soft_delete(actor=user)
                    messages.append(_(f'Existing workflow "{existing_code}" overwritten.'))
                elif conflict_resolution == 'rename':
                    # Generate unique code
                    counter = 1
                    new_code = existing_code
                    while WorkflowDefinition.objects.filter(
                        code=new_code,
                        organization=organization,
                        is_deleted=False
                    ).exists():
                        new_code = f"{existing_code}_import_{counter}"
                        counter += 1
                    workflow_data['code'] = new_code
                    workflow_data['name'] = f"{workflow_data.get('name', '')} (imported)"
                    messages.append(_(f'Workflow renamed to "{new_code}" to avoid conflict.'))

            # Validate graph data if requested
            if validate_before_import:
                graph_data = workflow_data.get('graph_data', {})
                is_valid, errors, warnings = self.validator.validate(graph_data)
                if not is_valid:
                    self.errors.extend(errors)
                    return False, None, self.errors
                self.warnings.extend(warnings)

            # Create workflow
            with transaction.atomic():
                # Remove fields that shouldn't be imported
                workflow_data.pop('id', None)
                workflow_data.pop('created_at', None)
                workflow_data.pop('updated_at', None)
                workflow_data.pop('created_by', None)
                workflow_data.pop('organization', None)

                # Create new instance
                workflow = WorkflowDefinition(**workflow_data)
                workflow.organization = organization
                workflow.created_by = user
                workflow.save()

                # Log import
                WorkflowOperationLog.log_import(
                    actor=user,
                    workflow_definition=workflow,
                    details={
                        'source_version': export_data.get('format_version'),
                        'original_code': export_data.get('workflow', {}).get('code')
                    }
                )

            messages.append(_(f'Workflow "{workflow.code}" imported successfully.'))
            return True, workflow, messages

        except json.JSONDecodeError as e:
            self.errors.append(_(f'Invalid JSON data: {str(e)}'))
            return False, None, self.errors
        except Exception as e:
            self.errors.append(_(f'Import failed: {str(e)}'))
            return False, None, self.errors

    def import_template(
        self,
        data: str,
        organization,
        user,
        conflict_resolution: str = 'skip'
    ) -> Tuple[bool, Optional[WorkflowTemplate], List[str]]:
        """
        Import a workflow template.

        Args:
            data: JSON string containing template export data
            organization: Organization to assign to the template
            user: User performing the import
            conflict_resolution: How to handle code conflicts ('skip', 'overwrite', 'rename')

        Returns:
            Tuple of (success, template_instance, messages)
        """
        self.errors = []
        self.warnings = []
        messages = []

        try:
            # Parse JSON
            export_data = json.loads(data)

            # Validate format
            if export_data.get('export_type') != 'workflow_template':
                self.errors.append(_('Invalid export format: expected workflow_template.'))
                return False, None, self.errors

            template_data = export_data.get('template', {})
            if not template_data:
                self.errors.append(_('No template data found in export.'))
                return False, None, self.errors

            # Check for existing template with same code
            existing_code = template_data.get('code')
            existing = WorkflowTemplate.objects.filter(
                code=existing_code,
                organization=organization,
                is_deleted=False
            ).first()

            if existing:
                if conflict_resolution == 'skip':
                    self.warnings.append(_(f'Template with code "{existing_code}" already exists. Skipping.'))
                    return False, None, self.warnings
                elif conflict_resolution == 'overwrite':
                    existing.soft_delete(actor=user)
                    messages.append(_(f'Existing template "{existing_code}" overwritten.'))
                elif conflict_resolution == 'rename':
                    counter = 1
                    new_code = existing_code
                    while WorkflowTemplate.objects.filter(
                        code=new_code,
                        organization=organization,
                        is_deleted=False
                    ).exists():
                        new_code = f"{existing_code}_import_{counter}"
                        counter += 1
                    template_data['code'] = new_code
                    template_data['name'] = f"{template_data.get('name', '')} (imported)"
                    messages.append(_(f'Template renamed to "{new_code}" to avoid conflict.'))

            # Create template
            with transaction.atomic():
                # Remove fields that shouldn't be imported
                template_data.pop('id', None)
                template_data.pop('created_at', None)
                template_data.pop('updated_at', None)
                template_data.pop('created_by', None)
                template_data.pop('organization', None)
                template_data.pop('usage_count', None)  # Reset usage count

                # Create new instance
                template = WorkflowTemplate(**template_data)
                template.organization = organization
                template.created_by = user
                template.usage_count = 0
                template.save()

            messages.append(_(f'Template "{template.code}" imported successfully.'))
            return True, template, messages

        except json.JSONDecodeError as e:
            self.errors.append(_(f'Invalid JSON data: {str(e)}'))
            return False, None, self.errors
        except Exception as e:
            self.errors.append(_(f'Import failed: {str(e)}'))
            return False, None, self.errors

    def _serialize_workflow(
        self,
        workflow: WorkflowDefinition,
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Serialize workflow definition to dict for export."""
        data = {
            'code': workflow.code,
            'name': workflow.name,
            'description': workflow.description or '',
            'business_object_code': workflow.business_object_code,
            'graph_data': workflow.graph_data,
            'status': workflow.status,
            'version': workflow.version,
            'is_active': workflow.is_active,
            'category': workflow.category or '',
            'tags': workflow.tags or [],
            'form_permissions': workflow.form_permissions or {},
        }

        if include_metadata:
            data.update({
                'created_at': workflow.created_at.isoformat() if workflow.created_at else None,
                'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else None,
                'created_by': str(workflow.created_by_id) if workflow.created_by_id else None,
            })

        return data

    def _serialize_template(
        self,
        template: WorkflowTemplate,
        include_usage_stats: bool
    ) -> Dict[str, Any]:
        """Serialize workflow template to dict for export."""
        data = {
            'code': template.code,
            'name': template.name,
            'description': template.description or '',
            'template_type': template.template_type,
            'business_object_code': template.business_object_code,
            'graph_data': template.graph_data,
            'form_permissions': template.form_permissions or {},
            'category': template.category or '',
            'tags': template.tags or [],
            'is_featured': template.is_featured,
            'is_public': template.is_public,
            'sort_order': template.sort_order,
        }

        if include_usage_stats:
            data['usage_count'] = template.usage_count

        return data

    def validate_export_data(self, data: str) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        Validate workflow export data without importing.

        Args:
            data: JSON string containing export data

        Returns:
            Tuple of (is_valid, errors, parsed_data)
        """
        self.errors = []

        try:
            export_data = json.loads(data)

            # Check format version
            format_version = export_data.get('format_version')
            if not format_version:
                self.errors.append(_('Missing format version in export data.'))
            else:
                # Check if format version is compatible
                major_version = format_version.split('.')[0]
                if major_version != self.FORMAT_VERSION.split('.')[0]:
                    self.warnings.append(_(f'Format version {format_version} may not be fully compatible.'))

            # Validate export type
            export_type = export_data.get('export_type')
            if export_type not in ['workflow_definition', 'workflow_template', 'workflow_bundle']:
                self.errors.append(_(f'Unknown export type: {export_type}'))

            # Validate workflow/template data
            if export_type == 'workflow_definition':
                workflow_data = export_data.get('workflow')
                if not workflow_data:
                    self.errors.append(_('Missing workflow data in export.'))
                else:
                    # Validate required fields
                    if 'code' not in workflow_data:
                        self.errors.append(_('Workflow missing required field: code.'))
                    if 'name' not in workflow_data:
                        self.errors.append(_('Workflow missing required field: name.'))
                    if 'graph_data' not in workflow_data:
                        self.errors.append(_('Workflow missing required field: graph_data.'))

            elif export_type == 'workflow_template':
                template_data = export_data.get('template')
                if not template_data:
                    self.errors.append(_('Missing template data in export.'))
                else:
                    if 'code' not in template_data:
                        self.errors.append(_('Template missing required field: code.'))
                    if 'name' not in template_data:
                        self.errors.append(_('Template missing required field: name.'))

            elif export_type == 'workflow_bundle':
                workflows = export_data.get('workflows', [])
                if not workflows:
                    self.errors.append(_('Bundle contains no workflows.'))

            return len(self.errors) == 0, self.errors, export_data

        except json.JSONDecodeError as e:
            self.errors.append(_(f'Invalid JSON data: {str(e)}'))
            return False, self.errors, None
        except Exception as e:
            self.errors.append(_(f'Validation error: {str(e)}'))
            return False, self.errors, None
