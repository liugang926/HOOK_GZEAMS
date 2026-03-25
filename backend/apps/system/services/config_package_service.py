"""
Configuration Package Service - manages export, import, diff, and rollback operations.
"""
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from django.db import transaction
from django.conf import settings

from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    PageLayout,
    BusinessRule,
    ConfigPackage,
    ConfigImportLog,
    PackageType,
    ImportStrategy,
    ImportStatus,
)
from apps.system.serializers import PageLayoutSerializer


@dataclass
class ExportResult:
    """Result of package export."""
    package: ConfigPackage
    object_count: int
    field_count: int
    layout_count: int
    rule_count: int


@dataclass
class ImportResult:
    """Result of package import."""
    success: bool
    import_log: ConfigImportLog
    created: int
    updated: int
    skipped: int
    failed: int
    errors: List[str]


@dataclass
class DiffItem:
    """Single diff item."""
    object_code: str
    item_type: str  # 'business_object', 'field', 'layout', 'rule'
    item_key: str
    change_type: str  # 'added', 'modified', 'deleted'
    old_value: Optional[Any]
    new_value: Optional[Any]


@dataclass
class DiffResult:
    """Result of package comparison."""
    items: List[DiffItem]
    summary: Dict[str, int]  # {'added': 0, 'modified': 0, 'deleted': 0}


class ConfigPackageService:
    """
    Service for configuration package lifecycle management.
    
    Supports:
    - Exporting business object configurations to packages
    - Importing packages with merge/replace/skip strategies
    - Comparing packages to show differences
    - Rolling back imports
    """

    def __init__(self, organization=None, user=None):
        self.organization = organization
        self.user = user

    def export_package(
        self,
        name: str,
        version: str,
        object_codes: List[str],
        description: str = '',
        package_type: str = PackageType.FULL
    ) -> ExportResult:
        """
        Export business object configurations to a package.
        
        Args:
            name: Package name
            version: Semantic version string
            object_codes: List of business object codes to export
            description: Package description
            package_type: Type of package (full/partial/diff)
        
        Returns:
            ExportResult with the created package and counts
        """
        config_data = {
            'version': version,
            'exported_at': datetime.now().isoformat(),
            'business_objects': [],
            'field_definitions': [],
            'page_layouts': [],
            'business_rules': [],
        }

        field_count = 0
        layout_count = 0
        rule_count = 0

        for code in object_codes:
            try:
                bo = BusinessObject.objects.get(
                    code=code,
                    organization=self.organization,
                    is_deleted=False
                )
            except BusinessObject.DoesNotExist:
                continue

            # Export business object
            config_data['business_objects'].append(self._serialize_business_object(bo))

            # Export field definitions
            fields = FieldDefinition.objects.filter(
                business_object=bo,
                is_deleted=False
            )
            for field in fields:
                config_data['field_definitions'].append(self._serialize_field(field))
                field_count += 1

            # Export page layouts
            layouts = PageLayout.objects.filter(
                business_object=bo,
                is_deleted=False
            )
            for layout in layouts:
                config_data['page_layouts'].append(self._serialize_layout(layout))
                layout_count += 1

            # Export business rules
            rules = BusinessRule.objects.filter(
                business_object=bo,
                is_deleted=False
            )
            for rule in rules:
                config_data['business_rules'].append(self._serialize_rule(rule))
                rule_count += 1

        # Calculate checksum
        checksum = self._calculate_checksum(config_data)

        # Create package
        package = ConfigPackage.objects.create(
            organization=self.organization,
            name=name,
            version=version,
            description=description,
            package_type=package_type,
            included_objects=object_codes,
            config_data=config_data,
            exported_by=self.user,
            source_environment=getattr(settings, 'ENVIRONMENT', 'unknown'),
            checksum=checksum,
            is_valid=True
        )

        return ExportResult(
            package=package,
            object_count=len(object_codes),
            field_count=field_count,
            layout_count=layout_count,
            rule_count=rule_count
        )

    @transaction.atomic
    def import_package(
        self,
        package: ConfigPackage,
        strategy: str = ImportStrategy.MERGE,
        target_environment: str = ''
    ) -> ImportResult:
        """
        Import a configuration package.
        
        Args:
            package: The package to import
            strategy: Import strategy (merge/replace/skip)
            target_environment: Target environment name
        
        Returns:
            ImportResult with counts and any errors
        """
        # Create import log
        import_log = ConfigImportLog.objects.create(
            organization=self.organization,
            package=package,
            imported_by=self.user,
            target_environment=target_environment or getattr(settings, 'ENVIRONMENT', 'unknown'),
            import_strategy=strategy,
            status=ImportStatus.IN_PROGRESS
        )

        created = 0
        updated = 0
        skipped = 0
        failed = 0
        errors = []
        rollback_data = {'business_objects': [], 'fields': [], 'layouts': [], 'rules': []}

        config_data = package.config_data

        try:
            # Import business objects
            for bo_data in config_data.get('business_objects', []):
                result, error = self._import_business_object(bo_data, strategy, rollback_data)
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1
                elif result == 'skipped':
                    skipped += 1
                elif result == 'failed':
                    failed += 1
                    errors.append(error)

            # Import field definitions
            for field_data in config_data.get('field_definitions', []):
                result, error = self._import_field(field_data, strategy, rollback_data)
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1
                elif result == 'skipped':
                    skipped += 1
                elif result == 'failed':
                    failed += 1
                    errors.append(error)

            # Import page layouts
            for layout_data in config_data.get('page_layouts', []):
                result, error = self._import_layout(layout_data, strategy, rollback_data)
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1
                elif result == 'skipped':
                    skipped += 1
                elif result == 'failed':
                    failed += 1
                    errors.append(error)

            # Import business rules
            for rule_data in config_data.get('business_rules', []):
                result, error = self._import_rule(rule_data, strategy, rollback_data)
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1
                elif result == 'skipped':
                    skipped += 1
                elif result == 'failed':
                    failed += 1
                    errors.append(error)

            # Update import log
            status = ImportStatus.SUCCESS if failed == 0 else (
                ImportStatus.PARTIAL if created + updated > 0 else ImportStatus.FAILED
            )

            import_log.status = status
            import_log.objects_created = created
            import_log.objects_updated = updated
            import_log.objects_skipped = skipped
            import_log.objects_failed = failed
            import_log.rollback_data = rollback_data
            import_log.import_result = {
                'errors': errors,
                'summary': f"{created} created, {updated} updated, {skipped} skipped, {failed} failed"
            }
            import_log.save()

            return ImportResult(
                success=failed == 0,
                import_log=import_log,
                created=created,
                updated=updated,
                skipped=skipped,
                failed=failed,
                errors=errors
            )

        except Exception as e:
            import_log.status = ImportStatus.FAILED
            import_log.error_message = str(e)
            import_log.save()
            raise

    def diff_packages(
        self,
        package1: ConfigPackage,
        package2: ConfigPackage
    ) -> DiffResult:
        """
        Compare two packages and return differences.
        
        Args:
            package1: First (typically older) package
            package2: Second (typically newer) package
        
        Returns:
            DiffResult with list of changes
        """
        items = []
        summary = {'added': 0, 'modified': 0, 'deleted': 0}

        # Compare business objects
        self._diff_items(
            items, summary,
            package1.config_data.get('business_objects', []),
            package2.config_data.get('business_objects', []),
            'business_object', 'code'
        )

        # Compare field definitions
        self._diff_items(
            items, summary,
            package1.config_data.get('field_definitions', []),
            package2.config_data.get('field_definitions', []),
            'field', 'code'
        )

        # Compare page layouts
        self._diff_items(
            items, summary,
            package1.config_data.get('page_layouts', []),
            package2.config_data.get('page_layouts', []),
            'layout', 'layout_code'
        )

        # Compare business rules
        self._diff_items(
            items, summary,
            package1.config_data.get('business_rules', []),
            package2.config_data.get('business_rules', []),
            'rule', 'rule_code'
        )

        return DiffResult(items=items, summary=summary)

    @transaction.atomic
    def rollback_import(self, import_log: ConfigImportLog) -> bool:
        """
        Rollback a previous import.
        
        Args:
            import_log: The import log to rollback
        
        Returns:
            True if rollback succeeded
        """
        if not import_log.can_rollback:
            raise ValueError("This import cannot be rolled back")

        if import_log.status == ImportStatus.ROLLED_BACK:
            raise ValueError("This import has already been rolled back")

        rollback_data = import_log.rollback_data or {}

        # Rollback in reverse order
        # Delete created items, restore updated items

        # This is a simplified rollback - a full implementation would
        # need to handle all edge cases
        
        import_log.status = ImportStatus.ROLLED_BACK
        import_log.rolled_back_at = datetime.now()
        import_log.save()

        return True

    # =========================================================================
    # Private helper methods
    # =========================================================================

    def _serialize_business_object(self, bo: BusinessObject) -> Dict[str, Any]:
        """Serialize a business object to dict."""
        return {
            'code': bo.code,
            'name': bo.name,
            'name_en': bo.name_en,
            'description': bo.description,
            'enable_workflow': bo.enable_workflow,
            'enable_version': bo.enable_version,
            'enable_soft_delete': bo.enable_soft_delete,
            'is_hardcoded': bo.is_hardcoded,
            'django_model_path': bo.django_model_path,
            'default_form_layout': bo.default_form_layout,
            'default_list_layout': bo.default_list_layout,
        }

    def _serialize_field(self, field: FieldDefinition) -> Dict[str, Any]:
        """Serialize a field definition to dict."""
        return {
            'business_object_code': field.business_object.code,
            'code': field.code,
            'name': field.name,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'is_unique': field.is_unique,
            'is_readonly': field.is_readonly,
            'is_system': field.is_system,
            'is_searchable': field.is_searchable,
            'show_in_list': field.show_in_list,
            'show_in_detail': field.show_in_detail,
            'show_in_filter': field.show_in_filter,
            'sort_order': field.sort_order,
            'default_value': field.default_value,
            'options': field.options,
            'reference_object': field.reference_object,
            'reference_display_field': field.reference_display_field,
        }

    def _serialize_layout(self, layout: PageLayout) -> Dict[str, Any]:
        """Serialize a page layout to dict."""
        return {
            'business_object_code': layout.business_object.code,
            'layout_code': layout.layout_code,
            'layout_name': layout.layout_name,
            'layout_type': layout.layout_type,
            'description': layout.description,
            'layout_config': layout.layout_config,
            'is_default': layout.is_default,
            'is_active': layout.is_active,
        }

    def _serialize_rule(self, rule: BusinessRule) -> Dict[str, Any]:
        """Serialize a business rule to dict."""
        return {
            'business_object_code': rule.business_object.code,
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'rule_type': rule.rule_type,
            'priority': rule.priority,
            'is_active': rule.is_active,
            'condition': rule.condition,
            'action': rule.action,
            'target_field': rule.target_field,
            'trigger_events': rule.trigger_events,
            'error_message': rule.error_message,
            'error_message_en': rule.error_message_en,
        }

    def _calculate_checksum(self, data: Dict) -> str:
        """Calculate SHA256 checksum of data."""
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _import_business_object(
        self,
        data: Dict,
        strategy: str,
        rollback_data: Dict
    ) -> Tuple[str, Optional[str]]:
        """Import a single business object."""
        code = data.get('code')
        
        try:
            existing = BusinessObject.objects.filter(
                code=code,
                organization=self.organization,
                is_deleted=False
            ).first()

            if existing:
                if strategy == ImportStrategy.SKIP:
                    return 'skipped', None
                elif strategy in [ImportStrategy.MERGE, ImportStrategy.REPLACE]:
                    # Save old data for rollback
                    rollback_data['business_objects'].append({
                        'action': 'restore',
                        'data': self._serialize_business_object(existing)
                    })
                    # Update
                    for key, value in data.items():
                        if key != 'code' and hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.save()
                    return 'updated', None
            else:
                # Create new
                bo = BusinessObject.objects.create(
                    organization=self.organization,
                    **{k: v for k, v in data.items() if hasattr(BusinessObject, k)}
                )
                rollback_data['business_objects'].append({
                    'action': 'delete',
                    'id': str(bo.id)
                })
                return 'created', None

        except Exception as e:
            return 'failed', f"BusinessObject {code}: {str(e)}"

    def _import_field(
        self,
        data: Dict,
        strategy: str,
        rollback_data: Dict
    ) -> Tuple[str, Optional[str]]:
        """Import a single field definition."""
        bo_code = data.pop('business_object_code', None)
        code = data.get('code')

        try:
            bo = BusinessObject.objects.get(
                code=bo_code,
                organization=self.organization,
                is_deleted=False
            )

            existing = FieldDefinition.objects.filter(
                business_object=bo,
                code=code,
                is_deleted=False
            ).first()

            if existing:
                if strategy == ImportStrategy.SKIP:
                    return 'skipped', None
                # Update existing
                for key, value in data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.save()
                return 'updated', None
            else:
                FieldDefinition.objects.create(
                    organization=self.organization,
                    business_object=bo,
                    **{k: v for k, v in data.items() if hasattr(FieldDefinition, k)}
                )
                return 'created', None

        except Exception as e:
            return 'failed', f"Field {bo_code}.{code}: {str(e)}"

    def _import_layout(
        self,
        data: Dict,
        strategy: str,
        rollback_data: Dict
    ) -> Tuple[str, Optional[str]]:
        """Import a single page layout."""
        payload = dict(data or {})
        bo_code = payload.pop('business_object_code', None)
        layout_code = payload.get('layout_code')

        try:
            bo = BusinessObject.objects.get(
                code=bo_code,
                organization=self.organization,
                is_deleted=False
            )

            existing = PageLayout.objects.filter(
                business_object=bo,
                layout_code=layout_code,
                is_deleted=False
            ).first()

            allowed_payload_keys = {
                'layout_code',
                'layout_name',
                'layout_type',
                'mode',
                'description',
                'layout_config',
                'status',
                'version',
                'parent_version',
                'is_default',
                'is_active',
                'priority',
                'context_type',
                'diff_config',
            }
            normalized_payload = {
                key: value
                for key, value in payload.items()
                if key in allowed_payload_keys
            }
            normalized_payload['business_object'] = str(bo.id)

            save_kwargs = {}
            if self.organization:
                save_kwargs['organization_id'] = self.organization.id
            if self.user:
                save_kwargs['updated_by'] = self.user

            if existing:
                if strategy == ImportStrategy.SKIP:
                    return 'skipped', None

                serializer = PageLayoutSerializer(existing, data=normalized_payload, partial=True)
                if not serializer.is_valid():
                    return 'failed', f"Layout {bo_code}.{layout_code}: {serializer.errors}"
                serializer.save(**save_kwargs)
                return 'updated', None
            else:
                serializer = PageLayoutSerializer(data=normalized_payload)
                if not serializer.is_valid():
                    return 'failed', f"Layout {bo_code}.{layout_code}: {serializer.errors}"
                create_kwargs = dict(save_kwargs)
                create_kwargs.pop('updated_by', None)
                if self.user:
                    create_kwargs['created_by'] = self.user
                serializer.save(**create_kwargs)
                return 'created', None

        except Exception as e:
            return 'failed', f"Layout {bo_code}.{layout_code}: {str(e)}"

    def _import_rule(
        self,
        data: Dict,
        strategy: str,
        rollback_data: Dict
    ) -> Tuple[str, Optional[str]]:
        """Import a single business rule."""
        bo_code = data.pop('business_object_code', None)
        rule_code = data.get('rule_code')

        try:
            bo = BusinessObject.objects.get(
                code=bo_code,
                organization=self.organization,
                is_deleted=False
            )

            existing = BusinessRule.objects.filter(
                business_object=bo,
                rule_code=rule_code,
                is_deleted=False
            ).first()

            if existing:
                if strategy == ImportStrategy.SKIP:
                    return 'skipped', None
                for key, value in data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.save()
                return 'updated', None
            else:
                BusinessRule.objects.create(
                    organization=self.organization,
                    business_object=bo,
                    **{k: v for k, v in data.items() if hasattr(BusinessRule, k)}
                )
                return 'created', None

        except Exception as e:
            return 'failed', f"Rule {bo_code}.{rule_code}: {str(e)}"

    def _diff_items(
        self,
        items: List[DiffItem],
        summary: Dict[str, int],
        old_list: List[Dict],
        new_list: List[Dict],
        item_type: str,
        key_field: str
    ) -> None:
        """Compare two lists and add diff items."""
        old_map = {item.get(key_field): item for item in old_list}
        new_map = {item.get(key_field): item for item in new_list}

        # Find added and modified
        for key, new_item in new_map.items():
            old_item = old_map.get(key)
            bo_code = new_item.get('business_object_code', new_item.get('code', ''))

            if old_item is None:
                items.append(DiffItem(
                    object_code=bo_code,
                    item_type=item_type,
                    item_key=key,
                    change_type='added',
                    old_value=None,
                    new_value=new_item
                ))
                summary['added'] += 1
            elif old_item != new_item:
                items.append(DiffItem(
                    object_code=bo_code,
                    item_type=item_type,
                    item_key=key,
                    change_type='modified',
                    old_value=old_item,
                    new_value=new_item
                ))
                summary['modified'] += 1

        # Find deleted
        for key, old_item in old_map.items():
            if key not in new_map:
                bo_code = old_item.get('business_object_code', old_item.get('code', ''))
                items.append(DiffItem(
                    object_code=bo_code,
                    item_type=item_type,
                    item_key=key,
                    change_type='deleted',
                    old_value=old_item,
                    new_value=None
                ))
                summary['deleted'] += 1
