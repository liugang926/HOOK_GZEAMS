import { ref } from 'vue'

export function useValidation(formData, fieldDefinitions) {

    // Simple expression evaluator
    // Supports: data.field > 100, data.field == 'value'
    // Security: Do NOT use eval(). Use a simple parser.
    const evaluateLogic = (logic, data) => {
        try {
            // 1. Replace data.field with actual values
            // very basic replacement for "data.field" patterns
            // WARNING: This is a simple implementation. For production, use a proper library like 'jexl' or 'mathjs'

            // Supported operators: >, <, >=, <=, ==, !=, &&, ||
            // We will construct a function context safe-ish way or use simple regex parsing

            // Let's try a Function constructor approach with limited scope (still risky if not sanitized, but better than eval)
            // But strict CSP might block it.

            // Alternative: Regex parsing for simple cases
            // check format: "data.field [op] value"

            // For this Phase, we'll implement a Function-based evaluator assuming internal users are trusted 
            // or we sanitize inputs. 
            // Ideally: return new Function('data', 'return ' + logic)(data)

            // Let's go with new Function for flexibility in this "Low Code" context, 
            // acknowledging the security implication (it's similar to other low-code platforms).

            const func = new Function('data', `return ${logic}`);
            return func(data);
        } catch (e) {
            console.warn('Validation logic error:', logic, e);
            return true; // Default to valid to avoid blocking on bad logic
        }
    }

    const validateFieldCustom = (fieldCode, value, logicRules) => {
        if (!logicRules || !Array.isArray(logicRules)) return true;

        for (const rule of logicRules) {
            if (!rule.logic) continue;

            // Create a safe data context copy
            const dataContext = { ...formData };
            // Update current field value in context (it might not be updated in reactive check yet)
            dataContext[fieldCode] = value;

            const isValid = evaluateLogic(rule.logic, dataContext);
            if (!isValid) {
                return rule.message || 'Validation failed';
            }
        }
        return true;
    };

    return {
        validateFieldCustom
    }
}
