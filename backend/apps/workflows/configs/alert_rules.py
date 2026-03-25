"""
Helpers for loading and persisting SLA alert rule configuration.
"""

import json
from pathlib import Path
from typing import Any, Dict

from django.conf import settings

DEFAULT_ALERT_RULES_PATH = Path(__file__).with_suffix('.json')
READABLE_WRITEABLE_MODE = 0o644


def get_alert_rules_path() -> Path:
    """Resolve the alert rules file path, allowing test overrides."""
    configured_path = getattr(settings, 'WORKFLOW_ALERT_RULES_PATH', None)
    return Path(configured_path) if configured_path else DEFAULT_ALERT_RULES_PATH


def load_alert_rules() -> Dict[str, Any]:
    """Load the current alert rule configuration from disk."""
    alert_rules_path = get_alert_rules_path()
    with alert_rules_path.open('r', encoding='utf-8') as config_file:
        return json.load(config_file)


def save_alert_rules(configuration: Dict[str, Any]) -> Dict[str, Any]:
    """Write the alert rule configuration to disk and return the saved data."""
    alert_rules_path = get_alert_rules_path()
    alert_rules_path.parent.mkdir(parents=True, exist_ok=True)

    with alert_rules_path.open('w', encoding='utf-8') as config_file:
        json.dump(configuration, config_file, indent=2)
        config_file.write('\n')

    alert_rules_path.chmod(READABLE_WRITEABLE_MODE)
    return reload_alert_rules()


def reload_alert_rules() -> Dict[str, Any]:
    """Reload the module-level alert rules cache from disk."""
    global alert_rules
    alert_rules = load_alert_rules()
    return alert_rules


alert_rules = load_alert_rules()
