"""
Validate that Django components inherit from proper GZEAMS base classes.

GZEAMS Standards:
- Models: BaseModel (apps.common.models.BaseModel)
- Serializers: BaseModelSerializer (apps.common.serializers.base.BaseModelSerializer)
- ViewSets: BaseModelViewSetWithBatch (apps.common.viewsets.base.BaseModelViewSetWithBatch)
- Services: BaseCRUDService (apps.common.services.base_crud.BaseCRUDService)
- Filters: BaseModelFilter (apps.common.filters.base.BaseModelFilter)
"""

import sys
import re
from pathlib import Path

def check_file(filepath):
    """Check a Python file for proper base class inheritance."""
    try:
        content = Path(filepath).read_text(encoding='utf-8')
    except:
        return []

    issues = []

    # Extract class definitions
    class_pattern = re.compile(r'^class\s+(\w+)\s*\(([^)]+)\):', re.MULTILINE)
    imports = {}

    # Track imports from common modules
    for match in re.finditer(r'^from\s+apps\.common\.(\w+)\s+import\s+([^\n]+)', content, re.MULTILINE):
        module, classes = match.groups()
        for cls in classes.split(','):
            imports[cls.strip()] = f'apps.common.{module}'

    # Check each class
    for match in class_pattern.finditer(content):
        class_name, base_classes = match.groups()
        bases = [b.strip() for b in base_classes.split(',')]

        # Determine expected base class by class name pattern
        expected_base = None
        if 'Model' in class_name and 'Serializer' not in class_name:
            if class_name == 'BaseModel':
                continue  # Skip BaseModel itself
            expected_base = 'BaseModel'
            source_module = 'models'
        elif class_name.endswith('Serializer'):
            if 'BaseModelSerializer' in class_name or 'Base' in class_name:
                continue  # Skip base classes themselves
            expected_base = 'BaseModelSerializer'
            source_module = 'serializers'
        elif class_name.endswith('ViewSet'):
            if 'Base' in class_name:
                continue  # Skip base classes themselves
            expected_base = 'BaseModelViewSetWithBatch'
            source_module = 'viewsets'
        elif class_name.endswith('Service'):
            if 'Base' in class_name:
                continue  # Skip base classes themselves
            expected_base = 'BaseCRUDService'
            source_module = 'services'
        elif class_name.endswith('Filter'):
            if 'Base' in class_name:
                continue  # Skip base classes themselves
            expected_base = 'BaseModelFilter'
            source_module = 'filters'

        if expected_base:
            # Check if it inherits from the expected base
            if expected_base not in bases:
                # Check if the base is imported
                base_imported = any(expected_base in imports.get(b, '') for b in bases)
                if not base_imported:
                    issues.append({
                        'class': class_name,
                        'expected': f'apps.common.{source_module}.{expected_base}',
                        'found': ', '.join(bases)
                    })

    return issues

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        issues = check_file(filepath)

        if issues:
            print(f"⚠️  Base class violations in {filepath}:")
            for issue in issues:
                print(f"  {issue['class']}: Expected '{issue['expected']}', found '{issue['found']}'")
            sys.exit(1)
        else:
            sys.exit(0)
    else:
        # Check all backend Python files
        backend_path = Path('backend/apps')
        if not backend_path.exists():
            print("Backend directory not found")
            sys.exit(0)

        all_issues = {}
        for py_file in backend_path.rglob('*.py'):
            issues = check_file(str(py_file))
            if issues:
                all_issues[str(py_file)] = issues

        if all_issues:
            print("⚠️  GZEAMS Base Class Validation Issues:")
            for filepath, issues in all_issues.items():
                print(f"\n{filepath}:")
                for issue in issues:
                    print(f"  {issue['class']}: Expected '{issue['expected']}', found '{issue['found']}'")
            sys.exit(1)
        else:
            print("✅ All classes inherit from proper GZEAMS base classes")
            sys.exit(0)
