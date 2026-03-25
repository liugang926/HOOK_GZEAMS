import type { AggregateDocumentResponse } from '@/types/runtime'

export interface DocumentWorkflowProgressStepDefinition {
  key: string
  translationKey?: string
  matches?: string[]
}

export interface DocumentWorkflowProgressDefinition {
  steps: DocumentWorkflowProgressStepDefinition[]
}

export interface ResolvedDocumentWorkflowProgressStep {
  key: string
  label: string
}

export interface ResolvedDocumentWorkflowProgress {
  currentStatus: string
  steps: ResolvedDocumentWorkflowProgressStep[]
}

const WORKFLOW_PROGRESS_REGISTRY: Record<string, DocumentWorkflowProgressDefinition> = {
  AssetPickup: {
    steps: [
      { key: 'draft', translationKey: 'assets.lifecycle.pickup.status.draft' },
      { key: 'pending', translationKey: 'assets.lifecycle.pickup.status.pending', matches: ['rejected', 'cancelled'] },
      { key: 'approved', translationKey: 'assets.lifecycle.pickup.status.approved' },
      { key: 'completed', translationKey: 'assets.lifecycle.pickup.status.completed' },
    ],
  },
  AssetTransfer: {
    steps: [
      { key: 'draft', translationKey: 'assets.lifecycle.transfer.status.draft' },
      { key: 'pending', translationKey: 'assets.lifecycle.transfer.status.pending', matches: ['rejected', 'cancelled'] },
      { key: 'approved', translationKey: 'assets.lifecycle.transfer.status.approved', matches: ['out_approved'] },
      { key: 'completed', translationKey: 'assets.lifecycle.transfer.status.completed' },
    ],
  },
  AssetReturn: {
    steps: [
      { key: 'draft', translationKey: 'assets.lifecycle.return.status.draft' },
      { key: 'pending', translationKey: 'assets.lifecycle.return.status.pending', matches: ['cancelled'] },
      { key: 'confirmed', translationKey: 'assets.lifecycle.return.status.confirmed' },
      { key: 'completed', translationKey: 'assets.lifecycle.return.status.completed' },
    ],
  },
  AssetLoan: {
    steps: [
      { key: 'draft', translationKey: 'assets.lifecycle.loan.status.draft' },
      { key: 'pending', translationKey: 'assets.lifecycle.loan.status.pending', matches: ['rejected', 'cancelled'] },
      { key: 'approved', translationKey: 'assets.lifecycle.loan.status.approved' },
      { key: 'borrowed', translationKey: 'assets.lifecycle.loan.status.borrowed', matches: ['overdue'] },
      { key: 'returned', translationKey: 'assets.lifecycle.loan.status.returned' },
    ],
  },
  PurchaseRequest: {
    steps: [
      { key: 'draft', translationKey: 'assets.lifecycle.purchaseRequest.status.draft' },
      { key: 'submitted', translationKey: 'assets.lifecycle.purchaseRequest.status.submitted', matches: ['rejected', 'cancelled'] },
      { key: 'approved', translationKey: 'assets.lifecycle.purchaseRequest.status.approved' },
      { key: 'processing', translationKey: 'assets.lifecycle.purchaseRequest.status.processing' },
      { key: 'completed', translationKey: 'assets.lifecycle.purchaseRequest.status.completed' },
    ],
  },
  AssetReceipt: {
    steps: [
      { key: 'draft', translationKey: 'assets.lifecycle.assetReceipt.status.draft', matches: ['cancelled'] },
      { key: 'inspecting', translationKey: 'assets.lifecycle.assetReceipt.status.inspecting', matches: ['submitted', 'rejected'] },
      { key: 'passed', translationKey: 'assets.lifecycle.assetReceipt.status.passed' },
    ],
  },
  Maintenance: {
    steps: [
      { key: 'reported', translationKey: 'assets.lifecycle.maintenance.status.reported' },
      { key: 'assigned', translationKey: 'assets.lifecycle.maintenance.status.assigned' },
      { key: 'processing', translationKey: 'assets.lifecycle.maintenance.status.processing', matches: ['cancelled'] },
      { key: 'completed', translationKey: 'assets.lifecycle.maintenance.status.completed' },
    ],
  },
  DisposalRequest: {
    steps: [
      { key: 'draft', translationKey: 'assets.lifecycle.disposalRequest.status.draft' },
      { key: 'submitted', translationKey: 'assets.lifecycle.disposalRequest.status.submitted', matches: ['rejected', 'cancelled'] },
      { key: 'appraising', translationKey: 'assets.lifecycle.disposalRequest.status.appraising' },
      { key: 'approved', translationKey: 'assets.lifecycle.disposalRequest.status.approved' },
      { key: 'executing', translationKey: 'assets.lifecycle.disposalRequest.status.executing' },
      { key: 'completed', translationKey: 'assets.lifecycle.disposalRequest.status.completed' },
    ],
  },
}

const resolveStepLabel = (
  step: DocumentWorkflowProgressStepDefinition,
  t: (key: string) => string,
) => {
  if (step.translationKey) {
    const translated = t(step.translationKey)
    if (translated && translated !== step.translationKey) {
      return translated
    }
  }

  return step.key
}

const resolveDefinition = (
  objectCode: string,
  steps?: DocumentWorkflowProgressStepDefinition[] | null,
): DocumentWorkflowProgressDefinition | null => {
  if (Array.isArray(steps) && steps.length > 0) {
    return { steps }
  }
  return WORKFLOW_PROGRESS_REGISTRY[String(objectCode || '').trim()] || null
}

const resolveActiveStepKey = (
  definition: DocumentWorkflowProgressDefinition,
  currentStatus: string,
): string => {
  const normalizedStatus = String(currentStatus || '').trim()
  if (!normalizedStatus) return ''

  for (const step of definition.steps) {
    const matches = new Set([step.key, ...(Array.isArray(step.matches) ? step.matches : [])])
    if (matches.has(normalizedStatus)) {
      return step.key
    }
  }

  return normalizedStatus
}

export const resolveDocumentWorkflowProgress = ({
  objectCode,
  document,
  currentStatus,
  steps,
  t,
}: {
  objectCode: string
  document?: AggregateDocumentResponse | null
  currentStatus?: string | null
  steps?: DocumentWorkflowProgressStepDefinition[] | null
  t: (key: string) => string
}): ResolvedDocumentWorkflowProgress | null => {
  const definition = resolveDefinition(objectCode, steps)
  const effectiveStatus = String(currentStatus ?? document?.master?.status ?? '').trim()

  if (!definition || !effectiveStatus || definition.steps.length === 0) {
    return null
  }

  return {
    currentStatus: resolveActiveStepKey(definition, effectiveStatus),
    steps: definition.steps.map((step) => ({
      key: step.key,
      label: resolveStepLabel(step, t),
    })),
  }
}
