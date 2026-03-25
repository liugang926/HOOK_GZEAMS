"""
Configuration Loader - Load/export business object configurations from YAML/JSON files.

Enables config-as-code workflow for versioning configurations in Git.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from django.db import transaction

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigLoader:
    """
    Load and export business object configurations from/to files.
    
    Supports YAML and JSON formats for config-as-code workflow.
    
    Usage:
        loader = ConfigLoader(organization=org)
        
        # Export to file
        loader.export_to_file(['Asset', 'AssetCategory'], './configs/asset.yaml')
        
        # Import from file
        loader.load_from_file('./configs/asset.yaml')
    """

    def __init__(self, organization=None, user=None):
        self.organization = organization
        self.user = user

    def load_from_file(self, filepath: str, merge: bool = True) -> Dict[str, Any]:
        """
        Load configuration from a YAML or JSON file.
        
        Args:
            filepath: Path to the configuration file
            merge: If True, merge with existing; if False, replace
        
        Returns:
            Dict with import results
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")

        # Determine format and load
        content = filepath.read_text(encoding='utf-8')
        
        if filepath.suffix in ['.yaml', '.yml']:
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")
            config = yaml.safe_load(content)
        elif filepath.suffix == '.json':
            config = json.loads(content)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")

        return self._import_config(config, merge)

    def export_to_file(
        self,
        object_codes: List[str],
        filepath: str,
        include_data: bool = False
    ) -> Dict[str, Any]:
        """
        Export business object configurations to a file.
        
        Args:
            object_codes: List of business object codes to export
            filepath: Output file path (.yaml or .json)
            include_data: If True, include sample data records
        
        Returns:
            Dict with export summary
        """
        from apps.system.models import BusinessObject, FieldDefinition, PageLayout, BusinessRule

        filepath = Path(filepath)
        config = {
            'version': '1.0',
            'objects': []
        }

        for code in object_codes:
            try:
                bo = BusinessObject.objects.get(
                    code=code,
                    is_deleted=False,
                    **({"organization": self.organization} if self.organization else {})
                )
            except BusinessObject.DoesNotExist:
                continue

            obj_config = {
                'code': bo.code,
                'name': bo.name,
                'name_en': bo.name_en,
                'description': bo.description,
                'enable_workflow': bo.enable_workflow,
                'enable_version': bo.enable_version,
                'fields': [],
                'layouts': [],
                'rules': []
            }

            # Export fields
            fields = FieldDefinition.objects.filter(
                business_object=bo, is_deleted=False
            ).order_by('sort_order')
            
            for field in fields:
                obj_config['fields'].append({
                    'code': field.code,
                    'name': field.name,
                    'type': field.field_type,
                    'required': field.is_required,
                    'unique': field.is_unique,
                    'readonly': field.is_readonly,
                    'searchable': field.is_searchable,
                    'show_in_list': field.show_in_list,
                    'show_in_detail': field.show_in_detail,
                    'sort_order': field.sort_order,
                    'options': field.options if field.options else None,
                    'default_value': field.default_value,
                })

            # Export layouts
            layouts = PageLayout.objects.filter(
                business_object=bo, is_deleted=False
            )
            
            for layout in layouts:
                obj_config['layouts'].append({
                    'code': layout.layout_code,
                    'name': layout.layout_name,
                    'type': layout.layout_type,
                    'is_default': layout.is_default,
                    'config': layout.layout_config
                })

            # Export rules
            rules = BusinessRule.objects.filter(
                business_object=bo, is_deleted=False
            ).order_by('-priority')
            
            for rule in rules:
                obj_config['rules'].append({
                    'code': rule.rule_code,
                    'name': rule.rule_name,
                    'type': rule.rule_type,
                    'priority': rule.priority,
                    'is_active': rule.is_active,
                    'condition': rule.condition,
                    'action': rule.action,
                    'target_field': rule.target_field,
                    'trigger_events': rule.trigger_events,
                    'error_message': rule.error_message,
                })

            config['objects'].append(obj_config)

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        if filepath.suffix in ['.yaml', '.yml']:
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML required for YAML export")
            content = yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False)
        else:
            content = json.dumps(config, indent=2, ensure_ascii=False)

        filepath.write_text(content, encoding='utf-8')

        return {
            'file': str(filepath),
            'objects': len(object_codes),
            'fields': sum(len(o['fields']) for o in config['objects']),
            'layouts': sum(len(o['layouts']) for o in config['objects']),
            'rules': sum(len(o['rules']) for o in config['objects'])
        }

    @transaction.atomic
    def _import_config(self, config: Dict, merge: bool) -> Dict[str, Any]:
        """Import configuration from parsed data."""
        from apps.system.models import BusinessObject, FieldDefinition, PageLayout, BusinessRule

        results = {
            'created': 0,
            'updated': 0,
            'errors': []
        }

        for obj_data in config.get('objects', []):
            try:
                # Get or create business object
                bo, created = BusinessObject.objects.update_or_create(
                    code=obj_data['code'],
                    defaults={
                        'name': obj_data.get('name', obj_data['code']),
                        'name_en': obj_data.get('name_en', ''),
                        'description': obj_data.get('description', ''),
                        'enable_workflow': obj_data.get('enable_workflow', False),
                        'enable_version': obj_data.get('enable_version', False),
                        'organization': self.organization,
                    }
                )
                
                if created:
                    results['created'] += 1
                else:
                    results['updated'] += 1

                # Import fields
                for field_data in obj_data.get('fields', []):
                    FieldDefinition.objects.update_or_create(
                        business_object=bo,
                        code=field_data['code'],
                        defaults={
                            'name': field_data.get('name', field_data['code']),
                            'field_type': field_data.get('type', 'string'),
                            'is_required': field_data.get('required', False),
                            'is_unique': field_data.get('unique', False),
                            'is_readonly': field_data.get('readonly', False),
                            'is_searchable': field_data.get('searchable', True),
                            'show_in_list': field_data.get('show_in_list', True),
                            'show_in_detail': field_data.get('show_in_detail', True),
                            'sort_order': field_data.get('sort_order', 0),
                            'options': field_data.get('options') or {},
                            'default_value': field_data.get('default_value'),
                            'organization': self.organization,
                        }
                    )

                # Import layouts
                for layout_data in obj_data.get('layouts', []):
                    PageLayout.objects.update_or_create(
                        business_object=bo,
                        layout_code=layout_data['code'],
                        defaults={
                            'layout_name': layout_data.get('name', layout_data['code']),
                            'layout_type': layout_data.get('type', 'form'),
                            'is_default': layout_data.get('is_default', False),
                            'layout_config': layout_data.get('config', {}),
                            'organization': self.organization,
                        }
                    )

                # Import rules
                for rule_data in obj_data.get('rules', []):
                    BusinessRule.objects.update_or_create(
                        business_object=bo,
                        rule_code=rule_data['code'],
                        defaults={
                            'rule_name': rule_data.get('name', rule_data['code']),
                            'rule_type': rule_data.get('type', 'validation'),
                            'priority': rule_data.get('priority', 0),
                            'is_active': rule_data.get('is_active', True),
                            'condition': rule_data.get('condition', {}),
                            'action': rule_data.get('action', {}),
                            'target_field': rule_data.get('target_field', ''),
                            'trigger_events': rule_data.get('trigger_events', []),
                            'error_message': rule_data.get('error_message', ''),
                            'organization': self.organization,
                        }
                    )

            except Exception as e:
                results['errors'].append(f"{obj_data.get('code', 'unknown')}: {str(e)}")

        return results

    def validate_file(self, filepath: str) -> Dict[str, Any]:
        """
        Validate a configuration file without importing.
        
        Args:
            filepath: Path to the configuration file
        
        Returns:
            Dict with validation results
        """
        filepath = Path(filepath)
        errors = []
        warnings = []

        try:
            content = filepath.read_text(encoding='utf-8')
            
            if filepath.suffix in ['.yaml', '.yml']:
                if not YAML_AVAILABLE:
                    return {'valid': False, 'errors': ['PyYAML not installed']}
                config = yaml.safe_load(content)
            else:
                config = json.loads(content)

            # Validate structure
            if 'objects' not in config:
                errors.append("Missing 'objects' key in config")
            else:
                for i, obj in enumerate(config['objects']):
                    if 'code' not in obj:
                        errors.append(f"Object {i}: missing 'code'")
                    if 'fields' in obj:
                        for j, field in enumerate(obj['fields']):
                            if 'code' not in field:
                                errors.append(f"Object {obj.get('code', i)}, field {j}: missing 'code'")

            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'object_count': len(config.get('objects', []))
            }

        except yaml.YAMLError as e:
            return {'valid': False, 'errors': [f"YAML parse error: {e}"]}
        except json.JSONDecodeError as e:
            return {'valid': False, 'errors': [f"JSON parse error: {e}"]}
        except Exception as e:
            return {'valid': False, 'errors': [str(e)]}
