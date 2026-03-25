import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'

export interface DynamicDetailResolvedPermissions {
  view: boolean
  add: boolean
  change: boolean
  delete: boolean
}

const fallbackPermissions: DynamicDetailResolvedPermissions = {
  view: true,
  add: true,
  change: true,
  delete: true,
}

export const resolveDynamicDetailEffectivePermissions = (
  runtimePermissions?: RuntimePermissions | null,
  metadataPermissions?: Partial<DynamicDetailResolvedPermissions> | null,
): DynamicDetailResolvedPermissions => {
  if (runtimePermissions) {
    return runtimePermissions
  }

  if (metadataPermissions) {
    return {
      view: metadataPermissions.view !== false,
      add: metadataPermissions.add !== false,
      change: metadataPermissions.change !== false,
      delete: metadataPermissions.delete !== false,
    }
  }

  return fallbackPermissions
}

export const shouldShowDynamicDetailEnhancements = ({
  isLifecycle,
  hasNavigationSection,
  hasTimelineConfig,
}: {
  isLifecycle: boolean
  hasNavigationSection: boolean
  hasTimelineConfig: boolean
}) => {
  return isLifecycle || hasNavigationSection || hasTimelineConfig
}
