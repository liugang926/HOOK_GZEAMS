"""
Metadata code generator for generating Python code from BusinessObject definitions.

Provides:
- Serializer generation
- ViewSet generation
- Filter generation
- URL route generation
"""
from typing import Optional, List
from textwrap import dedent


class MetadataCodeGenerator:
    """
    Generates Python code from BusinessObject and FieldDefinition metadata.

    Usage:
        generator = MetadataCodeGenerator(business_object)
        serializer_code = generator.generate_serializer()
        viewset_code = generator.generate_viewset()
    """

    # DRF field type mapping
    FIELD_TYPE_MAPPING = {
        'text': 'CharField',
        'textarea': 'CharField',
        'number': 'DecimalField',
        'integer': 'IntegerField',
        'float': 'FloatField',
        'boolean': 'BooleanField',
        'date': 'DateField',
        'datetime': 'DateTimeField',
        'time': 'TimeField',
        'email': 'EmailField',
        'url': 'URLField',
        'choice': 'ChoiceField',
        'multi_choice': 'MultipleChoiceField',
        'file': 'FileField',
        'image': 'ImageField',
        'reference': 'PrimaryKeyRelatedField',
        'user': 'PrimaryKeyRelatedField',
        'department': 'PrimaryKeyRelatedField',
        'json': 'JSONField',
    }

    def __init__(self, business_object):
        """
        Initialize generator.

        Args:
            business_object: BusinessObject instance
        """
        self.business_object = business_object
        self.field_definitions = list(
            business_object.field_definitions.filter(is_active=True).order_by('sort_order')
        )

    def generate_serializer(self) -> str:
        """Generate serializer class code."""
        class_name = f"{self._to_pascal_case(self.business_object.code)}Serializer"

        fields_code = []
        for fd in self.field_definitions:
            field_code = self._generate_field(fd)
            fields_code.append(f"    {fd.code} = {field_code}")

        field_names = [f"'{fd.code}'" for fd in self.field_definitions]

        code = dedent(f'''
        from rest_framework import serializers
        from apps.common.serializers.base import BaseModelSerializer


        class {class_name}(BaseModelSerializer):
            """
            Auto-generated serializer for {self.business_object.name}.
            Generated from BusinessObject: {self.business_object.code}
            """

        {chr(10).join(fields_code)}

            class Meta(BaseModelSerializer.Meta):
                model = None  # Set to actual model
                fields = BaseModelSerializer.Meta.fields + [
                    {', '.join(field_names)}
                ]
        ''').strip()

        return code

    def generate_viewset(self) -> str:
        """Generate ViewSet class code."""
        class_name = f"{self._to_pascal_case(self.business_object.code)}ViewSet"
        serializer_name = f"{self._to_pascal_case(self.business_object.code)}Serializer"
        filter_name = f"{self._to_pascal_case(self.business_object.code)}Filter"

        search_fields = [
            f"'{fd.code}'" for fd in self.field_definitions
            if fd.is_searchable
        ]
        ordering_fields = [
            f"'{fd.code}'" for fd in self.field_definitions
            if fd.sortable
        ]

        code = dedent(f'''
        from rest_framework import viewsets
        from apps.common.viewsets.base import BaseModelViewSet, BatchOperationMixin


        class {class_name}(BatchOperationMixin, BaseModelViewSet):
            """
            Auto-generated ViewSet for {self.business_object.name}.
            Generated from BusinessObject: {self.business_object.code}
            """

            # queryset = Model.objects.all()  # Set actual model
            serializer_class = {serializer_name}
            filterset_class = {filter_name}

            search_fields = [{', '.join(search_fields)}]
            ordering_fields = [{', '.join(ordering_fields)}]
            ordering = ['-created_at']
        ''').strip()

        return code

    def generate_filter(self) -> str:
        """Generate Filter class code."""
        class_name = f"{self._to_pascal_case(self.business_object.code)}Filter"

        filter_fields = []
        for fd in self.field_definitions:
            if fd.show_in_filter:
                filter_code = self._generate_filter_field(fd)
                filter_fields.append(f"    {fd.code} = {filter_code}")

        code = dedent(f'''
        import django_filters
        from apps.common.filters.base import BaseModelFilter


        class {class_name}(BaseModelFilter):
            """
            Auto-generated filter for {self.business_object.name}.
            Generated from BusinessObject: {self.business_object.code}
            """

        {chr(10).join(filter_fields)}

            class Meta(BaseModelFilter.Meta):
                model = None  # Set to actual model
                fields = BaseModelFilter.Meta.fields + [
                    {', '.join([f"'{fd.code}'" for fd in self.field_definitions if fd.show_in_filter])}
                ]
        ''').strip()

        return code

    def generate_urls(self, app_name: str = 'api') -> str:
        """Generate URL configuration code."""
        viewset_name = f"{self._to_pascal_case(self.business_object.code)}ViewSet"
        route_name = self.business_object.code.lower()

        code = dedent(f'''
        from django.urls import path, include
        from rest_framework.routers import DefaultRouter


        router = DefaultRouter()
        router.register(r'{route_name}', {viewset_name}, basename='{route_name}')

        urlpatterns = [
            path('{app_name}/', include(router.urls)),
        ]
        ''').strip()

        return code

    def generate_all(self) -> dict:
        """Generate all code files."""
        return {
            'serializer': self.generate_serializer(),
            'viewset': self.generate_viewset(),
            'filter': self.generate_filter(),
            'urls': self.generate_urls(),
        }

    def _generate_field(self, field_def) -> str:
        """Generate serializer field code."""
        field_class = self.FIELD_TYPE_MAPPING.get(field_def.field_type, 'CharField')
        kwargs = []

        if field_def.is_required:
            kwargs.append('required=True')
        else:
            kwargs.append('required=False')

        if field_def.is_readonly:
            kwargs.append('read_only=True')

        if field_def.max_length and field_def.field_type in ['text', 'textarea']:
            kwargs.append(f'max_length={field_def.max_length}')

        if field_def.field_type == 'number':
            kwargs.append(f"max_digits={getattr(field_def, 'max_digits', 10) or 10}")
            kwargs.append(f"decimal_places={field_def.decimal_places or 2}")

        if field_def.min_value is not None:
            kwargs.append(f'min_value={field_def.min_value}')

        if field_def.max_value is not None:
            kwargs.append(f'max_value={field_def.max_value}')

        if field_def.field_type in ['choice', 'multi_choice'] and field_def.options:
            options = field_def.options
            if isinstance(options, dict):
                choices = [(k, v) for k, v in options.items()]
            else:
                choices = [(o, o) for o in options]
            kwargs.append(f'choices={choices}')

        if field_def.default_value is not None:
            if isinstance(field_def.default_value, str):
                kwargs.append(f"default='{field_def.default_value}'")
            else:
                kwargs.append(f'default={field_def.default_value}')

        kwargs_str = ', '.join(kwargs)
        return f"serializers.{field_class}({kwargs_str})"

    def _generate_filter_field(self, field_def) -> str:
        """Generate filter field code."""
        filter_mapping = {
            'text': 'CharFilter',
            'textarea': 'CharFilter',
            'number': 'NumberFilter',
            'integer': 'NumberFilter',
            'float': 'NumberFilter',
            'boolean': 'BooleanFilter',
            'date': 'DateFilter',
            'datetime': 'DateTimeFilter',
            'choice': 'ChoiceFilter',
            'multi_choice': 'MultipleChoiceFilter',
            'reference': 'UUIDFilter',
            'user': 'UUIDFilter',
            'department': 'UUIDFilter',
        }

        filter_class = filter_mapping.get(field_def.field_type, 'CharFilter')
        kwargs = [f"label='{field_def.name}'"]

        if field_def.field_type in ['text', 'textarea']:
            kwargs.append("lookup_expr='icontains'")

        return f"django_filters.{filter_class}({', '.join(kwargs)})"

    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        words = text.replace('_', ' ').replace('-', ' ').split()
        return ''.join(word.capitalize() for word in words)


def generate_code_for_business_object(
    business_object_code: str,
    output_dir: Optional[str] = None
) -> dict:
    """
    Convenience function to generate code for a business object.

    Args:
        business_object_code: BusinessObject code
        output_dir: Optional directory to write files

    Returns:
        Dict of generated code
    """
    from apps.system.models import BusinessObject

    try:
        business_object = BusinessObject.objects.get(
            code=business_object_code,
            is_active=True
        )
    except BusinessObject.DoesNotExist:
        raise ValueError(f"BusinessObject '{business_object_code}' not found")

    generator = MetadataCodeGenerator(business_object)
    code = generator.generate_all()

    if output_dir:
        import os
        os.makedirs(output_dir, exist_ok=True)

        for filename, content in code.items():
            filepath = os.path.join(output_dir, f'{filename}.py')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

    return code
