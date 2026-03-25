"""
Low-Code CLI Management Command

Provides command-line interface for configuration management:

Usage:
    python manage.py lowcode export --objects Asset,AssetCategory --output ./configs/
    python manage.py lowcode import --file ./configs/asset.yaml
    python manage.py lowcode validate --file ./configs/asset.yaml
    python manage.py lowcode list
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Low-code configuration management CLI'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Action to perform')
        
        # Export command
        export_parser = subparsers.add_parser('export', help='Export configurations to file')
        export_parser.add_argument(
            '--objects', '-o',
            type=str,
            required=True,
            help='Comma-separated list of business object codes'
        )
        export_parser.add_argument(
            '--output', '-f',
            type=str,
            required=True,
            help='Output file path (.yaml or .json)'
        )
        export_parser.add_argument(
            '--format',
            type=str,
            choices=['yaml', 'json'],
            default='yaml',
            help='Output format (default: yaml)'
        )

        # Import command
        import_parser = subparsers.add_parser('import', help='Import configurations from file')
        import_parser.add_argument(
            '--file', '-f',
            type=str,
            required=True,
            help='Configuration file to import'
        )
        import_parser.add_argument(
            '--merge',
            action='store_true',
            default=True,
            help='Merge with existing configurations (default: True)'
        )
        import_parser.add_argument(
            '--replace',
            action='store_true',
            help='Replace existing configurations'
        )

        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate a configuration file')
        validate_parser.add_argument(
            '--file', '-f',
            type=str,
            required=True,
            help='Configuration file to validate'
        )

        # List command
        list_parser = subparsers.add_parser('list', help='List all business objects')
        list_parser.add_argument(
            '--format',
            type=str,
            choices=['table', 'json'],
            default='table',
            help='Output format'
        )

        # Diff command
        diff_parser = subparsers.add_parser('diff', help='Compare configurations')
        diff_parser.add_argument(
            '--file1',
            type=str,
            required=True,
            help='First configuration file'
        )
        diff_parser.add_argument(
            '--file2',
            type=str,
            required=True,
            help='Second configuration file'
        )

    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.print_help('manage.py', 'lowcode')
            return

        if action == 'export':
            self._handle_export(options)
        elif action == 'import':
            self._handle_import(options)
        elif action == 'validate':
            self._handle_validate(options)
        elif action == 'list':
            self._handle_list(options)
        elif action == 'diff':
            self._handle_diff(options)
        else:
            raise CommandError(f"Unknown action: {action}")

    def _handle_export(self, options):
        """Handle export command."""
        from apps.system.management.config_loader import ConfigLoader

        object_codes = [c.strip() for c in options['objects'].split(',')]
        output_path = options['output']

        # Add extension if not present
        if options['format'] == 'yaml' and not output_path.endswith(('.yaml', '.yml')):
            output_path += '.yaml'
        elif options['format'] == 'json' and not output_path.endswith('.json'):
            output_path += '.json'

        loader = ConfigLoader()
        
        try:
            result = loader.export_to_file(object_codes, output_path)
            
            self.stdout.write(self.style.SUCCESS(
                f"✓ Exported to {result['file']}"
            ))
            self.stdout.write(f"  Objects: {result['objects']}")
            self.stdout.write(f"  Fields: {result['fields']}")
            self.stdout.write(f"  Layouts: {result['layouts']}")
            self.stdout.write(f"  Rules: {result['rules']}")
            
        except Exception as e:
            raise CommandError(f"Export failed: {e}")

    def _handle_import(self, options):
        """Handle import command."""
        from apps.system.management.config_loader import ConfigLoader

        filepath = options['file']
        merge = not options.get('replace', False)

        loader = ConfigLoader()
        
        try:
            result = loader.load_from_file(filepath, merge=merge)
            
            self.stdout.write(self.style.SUCCESS(
                f"✓ Import completed"
            ))
            self.stdout.write(f"  Created: {result['created']}")
            self.stdout.write(f"  Updated: {result['updated']}")
            
            if result['errors']:
                self.stdout.write(self.style.WARNING("  Errors:"))
                for error in result['errors']:
                    self.stdout.write(f"    - {error}")
                    
        except FileNotFoundError:
            raise CommandError(f"File not found: {filepath}")
        except Exception as e:
            raise CommandError(f"Import failed: {e}")

    def _handle_validate(self, options):
        """Handle validate command."""
        from apps.system.management.config_loader import ConfigLoader

        filepath = options['file']
        loader = ConfigLoader()
        
        try:
            result = loader.validate_file(filepath)
            
            if result['valid']:
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Configuration is valid"
                ))
                self.stdout.write(f"  Objects: {result['object_count']}")
            else:
                self.stdout.write(self.style.ERROR(
                    f"✗ Configuration is invalid"
                ))
                for error in result['errors']:
                    self.stdout.write(f"  - {error}")
                    
            if result.get('warnings'):
                self.stdout.write(self.style.WARNING("Warnings:"))
                for warning in result['warnings']:
                    self.stdout.write(f"  - {warning}")
                    
        except Exception as e:
            raise CommandError(f"Validation failed: {e}")

    def _handle_list(self, options):
        """Handle list command."""
        from apps.system.models import BusinessObject
        import json as json_lib

        objects = BusinessObject.objects.filter(is_deleted=False).order_by('code')
        
        if options['format'] == 'json':
            data = [
                {
                    'code': bo.code,
                    'name': bo.name,
                    'is_hardcoded': bo.is_hardcoded,
                    'field_count': bo.field_definitions.filter(is_deleted=False).count()
                }
                for bo in objects
            ]
            self.stdout.write(json_lib.dumps(data, indent=2, ensure_ascii=False))
        else:
            # Table format
            self.stdout.write(f"{'Code':<30} {'Name':<30} {'Type':<12} {'Fields':>6}")
            self.stdout.write('-' * 80)
            
            for bo in objects:
                obj_type = 'Hardcoded' if bo.is_hardcoded else 'Dynamic'
                field_count = bo.field_definitions.filter(is_deleted=False).count()
                self.stdout.write(f"{bo.code:<30} {bo.name:<30} {obj_type:<12} {field_count:>6}")
            
            self.stdout.write(f"\nTotal: {objects.count()} objects")

    def _handle_diff(self, options):
        """Handle diff command."""
        from apps.system.management.config_loader import ConfigLoader
        from pathlib import Path
        import json as json_lib

        try:
            import yaml
        except ImportError:
            yaml = None

        file1 = Path(options['file1'])
        file2 = Path(options['file2'])

        def load_config(filepath):
            content = filepath.read_text(encoding='utf-8')
            if filepath.suffix in ['.yaml', '.yml']:
                if yaml is None:
                    raise CommandError("PyYAML required for YAML files")
                return yaml.safe_load(content)
            return json_lib.loads(content)

        try:
            config1 = load_config(file1)
            config2 = load_config(file2)

            objects1 = {o['code']: o for o in config1.get('objects', [])}
            objects2 = {o['code']: o for o in config2.get('objects', [])}

            all_codes = set(objects1.keys()) | set(objects2.keys())
            
            self.stdout.write(f"Comparing: {file1.name} <-> {file2.name}\n")
            
            added = set(objects2.keys()) - set(objects1.keys())
            removed = set(objects1.keys()) - set(objects2.keys())
            common = set(objects1.keys()) & set(objects2.keys())

            if added:
                self.stdout.write(self.style.SUCCESS(f"+ Added objects: {', '.join(added)}"))
            if removed:
                self.stdout.write(self.style.ERROR(f"- Removed objects: {', '.join(removed)}"))
            
            for code in common:
                obj1 = objects1[code]
                obj2 = objects2[code]
                
                fields1 = {f['code'] for f in obj1.get('fields', [])}
                fields2 = {f['code'] for f in obj2.get('fields', [])}
                
                added_fields = fields2 - fields1
                removed_fields = fields1 - fields2
                
                if added_fields or removed_fields:
                    self.stdout.write(f"\n{code}:")
                    if added_fields:
                        self.stdout.write(self.style.SUCCESS(f"  + Fields: {', '.join(added_fields)}"))
                    if removed_fields:
                        self.stdout.write(self.style.ERROR(f"  - Fields: {', '.join(removed_fields)}"))

        except FileNotFoundError as e:
            raise CommandError(f"File not found: {e}")
        except Exception as e:
            raise CommandError(f"Diff failed: {e}")
