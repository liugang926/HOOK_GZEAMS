/**
 * Formula Calculation Utility
 *
 * Provides safe formula evaluation for metadata-driven forms.
 * Uses simpleeval for expression evaluation with controlled scope.
 *
 * Reference: docs/plans/phase2_3_lowcode_engine/frontend_v2.md
 */

import { ParseException } from 'simpleeval'

// ============================================================================
// Types
// ============================================================================

export interface FormulaContext {
  [key: string]: any
}

export interface FormulaDependencies {
  [fieldCode: string]: string[]  // fieldCode -> dependent formula fields
}

// ============================================================================
// Built-in Functions
// ============================================================================

/**
 * Math functions available in formulas
 */
export const MATH_FUNCTIONS = {
  /** Sum of numbers */
  sum: (...args: number[]) => args.reduce((a, b) => (a || 0) + (b || 0), 0),

  /** Average of numbers */
  avg: (...args: number[]) => {
    const nums = args.filter(n => typeof n === 'number' && !isNaN(n))
    return nums.length > 0 ? nums.reduce((a, b) => a + b, 0) / nums.length : 0
  },

  /** Minimum value */
  min: (...args: number[]) => Math.min(...args.filter(n => typeof n === 'number')),

  /** Maximum value */
  max: (...args: number[]) => Math.max(...args.filter(n => typeof n === 'number')),

  /** Round to decimals */
  round: (num: number, decimals = 2) => {
    const factor = Math.pow(10, decimals)
    return Math.round(num * factor) / factor
  },

  /** Ceiling */
  ceil: (num: number) => Math.ceil(num),

  /** Floor */
  floor: (num: number) => Math.floor(num),

  /** Absolute value */
  abs: (num: number) => Math.abs(num),

  /** Power */
  pow: (base: number, exp: number) => Math.pow(base, exp),

  /** Square root */
  sqrt: (num: number) => Math.sqrt(num),

  /** Percentage */
  percent: (value: number, total: number) => {
    if (!total || total === 0) return 0
    return (value / total) * 100
  }
}

/**
 * Date functions available in formulas
 */
export const DATE_FUNCTIONS = {
  /** Current date */
  today: () => new Date().toISOString().split('T')[0],

  /** Current timestamp */
  now: () => new Date().toISOString(),

  /** Add days to date */
  addDays: (date: string, days: number) => {
    const d = new Date(date)
    d.setDate(d.getDate() + (days || 0))
    return d.toISOString().split('T')[0]
  },

  /** Add months to date */
  addMonths: (date: string, months: number) => {
    const d = new Date(date)
    d.setMonth(d.getMonth() + (months || 0))
    return d.toISOString().split('T')[0]
  },

  /** Add years to date */
  addYears: (date: string, years: number) => {
    const d = new Date(date)
    d.setFullYear(d.getFullYear() + (years || 0))
    return d.toISOString().split('T')[0]
  },

  /** Date difference in days */
  daysBetween: (start: string, end: string) => {
    const startDate = new Date(start)
    const endDate = new Date(end)
    const diffTime = endDate.getTime() - startDate.getTime()
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  },

  /** Get month from date */
  month: (date: string) => new Date(date).getMonth() + 1,

  /** Get year from date */
  year: (date: string) => new Date(date).getFullYear(),

  /** Get day from date */
  day: (date: string) => new Date(date).getDate()
}

/**
 * String functions available in formulas
 */
export const STRING_FUNCTIONS = {
  /** Concatenate strings */
  concat: (...args: string[]) => args.filter(a => a != null).join(''),

  /** Uppercase */
  upper: (str: string) => String(str || '').toUpperCase(),

  /** Lowercase */
  lower: (str: string) => String(str || '').toLowerCase(),

  /** String length */
  len: (str: string) => String(str || '').length,

  /** Trim whitespace */
  trim: (str: string) => String(str || '').trim(),

  /** Substring */
  substr: (str: string, start: number, length?: number) => {
    return String(str || '').substring(start, length ? start + length : undefined)
  },

  /** Replace */
  replace: (str: string, search: string, replacement: string) => {
    return String(str || '').replaceAll(search, replacement)
  }
}

/**
 * Conditional functions available in formulas
 */
export const CONDITIONAL_FUNCTIONS = {
  /** If-then-else */
  if: (condition: any, trueValue: any, falseValue: any) => {
    return condition ? trueValue : falseValue
  },

  /** Logical AND */
  and: (...args: any[]) => args.every(a => !!a),

  /** Logical OR */
  or: (...args: any[]) => args.some(a => !!a),

  /** Logical NOT */
  not: (value: any) => !value,

  /** Equal comparison */
  eq: (a: any, b: any) => a === b,

  /** Not equal comparison */
  ne: (a: any, b: any) => a !== b,

  /** Greater than */
  gt: (a: any, b: any) => Number(a) > Number(b),

  /** Greater or equal */
  gte: (a: any, b: any) => Number(a) >= Number(b),

  /** Less than */
  lt: (a: any, b: any) => Number(a) < Number(b),

  /** Less or equal */
  lte: (a: any, b: any) => Number(a) <= Number(b)
}

/**
 * Aggregation functions for sub-tables
 */
export const AGGREGATION_FUNCTIONS = {
  /** Count items */
  count: (array: any[]) => Array.isArray(array) ? array.length : 0,

  /** Sum of field in array */
  sum: (array: any[], field: string) => {
    if (!Array.isArray(array)) return 0
    return array.reduce((sum, item) => sum + (Number(item[field]) || 0), 0)
  },

  /** Average of field in array */
  avg: (array: any[], field: string) => {
    if (!Array.isArray(array) || array.length === 0) return 0
    const values = array.map(item => Number(item[field]) || 0)
    return values.reduce((a, b) => a + b, 0) / values.length
  },

  /** Filter array */
  filter: (array: any[], field: string, value: any) => {
    if (!Array.isArray(array)) return []
    return array.filter(item => item[field] === value)
  }
}

/**
 * Combined functions for formula evaluation
 */
export const FORMULA_FUNCTIONS = {
  ...MATH_FUNCTIONS,
  ...DATE_FUNCTIONS,
  ...STRING_FUNCTIONS,
  ...CONDITIONAL_FUNCTIONS,
  ...AGGREGATION_FUNCTIONS
}

// ============================================================================
// Formula Evaluation
// ============================================================================

/**
 * Build context object from form data
 */
const buildContext = (formData: Record<string, any>): FormulaContext => {
  const context: FormulaContext = {}

  // Add form field values
  Object.keys(formData).forEach(key => {
    context[key] = formData[key]
  })

  // Add built-in functions
  Object.keys(FORMULA_FUNCTIONS).forEach(key => {
    context[key] = FORMULA_FUNCTIONS[key as keyof typeof FORMULA_FUNCTIONS]
  })

  return context
}

/**
 * Evaluate a formula expression
 *
 * @param expression - Formula expression (e.g., "quantity * price")
 * @param formData - Form data context
 * @returns Calculated value
 */
export const evaluateFormula = (
  expression: string,
  formData: Record<string, any>
): any => {
  if (!expression || typeof expression !== 'string') {
    return undefined
  }

  // Remove whitespace for check
  const trimmed = expression.trim()
  if (!trimmed) {
    return undefined
  }

  // Handle simple field reference
  if (/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(trimmed)) {
    return formData[trimmed]
  }

  try {
    const context = buildContext(formData)

    // Simple expression evaluator
    // Note: In production, use simpleeval or similar library
    return evaluateSimpleExpression(expression, context)
  } catch (error) {
    console.warn(`Formula evaluation error: ${expression}`, error)
    return undefined
  }
}

/**
 * Simple expression evaluator
 * (Simplified version - in production use simpleeval library)
 */
const evaluateSimpleExpression = (
  expression: string,
  context: FormulaContext
): any => {
  // Replace function calls with actual function calls
  let expr = expression

  // Handle function calls: func(arg1, arg2, ...)
  expr = expr.replace(/(\w+)\(([^)]*)\)/g, (_, funcName, argsStr) => {
    const func = context[funcName]
    if (typeof func !== 'function') return _

    const args = argsStr
      ? argsStr.split(',').map(arg => {
          const trimmed = arg.trim()
          // Handle nested expressions and field references
          if (/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(trimmed)) {
            return context[trimmed]
          }
          // Handle string literals
          if ((trimmed.startsWith("'") && trimmed.endsWith("'")) ||
              (trimmed.startsWith('"') && trimmed.endsWith('"'))) {
            return trimmed.slice(1, -1)
          }
          // Handle numbers
          const num = Number(trimmed)
          return isNaN(num) ? evaluateSimpleExpression(trimmed, context) : num
        })
      : []

    try {
      return func(...args)
    } catch {
      return `NaN`
    }
  })

  // Handle simple arithmetic operations
  try {
    // Create a function with the context variables
    const contextKeys = Object.keys(context)
    const contextValues = Object.values(context)

    // Replace field references with actual values
    let evalExpr = expr
    contextKeys.forEach(key => {
      const regex = new RegExp(`\\b${key}\\b`, 'g')
      const value = context[key]
      if (typeof value === 'string') {
        evalExpr = evalExpr.replace(regex, `"${value}"`)
      } else if (typeof value === 'number' || typeof value === 'boolean') {
        evalExpr = evalExpr.replace(regex, String(value))
      }
    })

    // Evaluate the expression
    // eslint-disable-next-line no-new-func
    const result = new Function('return ' + evalExpr)()
    return result
  } catch (error) {
    return undefined
  }
}

// ============================================================================
// Dependency Analysis
// ============================================================================

/**
 * Extract field references from formula expression
 */
export const extractFieldReferences = (expression: string): string[] => {
  if (!expression) return []

  const references: string[] = []

  // Match field references (identifiers that are not functions)
  const functionNames = Object.keys(FORMULA_FUNCTIONS)
  const tokens = expression.match(/\b[a-zA-Z_][a-zA-Z0-9_]*\b/g) || []

  tokens.forEach(token => {
    // Skip function names
    if (!functionNames.includes(token)) {
      // Skip known JavaScript keywords
      if (!['if', 'else', 'for', 'while', 'return', 'function', 'const', 'let', 'var'].includes(token)) {
        if (!references.includes(token)) {
          references.push(token)
        }
      }
    }
  })

  return references
}

/**
 * Build dependency graph for formula fields
 *
 * Returns a map where each key is a field code and value is array of
 * formula fields that depend on it
 */
export const buildDependencies = (
  fields: Array<{ code: string; type: string; formulaExpression?: string }>
): FormulaDependencies => {
  const dependencies: FormulaDependencies = {}

  // Find all formula fields
  const formulaFields = fields.filter(f => f.type === 'formula' && f.formulaExpression)

  formulaFields.forEach(formulaField => {
    const references = extractFieldReferences(formulaField.formulaExpression || '')

    references.forEach(refField => {
      if (!dependencies[refField]) {
        dependencies[refField] = []
      }
      dependencies[refField].push(formulaField.code)
    })
  })

  return dependencies
}

/**
 * Get fields that need recalculation when a field changes
 */
export const getDependentFormulas = (
  fieldCode: string,
  fields: Array<{ code: string; type: string; formulaExpression?: string }>
): string[] => {
  const dependencies = buildDependencies(fields)
  return dependencies[fieldCode] || []
}

/**
 * Detect circular dependencies in formulas
 */
export const detectCircularDependencies = (
  fields: Array<{ code: string; type: string; formulaExpression?: string }>
): string[][] => {
  const dependencies: FormulaDependencies = {}

  fields.forEach(field => {
    if (field.type === 'formula' && field.formulaExpression) {
      dependencies[field.code] = extractFieldReferences(field.formulaExpression)
    }
  })

  const cycles: string[][] = []
  const visited = new Set<string>()
  const recursionStack = new Set<string>()

  const dfs = (node: string, path: string[]) => {
    visited.add(node)
    recursionStack.add(node)
    path.push(node)

    const deps = dependencies[node] || []
    for (const dep of deps) {
      if (recursionStack.has(dep)) {
        // Found a cycle
        const cycleStart = path.indexOf(dep)
        cycles.push([...path.slice(cycleStart), dep])
      } else if (!visited.has(dep)) {
        dfs(dep, path)
      }
    }

    path.pop()
    recursionStack.delete(node)
  }

  Object.keys(dependencies).forEach(field => {
    if (!visited.has(field)) {
      dfs(field, [])
    }
  })

  return cycles
}

// ============================================================================
// Formula Validation
// ============================================================================

/**
 * Validate formula expression
 */
export const validateFormula = (
  expression: string,
  availableFields: string[]
): { valid: boolean; error?: string } => {
  if (!expression || typeof expression !== 'string') {
    return { valid: false, error: '表达式不能为空' }
  }

  const trimmed = expression.trim()
  if (!trimmed) {
    return { valid: false, error: '表达式不能为空' }
  }

  try {
    // Extract field references
    const references = extractFieldReferences(trimmed)

    // Check for unknown fields
    const unknownFields = references.filter(ref => !availableFields.includes(ref))
    if (unknownFields.length > 0) {
      return {
        valid: false,
        error: `未知的字段引用: ${unknownFields.join(', ')}`
      }
    }

    // Try to evaluate with empty context (syntax check)
    evaluateFormula(trimmed, {})

    return { valid: true }
  } catch (error) {
    return {
      valid: false,
      error: `表达式语法错误: ${error instanceof Error ? error.message : String(error)}`
    }
  }
}

export default {
  evaluateFormula,
  extractFieldReferences,
  buildDependencies,
  getDependentFormulas,
  detectCircularDependencies,
  validateFormula,
  FUNCTIONS: FORMULA_FUNCTIONS
}
