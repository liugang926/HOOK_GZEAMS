import * as ElementPlusIcons from '@element-plus/icons-vue'

export const DEFAULT_ICON_LIBRARY = [
  'Menu',
  'Grid',
  'Folder',
  'FolderOpened',
  'Setting',
  'Document',
  'Files',
  'Monitor',
  'PieChart',
  'DataLine',
  'TrendCharts',
  'Box',
  'Goods',
  'Tickets',
  'Calendar',
  'User',
  'Wallet',
  'Bell',
  'Message',
  'ChatDotRound',
  'Brush',
]

export const iconComponents: Record<string, unknown> = ElementPlusIcons

export const resolveIcon = (iconName: string) => {
  const normalizedName = String(iconName || '').trim()
  return normalizedName ? iconComponents[normalizedName] || null : null
}

export const normalizeIconList = (payload: unknown) => {
  const source = Array.isArray((payload as { commonIcons?: unknown[] } | undefined)?.commonIcons)
    ? ((payload as { commonIcons: unknown[] }).commonIcons)
    : Array.isArray((payload as { common_icons?: unknown[] } | undefined)?.common_icons)
      ? ((payload as { common_icons: unknown[] }).common_icons)
      : []

  const allIcons = [
    ...DEFAULT_ICON_LIBRARY,
    ...source.map((icon) => String(icon || '').trim()).filter(Boolean),
    ...Object.keys(iconComponents),
  ]

  return Array.from(new Set(allIcons)).filter((iconName) => Boolean(resolveIcon(iconName)))
}
