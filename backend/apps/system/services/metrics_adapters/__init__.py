"""Closed-loop metrics adapters for cross-domain operational dashboards."""

from apps.system.services.metrics_adapters.closed_loop import (
    AssetProjectMetricsAdapter,
    ClaimRecordMetricsAdapter,
    FinanceVoucherMetricsAdapter,
    InsurancePolicyMetricsAdapter,
    InventoryTaskMetricsAdapter,
    LeasingContractMetricsAdapter,
)

DEFAULT_CLOSED_LOOP_METRICS_ADAPTERS = [
    AssetProjectMetricsAdapter,
    InventoryTaskMetricsAdapter,
    FinanceVoucherMetricsAdapter,
    InsurancePolicyMetricsAdapter,
    ClaimRecordMetricsAdapter,
    LeasingContractMetricsAdapter,
]

