import { resolveFieldType } from "@/utils/fieldType";
import i18n from "@/locales";
import { normalizeGridSpan24 } from "@/platform/layout/semanticGrid";

export type UnifiedDetailField = {
  prop: string;
  label: string;
  editorType?: string;
  type?:
    | "text"
    | "date"
    | "datetime"
    | "time"
    | "daterange"
    | "year"
    | "month"
    | "number"
    | "currency"
    | "percent"
    | "boolean"
    | "switch"
    | "checkbox"
    | "tag"
    | "slot"
    | "link"
    | "image"
    | "qr_code"
    | "barcode"
    | "color"
    | "rate"
    | "file"
    | "attachment"
    | "rich_text"
    | "sub_table"
    | "json"
    | "object"
    | "related_object"
    | "workflow_progress"
    | "reference"
    | "user"
    | "department"
    | "location"
    | "organization"
    | "asset";
  options?: { label: string; value: any; color?: string }[];
  dateFormat?: string;
  precision?: number;
  currency?: string;
  tagType?: Record<
    string,
    "success" | "warning" | "danger" | "info" | "primary"
  >;
  defaultTagType?: "success" | "warning" | "danger" | "info" | "primary";
  span?: number;
  minHeight?: number;
  href?: string;
  hidden?: boolean;
  labelClass?: string;
  valueClass?: string;
  referenceObject?: string;
  referenceDisplayField?: string;
  referenceSecondaryField?: string;
  componentProps?: Record<string, any>;
};

const AUDIT_FIELD_CODES = new Set([
  "created_at",
  "created_by",
  "updated_at",
  "updated_by",
  "createdAt",
  "createdBy",
  "updatedAt",
  "updatedBy",
]);

export function isAuditFieldCode(code: string): boolean {
  return AUDIT_FIELD_CODES.has(String(code || "").trim());
}

export function normalizeDetailSpan(rawSpan: any, rawColumns: any): number {
  return normalizeGridSpan24(rawSpan, rawColumns);
}

const resolveMinHeight = (field: Record<string, any>): number | undefined => {
  const raw =
    field.minHeight ??
    field.min_height ??
    field.componentProps?.minHeight ??
    field.componentProps?.min_height ??
    field.component_props?.minHeight ??
    field.component_props?.min_height;
  const normalized = Number(raw);
  return Number.isFinite(normalized) && normalized > 0
    ? Math.round(normalized)
    : undefined;
};

export function toUnifiedDetailField(
  field: Record<string, any>,
): UnifiedDetailField {
  const code = String(field.code || field.fieldCode || "").trim();
  const normalizedType = resolveFieldType(field, "text");
  const options = field.options || [];
  const componentProps = {
    ...(field.component_props || {}),
    ...(field.componentProps || {}),
  };

  const detailField: UnifiedDetailField = {
    prop: code,
    label: field.label || field.name || code,
    editorType: normalizedType,
    span: field.span || 12,
    minHeight: resolveMinHeight(field),
    options,
    componentProps,
  };

  if (
    normalizedType === "date" ||
    normalizedType === "datetime" ||
    normalizedType === "time" ||
    normalizedType === "year" ||
    normalizedType === "month"
  ) {
    detailField.type = normalizedType as UnifiedDetailField["type"];
    if (normalizedType === "date")
      detailField.dateFormat = field.dateFormat || "YYYY-MM-DD";
    if (normalizedType === "datetime")
      detailField.dateFormat = field.dateFormat || "YYYY-MM-DD HH:mm:ss";
    if (normalizedType === "time")
      detailField.dateFormat = field.dateFormat || "HH:mm:ss";
    if (normalizedType === "year")
      detailField.dateFormat = field.dateFormat || "YYYY";
    if (normalizedType === "month")
      detailField.dateFormat = field.dateFormat || "YYYY-MM";
  } else if (normalizedType === "daterange") {
    detailField.type = "daterange";
    detailField.dateFormat = field.dateFormat || "YYYY-MM-DD";
  } else if (normalizedType === "number" || normalizedType === "currency") {
    detailField.type = normalizedType === "currency" ? "currency" : "number";
    detailField.precision =
      field.precision ?? field.decimalPlaces ?? field.decimal_places ?? 2;
    detailField.currency = field.currencySymbol || field.currency || undefined;
  } else if (normalizedType === "percent") {
    detailField.type = "percent";
    detailField.precision =
      field.precision ?? field.decimalPlaces ?? field.decimal_places ?? 2;
  } else if (
    normalizedType === "boolean" ||
    normalizedType === "switch" ||
    normalizedType === "checkbox"
  ) {
    detailField.type = normalizedType as UnifiedDetailField["type"];
  } else if (normalizedType === "color" || normalizedType === "rate") {
    detailField.type = normalizedType as UnifiedDetailField["type"];
  } else if (normalizedType === "url") {
    detailField.type = "link";
    detailField.href = "{value}";
  } else if (normalizedType === "email") {
    detailField.type = "link";
    detailField.href = "mailto:{value}";
  } else if (normalizedType === "phone") {
    detailField.type = "link";
    detailField.href = "tel:{value}";
  } else if (normalizedType === "rich_text") {
    detailField.type = "rich_text";
    detailField.span = 24;
  } else if (normalizedType === "sub_table") {
    detailField.type = "sub_table";
    detailField.span = 24;
  } else if (normalizedType === "json" || normalizedType === "object") {
    detailField.type = normalizedType as UnifiedDetailField["type"];
    detailField.span = 24;
  } else if (normalizedType === "image") {
    detailField.type = "image";
    detailField.span = 24;
  } else if (normalizedType === "qr_code" || normalizedType === "barcode") {
    detailField.type = normalizedType as UnifiedDetailField["type"];
  } else if (normalizedType === "file" || normalizedType === "attachment") {
    detailField.type = normalizedType as UnifiedDetailField["type"];
    detailField.span = 24;
  } else if (normalizedType === "related_object") {
    detailField.type = "related_object";
    detailField.span = 24;
  } else if (normalizedType === "workflow_progress") {
    detailField.type = "workflow_progress";
    detailField.span = 24;
  } else if (
    normalizedType === "reference" ||
    normalizedType === "user" ||
    normalizedType === "department" ||
    normalizedType === "location" ||
    normalizedType === "organization" ||
    normalizedType === "asset"
  ) {
    detailField.type = normalizedType as UnifiedDetailField["type"];

    const typeObjectCodeMap: Record<string, string> = {
      user: "User",
      department: "Department",
      location: "Location",
      organization: "Organization",
      asset: "Asset",
    };

    detailField.referenceObject =
      String(
        field.referenceObject ||
          field.reference_object ||
          field.referenceModelPath ||
          field.reference_model_path ||
          field.relatedObject ||
          field.related_object ||
          componentProps.referenceObject ||
          componentProps.reference_object ||
          componentProps.referenceModelPath ||
          componentProps.reference_model_path ||
          typeObjectCodeMap[normalizedType] ||
          "",
      ).trim() || undefined;

    detailField.referenceDisplayField = String(
      field.referenceDisplayField ||
        field.reference_display_field ||
        field.displayField ||
        field.display_field ||
        componentProps.referenceDisplayField ||
        componentProps.reference_display_field ||
        componentProps.displayField ||
        componentProps.display_field ||
        "name",
    ).trim();

    detailField.referenceSecondaryField = String(
      field.referenceSecondaryField ||
        field.reference_secondary_field ||
        componentProps.referenceSecondaryField ||
        componentProps.reference_secondary_field ||
        componentProps.secondaryField ||
        componentProps.secondary_field ||
        "code",
    ).trim();
  } else {
    detailField.type = "text";
  }

  const shouldTag =
    normalizedType === "status" ||
    normalizedType === "enum" ||
    code === "status" ||
    !!field.tagTypeMapping ||
    options.some((opt: any) => opt?.color);

  if (shouldTag) {
    detailField.type = "tag";
    detailField.tagType = field.tagTypeMapping as Record<
      string,
      "success" | "warning" | "danger" | "info" | "primary"
    >;
    detailField.defaultTagType = (field.defaultTagType as any) || "info";
  }

  return detailField;
}

export function buildRequiredFormRules(
  fields: Array<Record<string, any>>,
): Record<string, any> {
  const rules: Record<string, any> = {};
  for (const field of fields || []) {
    const required = field.isRequired || field.is_required || field.required;
    if (!required) continue;
    const code = String(field.code || field.fieldCode || "").trim();
    if (!code) continue;
    const label = field.label || field.name || code;
    rules[code] = [
      {
        required: true,
        message: i18n.global.t("common.validation.requiredWithField", {
          field: label,
        }),
        trigger: ["blur", "change"],
      },
    ];
  }
  return rules;
}
