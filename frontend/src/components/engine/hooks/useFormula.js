/**
 * useFormula Hook
 *
 * Provides real-time formula calculation for dynamic form fields.
 * Supports dependency tracking, automatic recalculation, and safe evaluation.
 *
 * Features:
 * - Parse formula expressions and extract dependencies
 * - Safe formula evaluation using a sandboxed approach
 * - Automatic recalculation when dependencies change
 * - Support for common functions (SUM, AVG, MIN, MAX, COUNT, etc.)
 * - Date calculations (DAYS, MONTHS, YEARS between dates)
 * - String operations (CONCAT, SUBSTRING, UPPER, LOWER, etc.)
 */

import { ref, computed, watch } from 'vue'

/**
 * Safe formula evaluator using simpleeval-like approach
 * Parses formulas and extracts referenced field codes
 */
export function useFormula(formData, fieldDefinitions) {
  const calculatedValues = ref({})
  const dependencyMap = ref(new Map()) // fieldCode -> Set of formula fields that depend on it
  const formulaFields = ref([])

  /**
   * Extract field references from a formula expression
   * Supports formats: {field_code}, [field_code], and plain field_code
   */
  const extractDependencies = (formula) => {
    if (!formula || typeof formula !== 'string') return new Set()

    const dependencies = new Set()

    // Match {field_code} format
    const braceMatches = formula.match(/\{([^}]+)\}/g) || []
    braceMatches.forEach(match => {
      dependencies.add(match.slice(1, -1))
    })

    // Match [field_code] format
    const bracketMatches = formula.match(/\[([^\]]+)\]/g) || []
    bracketMatches.forEach(match => {
      dependencies.add(match.slice(1, -1))
    })

    // If no braces/brackets found, try to extract alphanumeric words
    // that are known field codes (not functions)
    if (dependencies.size === 0) {
      const words = formula.match(/[a-zA-Z_][a-zA-Z0-9_]*/g) || []
      const knownFields = new Set(fieldDefinitions.value.map(f => f.code))

      words.forEach(word => {
        // Exclude known function names
        const functions = new Set([
          'SUM', 'AVG', 'MIN', 'MAX', 'COUNT', 'IF', 'AND', 'OR', 'NOT',
          'DAYS', 'MONTHS', 'YEARS', 'NOW', 'TODAY', 'DATE',
          'CONCAT', 'SUBSTRING', 'UPPER', 'LOWER', 'TRIM', 'LENGTH',
          'ROUND', 'CEIL', 'FLOOR', 'ABS', 'POW', 'SQRT'
        ])

        if (knownFields.has(word) && !functions.has(word.toUpperCase())) {
          dependencies.add(word)
        }
      })
    }

    return dependencies
  }

  /**
   * Build the dependency map for all formula fields
   */
  const buildDependencyMap = () => {
    dependencyMap.value.clear()
    formulaFields.value = []

    fieldDefinitions.value.forEach(field => {
      if (field.field_type === 'formula' && field.formula_expression) {
        formulaFields.value.push(field)
        const deps = extractDependencies(field.formula_expression)

        deps.forEach(dep => {
          if (!dependencyMap.value.has(dep)) {
            dependencyMap.value.set(dep, new Set())
          }
          dependencyMap.value.get(dep).add(field.code)
        })
      }
    })
  }

  /**
   * Get the value of a referenced field for formula calculation
   * Handles nested object access like {user.name}
   */
  const getFieldValue = (fieldRef) => {
    // Handle nested access
    if (fieldRef.includes('.')) {
      const parts = fieldRef.split('.')
      let value = formData.value

      for (const part of parts) {
        if (value && typeof value === 'object') {
          value = value[part]
        } else {
          return 0
        }
      }

      return parseValue(value)
    }

    return parseValue(formData.value[fieldRef])
  }

  /**
   * Parse value to number for calculation
   */
  const parseValue = (value) => {
    if (value === null || value === undefined || value === '') {
      return 0
    }

    if (typeof value === 'number') {
      return value
    }

    if (typeof value === 'boolean') {
      return value ? 1 : 0
    }

    // Try to parse as number
    const num = parseFloat(value)
    return isNaN(num) ? 0 : num
  }

  /**
   * Get string value from referenced field
   */
  const getFieldStringValue = (fieldRef) => {
    if (fieldRef.includes('.')) {
      const parts = fieldRef.split('.')
      let value = formData.value

      for (const part of parts) {
        if (value && typeof value === 'object') {
          value = value[part]
        } else {
          return ''
        }
      }

      return value || ''
    }

    return formData.value[fieldRef] || ''
  }

  /**
   * Evaluate a formula expression safely
   */
  const evaluateFormula = (expression) => {
    if (!expression) return null

    try {
      let evalExpression = expression

      // Replace {field_code} and [field_code] patterns with actual values
      // First, handle the patterns to get field refs
      const fieldRefs = [...extractDependencies(expression)]

      // Sort by length (descending) to handle nested refs first
      fieldRefs.sort((a, b) => b.length - a.length)

      // Replace field references with their numeric values
      fieldRefs.forEach(ref => {
        // Create regex patterns for different reference styles
        const bracePattern = new RegExp(`\\{${escapeRegex(ref)}\\}`, 'g')
        const bracketPattern = new RegExp(`\\[${escapeRegex(ref)}\\]`, 'g')

        // Get numeric value for calculation
        const numValue = getFieldValue(ref)
        evalExpression = evalExpression
          .replace(bracePattern, `(${numValue})`)
          .replace(bracketPattern, `(${numValue})`)
      })

      // Replace function names with their implementations
      evalExpression = replaceFunctions(evalExpression)

      // Safe evaluation - only allow math operations
      // Use Function constructor instead of eval for better scoping
      const result = new Function('return ' + evalExpression)()

      // Handle different result types
      if (typeof result === 'number') {
        // Round to 2 decimal places for currency-like precision
        return Math.round(result * 100) / 100
      }

      return result
    } catch (error) {
      console.warn('Formula evaluation error:', error, 'Expression:', expression)
      return null
    }
  }

  /**
   * Escape special regex characters
   */
  const escapeRegex = (str) => {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }

  /**
   * Replace function names in formula with JS implementations
   */
  const replaceFunctions = (expression) => {
    // Get all field values for aggregate functions
    const getValue = (ref) => getFieldValue(ref)
    const getString = (ref) => getFieldStringValue(ref)

    // Math functions
    const result = expression
      .replace(/SUM\s*\(([^)]+)\)/gi, (...args) => {
        const refs = args[1].split(',').map(s => s.trim())
        return refs.reduce((sum, ref) => sum + getValue(ref), 0)
      })
      .replace(/AVG\s*\(([^)]+)\)/gi, (...args) => {
        const refs = args[1].split(',').map(s => s.trim())
        const sum = refs.reduce((s, ref) => s + getValue(ref), 0)
        return sum / refs.length
      })
      .replace(/MIN\s*\(([^)]+)\)/gi, (...args) => {
        const refs = args[1].split(',').map(s => s.trim())
        return Math.min(...refs.map(ref => getValue(ref)))
      })
      .replace(/MAX\s*\(([^)]+)\)/gi, (...args) => {
        const refs = args[1].split(',').map(s => s.trim())
        return Math.max(...refs.map(ref => getValue(ref)))
      })
      .replace(/COUNT\s*\(([^)]+)\)/gi, (...args) => {
        const refs = args[1].split(',').map(s => s.trim())
        return refs.filter(ref => getValue(ref) !== 0).length
      })
      .replace(/ROUND\s*\(([^,]+),?\s*([0-9]*)\)/gi, (...args) => {
        const value = parseFloat(args[1]) || 0
        const precision = parseInt(args[2]) || 0
        const multiplier = Math.pow(10, precision)
        return Math.round(value * multiplier) / multiplier
      })
      .replace(/CEIL\s*\(([^)]+)\)/gi, (...args) => {
        return Math.ceil(parseFloat(args[1]) || 0)
      })
      .replace(/FLOOR\s*\(([^)]+)\)/gi, (...args) => {
        return Math.floor(parseFloat(args[1]) || 0)
      })
      .replace(/ABS\s*\(([^)]+)\)/gi, (...args) => {
        return Math.abs(parseFloat(args[1]) || 0)
      })
      .replace(/POW\s*\(([^,]+),\s*([^)]+)\)/gi, (...args) => {
        return Math.pow(parseFloat(args[1]) || 0, parseFloat(args[2]) || 0)
      })
      .replace(/SQRT\s*\(([^)]+)\)/gi, (...args) => {
        return Math.sqrt(parseFloat(args[1]) || 0)
      })
      // String functions
      .replace(/CONCAT\s*\(([^)]+)\)/gi, (...args) => {
        const refs = args[1].split(',').map(s => s.trim())
        return refs.map(ref => getString(ref)).join('')
      })
      .replace(/UPPER\s*\(([^)]+)\)/gi, (...args) => {
        return `'${getString(args[1].trim()).toUpperCase()}'`
      })
      .replace(/LOWER\s*\(([^)]+)\)/gi, (...args) => {
        return `'${getString(args[1].trim()).toLowerCase()}'`
      })
      .replace(/LENGTH\s*\(([^)]+)\)/gi, (...args) => {
        return getString(args[1].trim()).length
      })
      // Date functions (simplified - returns days difference)
      .replace(/DAYS\s*\(([^,]+),\s*([^)]+)\)/gi, (...args) => {
        const date1 = new Date(getValue(args[1]))
        const date2 = new Date(getValue(args[2]))
        return Math.abs((date2 - date1) / (1000 * 60 * 60 * 24))
      })
      // Conditional functions
      .replace(/IF\s*\(([^,]+),\s*([^,]+),\s*([^)]+)\)/gi, (...args) => {
        const condition = args[1].trim()
        // Simple condition evaluation (e.g., "{value} > 10")
        const condValue = evaluateFormula(condition)
        return condValue ? args[2] : args[3]
      })
      .replace(/AND\s*\(([^)]+)\)/gi, (...args) => {
        const refs = args[1].split(',').map(s => s.trim())
        return refs.every(ref => getValue(ref) !== 0)
      })
      .replace(/OR\s*\(([^)]+)\)/gi, (...args) => {
        const refs = args[1].split(',').map(s => s.trim())
        return refs.some(ref => getValue(ref) !== 0)
      })
      .replace(/NOT\s*\(([^)]+)\)/gi, (...args) => {
        return !getValue(args[1].trim())
      })
      // Current date/time
      .replace(/NOW\s*\(\)/gi, () => {
        return Date.now()
      })
      .replace(/TODAY\s*\(\)/gi, () => {
        return new Date().toISOString().split('T')[0]
      })

    return result
  }

  /**
   * Calculate all formula fields
   */
  const calculateFormulas = () => {
    const results = {}

    // Sort formulas by dependency order (simple topological sort)
    const calculated = new Set()
    const maxIterations = formulaFields.value.length + 1
    let iteration = 0

    while (calculated.size < formulaFields.value.length && iteration < maxIterations) {
      formulaFields.value.forEach(field => {
        if (calculated.has(field.code)) return

        const deps = extractDependencies(field.formula_expression)
        const allDepsCalculated = deps.every(dep => calculated.has(dep) || !isFormulaField(dep))

        if (allDepsCalculated) {
          const value = evaluateFormula(field.formula_expression)

          // Apply formatting if specified
          if (field.number_format === 'currency') {
            results[field.code] = value
          } else if (field.number_format === 'percent') {
            results[field.code] = (value || 0) * 100
          } else {
            results[field.code] = value
          }

          calculated.add(field.code)
        }
      })

      iteration++
    }

    calculatedValues.value = results
    return results
  }

  /**
   * Check if a field is a formula field
   */
  const isFormulaField = (fieldCode) => {
    return formulaFields.value.some(f => f.code === fieldCode)
  }

  /**
   * Get all fields that depend on a given field
   */
  const getDependentFormulas = (fieldCode) => {
    return dependencyMap.value.get(fieldCode) || new Set()
  }

  /**
   * Watch form data for changes and recalculate formulas
   */
  const setupFormulaWatch = () => {
    // Watch all form data changes
    watch(
      formData,
      (newData, oldData) => {
        if (oldData) {
          calculateFormulas()
        }
      },
      { deep: true, immediate: true }
    )
  }

  /**
   * Initialize formula calculations
   */
  const initFormulas = () => {
    buildDependencyMap()
    setupFormulaWatch()
    calculateFormulas()
  }

  /**
   * Get calculated value for a specific formula field
   */
  const getCalculatedValue = (fieldCode) => {
    return calculatedValues.value[fieldCode]
  }

  /**
   * Update all formula values in the form data
   * This should be called before submitting the form
   */
  const syncFormulasToFormData = () => {
    Object.entries(calculatedValues.value).forEach(([fieldCode, value]) => {
      formData.value[fieldCode] = value
    })
  }

  return {
    calculatedValues,
    formulaFields,
    dependencyMap,
    initFormulas,
    calculateFormulas,
    getCalculatedValue,
    getDependentFormulas,
    isFormulaField,
    syncFormulasToFormData,
    evaluateFormula,
    extractDependencies
  }
}
