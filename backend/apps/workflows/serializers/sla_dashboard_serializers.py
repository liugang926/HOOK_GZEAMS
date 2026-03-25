"""
Serializers for SLA dashboard configuration APIs.
"""

from copy import deepcopy
from typing import Any, Dict

from rest_framework import serializers

from apps.workflows.configs.alert_rules import load_alert_rules, save_alert_rules


class SLAAlertConfigSerializer(serializers.Serializer):
    """Validate and persist SLA alert threshold updates."""

    alert_rules = serializers.DictField(required=True)

    MINIMUM_THRESHOLD_BY_TYPE = {
        'percentage': 0,
        'response_time': 1,
        'memory': 1,
    }

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate threshold updates against the current stored configuration."""
        current_config = load_alert_rules()
        attrs['alert_rules'] = self.validate_thresholds(attrs['alert_rules'], current_config)
        attrs['current_config'] = current_config
        return attrs

    def validate_thresholds(
        self,
        threshold_updates: Dict[str, Any],
        current_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate partial threshold updates and normalize the payload."""
        if not threshold_updates:
            raise serializers.ValidationError({
                'alert_rules': 'At least one alert rule update is required.'
            })

        current_rules = current_config.get('alert_rules', {})
        normalized_updates: Dict[str, Any] = {}

        for rule_code, rule_update in threshold_updates.items():
            current_rule = current_rules.get(rule_code)
            if current_rule is None:
                raise serializers.ValidationError({
                    'alert_rules': f'Unknown alert rule "{rule_code}".'
                })

            if not isinstance(rule_update, dict):
                raise serializers.ValidationError({
                    'alert_rules': f'Rule "{rule_code}" must be an object.'
                })

            metrics_update = rule_update.get('metrics')
            if not isinstance(metrics_update, dict) or not metrics_update:
                raise serializers.ValidationError({
                    'alert_rules': f'Rule "{rule_code}" must include a non-empty "metrics" object.'
                })

            normalized_updates[rule_code] = {'metrics': {}}

            for metric_code, metric_update in metrics_update.items():
                current_metric = current_rule.get('metrics', {}).get(metric_code)
                if current_metric is None:
                    raise serializers.ValidationError({
                        'alert_rules': f'Unknown metric "{rule_code}.{metric_code}".'
                    })

                if not isinstance(metric_update, dict) or not metric_update:
                    raise serializers.ValidationError({
                        'alert_rules': f'Metric "{rule_code}.{metric_code}" must include threshold values.'
                    })

                invalid_fields = set(metric_update.keys()) - {
                    'warning_threshold',
                    'critical_threshold',
                }
                if invalid_fields:
                    invalid_field_list = ', '.join(sorted(invalid_fields))
                    raise serializers.ValidationError({
                        'alert_rules': (
                            f'Metric "{rule_code}.{metric_code}" contains unsupported fields: '
                            f'{invalid_field_list}.'
                        )
                    })

                merged_metric = deepcopy(current_metric)
                for threshold_name, threshold_value in metric_update.items():
                    if isinstance(threshold_value, bool) or not isinstance(
                        threshold_value,
                        (int, float),
                    ):
                        raise serializers.ValidationError({
                            'alert_rules': (
                                f'"{rule_code}.{metric_code}.{threshold_name}" must be a number.'
                            )
                        })

                    minimum_value = self._get_minimum_threshold(current_metric, threshold_name)
                    if threshold_value < minimum_value:
                        raise serializers.ValidationError({
                            'alert_rules': (
                                f'"{rule_code}.{metric_code}.{threshold_name}" must be greater '
                                f'than or equal to {minimum_value}.'
                            )
                        })

                    merged_metric[threshold_name] = threshold_value

                self._validate_threshold_order(rule_code, metric_code, current_metric, merged_metric)

                normalized_updates[rule_code]['metrics'][metric_code] = {
                    'warning_threshold': merged_metric['warning_threshold'],
                    'critical_threshold': merged_metric['critical_threshold'],
                }

        return normalized_updates

    def update_alert_rules(self) -> Dict[str, Any]:
        """Persist the validated threshold updates to the alert rules file."""
        if not hasattr(self, 'validated_data'):
            raise AssertionError('Call is_valid() before update_alert_rules().')

        updated_config = deepcopy(self.validated_data['current_config'])
        validated_updates = self.validated_data['alert_rules']

        for rule_code, rule_update in validated_updates.items():
            for metric_code, metric_thresholds in rule_update['metrics'].items():
                updated_config['alert_rules'][rule_code]['metrics'][metric_code].update(
                    metric_thresholds
                )

        return save_alert_rules(updated_config)

    def _get_minimum_threshold(
        self,
        current_metric: Dict[str, Any],
        threshold_name: str,
    ) -> float:
        """Resolve the minimum allowed value for a threshold."""
        explicit_minimum = current_metric.get(f'minimum_{threshold_name}')
        if explicit_minimum is not None:
            return explicit_minimum

        return self.MINIMUM_THRESHOLD_BY_TYPE.get(current_metric.get('type'), 0)

    def _validate_threshold_order(
        self,
        rule_code: str,
        metric_code: str,
        current_metric: Dict[str, Any],
        merged_metric: Dict[str, Any],
    ) -> None:
        """Keep warning and critical thresholds in the same severity direction."""
        current_warning = current_metric['warning_threshold']
        current_critical = current_metric['critical_threshold']
        warning_threshold = merged_metric['warning_threshold']
        critical_threshold = merged_metric['critical_threshold']

        if current_warning <= current_critical and warning_threshold > critical_threshold:
            raise serializers.ValidationError({
                'alert_rules': (
                    f'"{rule_code}.{metric_code}" requires warning_threshold to be less than '
                    f'or equal to critical_threshold.'
                )
            })

        if current_warning > current_critical and warning_threshold < critical_threshold:
            raise serializers.ValidationError({
                'alert_rules': (
                    f'"{rule_code}.{metric_code}" requires warning_threshold to be greater than '
                    f'or equal to critical_threshold.'
                )
            })
