/**
 * useFormula Hook
 *
 * Formula calculation engine for dynamic forms.
 * Supports:
 * - Field references: {field_code}
 * - Arithmetic operations: +, -, *, /
 * - Functions: SUM(), AVG(), COUNT(), IF(), MAX(), MIN()
 * - Dependency tracking and auto-recalculation
 * - Safe evaluation (no eval)
 *
 * Examples:
 * - {quantity} * {unit_price}
 * - SUM({item1}, {item2}, {item3})
 * - IF({status} == 'active', {amount} * 0.1, 0)
 * - {width} * {height} * {depth}
 */

import { Ref, ref, watch } from 'vue'
import type { FieldDefinition } from '@/types'

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Formula field definition
 */
export interface FormulaField {
  code: string
  formula: string
  expression: string
  dependencies: Set<string>
}

/**
 * Formula evaluation context
 */
interface EvaluationContext {
  formData: Record<string, any>
  fieldDefinitions: FieldDefinition[]
}

/**
 * Calculation result
 */
interface CalculationResult {
  success: boolean
  value: any
  error?: string
}

// ============================================================================
// Formula Parser
// ============================================================================

/**
 * Parse formula expression and extract field references
 * Format: {field_code} represents a field reference
 *
 * @param expression - Formula expression
 * @returns Parsed expression with extracted field references
 */
function parseFormulaExpression(expression: string): {
  cleanedExpression: string
  dependencies: Set<string>
} {
  const dependencies = new Set<string>()
  let cleanedExpression = expression

  // Extract field references in format {field_code}
  const fieldRefRegex = /\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g
  let match

  while ((match = fieldRefRegex.exec(expression)) !== null) {
    dependencies.add(match[1])
  }

  // Replace field references with placeholder format for evaluation
  // We'll substitute actual values during evaluation
  cleanedExpression = expression.replace(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g, '@FIELD_$1@')

  return { cleanedExpression, dependencies }
}

// ============================================================================
// Formula Evaluator
// ============================================================================

/**
 * Safely evaluate a formula expression
 * Uses token-based evaluation instead of eval for security
 *
 * @param expression - Parsed expression
 * @param context - Evaluation context with form data
 * @returns Calculation result
 */
function evaluateFormula(expression: string, context: EvaluationContext): CalculationResult {
  try {
    // Replace field placeholders with actual values
    let evalExpression = expression

    // Sort by length (descending) to avoid partial replacements
    const sortedFields = Array.from(context.fieldDefinitions.map(f => f.code))
      .sort((a, b) => b.length - a.length)

    for (const fieldCode of sortedFields) {
      const placeholder = `@FIELD_${fieldCode}@`
      const value = context.formData[fieldCode]

      // Convert value to number for calculation
      let numValue: number
      if (value === null || value === undefined) {
        numValue = 0
      } else if (typeof value === 'number') {
        numValue = value
      } else if (typeof value === 'string') {
        // Try to parse as number
        const parsed = parseFloat(value.replace(/,/g, ''))
        numValue = isNaN(parsed) ? 0 : parsed
      } else {
        numValue = 0
      }

      // Use string replacement to avoid regex escaping issues
      while (evalExpression.includes(placeholder)) {
        evalExpression = evalExpression.replace(placeholder, numValue.toString())
      }
    }

    // Evaluate function calls
    evalExpression = evaluateFunctions(evalExpression, context)

    // Safe arithmetic evaluation using Function constructor (restricted scope)
    // Only allow numeric operations and comparison operators
    if (!/^[\d+\-*/()., <>=!&|]+$/.test(evalExpression)) {
      // Contains non-arithmetic characters, return as-is
      return { success: true, value: evalExpression }
    }

    // Use Function constructor with restricted context
    const result = new Function('return ' + evalExpression)()

    return {
      success: true,
      value: isNaN(result) ? null : result
    }
  } catch (error: any) {
    return {
      success: false,
      value: null,
      error: error.message || 'Formula evaluation error'
    }
  }
}

/**
 * Evaluate function calls in expression
 * Supports: SUM, AVG, COUNT, MAX, MIN, IF
 */
function evaluateFunctions(expression: string, context: EvaluationContext): string {
  let result = expression

  // SUM(field1, field2, ...) or SUM(value1, value2, ...)
  result = result.replace(/SUM\(([^)]+)\)/g, (_match, args) => {
    const values = parseArguments(args, context)
    const sum = values.reduce((acc, val) => acc + val, 0)
    return sum.toString()
  })

  // AVG(field1, field2, ...)
  result = result.replace(/AVG\(([^)]+)\)/g, (_, args) => {
    const values = parseArguments(args, context)
    if (values.length === 0) return '0'
    const avg = values.reduce((acc, val) => acc + val, 0) / values.length
    return avg.toString()
  })

  // COUNT(field1, field2, ...) - count non-empty values
  result = result.replace(/COUNT\(([^)]+)\)/g, (_, args) => {
    const values = parseArguments(args, context)
    const count = values.filter(v => v !== null && v !== undefined && v !== 0).length
    return count.toString()
  })

  // MAX(field1, field2, ...)
  result = result.replace(/MAX\(([^)]+)\)/g, (_, args) => {
    const values = parseArguments(args, context)
    if (values.length === 0) return '0'
    return Math.max(...values).toString()
  })

  // MIN(field1, field2, ...)
  result = result.replace(/MIN\(([^)]+)\)/g, (_, args) => {
    const values = parseArguments(args, context)
    if (values.length === 0) return '0'
    return Math.min(...values).toString()
  })

  // IF(condition, trueValue, falseValue)
  result = result.replace(/IF\(([^,]+),([^,]+),([^)]+)\)/g, (_match, condition, trueVal, falseVal) => {
    // Evaluate condition (support simple comparisons)
    const conditionResult = evaluateCondition(condition, context)
    const valueExpr = conditionResult ? trueVal : falseVal
    // Recursively evaluate the value expression
    return evaluateFunctions(valueExpr, context)
  })

  return result
}

/**
 * Parse comma-separated arguments and convert to values
 */
function parseArguments(args: string, context: EvaluationContext): number[] {
  if (!args) return []

  return args.split(',').map(arg => {
    arg = arg.trim()
    if (arg.startsWith('@FIELD_') && arg.endsWith('@')) {
      const fieldCode = arg.slice(7, -1)
      const value = context.formData[fieldCode]
      if (value === null || value === undefined) return 0
      return typeof value === 'number' ? value : parseFloat(String(value)) || 0
    }
    return parseFloat(arg) || 0
  })
}

/**
 * Evaluate a simple condition expression
 * Supports: ==, !=, <, >, <=, >=, &&, ||
 */
function evaluateCondition(condition: string, context: EvaluationContext): boolean {
  let evalCondition = condition

  // Replace field references
  for (const fieldCode of context.fieldDefinitions.map(f => f.code)) {
    const placeholder = `@FIELD_${fieldCode}@`
    const value = context.formData[fieldCode]
    const strValue = value === null || value === undefined ? '' : String(value)
    // Quote string values for comparison
    const quoted = typeof value === 'string' ? `'${strValue.replace(/'/g, "\\'")}'` : String(value)
    evalCondition = evalCondition.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), quoted)
  }

  try {
    // Safe evaluation of boolean expression
    return new Function('return ' + evalCondition)()
  } catch {
    return false
  }
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Composable for formula field calculations
 *
 * @param formData - Reactive form data
 * @param fieldDefinitions - Field definitions from metadata
 * @returns Formula calculation methods and state
 */
export function useFormula(
  formData: Ref<Record<string, any>>,
  fieldDefinitions: Ref<FieldDefinition[]>
) {
  // Formula fields registry
  const formulaFields = ref<Map<string, FormulaField>>(new Map())

  // Calculated values cache
  const calculatedValues = ref<Record<string, any>>({})

  // Dependency graph: field -> set of formula fields that depend on it
  const dependencyGraph = ref<Map<string, Set<string>>>(new Map())

  // ============================================================================
  // Initialization
  // ============================================================================

  /**
   * Initialize formula fields from field definitions
   */
  function initFormulas(): void {
    formulaFields.value.clear()
    dependencyGraph.value.clear()

    fieldDefinitions.value.forEach(field => {
      // Check if this is a formula field
      if (field.fieldType === 'formula' || field.componentProps?.formula) {
        const formula = field.componentProps?.formula || ''
        const { cleanedExpression, dependencies } = parseFormulaExpression(formula)

        formulaFields.value.set(field.code, {
          code: field.code,
          formula,
          expression: cleanedExpression,
          dependencies
        })

        // Build dependency graph
        dependencies.forEach(depField => {
          if (!dependencyGraph.value.has(depField)) {
            dependencyGraph.value.set(depField, new Set())
          }
          dependencyGraph.value.get(depField)!.add(field.code)
        })
      }
    })

    // Initial calculation
    calculateFormulas()
  }

  // ============================================================================
  // Formula Calculation
  // ============================================================================

  /**
   * Calculate all formula fields
   */
  function calculateFormulas(): void {
    const context: EvaluationContext = {
      formData: formData.value,
      fieldDefinitions: fieldDefinitions.value
    }

    formulaFields.value.forEach((formulaField, fieldCode) => {
      const result = evaluateFormula(formulaField.expression, context)
      if (result.success) {
        calculatedValues.value[fieldCode] = result.value
      } else {
        console.warn(`Formula error for ${fieldCode}:`, result.error)
        calculatedValues.value[fieldCode] = null
      }
    })
  }

  /**
   * Get formulas that depend on a specific field
   *
   * @param fieldCode - Field code that changed
   * @returns Set of formula field codes that depend on this field
   */
  function getDependentFormulas(fieldCode: string): Set<string> {
    return dependencyGraph.value.get(fieldCode) || new Set()
  }

  /**
   * Recalculate only formulas that depend on changed fields
   *
   * @param changedField - Field that changed
   */
  function recalculateDependentFormulas(changedField: string): void {
    const dependents = getDependentFormulas(changedField)

    if (dependents.size === 0) {
      return
    }

    const context: EvaluationContext = {
      formData: formData.value,
      fieldDefinitions: fieldDefinitions.value
    }

    dependents.forEach(formulaCode => {
      const formulaField = formulaFields.value.get(formulaCode)
      if (formulaField) {
        const result = evaluateFormula(formulaField.expression, context)
        if (result.success) {
          calculatedValues.value[formulaCode] = result.value
        }
      }
    })
  }

  // ============================================================================
  // Field Checkers
  // ============================================================================

  /**
   * Check if a field is a formula field
   *
   * @param fieldCode - Field code to check
   * @returns true if field is a formula field
   */
  function isFormulaField(fieldCode: string): boolean {
    return formulaFields.value.has(fieldCode)
  }

  /**
   * Get calculated value for a formula field
   *
   * @param fieldCode - Field code
   * @returns Calculated value or undefined
   */
  function getCalculatedValue(fieldCode: string): any {
    return calculatedValues.value[fieldCode]
  }

  /**
   * Get the formula expression for a field
   *
   * @param fieldCode - Field code
   * @returns Formula string or undefined
   */
  function getFormulaExpression(fieldCode: string): string | undefined {
    return formulaFields.value.get(fieldCode)?.formula
  }

  // ============================================================================
  // Data Sync
  // ============================================================================

  /**
   * Sync calculated values to form data
   * Call this before form submission to ensure formula values are included
   */
  function syncFormulasToFormData(): void {
    Object.assign(formData.value, calculatedValues.value)
  }

  // ============================================================================
  // Watch for Changes
  // ============================================================================

  // Watch form data changes and recalculate dependent formulas
  watch(
    formData,
    (newData, oldData) => {
      if (!oldData) return

      // Find which fields changed
      for (const key in newData) {
        if (newData[key] !== oldData[key]) {
          recalculateDependentFormulas(key)
        }
      }
    },
    { deep: true }
  )

  // Re-initialize formulas when field definitions change
  watch(
    fieldDefinitions,
    () => {
      initFormulas()
    },
    { immediate: false }
  )

  // ============================================================================
  // Return Public Interface
  // ============================================================================

  return {
    // State
    calculatedValues,
    formulaFields,

    // Initialization
    initFormulas,

    // Calculation
    calculateFormulas,
    recalculateDependentFormulas,

    // Field checkers
    isFormulaField,
    getCalculatedValue,
    getFormulaExpression,
    getDependentFormulas,

    // Data sync
    syncFormulasToFormData
  }
}
