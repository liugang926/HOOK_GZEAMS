from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Type

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Model, QuerySet
from rest_framework import serializers

from apps.assets.models import (
    AssetLoan,
    AssetPickup,
    AssetReturn,
    AssetTransfer,
    LoanItem,
    PickupItem,
    ReturnItem,
    TransferItem,
)
from apps.assets.serializers.operation import (
    AssetLoanCreateSerializer,
    AssetLoanDetailSerializer,
    AssetLoanUpdateSerializer,
    AssetPickupCreateSerializer,
    AssetPickupDetailSerializer,
    AssetPickupUpdateSerializer,
    AssetReturnCreateSerializer,
    AssetReturnDetailSerializer,
    AssetReturnUpdateSerializer,
    AssetTransferCreateSerializer,
    AssetTransferDetailSerializer,
    AssetTransferUpdateSerializer,
    LoanItemSerializer,
    PickupItemSerializer,
    ReturnItemSerializer,
    TransferItemSerializer,
)
from apps.assets.services.operation_service import (
    AssetLoanService,
    AssetPickupService,
    AssetReturnService,
    AssetTransferService,
)
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptItem,
    DisposalItem,
    DisposalRequest,
    PurchaseRequest,
    PurchaseRequestItem,
)
from apps.lifecycle.serializers.disposal import (
    DisposalItemSerializer,
    DisposalRequestCreateSerializer,
    DisposalRequestDetailSerializer,
)
from apps.lifecycle.serializers.purchase import (
    PurchaseRequestCreateSerializer,
    PurchaseRequestDetailSerializer,
    PurchaseRequestItemSerializer,
)
from apps.lifecycle.serializers.receipt import (
    AssetReceiptCreateSerializer,
    AssetReceiptDetailSerializer,
    AssetReceiptItemSerializer,
)
from apps.lifecycle.services.disposal_service import DisposalRequestService
from apps.lifecycle.services.purchase_service import PurchaseRequestService
from apps.lifecycle.services.receipt_service import AssetReceiptService
from apps.system.models import BusinessObject, ObjectRelationDefinition
from apps.system.services.activity_log_service import ActivityLogService
from apps.system.services.timeline_highlight_service import (
    build_timeline_highlight,
    build_timeline_highlights_from_changes,
    build_timeline_highlights_from_description,
    merge_timeline_highlights,
)


@dataclass(frozen=True)
class AggregateDocumentAdapter:
    object_code: str
    target_object_code: str
    relation_code: str
    field_code: str
    workflow_business_object_code: str
    model_class: Type[Model]
    detail_serializer_class: Type[serializers.Serializer]
    document_serializer_class: Type[serializers.Serializer]
    create_serializer_class: Type[serializers.Serializer]
    update_serializer_class: Type[serializers.Serializer]
    service_class: Type[Any]
    master_editable_statuses: frozenset[str] = frozenset({"draft"})
    detail_editable_statuses: Optional[frozenset[str]] = None
    submittable_statuses: frozenset[str] = frozenset({"draft"})
    approvable_statuses: frozenset[str] = frozenset()

    @property
    def detail_accessor(self) -> str:
        return "items"

    @property
    def effective_detail_editable_statuses(self) -> frozenset[str]:
        return self.detail_editable_statuses or self.master_editable_statuses


class AggregateDocumentService:
    """
    Unified aggregate document read/write service for first-batch master-detail documents.

    This phase intentionally scopes to the first asset operation document family and
    standardizes:
    - read contract
    - write contract
    - capability payload
    - detail region metadata
    """

    _ADAPTERS: Dict[str, AggregateDocumentAdapter] = {
        "AssetPickup": AggregateDocumentAdapter(
            object_code="AssetPickup",
            target_object_code="PickupItem",
            relation_code="pickup_items",
            field_code="items",
            workflow_business_object_code="asset_pickup",
            model_class=AssetPickup,
            detail_serializer_class=PickupItemSerializer,
            document_serializer_class=AssetPickupDetailSerializer,
            create_serializer_class=AssetPickupCreateSerializer,
            update_serializer_class=AssetPickupUpdateSerializer,
            service_class=AssetPickupService,
            approvable_statuses=frozenset({"pending"}),
        ),
        "AssetTransfer": AggregateDocumentAdapter(
            object_code="AssetTransfer",
            target_object_code="TransferItem",
            relation_code="transfer_items",
            field_code="items",
            workflow_business_object_code="asset_transfer",
            model_class=AssetTransfer,
            detail_serializer_class=TransferItemSerializer,
            document_serializer_class=AssetTransferDetailSerializer,
            create_serializer_class=AssetTransferCreateSerializer,
            update_serializer_class=AssetTransferUpdateSerializer,
            service_class=AssetTransferService,
            approvable_statuses=frozenset({"pending", "out_approved"}),
        ),
        "AssetReturn": AggregateDocumentAdapter(
            object_code="AssetReturn",
            target_object_code="ReturnItem",
            relation_code="return_items",
            field_code="items",
            workflow_business_object_code="asset_return",
            model_class=AssetReturn,
            detail_serializer_class=ReturnItemSerializer,
            document_serializer_class=AssetReturnDetailSerializer,
            create_serializer_class=AssetReturnCreateSerializer,
            update_serializer_class=AssetReturnUpdateSerializer,
            service_class=AssetReturnService,
            approvable_statuses=frozenset({"pending"}),
        ),
        "AssetLoan": AggregateDocumentAdapter(
            object_code="AssetLoan",
            target_object_code="LoanItem",
            relation_code="loan_items",
            field_code="items",
            workflow_business_object_code="asset_loan",
            model_class=AssetLoan,
            detail_serializer_class=LoanItemSerializer,
            document_serializer_class=AssetLoanDetailSerializer,
            create_serializer_class=AssetLoanCreateSerializer,
            update_serializer_class=AssetLoanUpdateSerializer,
            service_class=AssetLoanService,
            approvable_statuses=frozenset({"pending"}),
        ),
        "PurchaseRequest": AggregateDocumentAdapter(
            object_code="PurchaseRequest",
            target_object_code="PurchaseRequestItem",
            relation_code="purchase_request_items",
            field_code="items",
            workflow_business_object_code="purchase_request",
            model_class=PurchaseRequest,
            detail_serializer_class=PurchaseRequestItemSerializer,
            document_serializer_class=PurchaseRequestDetailSerializer,
            create_serializer_class=PurchaseRequestCreateSerializer,
            update_serializer_class=PurchaseRequestCreateSerializer,
            service_class=PurchaseRequestService,
            master_editable_statuses=frozenset({"draft", "rejected"}),
            submittable_statuses=frozenset({"draft", "rejected"}),
            approvable_statuses=frozenset({"submitted"}),
        ),
        "AssetReceipt": AggregateDocumentAdapter(
            object_code="AssetReceipt",
            target_object_code="AssetReceiptItem",
            relation_code="receipt_items",
            field_code="items",
            workflow_business_object_code="asset_receipt",
            model_class=AssetReceipt,
            detail_serializer_class=AssetReceiptItemSerializer,
            document_serializer_class=AssetReceiptDetailSerializer,
            create_serializer_class=AssetReceiptCreateSerializer,
            update_serializer_class=AssetReceiptCreateSerializer,
            service_class=AssetReceiptService,
            master_editable_statuses=frozenset({"draft", "rejected"}),
            submittable_statuses=frozenset({"draft", "rejected"}),
            approvable_statuses=frozenset({"inspecting"}),
        ),
        "DisposalRequest": AggregateDocumentAdapter(
            object_code="DisposalRequest",
            target_object_code="DisposalItem",
            relation_code="disposal_items",
            field_code="items",
            workflow_business_object_code="disposal_request",
            model_class=DisposalRequest,
            detail_serializer_class=DisposalItemSerializer,
            document_serializer_class=DisposalRequestDetailSerializer,
            create_serializer_class=DisposalRequestCreateSerializer,
            update_serializer_class=DisposalRequestCreateSerializer,
            service_class=DisposalRequestService,
            master_editable_statuses=frozenset({"draft", "rejected"}),
            detail_editable_statuses=frozenset({"draft", "rejected", "appraising", "executing"}),
            submittable_statuses=frozenset({"draft", "rejected"}),
            approvable_statuses=frozenset({"submitted", "appraising"}),
        ),
    }

    def supports_object(self, object_code: str) -> bool:
        return object_code in self._ADAPTERS

    def get_adapter(self, object_code: str) -> AggregateDocumentAdapter:
        adapter = self._ADAPTERS.get(str(object_code or "").strip())
        if adapter is None:
            raise DjangoValidationError({"object_code": ["Unsupported aggregate document object"]})
        return adapter

    def get_document(
        self,
        *,
        object_code: str,
        record_id: str,
        user,
        organization_id: Optional[str],
        page_mode: str = "readonly",
    ) -> Dict[str, Any]:
        adapter = self.get_adapter(object_code)
        instance = self._get_instance(adapter=adapter, record_id=record_id, organization_id=organization_id)
        return self._build_document_payload(
            adapter=adapter,
            instance=instance,
            organization_id=organization_id,
            page_mode=page_mode,
        )

    def create_document(
        self,
        *,
        object_code: str,
        payload: Dict[str, Any],
        user,
        organization_id: Optional[str],
        page_mode: str = "edit",
    ) -> Model:
        adapter = self.get_adapter(object_code)
        master_payload = self._extract_master_payload(payload)
        detail_rows = self._extract_detail_rows(payload, adapter)
        serializer_input = {
            **master_payload,
            adapter.field_code: detail_rows,
        }

        serializer = adapter.create_serializer_class(data=serializer_input)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data.pop(adapter.field_code, [])
        service = adapter.service_class()
        return service.create_with_items(
            serializer.validated_data,
            items,
            user,
            organization_id,
        )

    def update_document(
        self,
        *,
        object_code: str,
        record_id: str,
        payload: Dict[str, Any],
        user,
        organization_id: Optional[str],
        partial: bool = False,
        page_mode: str = "edit",
    ) -> Model:
        adapter = self.get_adapter(object_code)
        instance = self._get_instance(adapter=adapter, record_id=record_id, organization_id=organization_id)

        master_payload = self._extract_master_payload(payload)
        detail_rows = self._extract_detail_rows(payload, adapter, allow_missing=True)

        # Aggregate document updates only submit editable master fields.
        # Existing business serializers may still declare required read-only
        # fields (for example applicant/borrower on full PUT). We therefore
        # validate master updates using document semantics instead of raw
        # REST-resource replacement semantics.
        serializer = adapter.update_serializer_class(instance, data=master_payload, partial=True)
        serializer.is_valid(raise_exception=True)

        service = adapter.service_class()
        return service.update_with_items(
            str(record_id),
            serializer.validated_data,
            detail_rows,
            user,
            organization_id,
        )

    def build_document_response(
        self,
        *,
        object_code: str,
        instance: Model,
        organization_id: Optional[str],
        page_mode: str,
    ) -> Dict[str, Any]:
        adapter = self.get_adapter(object_code)
        return self._build_document_payload(
            adapter=adapter,
            instance=instance,
            organization_id=organization_id,
            page_mode=page_mode,
        )

    def _get_instance(
        self,
        *,
        adapter: AggregateDocumentAdapter,
        record_id: str,
        organization_id: Optional[str],
    ) -> Model:
        queryset = self._get_base_queryset(adapter.model_class, organization_id=organization_id)
        try:
            return queryset.get(id=record_id)
        except adapter.model_class.DoesNotExist as exc:
            raise DjangoValidationError({"id": ["Record not found"]}) from exc

    def _get_base_queryset(self, model_class: Type[Model], *, organization_id: Optional[str]) -> QuerySet:
        manager = getattr(model_class, "all_objects", None) or model_class._default_manager
        queryset = manager.filter(is_deleted=False)
        field_names = {field.name for field in model_class._meta.fields}
        normalized_org_id = str(organization_id or "").strip()
        if "organization" in field_names and normalized_org_id:
            queryset = queryset.filter(organization_id=normalized_org_id)
        return queryset

    def _build_document_payload(
        self,
        *,
        adapter: AggregateDocumentAdapter,
        instance: Model,
        organization_id: Optional[str],
        page_mode: str,
    ) -> Dict[str, Any]:
        document_data = adapter.document_serializer_class(instance).data
        detail_rows = list(getattr(instance, adapter.detail_accessor).all())
        detail_region_meta = self._resolve_detail_region_metadata(
            adapter=adapter,
            organization_id=organization_id,
        )
        detail_rows_payload = adapter.detail_serializer_class(detail_rows, many=True).data
        master_payload = dict(document_data)
        master_payload.pop(adapter.field_code, None)
        trace_context = self._collect_trace_context(
            adapter=adapter,
            instance=instance,
            organization_id=organization_id,
        )

        capabilities = self._build_capabilities(
            adapter=adapter,
            instance=instance,
            page_mode=page_mode,
            row_count=len(detail_rows_payload),
        )

        return {
            "documentVersion": 1,
            "context": {
                "objectCode": adapter.object_code,
                "recordId": str(instance.id),
                "pageMode": str(page_mode or "readonly"),
                "recordLabel": str(instance),
            },
            "aggregate": {
                "isAggregateRoot": True,
                "objectCode": adapter.object_code,
                "detailRegions": [detail_region_meta],
            },
            "master": master_payload,
            "details": {
                adapter.relation_code: {
                    **detail_region_meta,
                    "rows": detail_rows_payload,
                    "rowCount": len(detail_rows_payload),
                    "editable": bool(capabilities["canEditDetails"]),
                }
            },
            "capabilities": capabilities,
            "workflow": self._build_workflow_section(trace_context),
            "timeline": self._build_document_timeline(trace_context),
            "audit": self._build_audit_section(trace_context),
        }

    def _build_capabilities(
        self,
        *,
        adapter: AggregateDocumentAdapter,
        instance: Model,
        page_mode: str,
        row_count: int,
    ) -> Dict[str, Any]:
        normalized_mode = str(page_mode or "readonly").strip().lower() or "readonly"
        status_value = str(getattr(instance, "status", "") or "").strip().lower()
        can_edit_master = normalized_mode != "readonly" and status_value in adapter.master_editable_statuses
        can_edit_details = normalized_mode != "readonly" and status_value in adapter.effective_detail_editable_statuses
        can_save = can_edit_master or can_edit_details
        can_submit = status_value in adapter.submittable_statuses and row_count > 0
        can_approve = status_value in adapter.approvable_statuses
        can_delete = status_value in adapter.master_editable_statuses

        return {
            "canEditMaster": can_edit_master,
            "canEditDetails": can_edit_details,
            "canSave": can_save,
            "canSubmit": can_submit,
            "canDelete": can_delete,
            "canApprove": can_approve,
            "readOnly": not can_save,
        }

    def _extract_master_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise DjangoValidationError({"payload": ["Document payload must be an object"]})

        master = payload.get("master")
        if isinstance(master, dict):
            return dict(master)

        master_payload = {}
        for key, value in payload.items():
            if key in {"master", "details", "context", "aggregate", "capabilities"}:
                continue
            master_payload[key] = value
        return master_payload

    def _extract_detail_rows(
        self,
        payload: Dict[str, Any],
        adapter: AggregateDocumentAdapter,
        *,
        allow_missing: bool = False,
    ) -> Optional[list]:
        if not isinstance(payload, dict):
            if allow_missing:
                return None
            raise DjangoValidationError({"details": ["Document details must be provided"]})

        details = payload.get("details")
        candidate: Any = None
        if isinstance(details, dict):
            for key in (adapter.relation_code, adapter.field_code, "items"):
                if key in details:
                    candidate = details.get(key)
                    break

        if candidate is None:
            for key in (adapter.relation_code, adapter.field_code, "items"):
                if key in payload:
                    candidate = payload.get(key)
                    break

        if candidate is None:
            if allow_missing:
                return None
            raise DjangoValidationError({"details": ["Document details must be provided"]})

        if isinstance(candidate, dict):
            if isinstance(candidate.get("rows"), list):
                return list(candidate.get("rows") or [])
            if isinstance(candidate.get("items"), list):
                return list(candidate.get("items") or [])

        if isinstance(candidate, list):
            return list(candidate)

        raise DjangoValidationError({"details": ["Document detail rows must be a list"]})

    def _resolve_detail_region_metadata(
        self,
        *,
        adapter: AggregateDocumentAdapter,
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        relation = self._get_relation_definition(adapter=adapter, organization_id=organization_id)
        target_object = self._get_business_object(adapter.target_object_code, organization_id=organization_id)

        relation_name = ""
        relation_name_en = ""
        relation_type = "master_detail"
        detail_edit_mode = adapter.effective_detail_editable_statuses and "inline_table" or "readonly_table"
        cascade_soft_delete = True
        toolbar_config: Dict[str, Any] = {}
        summary_rules: list = []
        validation_rules: list = []

        if relation is not None:
            relation_name = str(relation.relation_name or "").strip()
            relation_name_en = str(relation.relation_name_en or relation.relation_name or "").strip()
            relation_type = str(relation.relation_type or relation_type).strip() or relation_type
            detail_edit_mode = str(relation.detail_edit_mode or detail_edit_mode).strip() or detail_edit_mode
            cascade_soft_delete = bool(relation.cascade_soft_delete)
            toolbar_config = relation.detail_toolbar_config or {}
            summary_rules = relation.detail_summary_rules or []
            validation_rules = relation.detail_validation_rules or []

        target_name = str(getattr(target_object, "name", "") or adapter.target_object_code).strip()
        target_name_en = str(
            getattr(target_object, "name_en", "") or getattr(target_object, "name", "") or adapter.target_object_code
        ).strip()
        target_object_role = str(getattr(target_object, "object_role", "") or "detail").strip()
        allow_standalone_route = bool(getattr(target_object, "allow_standalone_route", False))
        allow_standalone_query = bool(getattr(target_object, "allow_standalone_query", True))
        inherit_permissions = bool(getattr(target_object, "inherit_permissions", True))
        inherit_workflow = bool(getattr(target_object, "inherit_workflow", True))
        inherit_status = bool(getattr(target_object, "inherit_status", True))
        inherit_lifecycle = bool(getattr(target_object, "inherit_lifecycle", True))

        return {
            "relationCode": adapter.relation_code,
            "fieldCode": adapter.field_code,
            "title": relation_name or adapter.relation_code,
            "titleEn": relation_name_en or relation_name or adapter.relation_code,
            "translationKey": "",
            "targetObjectCode": adapter.target_object_code,
            "targetObjectName": target_name,
            "targetObjectNameEn": target_name_en,
            "targetObjectRole": target_object_role,
            "relationType": relation_type,
            "detailEditMode": detail_edit_mode,
            "cascadeSoftDelete": cascade_soft_delete,
            "toolbarConfig": toolbar_config,
            "summaryRules": summary_rules,
            "validationRules": validation_rules,
            "allowStandaloneRoute": allow_standalone_route,
            "allowStandaloneQuery": allow_standalone_query,
            "inheritPermissions": inherit_permissions,
            "inheritWorkflow": inherit_workflow,
            "inheritStatus": inherit_status,
            "inheritLifecycle": inherit_lifecycle,
        }

    def _get_relation_definition(
        self,
        *,
        adapter: AggregateDocumentAdapter,
        organization_id: Optional[str],
    ) -> Optional[ObjectRelationDefinition]:
        queryset = ObjectRelationDefinition.all_objects.filter(
            parent_object_code=adapter.object_code,
            target_object_code=adapter.target_object_code,
            relation_code=adapter.relation_code,
            is_deleted=False,
            is_active=True,
        )

        org_specific = self._prefer_organization_scope(queryset, organization_id=organization_id)
        return org_specific.first()

    def _get_business_object(self, code: str, *, organization_id: Optional[str]) -> Optional[BusinessObject]:
        queryset = BusinessObject.all_objects.filter(
            code=code,
            is_deleted=False,
        )
        org_specific = self._prefer_organization_scope(queryset, organization_id=organization_id)
        return org_specific.first()

    def _collect_trace_context(
        self,
        *,
        adapter: AggregateDocumentAdapter,
        instance: Model,
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        workflow_definition = self._get_workflow_definition(adapter=adapter, organization_id=organization_id)
        workflow_instance = self._get_workflow_instance(
            adapter=adapter,
            instance=instance,
            organization_id=organization_id,
        )
        activity_logs = list(ActivityLogService.get_object_timeline(instance)[:50])
        workflow_approvals = self._get_workflow_approvals(workflow_instance)
        workflow_operation_logs = self._get_workflow_operation_logs(workflow_instance)
        return {
            "adapter": adapter,
            "instance": instance,
            "workflowDefinition": workflow_definition,
            "workflowInstance": workflow_instance,
            "activityLogs": activity_logs,
            "workflowApprovals": workflow_approvals,
            "workflowOperationLogs": workflow_operation_logs,
        }

    def _build_workflow_section(self, trace_context: Dict[str, Any]) -> Dict[str, Any]:
        adapter: AggregateDocumentAdapter = trace_context["adapter"]
        workflow_definition = trace_context["workflowDefinition"]
        workflow_instance = trace_context["workflowInstance"]
        workflow_approvals = trace_context["workflowApprovals"]
        workflow_operation_logs = trace_context["workflowOperationLogs"]

        return {
            "businessObjectCode": adapter.workflow_business_object_code,
            "hasPublishedDefinition": workflow_definition is not None,
            "definition": self._serialize_workflow_definition(workflow_definition),
            "hasInstance": workflow_instance is not None,
            "isActive": bool(getattr(workflow_instance, "is_active", False)) if workflow_instance is not None else False,
            "instance": self._serialize_workflow_instance(workflow_instance),
            "timeline": self._serialize_workflow_timeline(
                workflow_approvals=workflow_approvals,
                workflow_operation_logs=workflow_operation_logs,
            ),
        }

    def _build_document_timeline(self, trace_context: Dict[str, Any]) -> list[Dict[str, Any]]:
        items: list[Dict[str, Any]] = []
        for activity_log in trace_context["activityLogs"]:
            items.append(self._normalize_activity_timeline_entry(activity_log))
        for workflow_approval in trace_context["workflowApprovals"]:
            items.append(self._normalize_workflow_approval_timeline_entry(workflow_approval))
        for workflow_operation_log in trace_context["workflowOperationLogs"]:
            items.append(self._normalize_workflow_operation_timeline_entry(workflow_operation_log))

        items.sort(
            key=lambda item: (
                str(item.get("createdAt") or ""),
                str(item.get("id") or ""),
            ),
            reverse=True,
        )
        return items

    def _build_audit_section(self, trace_context: Dict[str, Any]) -> Dict[str, Any]:
        activity_logs = trace_context["activityLogs"]
        workflow_approvals = trace_context["workflowApprovals"]
        workflow_operation_logs = trace_context["workflowOperationLogs"]

        return {
            "counts": {
                "activityLogs": len(activity_logs),
                "workflowApprovals": len(workflow_approvals),
                "workflowOperationLogs": len(workflow_operation_logs),
            },
            "activityLogs": self._serialize_activity_logs(activity_logs),
            "workflowApprovals": self._serialize_workflow_approvals(workflow_approvals),
            "workflowOperationLogs": self._serialize_workflow_operation_logs(workflow_operation_logs),
        }

    def _get_workflow_definition(
        self,
        *,
        adapter: AggregateDocumentAdapter,
        organization_id: Optional[str],
    ):
        from apps.workflows.models import WorkflowDefinition

        queryset = WorkflowDefinition.objects.filter(
            business_object_code=adapter.workflow_business_object_code,
            status="published",
            is_active=True,
            is_deleted=False,
        )
        normalized_org_id = str(organization_id or "").strip()
        if normalized_org_id:
            queryset = queryset.filter(organization_id=normalized_org_id)
        return queryset.order_by("-published_at", "-version", "-created_at").first()

    def _get_workflow_instance(
        self,
        *,
        adapter: AggregateDocumentAdapter,
        instance: Model,
        organization_id: Optional[str],
    ):
        from apps.workflows.models import WorkflowInstance

        queryset = WorkflowInstance.objects.filter(
            business_object_code=adapter.workflow_business_object_code,
            business_id=str(instance.pk),
            is_deleted=False,
        )
        normalized_org_id = str(organization_id or "").strip()
        if normalized_org_id:
            queryset = queryset.filter(organization_id=normalized_org_id)
        return queryset.select_related("definition", "initiator", "organization").order_by("-created_at").first()

    def _get_workflow_approvals(self, workflow_instance) -> list[Any]:
        if workflow_instance is None:
            return []

        from apps.workflows.models import WorkflowApproval

        return list(
            WorkflowApproval.objects.filter(
                task__instance=workflow_instance,
                is_deleted=False,
            )
            .select_related("approver", "task")
            .order_by("-created_at")[:50]
        )

    def _get_workflow_operation_logs(self, workflow_instance) -> list[Any]:
        if workflow_instance is None:
            return []

        from apps.workflows.models.workflow_operation_log import WorkflowOperationLog

        return list(
            WorkflowOperationLog.objects.filter(
                workflow_instance=workflow_instance,
                is_deleted=False,
            )
            .select_related("actor", "workflow_definition", "workflow_template", "workflow_instance")
            .order_by("-created_at")[:50]
        )

    @staticmethod
    def _serialize_workflow_definition(workflow_definition) -> Optional[Dict[str, Any]]:
        if workflow_definition is None:
            return None

        return {
            "id": str(workflow_definition.id),
            "code": workflow_definition.code,
            "name": workflow_definition.name,
            "version": workflow_definition.version,
            "status": workflow_definition.status,
            "publishedAt": workflow_definition.published_at.isoformat() if workflow_definition.published_at else None,
        }

    @staticmethod
    def _serialize_workflow_instance(workflow_instance) -> Optional[Dict[str, Any]]:
        if workflow_instance is None:
            return None

        from apps.workflows.serializers.workflow_instance_serializers import WorkflowInstanceDetailSerializer

        return WorkflowInstanceDetailSerializer(workflow_instance).data

    @staticmethod
    def _serialize_activity_logs(activity_logs: list[Any]) -> list[Dict[str, Any]]:
        if not activity_logs:
            return []

        from apps.system.activity_log_serializers import ActivityLogSerializer

        return ActivityLogSerializer(activity_logs, many=True).data

    @staticmethod
    def _serialize_workflow_approvals(workflow_approvals: list[Any]) -> list[Dict[str, Any]]:
        if not workflow_approvals:
            return []

        from apps.workflows.serializers.workflow_instance_serializers import WorkflowApprovalSerializer

        return WorkflowApprovalSerializer(workflow_approvals, many=True).data

    @staticmethod
    def _serialize_workflow_operation_logs(workflow_operation_logs: list[Any]) -> list[Dict[str, Any]]:
        if not workflow_operation_logs:
            return []

        from apps.workflows.serializers.workflow_operation_log_serializers import WorkflowOperationLogSerializer

        return WorkflowOperationLogSerializer(workflow_operation_logs, many=True).data

    def _serialize_workflow_timeline(
        self,
        *,
        workflow_approvals: list[Any],
        workflow_operation_logs: list[Any],
    ) -> list[Dict[str, Any]]:
        items: list[Dict[str, Any]] = []
        for workflow_approval in workflow_approvals:
            items.append(self._normalize_workflow_approval_timeline_entry(workflow_approval))
        for workflow_operation_log in workflow_operation_logs:
            items.append(self._normalize_workflow_operation_timeline_entry(workflow_operation_log))
        items.sort(
            key=lambda item: (
                str(item.get("createdAt") or ""),
                str(item.get("id") or ""),
            ),
            reverse=True,
        )
        return items

    @staticmethod
    def _normalize_activity_timeline_entry(activity_log) -> Dict[str, Any]:
        actor_name = ""
        if getattr(activity_log, "actor", None) is not None:
            actor_name = activity_log.actor.get_full_name() or activity_log.actor.username
        changes = activity_log.changes or []

        return {
            "id": str(activity_log.id),
            "source": "activity",
            "createdAt": activity_log.created_at.isoformat() if activity_log.created_at else None,
            "title": activity_log.get_action_display(),
            "description": activity_log.description,
            "action": activity_log.action,
            "actorName": actor_name,
            "changes": changes,
            "highlights": merge_timeline_highlights(
                build_timeline_highlights_from_changes(changes),
                build_timeline_highlights_from_description(activity_log.description),
            ),
        }

    @staticmethod
    def _normalize_workflow_approval_timeline_entry(workflow_approval) -> Dict[str, Any]:
        approver_name = workflow_approval.approver.get_full_name() or workflow_approval.approver.username
        comment_highlight = build_timeline_highlight(code="workflow_comment", value=workflow_approval.comment)
        return {
            "id": str(workflow_approval.id),
            "source": "workflowApproval",
            "createdAt": workflow_approval.created_at.isoformat() if workflow_approval.created_at else None,
            "title": workflow_approval.get_action_display(),
            "description": workflow_approval.task.node_name,
            "action": workflow_approval.action,
            "actionDisplay": workflow_approval.get_action_display(),
            "actorName": approver_name,
            "taskName": workflow_approval.task.node_name,
            "comment": workflow_approval.comment,
            "highlights": [comment_highlight] if comment_highlight else [],
        }

    @staticmethod
    def _normalize_workflow_operation_timeline_entry(workflow_operation_log) -> Dict[str, Any]:
        actor_name = ""
        if getattr(workflow_operation_log, "actor", None) is not None:
            actor_name = workflow_operation_log.actor.get_full_name() or workflow_operation_log.actor.username
        result_highlight = build_timeline_highlight(
            code="workflow_result",
            value=workflow_operation_log.get_result_display(),
        )

        return {
            "id": str(workflow_operation_log.id),
            "source": "workflowOperation",
            "createdAt": workflow_operation_log.created_at.isoformat() if workflow_operation_log.created_at else None,
            "title": workflow_operation_log.get_operation_type_display(),
            "description": workflow_operation_log.target_name or workflow_operation_log.target_code,
            "operationType": workflow_operation_log.operation_type,
            "operationTypeDisplay": workflow_operation_log.get_operation_type_display(),
            "actorName": actor_name,
            "result": workflow_operation_log.result,
            "resultDisplay": workflow_operation_log.get_result_display(),
            "highlights": [result_highlight] if result_highlight else [],
        }

    @staticmethod
    def _prefer_organization_scope(queryset: QuerySet, *, organization_id: Optional[str]) -> QuerySet:
        normalized_org_id = str(organization_id or "").strip()
        if not normalized_org_id:
            return queryset.order_by("created_at")

        org_queryset = queryset.filter(organization_id=normalized_org_id)
        if org_queryset.exists():
            return org_queryset.order_by("created_at")
        return queryset.filter(organization__isnull=True).order_by("created_at")
