let xlsxModulePromise: Promise<typeof import('xlsx')> | null = null

export const loadXlsx = async () => {
  if (!xlsxModulePromise) {
    xlsxModulePromise = import('xlsx')
  }
  return xlsxModulePromise
}

export const prefetchXlsx = () => {
  void loadXlsx()
}
