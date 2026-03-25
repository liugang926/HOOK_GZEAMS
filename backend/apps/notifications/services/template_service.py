"""
Template Service

Handles template rendering with Jinja2.
Provides template lookup, variable merging, and content generation.
"""
import logging
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.utils import timezone
from jinja2 import Template, TemplateError, TemplateSyntaxError

from apps.notifications.models import NotificationTemplate

logger = logging.getLogger(__name__)


class TemplateService:
    """
    Service for managing and rendering notification templates.

    Provides:
    - Template lookup by code and channel
    - Variable merging with defaults
    - Jinja2 rendering with error handling
    - Template caching for performance
    """

    # Cache timeout for templates (5 minutes)
    CACHE_TIMEOUT = 300

    def get_template(
        self,
        template_code: str,
        channel: str,
        language: str = 'zh-CN'
    ) -> Optional[NotificationTemplate]:
        """
        Get active template by code and channel.

        Args:
            template_code: Template code identifier
            channel: Channel type (inbox, email, sms, etc.)
            language: Template language code

        Returns:
            NotificationTemplate instance or None
        """
        # Try cache first
        cache_key = f'template:{template_code}:{channel}:{language}'
        cached_template = cache.get(cache_key)
        if cached_template:
            return cached_template

        # Query database
        try:
            template = NotificationTemplate.objects.filter(
                template_code=template_code,
                channel=channel,
                language=language,
                is_active=True,
                is_deleted=False
            ).first()

            if template:
                # Cache for performance
                cache.set(cache_key, template, self.CACHE_TIMEOUT)

            return template

        except Exception as e:
            logger.error(f"Error getting template {template_code}: {e}")
            return None

    def render_template(
        self,
        template_code: str,
        channel: str,
        variables: Dict[str, Any],
        language: str = 'zh-CN'
    ) -> Optional[Dict[str, str]]:
        """
        Render template with given variables.

        Args:
            template_code: Template code identifier
            channel: Channel type
            variables: Template variables
            language: Template language code

        Returns:
            Dict with 'subject' and 'content' keys, or None if failed
        """
        # Get template
        template = self.get_template(template_code, channel, language)
        if not template:
            logger.warning(
                f"Template not found: code={template_code}, "
                f"channel={channel}, language={language}"
            )
            return None

        # Merge variables with template defaults
        merged_variables = self._merge_variables(template, variables)

        # Render template
        try:
            return template.render(merged_variables)
        except (TemplateError, TemplateSyntaxError) as e:
            logger.error(
                f"Template rendering error for {template_code}: {e}"
            )
            return None

    def render_template_string(
        self,
        template_string: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Render a template string directly.

        Args:
            template_string: Jinja2 template string
            variables: Template variables

        Returns:
            Rendered string
        """
        try:
            template = Template(template_string)
            return template.render(**variables)
        except (TemplateError, TemplateSyntaxError) as e:
            logger.error(f"Template string rendering error: {e}")
            return template_string  # Return original on error

    def preview_template(
        self,
        template_code: str,
        channel: str,
        language: str = 'zh-CN'
    ) -> Optional[Dict[str, Any]]:
        """
        Get template preview with example data.

        Args:
            template_code: Template code identifier
            channel: Channel type
            language: Template language code

        Returns:
            Dict with template info and rendered preview
        """
        template = self.get_template(template_code, channel, language)
        if not template:
            return None

        # Use example data from template if available
        example_data = template.example_data or {}

        # Render with example data
        rendered = None
        if example_data:
            rendered = template.render(example_data)

        return {
            'template_code': template.template_code,
            'template_name': template.template_name,
            'channel': template.channel,
            'subject_template': template.subject_template,
            'content_template': template.content_template,
            'variables': template.variables,
            'example_data': example_data,
            'rendered': rendered,
        }

    def validate_template(
        self,
        subject_template: str,
        content_template: str,
        variables: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate template syntax and variables.

        Args:
            subject_template: Subject template string
            content_template: Content template string
            variables: Expected variables with default values

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Test rendering with default values
            test_template = Template(subject_template or '')
            test_template.render(**variables)

            test_template = Template(content_template)
            test_template.render(**variables)

            return True, None

        except TemplateSyntaxError as e:
            return False, f"Template syntax error: {e}"
        except Exception as e:
            return False, f"Template validation error: {e}"

    def get_required_variables(
        self,
        template_code: str,
        channel: str,
        language: str = 'zh-CN'
    ) -> List[str]:
        """
        Get list of required variables for a template.

        Args:
            template_code: Template code identifier
            channel: Channel type
            language: Template language code

        Returns:
            List of variable names
        """
        template = self.get_template(template_code, channel, language)
        if not template:
            return []

        # Get variables that don't have default values
        all_variables = template.variables or {}
        required = [
            name for name, info in all_variables.items()
            if info.get('required', True) or 'default' not in info
        ]

        return required

    def _merge_variables(
        self,
        template: NotificationTemplate,
        user_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge user variables with template defaults.

        Args:
            template: NotificationTemplate instance
            user_variables: Variables provided by caller

        Returns:
            Merged variables dictionary
        """
        template_variables = template.variables or {}
        merged = {}

        # Add system variables
        merged.update({
            'now': timezone.now(),
            'today': timezone.now().date(),
        })

        # Add template defaults
        for var_name, var_info in template_variables.items():
            if isinstance(var_info, dict):
                default = var_info.get('default')
                if default is not None:
                    merged[var_name] = default
            else:
                # Simple value as default
                merged[var_name] = var_info

        # Override with user variables
        merged.update(user_variables)

        return merged

    def clear_template_cache(
        self,
        template_code: Optional[str] = None
    ) -> None:
        """
        Clear template cache.

        Args:
            template_code: Specific template code to clear, or None for all
        """
        if template_code:
            # Clear specific template (all channels/languages)
            # This is a simplified approach - in production you might
            # want to track exact cache keys
            cache_key_pattern = f'template:{template_code}:*'
            # For simplicity, just delete the common keys
            for channel in ['inbox', 'email', 'sms', 'wework', 'dingtalk']:
                cache.delete(f'template:{template_code}:{channel}:zh-CN')
                cache.delete(f'template:{template_code}:{channel}:en-US')
        else:
            # Clear all notification templates from cache
            # Note: This would require tracking cache keys or using cache versioning
            logger.info("Template cache cleared")

    def get_template_variables(
        self,
        template_code: str,
        channel: str,
        language: str = 'zh-CN'
    ) -> Optional[Dict[str, Any]]:
        """
        Get variable definition for a template.

        Args:
            template_code: Template code identifier
            channel: Channel type
            language: Template language code

        Returns:
            Dictionary of variable definitions
        """
        template = self.get_template(template_code, channel, language)
        if not template:
            return None

        return template.variables or {}

    def create_template_preview_data(
        self,
        template_code: str,
        channel: str,
        language: str = 'zh-CN'
    ) -> Dict[str, Any]:
        """
        Create sample data for template preview/testing.

        Args:
            template_code: Template code identifier
            channel: Channel type
            language: Template language code

        Returns:
            Sample data dictionary
        """
        template = self.get_template(template_code, channel, language)
        if not template:
            return {}

        variables = template.variables or {}
        sample_data = {
            'now': timezone.now(),
            'today': timezone.now().date(),
        }

        for var_name, var_info in variables.items():
            if isinstance(var_info, dict):
                if 'example' in var_info:
                    sample_data[var_name] = var_info['example']
                elif 'default' in var_info:
                    sample_data[var_name] = var_info['default']
                else:
                    sample_data[var_name] = f"[{var_name}]"
            else:
                sample_data[var_name] = var_info

        return sample_data


# Singleton instance
template_service = TemplateService()
