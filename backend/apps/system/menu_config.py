"""
Standard menu configuration for metadata-driven navigation.

This module is the single runtime source of truth for:
- standard menu groups
- default menu placement for registered business objects
- static system pages that belong in the main navigation

No localized labels are stored here. Runtime consumers must resolve
`translation_key` fields through the i18n layer.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional

from apps.system.models import BusinessObject, MenuEntry, MenuGroup
from apps.system.services.hardcoded_object_sync_service import HardcodedObjectSyncService


MenuConfig = Dict[str, Any]
MenuManagementSettings = Dict[str, Any]


ASSET_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/Asset",
    "toolbar": {
        "primary_actions": [],
        "secondary_actions": [],
    },
    "detail_panels": [],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "asset_source_request",
            "label_key": "assets.workbench.summary.sourcePurchaseRequest",
            "value_field": "source_purchase_request_no",
        },
        {
            "code": "asset_source_receipt",
            "label_key": "assets.workbench.summary.sourceReceipt",
            "value_field": "source_receipt_no",
        },
        {
            "code": "asset_active_project_allocations",
            "label_key": "assets.workbench.summary.activeProjectAllocations",
            "value_field": "closure_summary.metrics.active_project_allocation_count",
            "tone": "warning",
        },
        {
            "code": "asset_pending_inventory_differences",
            "label_key": "assets.workbench.summary.pendingInventoryDifferences",
            "value_field": "closure_summary.metrics.pending_inventory_difference_count",
            "tone": "warning",
        },
        {
            "code": "asset_open_maintenance",
            "label_key": "assets.workbench.summary.openMaintenance",
            "value_field": "closure_summary.metrics.open_maintenance_count",
        },
        {
            "code": "asset_open_disposals",
            "label_key": "assets.workbench.summary.openDisposals",
            "value_field": "closure_summary.metrics.open_disposal_count",
        },
        {
            "code": "asset_linked_finance_vouchers",
            "label_key": "assets.workbench.summary.linkedFinanceVouchers",
            "value_field": "closure_summary.metrics.linked_finance_voucher_count",
        },
        {
            "code": "asset_open_finance_vouchers",
            "label_key": "assets.workbench.summary.openFinanceVouchers",
            "value_field": "closure_summary.metrics.open_finance_voucher_count",
            "tone": "warning",
        },
    ],
    "queue_panels": [
        {
            "code": "asset_project_allocations",
            "title_key": "assets.workbench.queues.projectAllocations",
            "count_field": "closure_summary.metrics.active_project_allocation_count",
            "route": "/objects/ProjectAsset?asset={id}&return_status=in_use",
        },
        {
            "code": "asset_inventory_differences",
            "title_key": "assets.workbench.queues.inventoryDifferences",
            "count_field": "closure_summary.metrics.pending_inventory_difference_count",
            "route": "/objects/InventoryItem?asset={id}&unresolved_only=true",
        },
        {
            "code": "asset_maintenance_records",
            "title_key": "assets.workbench.queues.maintenanceRecords",
            "count_field": "closure_summary.metrics.open_maintenance_count",
            "route": "/objects/Maintenance?asset_id={id}",
        },
        {
            "code": "asset_disposal_requests",
            "title_key": "assets.workbench.queues.disposalRequests",
            "count_field": "closure_summary.metrics.open_disposal_count",
            "route": "/objects/DisposalRequest?asset_id={id}",
        },
        {
            "code": "asset_finance_vouchers",
            "title_key": "assets.workbench.queues.financeVouchers",
            "count_field": "closure_summary.metrics.linked_finance_voucher_count",
            "route": "/objects/FinanceVoucher?source_asset={id}",
        },
    ],
    "exception_panels": [
        {
            "code": "asset_inventory_follow_up_tasks",
            "title_key": "assets.workbench.queues.inventoryFollowUps",
            "count_field": "closure_summary.metrics.pending_inventory_follow_up_count",
            "route": "/objects/InventoryItem?asset={id}&manual_follow_up_only=true&unresolved_only=true",
            "tone": "danger",
        }
    ],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion_display",
    },
    "sla_indicators": [],
    "recommended_actions": [],
}

ASSET_PROJECT_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/AssetProject",
    "toolbar": {
        "primary_actions": [
            {
                "code": "refresh_rollups",
                "label_key": "projects.actions.refreshRollups",
                "action_path": "refresh_rollups",
                "button_type": "primary",
            }
        ],
        "secondary_actions": [
            {
                "code": "close_project",
                "label_key": "projects.actions.closeProject",
                "action_path": "close",
                "button_type": "warning",
                "confirm_message_key": "projects.messages.confirmCloseProject",
                "visible_when": {
                    "status_in": ["active", "suspended"],
                },
            }
        ],
    },
    "detail_panels": [
        {
            "code": "project_overview",
            "title_key": "projects.panels.overview",
            "component": "asset-project-overview",
        },
        {
            "code": "project_assets",
            "title_key": "projects.panels.assets",
            "component": "asset-project-assets",
        },
        {
            "code": "project_members",
            "title_key": "projects.panels.members",
            "component": "asset-project-members",
        },
        {
            "code": "project_returns",
            "title_key": "projects.panels.pendingReturns",
            "component": "asset-project-returns",
        },
        {
            "code": "project_return_history",
            "title_key": "projects.panels.returnHistory",
            "component": "asset-project-return-history",
        },
    ],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "project_asset_count",
            "label_key": "projects.workbench.summary.assetCount",
            "value_field": "asset_count",
        },
        {
            "code": "project_active_asset_count",
            "label_key": "projects.workbench.summary.activeAssetCount",
            "value_field": "active_asset_count",
            "tone": "warning",
        },
        {
            "code": "project_member_count",
            "label_key": "projects.workbench.summary.memberCount",
            "value_field": "member_count",
        },
        {
            "code": "project_progress",
            "label_key": "projects.workbench.summary.progress",
            "value_field": "progress",
            "suffix": "%",
            "tone": "success",
        },
        {
            "code": "project_pending_returns",
            "label_key": "projects.workbench.summary.pendingReturnCount",
            "value_field": "closure_summary.metrics.pending_return_count",
            "tone": "warning",
        },
    ],
    "queue_panels": [
        {
            "code": "project_active_allocations",
            "title_key": "projects.workbench.queues.activeAllocations",
            "count_field": "closure_summary.metrics.active_assets",
            "route": "/objects/ProjectAsset?project={id}&return_status=in_use",
        },
        {
            "code": "project_pending_returns",
            "title_key": "projects.workbench.queues.pendingReturns",
            "count_field": "closure_summary.metrics.pending_return_count",
            "route": "/objects/AssetReturn?project={id}&status=pending",
        },
        {
            "code": "project_members",
            "title_key": "projects.workbench.queues.members",
            "count_field": "closure_summary.metrics.member_count",
            "route": "/objects/ProjectMember?project={id}&is_active=true",
        },
    ],
    "exception_panels": [],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion_display",
    },
    "sla_indicators": [],
    "recommended_actions": [
        {
            "code": "project_close_recommended",
            "label_key": "projects.actions.closeProject",
            "description_key": "projects.workbench.messages.closeProjectHint",
            "action_path": "close",
            "button_type": "warning",
            "visible_when": {
                "status_in": ["active", "suspended"],
            },
        }
    ],
}

PURCHASE_REQUEST_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/PurchaseRequest",
    "toolbar": {
        "primary_actions": [],
        "secondary_actions": [],
    },
    "detail_panels": [],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "purchase_request_total_amount",
            "label_key": "assets.lifecycle.purchaseRequest.workbench.summary.totalAmount",
            "value_field": "total_amount",
        },
        {
            "code": "purchase_request_linked_receipts",
            "label_key": "assets.lifecycle.purchaseRequest.workbench.summary.linkedReceiptCount",
            "value_field": "closure_summary.metrics.linked_receipt_count",
        },
        {
            "code": "purchase_request_generated_assets",
            "label_key": "assets.lifecycle.purchaseRequest.workbench.summary.generatedAssetCount",
            "value_field": "closure_summary.metrics.generated_asset_count",
        },
        {
            "code": "purchase_request_pending_generation",
            "label_key": "assets.lifecycle.purchaseRequest.workbench.summary.pendingGenerationCount",
            "value_field": "closure_summary.metrics.pending_generation_count",
            "tone": "warning",
        },
        {
            "code": "purchase_request_linked_finance_vouchers",
            "label_key": "assets.lifecycle.purchaseRequest.workbench.summary.linkedFinanceVoucherCount",
            "value_field": "closure_summary.metrics.linked_finance_voucher_count",
        },
        {
            "code": "purchase_request_open_finance_vouchers",
            "label_key": "assets.lifecycle.purchaseRequest.workbench.summary.openFinanceVoucherCount",
            "value_field": "closure_summary.metrics.open_finance_voucher_count",
            "tone": "warning",
        },
    ],
    "queue_panels": [
        {
            "code": "purchase_request_receipts",
            "title_key": "assets.lifecycle.purchaseRequest.workbench.queues.receipts",
            "count_field": "closure_summary.metrics.linked_receipt_count",
            "route": "/objects/AssetReceipt?purchase_request_id={id}",
        },
        {
            "code": "purchase_request_assets",
            "title_key": "assets.lifecycle.purchaseRequest.workbench.queues.generatedAssets",
            "count_field": "closure_summary.metrics.generated_asset_count",
            "route": "/objects/Asset?source_purchase_request={id}",
        },
        {
            "code": "purchase_request_finance_vouchers",
            "title_key": "assets.lifecycle.purchaseRequest.workbench.queues.financeVouchers",
            "count_field": "closure_summary.metrics.linked_finance_voucher_count",
            "route": "/objects/FinanceVoucher?source_purchase_request={id}",
        },
    ],
    "exception_panels": [
        {
            "code": "purchase_request_pending_generation",
            "title_key": "assets.lifecycle.purchaseRequest.workbench.queues.pendingGeneration",
            "count_field": "closure_summary.metrics.pending_generation_count",
            "route": "/objects/AssetReceipt?purchase_request_id={id}&status=passed",
            "tone": "warning",
        }
    ],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion_display",
    },
    "sla_indicators": [],
    "recommended_actions": [],
}

ASSET_RECEIPT_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/AssetReceipt",
    "toolbar": {
        "primary_actions": [],
        "secondary_actions": [],
    },
    "detail_panels": [],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "asset_receipt_source_request",
            "label_key": "assets.lifecycle.assetReceipt.workbench.summary.sourcePurchaseRequest",
            "value_field": "closure_summary.metrics.source_purchase_request_no",
        },
        {
            "code": "asset_receipt_total_amount",
            "label_key": "assets.lifecycle.assetReceipt.workbench.summary.totalAmount",
            "value_field": "total_amount",
        },
        {
            "code": "asset_receipt_generated_assets",
            "label_key": "assets.lifecycle.assetReceipt.workbench.summary.generatedAssetCount",
            "value_field": "closure_summary.metrics.generated_asset_count",
        },
        {
            "code": "asset_receipt_pending_generation",
            "label_key": "assets.lifecycle.assetReceipt.workbench.summary.pendingGenerationCount",
            "value_field": "closure_summary.metrics.pending_generation_count",
            "tone": "warning",
        },
        {
            "code": "asset_receipt_linked_finance_vouchers",
            "label_key": "assets.lifecycle.assetReceipt.workbench.summary.linkedFinanceVoucherCount",
            "value_field": "closure_summary.metrics.linked_finance_voucher_count",
        },
        {
            "code": "asset_receipt_open_finance_vouchers",
            "label_key": "assets.lifecycle.assetReceipt.workbench.summary.openFinanceVoucherCount",
            "value_field": "closure_summary.metrics.open_finance_voucher_count",
            "tone": "warning",
        },
    ],
    "queue_panels": [
        {
            "code": "asset_receipt_generated_assets",
            "title_key": "assets.lifecycle.assetReceipt.workbench.queues.generatedAssets",
            "count_field": "closure_summary.metrics.generated_asset_count",
            "route": "/objects/Asset?source_receipt={id}",
        },
        {
            "code": "asset_receipt_finance_vouchers",
            "title_key": "assets.lifecycle.assetReceipt.workbench.queues.financeVouchers",
            "count_field": "closure_summary.metrics.linked_finance_voucher_count",
            "route": "/objects/FinanceVoucher?source_receipt={id}",
        },
    ],
    "exception_panels": [
        {
            "code": "asset_receipt_pending_generation",
            "title_key": "assets.lifecycle.assetReceipt.workbench.queues.pendingGeneration",
            "count_field": "closure_summary.metrics.pending_generation_count",
            "route": "/objects/AssetReceiptItem?asset_receipt_id={id}&asset_generated=false",
            "tone": "warning",
        }
    ],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion_display",
    },
    "sla_indicators": [],
    "recommended_actions": [],
}

FINANCE_VOUCHER_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/FinanceVoucher",
    "legacy_aliases": ["/finance/vouchers"],
    "toolbar": {
        "primary_actions": [
            {
                "code": "submit_voucher",
                "label_key": "finance.workbench.actions.submitVoucher",
                "action_path": "submit",
                "button_type": "primary",
                "visible_when": {
                    "status_in": ["draft"],
                },
            },
            {
                "code": "approve_voucher",
                "label_key": "finance.workbench.actions.approveVoucher",
                "action_path": "approve",
                "button_type": "success",
                "visible_when": {
                    "status_in": ["submitted"],
                },
            },
            {
                "code": "push_voucher",
                "label_key": "finance.workbench.actions.pushVoucher",
                "action_path": "push",
                "button_type": "warning",
                "visible_when": {
                    "status_in": ["approved"],
                },
            },
        ],
        "secondary_actions": [
            {
                "code": "retry_push",
                "label_key": "finance.workbench.actions.retryPush",
                "action_path": "retry",
                "button_type": "default",
                "visible_when": {
                    "status_in": ["approved", "posted"],
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
            "code": "voucher_sync_status",
            "title_key": "finance.panels.syncStatus",
            "component": "finance-voucher-sync-status",
        },
        {
            "code": "voucher_integration_logs",
            "title_key": "finance.panels.integrationLogs",
            "component": "finance-voucher-integration-logs",
        },
    ],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "voucher_total_amount",
            "label_key": "finance.workbench.summary.totalAmount",
            "value_field": "total_amount",
            "tone": "info",
        },
        {
            "code": "voucher_entry_count",
            "label_key": "finance.workbench.summary.entryCount",
            "value_field": "entry_count",
        },
        {
            "code": "voucher_balance_state",
            "label_key": "finance.workbench.summary.balanceState",
            "value_field": "is_balanced",
            "tone": "success",
        },
        {
            "code": "voucher_source_object",
            "label_key": "finance.workbench.summary.sourceObject",
            "value_field": "source_object_label",
        },
        {
            "code": "voucher_source_document",
            "label_key": "finance.workbench.summary.sourceDocument",
            "value_field": "source_record_no",
        },
    ],
    "queue_panels": [
        {
            "code": "voucher_review_queue",
            "title_key": "finance.workbench.queues.reviewQueue",
            "count": 1,
            "route": "/objects/FinanceVoucher?status=submitted",
            "visible_when": {
                "status_in": ["submitted"],
            },
        },
        {
            "code": "voucher_posting_queue",
            "title_key": "finance.workbench.queues.postingQueue",
            "count": 1,
            "route": "/objects/FinanceVoucher?status=approved",
            "visible_when": {
                "status_in": ["approved"],
            },
        },
    ],
    "exception_panels": [
        {
            "code": "voucher_integration_attention",
            "title_key": "finance.workbench.queues.integrationAttention",
            "count_field": "closure_summary.metrics.failed_sync_count",
            "route": "/objects/FinanceVoucher?status=approved",
            "visible_when": {
                "status_in": ["approved", "rejected"],
            },
            "tone": "danger",
        }
    ],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion_display",
    },
    "sla_indicators": [],
    "recommended_actions": [
        {
            "code": "voucher_push_recommended",
            "label_key": "finance.workbench.actions.pushVoucher",
            "description_key": "finance.workbench.messages.pushVoucherHint",
            "action_path": "push",
            "button_type": "warning",
            "visible_when": {
                "status_in": ["approved"],
            },
        },
        {
            "code": "voucher_retry_recommended",
            "label_key": "finance.workbench.actions.retryPush",
            "description_key": "finance.workbench.messages.retryPushHint",
            "action_path": "retry",
            "button_type": "default",
            "visible_when": {
                "status_in": ["approved", "posted"],
            },
        },
    ],
}

INSURANCE_POLICY_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/InsurancePolicy",
    "toolbar": {
        "primary_actions": [
            {
                "code": "activate_policy",
                "label_key": "insurance.workbench.actions.activatePolicy",
                "action_path": "activate",
                "button_type": "primary",
                "visible_when": {
                    "status_in": ["draft"],
                },
            },
        ],
        "secondary_actions": [
            {
                "code": "cancel_policy",
                "label_key": "insurance.workbench.actions.cancelPolicy",
                "action_path": "cancel",
                "button_type": "warning",
                "visible_when": {
                    "status_in": ["draft", "active"],
                },
            },
        ],
    },
    "detail_panels": [],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "insurance_policy_assets",
            "label_key": "insurance.workbench.summary.insuredAssetCount",
            "value_field": "total_insured_assets",
            "tone": "info",
        },
        {
            "code": "insurance_policy_claims",
            "label_key": "insurance.workbench.summary.claimCount",
            "value_field": "total_claims",
        },
        {
            "code": "insurance_policy_pending_premiums",
            "label_key": "insurance.workbench.summary.pendingPremiumCount",
            "value_field": "closure_summary.metrics.pending_payment_count",
            "tone": "warning",
        },
        {
            "code": "insurance_policy_days_to_expiry",
            "label_key": "insurance.workbench.summary.daysUntilExpiry",
            "value_field": "days_until_expiry",
        },
    ],
    "queue_panels": [
        {
            "code": "insurance_policy_asset_queue",
            "title_key": "insurance.workbench.queues.insuredAssets",
            "count_field": "total_insured_assets",
            "route": "/objects/InsuredAsset?policy={id}",
        },
        {
            "code": "insurance_policy_claim_queue",
            "title_key": "insurance.workbench.queues.claims",
            "count_field": "total_claims",
            "route": "/objects/ClaimRecord?policy={id}",
        },
    ],
    "exception_panels": [
        {
            "code": "insurance_policy_pending_premium_attention",
            "title_key": "insurance.workbench.queues.pendingPremiums",
            "count_field": "closure_summary.metrics.pending_payment_count",
            "route": "/objects/PremiumPayment?policy={id}",
            "tone": "warning",
        },
    ],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion_display",
    },
    "sla_indicators": [],
    "recommended_actions": [
        {
            "code": "insurance_policy_activate_recommended",
            "label_key": "insurance.workbench.actions.activatePolicy",
            "description_key": "insurance.workbench.messages.activatePolicyHint",
            "action_path": "activate",
            "button_type": "primary",
            "visible_when": {
                "status_in": ["draft"],
            },
        },
        {
            "code": "insurance_policy_cancel_recommended",
            "label_key": "insurance.workbench.actions.cancelPolicy",
            "description_key": "insurance.workbench.messages.cancelPolicyHint",
            "action_path": "cancel",
            "button_type": "warning",
            "visible_when": {
                "status_in": ["draft", "active"],
            },
        },
    ],
}

CLAIM_RECORD_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/ClaimRecord",
    "toolbar": {
        "primary_actions": [
            {
                "code": "approve_claim",
                "label_key": "insurance.workbench.actions.approveClaim",
                "action_path": "approve",
                "button_type": "primary",
                "visible_when": {
                    "status_in": ["reported", "investigating"],
                },
            },
            {
                "code": "record_claim_payment",
                "label_key": "insurance.workbench.actions.recordSettlement",
                "action_path": "record-payment",
                "button_type": "success",
                "visible_when": {
                    "status_in": ["approved"],
                },
            },
        ],
        "secondary_actions": [
            {
                "code": "reject_claim",
                "label_key": "insurance.workbench.actions.rejectClaim",
                "action_path": "reject",
                "button_type": "warning",
                "visible_when": {
                    "status_in": ["reported", "investigating", "approved"],
                },
            },
            {
                "code": "close_claim",
                "label_key": "insurance.workbench.actions.closeClaim",
                "action_path": "close",
                "button_type": "default",
                "visible_when": {
                    "status_in": ["paid", "rejected"],
                },
            },
        ],
    },
    "detail_panels": [],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "claim_record_claimed_amount",
            "label_key": "insurance.workbench.summary.claimedAmount",
            "value_field": "claimed_amount",
            "tone": "warning",
        },
        {
            "code": "claim_record_approved_amount",
            "label_key": "insurance.workbench.summary.approvedAmount",
            "value_field": "approved_amount",
        },
        {
            "code": "claim_record_paid_amount",
            "label_key": "insurance.workbench.summary.paidAmount",
            "value_field": "paid_amount",
            "tone": "success",
        },
        {
            "code": "claim_record_payout_ratio",
            "label_key": "insurance.workbench.summary.payoutRatio",
            "value_field": "payout_ratio",
            "suffix": "%",
        },
    ],
    "queue_panels": [
        {
            "code": "claim_record_settlement_queue",
            "title_key": "insurance.workbench.queues.settlementQueue",
            "count": 1,
            "route": "/objects/ClaimRecord?status=approved",
            "visible_when": {
                "status_in": ["approved"],
            },
        },
        {
            "code": "claim_record_closure_queue",
            "title_key": "insurance.workbench.queues.closureQueue",
            "count": 1,
            "route": "/objects/ClaimRecord?status=paid",
            "visible_when": {
                "status_in": ["paid", "rejected"],
            },
        },
    ],
    "exception_panels": [],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion_display",
    },
    "sla_indicators": [],
    "recommended_actions": [
        {
            "code": "claim_record_approve_recommended",
            "label_key": "insurance.workbench.actions.approveClaim",
            "description_key": "insurance.workbench.messages.approveClaimHint",
            "action_path": "approve",
            "button_type": "primary",
            "visible_when": {
                "status_in": ["reported", "investigating"],
            },
        },
        {
            "code": "claim_record_settlement_recommended",
            "label_key": "insurance.workbench.actions.recordSettlement",
            "description_key": "insurance.workbench.messages.recordSettlementHint",
            "action_path": "record-payment",
            "button_type": "success",
            "visible_when": {
                "status_in": ["approved"],
            },
        },
        {
            "code": "claim_record_close_recommended",
            "label_key": "insurance.workbench.actions.closeClaim",
            "description_key": "insurance.workbench.messages.closeClaimHint",
            "action_path": "close",
            "button_type": "default",
            "visible_when": {
                "status_in": ["paid", "rejected"],
            },
        },
    ],
}

LEASING_CONTRACT_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/LeasingContract",
    "toolbar": {
        "primary_actions": [
            {
                "code": "activate_contract",
                "label_key": "leasing.workbench.actions.activateContract",
                "action_path": "activate",
                "button_type": "primary",
                "visible_when": {
                    "status_in": ["draft"],
                },
            },
            {
                "code": "complete_contract",
                "label_key": "leasing.workbench.actions.completeContract",
                "action_path": "complete",
                "button_type": "success",
                "visible_when": {
                    "status_in": ["active", "suspended"],
                },
            },
        ],
        "secondary_actions": [
            {
                "code": "suspend_contract",
                "label_key": "leasing.workbench.actions.suspendContract",
                "action_path": "suspend",
                "button_type": "warning",
                "visible_when": {
                    "status_in": ["active"],
                },
            },
            {
                "code": "reactivate_contract",
                "label_key": "leasing.workbench.actions.reactivateContract",
                "action_path": "reactivate",
                "button_type": "primary",
                "visible_when": {
                    "status_in": ["suspended"],
                },
            },
            {
                "code": "terminate_contract",
                "label_key": "leasing.workbench.actions.terminateContract",
                "action_path": "terminate",
                "button_type": "danger",
                "visible_when": {
                    "status_in": ["active", "suspended"],
                },
            },
        ],
    },
    "detail_panels": [],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "leasing_contract_asset_count",
            "label_key": "leasing.workbench.summary.assetCount",
            "value_field": "closure_summary.metrics.leased_asset_count",
            "tone": "info",
        },
        {
            "code": "leasing_contract_returned_asset_count",
            "label_key": "leasing.workbench.summary.returnedAssetCount",
            "value_field": "closure_summary.metrics.returned_asset_count",
            "tone": "success",
        },
        {
            "code": "leasing_contract_pending_returns",
            "label_key": "leasing.workbench.summary.pendingReturnCount",
            "value_field": "closure_summary.metrics.pending_return_count",
            "tone": "warning",
        },
        {
            "code": "leasing_contract_unpaid_amount",
            "label_key": "leasing.workbench.summary.unpaidAmount",
            "value_field": "closure_summary.metrics.unpaid_amount",
            "tone": "danger",
        },
    ],
    "queue_panels": [
        {
            "code": "leasing_contract_pending_return_queue",
            "title_key": "leasing.workbench.queues.pendingReturns",
            "count_field": "closure_summary.metrics.pending_return_count",
            "route": "/objects/LeaseItem?contract={id}",
        },
        {
            "code": "leasing_contract_open_payment_queue",
            "title_key": "leasing.workbench.queues.openPayments",
            "count_field": "closure_summary.metrics.open_payment_count",
            "route": "/objects/RentPayment?contract={id}",
        },
    ],
    "exception_panels": [
        {
            "code": "leasing_contract_damage_attention",
            "title_key": "leasing.workbench.queues.unsettledDamage",
            "count_field": "closure_summary.metrics.unsettled_damage_count",
            "route": "/objects/LeaseReturn?contract={id}",
            "tone": "warning",
        },
    ],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion_display",
    },
    "sla_indicators": [],
    "recommended_actions": [
        {
            "code": "leasing_contract_activate_recommended",
            "label_key": "leasing.workbench.actions.activateContract",
            "description_key": "leasing.workbench.messages.activateContractHint",
            "action_path": "activate",
            "button_type": "primary",
            "visible_when": {
                "status_in": ["draft"],
            },
        },
        {
            "code": "leasing_contract_complete_recommended",
            "label_key": "leasing.workbench.actions.completeContract",
            "description_key": "leasing.workbench.messages.completeContractHint",
            "action_path": "complete",
            "button_type": "success",
            "visible_when": {
                "status_in": ["active", "suspended"],
            },
        },
        {
            "code": "leasing_contract_reactivate_recommended",
            "label_key": "leasing.workbench.actions.reactivateContract",
            "description_key": "leasing.workbench.messages.reactivateContractHint",
            "action_path": "reactivate",
            "button_type": "primary",
            "visible_when": {
                "status_in": ["suspended"],
            },
        },
    ],
}

INVENTORY_TASK_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/InventoryTask",
    "toolbar": {
        "primary_actions": [
            {
                "code": "submit_inventory_task_workflow",
                "label_key": "inventory.workbench.actions.submitTask",
                "action_path": "submit-workflow",
                "button_type": "primary",
                "visible_when": {
                    "status_in": ["draft"],
                },
            },
            {
                "code": "start_inventory_task",
                "label_key": "inventory.workbench.actions.startTask",
                "action_path": "start",
                "button_type": "primary",
                "visible_when": {
                    "status_in": ["pending"],
                },
            },
            {
                "code": "complete_inventory_task",
                "label_key": "inventory.workbench.actions.completeTask",
                "action_path": "complete",
                "button_type": "success",
                "visible_when": {
                    "status_in": ["in_progress"],
                },
            },
        ],
        "secondary_actions": [
            {
                "code": "refresh_inventory_stats",
                "label_key": "inventory.workbench.actions.refreshStats",
                "action_path": "refresh-stats",
                "button_type": "default",
                "visible_when": {
                    "status_in": ["in_progress", "completed"],
                },
            },
            {
                "code": "cancel_inventory_task",
                "label_key": "inventory.workbench.actions.cancelTask",
                "action_path": "cancel",
                "button_type": "warning",
                "visible_when": {
                    "status_in": ["draft", "pending_approval", "pending", "in_progress"],
                },
            },
        ],
    },
    "detail_panels": [
        {
            "code": "inventory_task_executor_progress_panel",
            "component": "inventory-task-executor-progress",
            "title_key": "inventory.workbench.panels.executorProgress",
        },
    ],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "inventory_total_count",
            "label_key": "inventory.workbench.summary.totalCount",
            "value_field": "total_count",
            "tone": "info",
        },
        {
            "code": "inventory_scanned_count",
            "label_key": "inventory.workbench.summary.scannedCount",
            "value_field": "scanned_count",
        },
        {
            "code": "inventory_progress",
            "label_key": "inventory.workbench.summary.progress",
            "value_field": "progress_percentage",
            "suffix": "%",
            "tone": "success",
        },
        {
            "code": "inventory_difference_total",
            "label_key": "inventory.workbench.summary.differenceTotal",
            "value_field": "difference_summary.total_differences",
            "tone": "warning",
        },
        {
            "code": "inventory_pending_closure",
            "label_key": "inventory.workbench.summary.pendingClosure",
            "value_field": "difference_summary.pending_closure_count",
            "tone": "danger",
        },
        {
            "code": "inventory_pending_follow_up",
            "label_key": "inventory.workbench.summary.pendingFollowUp",
            "value_field": "difference_summary.manual_follow_up_open_count",
            "tone": "warning",
        },
    ],
    "queue_panels": [
        {
            "code": "inventory_active_execution",
            "title_key": "inventory.workbench.queues.activeExecution",
            "count": 1,
            "route": "/objects/InventoryTask?status=in_progress",
            "visible_when": {
                "status_in": ["in_progress"],
            },
        },
        {
            "code": "inventory_awaiting_confirmation",
            "title_key": "inventory.workbench.queues.awaitingConfirmation",
            "count_field": "difference_summary.pending_confirmation_count",
            "route": "/objects/InventoryItem?task={id}&status=pending",
            "visible_when": {
                "status_in": ["completed"],
            },
        },
        {
            "code": "inventory_awaiting_review",
            "title_key": "inventory.workbench.queues.awaitingReview",
            "count_field": "difference_summary.pending_review_count",
            "route": "/objects/InventoryItem?task={id}&status=confirmed",
            "visible_when": {
                "status_in": ["completed"],
            },
        },
        {
            "code": "inventory_awaiting_approval",
            "title_key": "inventory.workbench.queues.awaitingApproval",
            "count_field": "difference_summary.pending_approval_count",
            "route": "/objects/InventoryItem?task={id}&status=in_review",
            "visible_when": {
                "status_in": ["completed"],
            },
        },
        {
            "code": "inventory_awaiting_execution",
            "title_key": "inventory.workbench.queues.awaitingExecution",
            "count_field": "difference_summary.pending_execution_count",
            "route": "/objects/InventoryItem?task={id}&status=approved",
            "visible_when": {
                "status_in": ["completed"],
            },
        },
        {
            "code": "inventory_awaiting_closure",
            "title_key": "inventory.workbench.queues.awaitingClosure",
            "count_field": "difference_summary.pending_closure_count",
            "route": "/objects/InventoryItem?task={id}&status=resolved",
            "visible_when": {
                "status_in": ["completed"],
            },
        },
        {
            "code": "inventory_awaiting_follow_up",
            "title_key": "inventory.workbench.queues.awaitingFollowUp",
            "count_field": "difference_summary.manual_follow_up_open_count",
            "route": "/objects/InventoryItem?task={id}&manual_follow_up_only=true&unresolved_only=true",
            "visible_when": {
                "status_in": ["completed"],
            },
            "tone": "warning",
        },
    ],
    "exception_panels": [
        {
            "code": "inventory_missing_difference",
            "title_key": "inventory.workbench.queues.missingDifferences",
            "count_field": "difference_summary.by_type.missing",
            "route": "/objects/InventoryItem?task={id}&difference_type=missing",
            "tone": "danger",
        },
        {
            "code": "inventory_damaged_difference",
            "title_key": "inventory.workbench.queues.damagedDifferences",
            "count_field": "difference_summary.by_type.damaged",
            "route": "/objects/InventoryItem?task={id}&difference_type=damaged",
            "tone": "warning",
        },
        {
            "code": "inventory_location_difference",
            "title_key": "inventory.workbench.queues.locationDifferences",
            "count_field": "difference_summary.by_type.location_mismatch",
            "route": "/objects/InventoryItem?task={id}&difference_type=location_mismatch",
        },
        {
            "code": "inventory_custodian_difference",
            "title_key": "inventory.workbench.queues.custodianDifferences",
            "count_field": "difference_summary.by_type.custodian_mismatch",
            "route": "/objects/InventoryItem?task={id}&difference_type=custodian_mismatch",
        },
        {
            "code": "inventory_surplus_difference",
            "title_key": "inventory.workbench.queues.surplusDifferences",
            "count_field": "difference_summary.by_type.surplus",
            "route": "/objects/InventoryItem?task={id}&difference_type=surplus",
        },
    ],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion_display",
    },
    "sla_indicators": [
        {
            "code": "inventory_task_workflow_sla",
            "label_key": "inventory.workbench.sla.workflow",
        },
    ],
    "recommended_actions": [
        {
            "code": "inventory_submit_task_recommended",
            "label_key": "inventory.workbench.actions.submitTask",
            "description_key": "inventory.workbench.messages.submitTaskHint",
            "action_path": "submit-workflow",
            "button_type": "primary",
            "visible_when": {
                "status_in": ["draft"],
            },
        },
        {
            "code": "inventory_refresh_stats_recommended",
            "label_key": "inventory.workbench.actions.refreshStats",
            "description_key": "inventory.workbench.messages.refreshStatsHint",
            "action_path": "refresh-stats",
            "button_type": "default",
            "visible_when": {
                "status_in": ["in_progress", "completed"],
            },
        },
        {
            "code": "inventory_complete_task_recommended",
            "label_key": "inventory.workbench.actions.completeTask",
            "description_key": "inventory.workbench.messages.completeTaskHint",
            "action_path": "complete",
            "button_type": "success",
            "visible_when": {
                "status_in": ["in_progress"],
            },
        },
    ],
}

INVENTORY_ITEM_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/InventoryItem",
    "toolbar": {
        "primary_actions": [
            {
                "code": "inventory_difference_confirm",
                "label_key": "inventory.workbench.actions.confirmDifference",
                "action_path": "confirm",
                "button_type": "primary",
                "confirm_message_key": "inventory.workbench.messages.confirmDifferenceConfirm",
                "visible_when": {
                    "status_in": ["pending"],
                },
            },
        ],
        "secondary_actions": [
            {
                "code": "inventory_difference_ignore",
                "label_key": "inventory.workbench.actions.ignoreDifference",
                "action_path": "ignore",
                "button_type": "warning",
                "visible_when": {
                    "status_in": ["pending", "confirmed", "approved"],
                },
            },
            {
                "code": "inventory_difference_reject",
                "label_key": "inventory.workbench.actions.rejectResolution",
                "action_path": "reject-resolution",
                "button_type": "danger",
                "visible_when": {
                    "status_in": ["in_review"],
                },
            },
        ],
    },
    "detail_panels": [
        {
            "code": "inventory_difference_closure_panel",
            "component": "inventory-difference-closure",
            "title_key": "inventory.workbench.panels.differenceClosure",
            "props": {
                "linked_action_options": [
                    {
                        "code": "location_correction",
                        "label_key": "inventory.workbench.linkedActions.locationCorrection",
                        "closure_types": ["location_correction"],
                    },
                    {
                        "code": "custodian_correction",
                        "label_key": "inventory.workbench.linkedActions.custodianCorrection",
                        "closure_types": ["custodian_correction"],
                    },
                    {
                        "code": "asset.create_maintenance",
                        "label_key": "inventory.workbench.linkedActions.createMaintenance",
                        "closure_types": ["repair"],
                    },
                    {
                        "code": "asset.create_disposal",
                        "label_key": "inventory.workbench.linkedActions.createDisposal",
                        "closure_types": ["disposal"],
                    },
                    {
                        "code": "create_asset_card",
                        "label_key": "inventory.workbench.linkedActions.createAssetCard",
                        "closure_types": ["create_asset_card"],
                    },
                    {
                        "code": "finance_adjustment",
                        "label_key": "inventory.workbench.linkedActions.financialAdjustment",
                        "closure_types": ["financial_adjustment"],
                    },
                    {
                        "code": "invalid_difference",
                        "label_key": "inventory.workbench.linkedActions.invalidDifference",
                        "closure_types": ["invalid_difference"],
                    },
                ],
            },
        },
    ],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "inventory_difference_type",
            "label_key": "inventory.workbench.summary.differenceType",
            "value_field": "difference_type_label",
            "tone": "warning",
        },
        {
            "code": "inventory_difference_status",
            "label_key": "inventory.workbench.summary.currentStatus",
            "value_field": "status_label",
        },
        {
            "code": "inventory_difference_task_code",
            "label_key": "inventory.workbench.summary.taskCode",
            "value_field": "task_code",
            "tone": "info",
        },
        {
            "code": "inventory_difference_quantity",
            "label_key": "inventory.workbench.summary.quantityDifference",
            "value_field": "quantity_difference",
        },
    ],
    "queue_panels": [],
    "exception_panels": [],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion",
    },
    "sla_indicators": [],
    "recommended_actions": [],
}

INVENTORY_FOLLOW_UP_WORKBENCH: Dict[str, Any] = {
    "workspace_mode": "extended",
    "primary_entry_route": "/objects/InventoryFollowUp",
    "toolbar": {
        "primary_actions": [
            {
                "code": "inventory_follow_up_complete",
                "label_key": "inventory.workbench.actions.completeFollowUp",
                "action_path": "complete",
                "button_type": "success",
                "visible_when": {
                    "status_in": ["pending"],
                },
            },
        ],
        "secondary_actions": [
            {
                "code": "inventory_follow_up_reopen",
                "label_key": "inventory.workbench.actions.reopenFollowUp",
                "action_path": "reopen",
                "button_type": "primary",
                "visible_when": {
                    "status_in": ["completed", "cancelled"],
                },
            },
        ],
    },
    "detail_panels": [],
    "async_indicators": [],
    "summary_cards": [
        {
            "code": "inventory_follow_up_status",
            "label_key": "inventory.workbench.summary.currentStatus",
            "value_field": "status_label",
            "tone": "warning",
        },
        {
            "code": "inventory_follow_up_task_code",
            "label_key": "inventory.workbench.summary.taskCode",
            "value_field": "task_code",
            "tone": "info",
        },
        {
            "code": "inventory_follow_up_difference_type",
            "label_key": "inventory.workbench.summary.differenceType",
            "value_field": "difference_type_label",
        },
        {
            "code": "inventory_follow_up_reminder_count",
            "label_key": "inventory.workbench.summary.reminderCount",
            "value_field": "reminder_count",
        },
    ],
    "queue_panels": [],
    "exception_panels": [],
    "closure_panel": {
        "title_key": "common.workbench.titles.closure",
        "stage_field": "closure_summary.stage",
        "owner_field": "closure_summary.owner",
        "blocker_field": "closure_summary.blocker",
        "progress_field": "closure_summary.completion",
    },
    "sla_indicators": [],
    "recommended_actions": [],
}


MENU_GROUPS: Dict[str, Dict[str, Any]] = {
    "asset_master": {
        "order": 10,
        "icon": "FolderOpened",
        "translation_key": "menu.categories.asset_master",
    },
    "asset_operation": {
        "order": 20,
        "icon": "Operation",
        "translation_key": "menu.categories.asset_operation",
    },
    "lifecycle": {
        "order": 30,
        "icon": "Refresh",
        "translation_key": "menu.categories.lifecycle",
    },
    "consumable": {
        "order": 40,
        "icon": "Box",
        "translation_key": "menu.categories.consumable",
    },
    "inventory": {
        "order": 50,
        "icon": "Box",
        "translation_key": "menu.categories.inventory",
    },
    "finance": {
        "order": 60,
        "icon": "Wallet",
        "translation_key": "menu.categories.finance",
    },
    "organization": {
        "order": 70,
        "icon": "OfficeBuilding",
        "translation_key": "menu.categories.organization",
    },
    "workflow": {
        "order": 80,
        "icon": "Connection",
        "translation_key": "menu.categories.workflow",
    },
    "system": {
        "order": 90,
        "icon": "Setting",
        "translation_key": "menu.categories.system",
    },
    "reports": {
        "order": 100,
        "icon": "DataAnalysis",
        "translation_key": "menu.categories.reports",
    },
    "other": {
        "order": 999,
        "icon": "Menu",
        "translation_key": "menu.categories.other",
    },
}


OBJECT_ROUTE_KEY_MAP: Dict[str, str] = {
    "Asset": "assetList",
    "AssetCategory": "assetCategory",
    "Location": "location",
    "Supplier": "supplier",
    "AssetStatusLog": "assetStatusLog",
    "AssetPickup": "assetPickup",
    "AssetTransfer": "assetTransfer",
    "AssetReturn": "assetReturn",
    "AssetLoan": "assetLoan",
    "Consumable": "consumable",
    "ConsumableCategory": "consumableCategory",
    "ConsumableStock": "consumableStock",
    "ConsumablePurchase": "consumablePurchase",
    "ConsumableIssue": "consumableIssue",
    "PurchaseRequest": "purchaseRequest",
    "AssetReceipt": "assetReceipt",
    "Maintenance": "maintenance",
    "MaintenanceTask": "maintenanceTask",
    "MaintenancePlan": "maintenancePlan",
    "DisposalRequest": "disposalRequest",
    "InventoryTask": "inventoryTask",
    "InventorySnapshot": "inventorySnapshot",
    "InventoryItem": "inventoryItem",
    "InventoryFollowUp": "inventoryFollowUp",
    "InventoryReconciliation": "inventoryReconciliation",
    "InventoryReport": "inventoryReport",
    "Organization": "organization",
    "Department": "department",
    "User": "users",
    "WorkflowDefinition": "workflowDefinitions",
    "WorkflowInstance": "workflowInstances",
    "FinanceVoucher": "financeVoucher",
    "VoucherTemplate": "voucherTemplate",
    "DepreciationConfig": "depreciationConfig",
    "DepreciationRecord": "depreciationRecord",
    "DepreciationRun": "depreciationRun",
    "ITAsset": "itAsset",
    "ITMaintenanceRecord": "itMaintenanceRecord",
    "ConfigurationChange": "configurationChange",
    "ITSoftware": "itSoftware",
    "ITSoftwareLicense": "itSoftwareLicense",
    "ITLicenseAllocation": "itLicenseAllocation",
    "Software": "software",
    "SoftwareLicense": "softwareLicense",
    "LicenseAllocation": "licenseAllocation",
    "LeasingContract": "leasingContract",
    "LeaseItem": "leaseItem",
    "LeaseExtension": "leaseExtension",
    "LeaseReturn": "leaseReturn",
    "RentPayment": "rentPayment",
    "InsuranceCompany": "insuranceCompany",
    "InsurancePolicy": "insurancePolicy",
    "InsuredAsset": "insuredAsset",
    "PremiumPayment": "premiumPayment",
    "ClaimRecord": "claimRecord",
    "PolicyRenewal": "policyRenewal",
    "AssetProject": "assetProject",
    "ProjectAsset": "projectAsset",
    "ProjectMember": "projectMember",
}


DEFAULT_OBJECT_MENU_RULES: Dict[str, Dict[str, Any]] = {
    "Asset": {
        "group_code": "asset_master",
        "item_order": 10,
        "icon": "Document",
        "url": "/objects/Asset",
        "workbench": ASSET_WORKBENCH,
    },
    "TagGroup": {"group_code": "asset_master", "item_order": 15, "icon": "Collection"},
    "AssetTag": {"group_code": "asset_master", "item_order": 18, "icon": "PriceTag"},
    "AssetCategory": {"group_code": "asset_master", "item_order": 20, "icon": "Folder"},
    "Location": {"group_code": "asset_master", "item_order": 30, "icon": "Location"},
    "Supplier": {"group_code": "asset_master", "item_order": 40, "icon": "OfficeBuilding"},
    "AssetStatusLog": {"group_code": "asset_master", "item_order": 50, "icon": "Clock", "show_in_menu": False},
    "ITAsset": {"group_code": "asset_master", "item_order": 60, "icon": "Monitor"},
    "InsuredAsset": {"group_code": "asset_master", "item_order": 70, "icon": "DocumentChecked"},
    "AssetPickup": {"group_code": "asset_operation", "item_order": 10, "icon": "Upload"},
    "AssetTransfer": {"group_code": "asset_operation", "item_order": 20, "icon": "Switch"},
    "AssetReturn": {"group_code": "asset_operation", "item_order": 30, "icon": "Download"},
    "AssetLoan": {"group_code": "asset_operation", "item_order": 40, "icon": "Connection"},
    "PurchaseRequest": {
        "group_code": "lifecycle",
        "item_order": 10,
        "icon": "ShoppingCart",
        "url": "/objects/PurchaseRequest",
        "workbench": PURCHASE_REQUEST_WORKBENCH,
    },
    "AssetReceipt": {
        "group_code": "lifecycle",
        "item_order": 20,
        "icon": "Box",
        "url": "/objects/AssetReceipt",
        "workbench": ASSET_RECEIPT_WORKBENCH,
    },
    "Maintenance": {"group_code": "lifecycle", "item_order": 30, "icon": "Tools"},
    "MaintenancePlan": {"group_code": "lifecycle", "item_order": 40, "icon": "Calendar"},
    "MaintenanceTask": {"group_code": "lifecycle", "item_order": 50, "icon": "List"},
    "DisposalRequest": {"group_code": "lifecycle", "item_order": 60, "icon": "Delete"},
    "AssetProject": {
        "group_code": "lifecycle",
        "item_order": 25,
        "icon": "Collection",
        "url": "/objects/AssetProject",
        "workbench": ASSET_PROJECT_WORKBENCH,
    },
    "ProjectAsset": {
        "group_code": "lifecycle",
        "item_order": 26,
        "icon": "Link",
        "show_in_menu": False,
    },
    "ProjectMember": {
        "group_code": "lifecycle",
        "item_order": 27,
        "icon": "UserFilled",
        "show_in_menu": False,
    },
    "Consumable": {"group_code": "consumable", "item_order": 10, "icon": "Box"},
    "ConsumableCategory": {"group_code": "consumable", "item_order": 20, "icon": "Folder"},
    "ConsumableStock": {"group_code": "consumable", "item_order": 30, "icon": "Goods"},
    "ConsumablePurchase": {"group_code": "consumable", "item_order": 40, "icon": "ShoppingCart"},
    "ConsumableIssue": {"group_code": "consumable", "item_order": 50, "icon": "Sell"},
    "InventoryTask": {
        "group_code": "inventory",
        "item_order": 10,
        "icon": "Clipboard",
        "url": "/objects/InventoryTask",
        "workbench": INVENTORY_TASK_WORKBENCH,
    },
    "InventorySnapshot": {
        "group_code": "inventory",
        "item_order": 20,
        "icon": "Camera",
        "show_in_menu": False,
    },
    "InventoryItem": {
        "group_code": "inventory",
        "item_order": 30,
        "icon": "Document",
        "show_in_menu": False,
        "url": "/objects/InventoryItem",
        "workbench": INVENTORY_ITEM_WORKBENCH,
    },
    "InventoryFollowUp": {
        "group_code": "inventory",
        "item_order": 35,
        "icon": "Bell",
        "show_in_menu": False,
        "url": "/objects/InventoryFollowUp",
        "workbench": INVENTORY_FOLLOW_UP_WORKBENCH,
    },
    "InventoryReconciliation": {
        "group_code": "inventory",
        "item_order": 36,
        "icon": "DocumentChecked",
        "show_in_menu": False,
        "url": "/objects/InventoryReconciliation",
    },
    "InventoryReport": {
        "group_code": "inventory",
        "item_order": 37,
        "icon": "DataAnalysis",
        "show_in_menu": False,
        "url": "/objects/InventoryReport",
    },
    "FinanceVoucher": {
        "group_code": "finance",
        "item_order": 10,
        "icon": "Tickets",
        "show_in_menu": False,
        "url": "/objects/FinanceVoucher",
        "workbench": FINANCE_VOUCHER_WORKBENCH,
    },
    "VoucherTemplate": {"group_code": "finance", "item_order": 20, "icon": "Files"},
    "DepreciationConfig": {"group_code": "finance", "item_order": 30, "icon": "Setting"},
    "DepreciationRun": {"group_code": "finance", "item_order": 40, "icon": "VideoPlay"},
    "DepreciationRecord": {"group_code": "finance", "item_order": 50, "icon": "Histogram"},
    "InsuranceCompany": {"group_code": "finance", "item_order": 60, "icon": "OfficeBuilding"},
    "InsurancePolicy": {
        "group_code": "finance",
        "item_order": 70,
        "icon": "Shield",
        "url": "/objects/InsurancePolicy",
        "workbench": INSURANCE_POLICY_WORKBENCH,
    },
    "PremiumPayment": {"group_code": "finance", "item_order": 80, "icon": "Wallet"},
    "ClaimRecord": {
        "group_code": "finance",
        "item_order": 90,
        "icon": "Warning",
        "url": "/objects/ClaimRecord",
        "workbench": CLAIM_RECORD_WORKBENCH,
    },
    "PolicyRenewal": {"group_code": "finance", "item_order": 100, "icon": "Refresh"},
    "LeasingContract": {
        "group_code": "finance",
        "item_order": 110,
        "icon": "Files",
        "url": "/objects/LeasingContract",
        "workbench": LEASING_CONTRACT_WORKBENCH,
    },
    "LeaseItem": {"group_code": "finance", "item_order": 120, "icon": "List"},
    "LeaseExtension": {"group_code": "finance", "item_order": 130, "icon": "Clock"},
    "LeaseReturn": {"group_code": "finance", "item_order": 140, "icon": "Back"},
    "RentPayment": {"group_code": "finance", "item_order": 150, "icon": "Wallet"},
    "Software": {"group_code": "finance", "item_order": 160, "icon": "Monitor"},
    "SoftwareLicense": {"group_code": "finance", "item_order": 170, "icon": "Key"},
    "LicenseAllocation": {"group_code": "finance", "item_order": 180, "icon": "Share"},
    "ITSoftware": {"group_code": "finance", "item_order": 190, "icon": "Monitor"},
    "ITSoftwareLicense": {"group_code": "finance", "item_order": 200, "icon": "Key"},
    "ITLicenseAllocation": {"group_code": "finance", "item_order": 210, "icon": "Share"},
    "Organization": {
        "group_code": "organization",
        "item_order": 10,
        "icon": "OfficeBuilding",
        "show_in_menu": False,
    },
    "Department": {"group_code": "organization", "item_order": 20, "icon": "Guide"},
    "User": {"group_code": "organization", "item_order": 30, "icon": "User", "show_in_menu": False},
    "Role": {
        "group_code": "organization",
        "item_order": 40,
        "icon": "UserFilled",
        "show_in_menu": False,
    },
    "WorkflowDefinition": {
        "group_code": "workflow",
        "item_order": 10,
        "icon": "Connection",
        "show_in_menu": False,
    },
    "WorkflowInstance": {
        "group_code": "workflow",
        "item_order": 20,
        "icon": "List",
        "show_in_menu": False,
    },
    "ConfigurationChange": {
        "group_code": "system",
        "item_order": 10,
        "icon": "Edit",
        "show_in_menu": False,
    },
}


STATIC_MENU_ITEMS: List[Dict[str, Any]] = [
    {
        "code": "VoucherList",
        "translation_key": "menu.routes.vouchers",
        "url": "/objects/FinanceVoucher",
        "group_code": "finance",
        "item_order": 1,
        "icon": "Tickets",
    },
    {
        "code": "DepreciationList",
        "translation_key": "menu.routes.depreciation",
        "url": "/finance/depreciation",
        "group_code": "finance",
        "item_order": 2,
        "icon": "TrendCharts",
    },
    {
        "code": "InsuranceDashboard",
        "translation_key": "menu.routes.insuranceDashboard",
        "url": "/insurance/dashboard",
        "group_code": "finance",
        "item_order": 3,
        "icon": "DataLine",
    },
    {
        "code": "ClaimList",
        "translation_key": "menu.routes.claimList",
        "url": "/insurance/claims",
        "group_code": "finance",
        "item_order": 4,
        "icon": "Tickets",
    },
    {
        "code": "LeasingDashboard",
        "translation_key": "menu.routes.leasingDashboard",
        "url": "/leasing/dashboard",
        "group_code": "finance",
        "item_order": 5,
        "icon": "DataLine",
    },
    {
        "code": "RentPaymentList",
        "translation_key": "menu.routes.rentPayments",
        "url": "/leasing/payments",
        "group_code": "finance",
        "item_order": 6,
        "icon": "Wallet",
    },
    {
        "code": "UserPortal",
        "translation_key": "menu.routes.userPortal",
        "url": "/portal",
        "group_code": "workflow",
        "item_order": 5,
        "icon": "User",
    },
    {
        "code": "TaskCenter",
        "translation_key": "menu.routes.taskCenter",
        "url": "/workflow/tasks",
        "group_code": "workflow",
        "item_order": 10,
        "icon": "List",
    },
    {
        "code": "MyApprovals",
        "translation_key": "menu.routes.myApprovals",
        "url": "/workflow/my-approvals",
        "group_code": "workflow",
        "item_order": 20,
        "icon": "CircleCheck",
    },
    {
        "code": "WorkflowList",
        "translation_key": "menu.routes.workflowList",
        "url": "/admin/workflows",
        "group_code": "workflow",
        "item_order": 30,
        "icon": "Connection",
    },
    {
        "code": "PermissionManagement",
        "translation_key": "menu.routes.permissions",
        "url": "/admin/permissions",
        "group_code": "workflow",
        "item_order": 40,
        "icon": "Lock",
    },
    {
        "code": "BusinessObjectList",
        "translation_key": "menu.routes.businessObjects",
        "url": "/system/business-objects",
        "group_code": "system",
        "item_order": 10,
        "icon": "Grid",
    },
    {
        "code": "FieldDefinitionList",
        "translation_key": "menu.routes.fieldDefinitions",
        "url": "/system/field-definitions",
        "group_code": "system",
        "item_order": 20,
        "icon": "List",
    },
    {
        "code": "PageLayoutList",
        "translation_key": "menu.routes.pageLayouts",
        "url": "/system/page-layouts",
        "group_code": "system",
        "item_order": 30,
        "icon": "Files",
    },
    {
        "code": "LanguageList",
        "translation_key": "menu.routes.languages",
        "url": "/system/languages",
        "group_code": "system",
        "item_order": 40,
        "icon": "ChatDotRound",
    },
    {
        "code": "TranslationList",
        "translation_key": "menu.routes.translations",
        "url": "/system/translations",
        "group_code": "system",
        "item_order": 50,
        "icon": "DocumentCopy",
    },
    {
        "code": "BusinessRuleList",
        "translation_key": "menu.routes.businessRules",
        "url": "/system/business-rules",
        "group_code": "system",
        "item_order": 60,
        "icon": "Connection",
    },
    {
        "code": "ConfigPackageList",
        "translation_key": "menu.routes.configPackages",
        "url": "/system/config-packages",
        "group_code": "system",
        "item_order": 70,
        "icon": "Box",
    },
    {
        "code": "DictionaryTypeList",
        "translation_key": "menu.routes.dictionaryTypes",
        "url": "/system/dictionary-types",
        "group_code": "system",
        "item_order": 80,
        "icon": "Collection",
    },
    {
        "code": "TagList",
        "translation_key": "menu.routes.tags",
        "url": "/system/tags",
        "group_code": "system",
        "item_order": 85,
        "icon": "Tickets",
    },
    {
        "code": "SequenceRuleList",
        "translation_key": "menu.routes.sequenceRules",
        "url": "/system/sequence-rules",
        "group_code": "system",
        "item_order": 90,
        "icon": "Sort",
    },
    {
        "code": "SystemConfigList",
        "translation_key": "menu.routes.systemConfig",
        "url": "/system/config",
        "group_code": "system",
        "item_order": 100,
        "icon": "Tools",
    },
    {
        "code": "MenuManagement",
        "translation_key": "menu.routes.menuManagement",
        "url": "/system/menu-management",
        "group_code": "system",
        "item_order": 102,
        "icon": "Grid",
    },
    {
        "code": "MenuLayoutManagement",
        "translation_key": "menu.routes.menuLayoutManagement",
        "url": "/system/menu-layout-management",
        "group_code": "system",
        "item_order": 103,
        "icon": "Sort",
    },
    {
        "code": "SystemBranding",
        "translation_key": "menu.routes.systemBranding",
        "url": "/system/branding",
        "group_code": "system",
        "item_order": 105,
        "icon": "Brush",
    },
    {
        "code": "SystemFileList",
        "translation_key": "menu.routes.systemFiles",
        "url": "/system/files",
        "group_code": "system",
        "item_order": 110,
        "icon": "FolderOpened",
    },
    {
        "code": "ModuleWorkbench",
        "translation_key": "menu.routes.moduleWorkbench",
        "url": "/system/module-workbench",
        "group_code": "system",
        "item_order": 120,
        "icon": "Operation",
    },
    {
        "code": "SSOConfigPage",
        "translation_key": "menu.routes.ssoConfig",
        "url": "/system/sso",
        "group_code": "system",
        "item_order": 130,
        "icon": "Key",
    },
    {
        "code": "OrganizationTree",
        "translation_key": "menu.routes.organizationTree",
        "url": "/system/organization-tree",
        "group_code": "system",
        "item_order": 140,
        "icon": "Share",
    },
    {
        "code": "IntegrationConfigList",
        "translation_key": "menu.routes.integrationConfigs",
        "url": "/integration/configs",
        "group_code": "system",
        "item_order": 150,
        "icon": "Link",
    },
    {
        "code": "ReportCenter",
        "translation_key": "menu.routes.reportCenter",
        "url": "/reports/center",
        "group_code": "reports",
        "item_order": 10,
        "icon": "DataAnalysis",
    },
]


def get_menu_item_identity(source_type: str, code: str) -> str:
    return f"{source_type}:{code}"


def is_default_business_object(code: str, is_hardcoded: bool = False) -> bool:
    return bool(is_hardcoded or code in DEFAULT_OBJECT_MENU_RULES)


def _humanize_group_code(code: str) -> str:
    return str(code or "").replace("_", " ").strip().title() or "Other"


def _get_default_group_definitions() -> Dict[str, Dict[str, Any]]:
    return {
        code: {
            "code": code,
            "name": _humanize_group_code(code),
            "translation_key": group["translation_key"],
            "order": int(group["order"]),
            "icon": group["icon"],
            "is_visible": True,
            "is_default": True,
            "is_locked": False,
        }
        for code, group in MENU_GROUPS.items()
    }


def _normalize_route_path(value: Optional[str], fallback: str) -> str:
    path = str(value or fallback or "").strip()
    if not path:
        return fallback
    if path.startswith("/"):
        return path
    return f"/{path.lstrip('/')}"


def sync_menu_registry_models() -> Dict[str, Any]:
    HardcodedObjectSyncService().sync_catalog()
    default_groups = _get_default_group_definitions()
    groups_by_code: Dict[str, MenuGroup] = {}
    created_groups: List[str] = []
    created_entries: List[str] = []
    updated_entries: List[str] = []

    def ensure_group(code: str) -> MenuGroup:
        spec = default_groups.get(code, {})
        group = groups_by_code.get(code)
        if group is None:
            group = MenuGroup.all_objects.filter(code=code).first()
        created = group is None
        if group is None:
            group = MenuGroup(
                code=code,
                name=str(spec.get("name") or _humanize_group_code(code)),
                translation_key=str(spec.get("translation_key") or ""),
                icon=str(spec.get("icon") or "Menu"),
                sort_order=int(spec.get("order") or 999),
                is_visible=bool(spec.get("is_visible", True)),
                is_locked=False,
                is_system=code in default_groups,
            )
            group.save()
        changed_fields: List[str] = []
        if group.is_deleted:
            group.is_deleted = False
            group.deleted_at = None
            group.deleted_by = None
            changed_fields.extend(["is_deleted", "deleted_at", "deleted_by"])
        desired_translation_key = str(spec.get("translation_key") or "")
        if group.translation_key != desired_translation_key:
            group.translation_key = desired_translation_key
            changed_fields.append("translation_key")
        if group.is_locked:
            group.is_locked = False
            changed_fields.append("is_locked")
        desired_is_system = code in default_groups
        if group.is_system != desired_is_system:
            group.is_system = desired_is_system
            changed_fields.append("is_system")
        desired_name = str(spec.get("name") or _humanize_group_code(code))
        if not group.name or group.name == desired_translation_key or group.name.startswith("menu."):
            group.name = desired_name
            changed_fields.append("name")
        if created:
            created_groups.append(code)
        elif changed_fields:
            group.save(update_fields=changed_fields)
        groups_by_code[code] = group
        return group

    existing_groups = MenuGroup.all_objects.all()
    groups_by_code.update({group.code: group for group in existing_groups})
    ensure_group("other")

    for item in deepcopy(STATIC_MENU_ITEMS):
        default_group = ensure_group(item["group_code"])
        entry = MenuEntry.all_objects.filter(source_type="static", source_code=item["code"]).first()
        created = entry is None
        if entry is None:
            entry = MenuEntry(
                source_type="static",
                source_code=item["code"],
                code=item["code"],
                name=item["code"],
                name_en=item["code"],
                translation_key=item["translation_key"],
                route_path=item["url"],
                icon=item["icon"],
                sort_order=int(item["item_order"]),
                is_visible=True,
                is_locked=False,
                is_system=True,
                menu_group=default_group,
            )
            entry.save()
        changed_fields: List[str] = []
        if entry.is_deleted:
            entry.is_deleted = False
            entry.deleted_at = None
            entry.deleted_by = None
            changed_fields.extend(["is_deleted", "deleted_at", "deleted_by"])
        desired_path = _normalize_route_path(item["url"], item["url"])
        if entry.code != item["code"]:
            entry.code = item["code"]
            changed_fields.append("code")
        if entry.name != item["code"]:
            entry.name = item["code"]
            changed_fields.append("name")
        if entry.name_en != item["code"]:
            entry.name_en = item["code"]
            changed_fields.append("name_en")
        if entry.translation_key != item["translation_key"]:
            entry.translation_key = item["translation_key"]
            changed_fields.append("translation_key")
        if entry.route_path != desired_path:
            entry.route_path = desired_path
            changed_fields.append("route_path")
        if entry.icon != item["icon"]:
            entry.icon = item["icon"]
            changed_fields.append("icon")
        if entry.is_locked:
            entry.is_locked = False
            changed_fields.append("is_locked")
        if entry.is_system is not True:
            entry.is_system = True
            changed_fields.append("is_system")
        if entry.menu_group_id is None or getattr(entry.menu_group, "is_deleted", False):
            entry.menu_group = default_group
            changed_fields.append("menu_group")
        if created:
            created_entries.append(entry.code)
        elif changed_fields:
            entry.save(update_fields=changed_fields)

    object_entries = {
        entry.source_code: entry
        for entry in MenuEntry.all_objects.filter(source_type="business_object").select_related("menu_group")
    }
    active_object_codes: set[str] = set()
    seed_group_definitions = _get_default_group_definitions()

    for obj in BusinessObject.objects.filter(is_deleted=False).order_by("code"):
        active_object_codes.add(obj.code)
        legacy_menu = build_menu_config_for_object(
            obj.code,
            obj.menu_config or {},
            group_definitions=seed_group_definitions,
        )
        group_code = str(legacy_menu.get("group_code") or "other")
        group = ensure_group(group_code)
        entry = object_entries.get(obj.code)
        if entry is None:
            entry = MenuEntry.objects.create(
                source_type="business_object",
                source_code=obj.code,
                code=obj.code,
                name=obj.name,
                name_en=obj.name_en or "",
                translation_key=str(legacy_menu.get("translation_key") or get_object_translation_key(obj.code)),
                route_path=_normalize_route_path(legacy_menu.get("url"), f"/objects/{obj.code}"),
                icon=str(legacy_menu.get("icon") or "Document"),
                sort_order=int(legacy_menu.get("item_order") or 999),
                is_visible=bool(legacy_menu.get("show_in_menu", True)),
                is_locked=is_default_business_object(obj.code, obj.is_hardcoded),
                is_system=is_default_business_object(obj.code, obj.is_hardcoded),
                menu_group=group,
                business_object=obj,
            )
            created_entries.append(entry.code)
            continue

        changed_fields: List[str] = []
        if entry.is_deleted:
            entry.is_deleted = False
            entry.deleted_at = None
            entry.deleted_by = None
            changed_fields.extend(["is_deleted", "deleted_at", "deleted_by"])
        if entry.code != obj.code:
            entry.code = obj.code
            changed_fields.append("code")
        if entry.name != obj.name:
            entry.name = obj.name
            changed_fields.append("name")
        desired_name_en = obj.name_en or ""
        if entry.name_en != desired_name_en:
            entry.name_en = desired_name_en
            changed_fields.append("name_en")
        desired_translation_key = str(legacy_menu.get("translation_key") or get_object_translation_key(obj.code))
        if entry.translation_key != desired_translation_key:
            entry.translation_key = desired_translation_key
            changed_fields.append("translation_key")
        desired_path = _normalize_route_path(legacy_menu.get("url"), f"/objects/{obj.code}")
        if entry.route_path != desired_path:
            entry.route_path = desired_path
            changed_fields.append("route_path")
        desired_icon = str(legacy_menu.get("icon") or "Document")
        if entry.icon != desired_icon:
            entry.icon = desired_icon
            changed_fields.append("icon")
        desired_sort_order = int(legacy_menu.get("item_order") or 999)
        if entry.sort_order != desired_sort_order:
            entry.sort_order = desired_sort_order
            changed_fields.append("sort_order")
        desired_visibility = bool(legacy_menu.get("show_in_menu", True))
        if entry.is_visible != desired_visibility:
            entry.is_visible = desired_visibility
            changed_fields.append("is_visible")
        if entry.business_object_id != obj.id:
            entry.business_object = obj
            changed_fields.append("business_object")
        desired_locked = is_default_business_object(obj.code, obj.is_hardcoded)
        if entry.is_locked != desired_locked:
            entry.is_locked = desired_locked
            changed_fields.append("is_locked")
        if entry.is_system != desired_locked:
            entry.is_system = desired_locked
            changed_fields.append("is_system")
        if entry.menu_group_id is None or getattr(entry.menu_group, "is_deleted", False):
            entry.menu_group = group
            changed_fields.append("menu_group")
        if changed_fields:
            entry.save(update_fields=changed_fields)
            updated_entries.append(entry.code)

    for source_code, entry in object_entries.items():
        if source_code in active_object_codes:
            continue
        if not entry.is_deleted:
            entry.soft_delete()

    return {
        "created_groups": created_groups,
        "created_entries": created_entries,
        "updated_entries": updated_entries,
    }


def get_menu_group_definitions(settings: Optional[MenuManagementSettings] = None) -> Dict[str, Dict[str, Any]]:
    sync_menu_registry_models()
    definitions: Dict[str, Dict[str, Any]] = {}
    for group in MenuGroup.objects.filter(is_deleted=False).order_by("sort_order", "code"):
        definitions[group.code] = {
            "code": group.code,
            "name": group.name,
            "translation_key": group.translation_key,
            "order": int(group.sort_order),
            "icon": group.icon,
            "is_visible": bool(group.is_visible),
            "is_default": bool(group.is_system),
            "is_locked": bool(group.is_locked),
        }
    if "other" not in definitions:
        definitions["other"] = _get_default_group_definitions()["other"]
    return definitions


def get_menu_group_definition(
    group_code: str,
    group_definitions: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    definitions = group_definitions or get_menu_group_definitions()
    return definitions.get(group_code, definitions.get("other", _get_default_group_definitions()["other"]))


def get_static_menu_items(settings: Optional[MenuManagementSettings] = None) -> List[Dict[str, Any]]:
    sync_menu_registry_models()
    items: List[Dict[str, Any]] = []
    for entry in (
        MenuEntry.objects
        .filter(source_type="static", is_deleted=False)
        .select_related("menu_group")
        .order_by("menu_group__sort_order", "sort_order", "code")
    ):
        items.append({
            "code": entry.code,
            "translation_key": entry.translation_key,
            "url": entry.route_path,
            "group_code": entry.menu_group.code,
            "item_order": int(entry.sort_order),
            "icon": entry.icon,
            "show_in_menu": bool(entry.is_visible),
        })
    return items


def get_object_translation_key(object_code: str) -> str:
    mapped = OBJECT_ROUTE_KEY_MAP.get(object_code, object_code)
    return f"menu.routes.{mapped}"


def _infer_group_code(object_code: str, old_config: Optional[MenuConfig] = None) -> str:
    legacy_group_code = str((old_config or {}).get("group_code") or "").strip()
    if legacy_group_code in MENU_GROUPS:
        return legacy_group_code

    normalized = str(object_code or "").lower()

    if normalized.startswith("workflow"):
        return "workflow"
    if "inventory" in normalized:
        return "inventory"
    if "consumable" in normalized:
        return "consumable"
    if any(token in normalized for token in ("purchase", "receipt", "maintenance", "disposal")):
        return "lifecycle"
    if any(token in normalized for token in ("organization", "department", "user", "role")):
        return "organization"
    if any(token in normalized for token in ("asset", "location", "supplier")):
        return "asset_master"
    if any(
        token in normalized
        for token in (
            "finance",
            "voucher",
            "depreciation",
            "insurance",
            "policy",
            "premium",
            "claim",
            "lease",
            "rent",
            "software",
            "license",
        )
    ):
        return "finance"

    return "other"


def _infer_icon(object_code: str, group_code: str) -> str:
    normalized = str(object_code or "").lower()

    if group_code == "asset_operation":
        if "pickup" in normalized:
            return "Upload"
        if "transfer" in normalized:
            return "Switch"
        if "return" in normalized:
            return "Download"
        if "loan" in normalized:
            return "Connection"
        return "Operation"

    if group_code == "lifecycle":
        if "purchase" in normalized:
            return "ShoppingCart"
        if "receipt" in normalized:
            return "Box"
        if "plan" in normalized:
            return "Calendar"
        if "task" in normalized:
            return "List"
        if "maintenance" in normalized:
            return "Tools"
        if "disposal" in normalized:
            return "Delete"

    return _get_default_group_definitions().get(group_code, _get_default_group_definitions()["other"])["icon"] or "Document"


def _merge_nested_config(base: Optional[Dict[str, Any]], overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged: Dict[str, Any] = deepcopy(base or {})
    if not isinstance(overrides, dict):
        return merged

    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_nested_config(merged[key], value)
            continue
        merged[key] = deepcopy(value)

    return merged


def build_menu_config_for_object(
    object_code: str,
    old_config: Optional[MenuConfig] = None,
    group_definitions: Optional[Dict[str, Dict[str, Any]]] = None,
) -> MenuConfig:
    existing = old_config or {}
    explicit = DEFAULT_OBJECT_MENU_RULES.get(object_code, {})
    group_code = explicit.get("group_code") or _infer_group_code(object_code, existing)
    group = (group_definitions or _get_default_group_definitions()).get(
        group_code,
        (group_definitions or _get_default_group_definitions()).get("other", _get_default_group_definitions()["other"]),
    )
    inferred_icon = _infer_icon(object_code, group_code)

    show_in_menu = explicit.get("show_in_menu")
    if show_in_menu is None:
        show_in_menu = bool(existing.get("show_in_menu", True))

    item_order = explicit.get("item_order")
    if item_order is None:
        item_order = int(existing.get("item_order") or 999)

    menu_config: MenuConfig = {
        "show_in_menu": show_in_menu,
        "group_code": group_code,
        "group_translation_key": group["translation_key"],
        "group_order": int(group["order"]),
        "group_icon": group["icon"],
        "item_order": int(item_order),
        "icon": explicit.get("icon") or existing.get("icon") or inferred_icon or "Document",
        "translation_key": explicit.get("translation_key")
        or existing.get("translation_key")
        or get_object_translation_key(object_code),
    }

    menu_config["url"] = (
        explicit.get("url")
        or existing.get("url")
        or (f"/objects/{object_code}" if object_code else "")
    )

    if existing.get("badge") is not None:
        menu_config["badge"] = deepcopy(existing["badge"])

    explicit_workbench = explicit.get("workbench")
    existing_workbench = existing.get("workbench")
    merged_workbench = _merge_nested_config(
        explicit_workbench if isinstance(explicit_workbench, dict) else {},
        existing_workbench if isinstance(existing_workbench, dict) else {},
    )
    if merged_workbench:
        menu_config["workbench"] = merged_workbench

    return menu_config


def sync_business_object_menu_configs(
    queryset: Optional[Iterable[BusinessObject]] = None,
) -> Dict[str, Any]:
    if queryset is None:
        queryset = BusinessObject.objects.filter(is_deleted=False).order_by("code")
    objects = list(queryset)
    group_definitions = get_menu_group_definitions()
    updated_codes: List[str] = []
    unchanged_codes: List[str] = []

    for obj in objects:
        new_config = build_menu_config_for_object(
            obj.code,
            obj.menu_config or {},
            group_definitions=group_definitions,
        )
        if (obj.menu_config or {}) == new_config:
            unchanged_codes.append(obj.code)
            continue

        obj.menu_config = new_config
        obj.save(update_fields=["menu_config"])
        updated_codes.append(obj.code)

    return {
        "total": len(objects),
        "updated": updated_codes,
        "unchanged": unchanged_codes,
    }
