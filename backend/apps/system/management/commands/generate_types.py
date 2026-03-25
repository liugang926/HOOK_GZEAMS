"""
Generate TypeScript Types Command

Automatically generates TypeScript interfaces from Business Object metadata.

Usage:
    python manage.py generate_types --output ../frontend/src/types/generated/
    python manage.py generate_types --object Asset --output ./asset.ts
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from django.core.management.base import BaseCommand, CommandError
from apps.system.models import BusinessObject, FieldDefinition


class Command(BaseCommand):
    help = 'Generate TypeScript interfaces from Business Objects'

    TYPE_MAPPING = {
        'string': 'string',
        'text': 'string',
        'integer': 'number',
        'decimal': 'number',
        'boolean': 'boolean',
        'date': 'string',
        'datetime': 'string',
        'uuid': 'string',
        'select': 'string',  # Could be union type if options known
        'multiselect': 'string[]',
        'json': 'any',
        'file': 'any',
        'reference': 'any',  # Could be refined
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            type=str,
            required=True,
            help='Output directory or file path'
        )
        parser.add_argument(
            '--object', '-b',
            type=str,
            help='Specific business object code (optional)'
        )
        parser.add_argument(
            '--namespace',
            type=str,
            default='Schema',
            help='Namespace for generated types (default: Schema)'
        )

    def handle(self, *args, **options):
        output_path = Path(options['output'])
        target_object = options.get('object')
        namespace = options.get('namespace')

        # Filter objects
        qs = BusinessObject.objects.filter(is_deleted=False)
        if target_object:
            qs = qs.filter(code=target_object)
        
        objects = list(qs)
        
        if not objects:
            self.stdout.write(self.style.WARNING("No business objects found."))
            return

        # Generate content
        content = []
        content.append("/**")
        content.append(" * Auto-generated TypeScript Definitions")
        content.append(" * Do not edit manually.")
        content.append(" */")
        content.append("")
        
        if namespace:
            content.append(f"export namespace {namespace} {{")
            indent = "  "
        else:
            indent = ""

        for bo in objects:
            self.stdout.write(f"Generating type for {bo.code}...")
            ts_interface = self._generate_interface(bo, indent)
            content.append(ts_interface)
            content.append("")

        if namespace:
            content.append("}")

        # Write to file
        if output_path.suffix:
            # It's a file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(content), encoding='utf-8')
            self.stdout.write(self.style.SUCCESS(f"✓ Generated types in {output_path}"))
        else:
            # It's a directory
            output_path.mkdir(parents=True, exist_ok=True)
            file_path = output_path / 'schema.d.ts'
            file_path.write_text("\n".join(content), encoding='utf-8')
            self.stdout.write(self.style.SUCCESS(f"✓ Generated types in {file_path}"))

    def _generate_interface(self, bo: BusinessObject, indent: str) -> str:
        """Generate TypeScript interface for a single BO."""
        lines = []
        
        # Docstring
        if bo.description:
            lines.append(f"{indent}/**")
            lines.append(f"{indent} * {bo.name} ({bo.code})")
            lines.append(f"{indent} * {bo.description}")
            lines.append(f"{indent} */")
        
        lines.append(f"{indent}export interface {bo.code} {{")
        
        # Standard fields
        lines.append(f"{indent}  id: string;")
        lines.append(f"{indent}  created_at: string;")
        lines.append(f"{indent}  updated_at: string;")
        lines.append(f"{indent}  created_by?: string;")
        
        if bo.enable_version:
             lines.append(f"{indent}  version: number;")
        
        if bo.enable_workflow:
            lines.append(f"{indent}  workflow_status?: string;")
            lines.append(f"{indent}  workflow_instance_id?: string;")

        # Custom fields
        fields = bo.field_definitions.filter(is_deleted=False).order_by('sort_order')
        
        for field in fields:
            ts_type = self.TYPE_MAPPING.get(field.field_type, 'any')
            
            # Handle options for select types as union types if simpler
            # For now keeping it simple mapped types
            
            optional = "?" if not field.is_required else ""
            readonly = "readonly " if field.is_readonly else ""
            
            # Add field comment
            lines.append(f"{indent}  /** {field.name} */")
            lines.append(f"{indent}  {readonly}{field.code}{optional}: {ts_type};")

        # Dynamic fields container for non-hardcoded objects
        if not bo.is_hardcoded:
            lines.append(f"{indent}  // Dynamic fields storage")
            lines.append(f"{indent}  [key: string]: any;")

        lines.append(f"{indent}}}")
        return "\n".join(lines)
