export const executeDynamicListDeleteOperation = async ({
  runDelete,
  refresh,
  notifySuccess,
  notifyError,
  successMessage,
  fallbackErrorMessage,
}: {
  runDelete: () => Promise<void>
  refresh: () => void
  notifySuccess: (message: string) => void
  notifyError: (message: string) => void
  successMessage: string
  fallbackErrorMessage: string
}) => {
  try {
    await runDelete()
    notifySuccess(successMessage)
    refresh()
  } catch (error: any) {
    if (error !== 'cancel') {
      notifyError(error?.message || fallbackErrorMessage)
    }
  }
}
