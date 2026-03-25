from django.db import migrations


FINANCE_VOUCHER_WORKBENCH = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/FinanceVoucher",
    "legacy_aliases": ["/finance/vouchers"],
    "toolbar": {
        "primary_actions": [
            {
                "code": "post",
                "label_key": "finance.actions.post",
                "action_path": "post",
                "button_type": "success",
                "confirm_message_key": "finance.messages.confirmPost",
                "visible_when": {
                    "statuses": ["approved"],
                },
            }
        ],
        "secondary_actions": [
            {
                "code": "retry_push",
                "label_key": "finance.actions.retryPush",
                "action_path": "retry",
                "button_type": "warning",
                "confirm_message_key": "finance.messages.confirmRetryPush",
                "visible_when": {
                    "statuses": ["approved", "posted"],
                },
            }
        ],
    },
    "detail_panels": [
        {
            "code": "voucher_entries",
            "title_key": "finance.panels.entries",
            "component": "finance-voucher-entries",
        },
        {
            "code": "sync_status",
            "title_key": "finance.panels.syncStatus",
            "component": "finance-voucher-sync-status",
            "visible_when": {
                "statuses": ["approved", "posted"],
            },
        },
        {
            "code": "integration_logs",
            "title_key": "finance.panels.integrationLogs",
            "component": "finance-voucher-integration-logs",
        },
    ],
    "async_indicators": [
        {
            "code": "sync_task",
            "type": "sync-task",
            "label_key": "finance.panels.syncStatus",
            "visible_when": {
                "statuses": ["approved", "posted"],
            },
        }
    ],
}


def seed_finance_voucher_workbench(apps, schema_editor):
    BusinessObject = apps.get_model("system", "BusinessObject")
    finance_voucher = BusinessObject.objects.filter(code="FinanceVoucher").first()
    if finance_voucher is None:
        return

    menu_config = dict(finance_voucher.menu_config or {})
    workbench = dict(menu_config.get("workbench") or {})
    workbench.update(FINANCE_VOUCHER_WORKBENCH)

    menu_config.update(
        {
            "url": "/objects/FinanceVoucher",
            "show_in_menu": False,
            "workbench": workbench,
        }
    )

    finance_voucher.menu_config = menu_config
    finance_voucher.save(update_fields=["menu_config"])


class Migration(migrations.Migration):
    dependencies = [
        ("system", "0044_receipt_disposal_master_detail_protocol"),
    ]

    operations = [
        migrations.RunPython(seed_finance_voucher_workbench, migrations.RunPython.noop),
    ]
