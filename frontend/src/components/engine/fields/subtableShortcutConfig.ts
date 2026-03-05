export interface SubTableShortcutItem {
  combo: string
  descriptionKey: string
}

export interface SubTableShortcutBuilderOptions {
  commandCombo: (key: string) => string
  shiftCommandCombo: (key: string) => string
}

export const buildSubTableShortcutItems = (
  options: SubTableShortcutBuilderOptions
): SubTableShortcutItem[] => {
  const { commandCombo, shiftCommandCombo } = options

  return [
    { combo: 'F1', descriptionKey: 'common.hotkeys.subtable.toggleHelp' },
    { combo: 'Shift + F1', descriptionKey: 'common.hotkeys.subtable.togglePin' },
    { combo: 'Enter / Tab', descriptionKey: 'common.hotkeys.subtable.nextCell' },
    { combo: 'Shift + Tab', descriptionKey: 'common.hotkeys.subtable.previousCell' },
    { combo: 'Home / End', descriptionKey: 'common.hotkeys.subtable.rowBoundary' },
    { combo: 'Arrow Up / Arrow Down', descriptionKey: 'common.hotkeys.subtable.verticalMove' },
    { combo: 'Page Up / Page Down', descriptionKey: 'common.hotkeys.subtable.pageJump' },
    { combo: commandCombo('Enter'), descriptionKey: 'common.hotkeys.subtable.addRowBelow' },
    { combo: shiftCommandCombo('Enter'), descriptionKey: 'common.hotkeys.subtable.insertRowAbove' },
    { combo: commandCombo('Backspace'), descriptionKey: 'common.hotkeys.subtable.deleteRow' },
    { combo: commandCombo('D'), descriptionKey: 'common.hotkeys.subtable.duplicateBelow' },
    { combo: shiftCommandCombo('D'), descriptionKey: 'common.hotkeys.subtable.duplicateAbove' },
    { combo: commandCombo('S'), descriptionKey: 'common.hotkeys.subtable.requestSave' }
  ]
}
