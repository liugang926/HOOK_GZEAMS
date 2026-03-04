/**
 * Business Rules API Client
 * Provides functions for interacting with the business rules API
 */

import request from '@/utils/request'
import { toData, toPaginated } from '@/api/contract'

const BASE_URL = '/system/rules'

export interface BusinessRule {
    id: string
    business_object: string
    business_object_code?: string
    business_object_name?: string
    rule_code: string
    rule_name: string
    description?: string
    rule_type: 'validation' | 'visibility' | 'computed' | 'linkage' | 'trigger'
    rule_type_display?: string
    priority: number
    is_active: boolean
    condition: Record<string, any>
    action: Record<string, any>
    target_field?: string
    trigger_events: string[]
    error_message?: string
    error_message_en?: string
    created_at?: string
    updated_at?: string
}

export interface RuleExecution {
    id: string
    rule: string
    rule_code: string
    rule_name: string
    target_record_id: string
    target_record_type: string
    trigger_event: string
    input_data: Record<string, any>
    condition_result: boolean
    action_executed: boolean
    execution_result: Record<string, any>
    executed_at: string
    execution_time_ms: number
    has_error: boolean
    error_message?: string
}

export interface RuleEvaluationRequest {
    record: Record<string, any>
    event?: 'create' | 'update' | 'submit' | 'approve'
}

export interface RuleEvaluationResult {
    is_valid: boolean
    errors: Array<{
        field?: string
        message: string
        rule_code: string
    }>
    visibility: Record<string, boolean>
    computed_values: Record<string, any>
    linkage_updates: Record<string, any>
}

/**
 * Composable for business rules API
 */
export function useBusinessRulesApi() {
    /**
     * Get all rules for a business object
     */
    async function getRulesByObject(objectCode: string): Promise<BusinessRule[]> {
        const response = await request({
            url: `${BASE_URL}/by-object/${objectCode}/`,
            method: 'get'
        })
        return toPaginated<BusinessRule>(response).results
    }

    /**
     * Get a single rule by ID
     */
    async function getRuleById(id: string): Promise<BusinessRule> {
        const response = await request({
            url: `${BASE_URL}/${id}/`,
            method: 'get'
        })
        return toData<BusinessRule>(response)
    }

    /**
     * Create a new rule
     */
    async function createRule(data: Partial<BusinessRule> & { business_object_code: string }): Promise<BusinessRule> {
        const response = await request({
            url: `${BASE_URL}/`,
            method: 'post',
            data
        })
        return toData<BusinessRule>(response)
    }

    /**
     * Update an existing rule
     */
    async function updateRule(id: string, data: Partial<BusinessRule>): Promise<BusinessRule> {
        const response = await request({
            url: `${BASE_URL}/${id}/`,
            method: 'patch',
            data
        })
        return toData<BusinessRule>(response)
    }

    /**
     * Delete a rule
     */
    async function deleteRule(id: string): Promise<void> {
        await request({
            url: `${BASE_URL}/${id}/`,
            method: 'delete'
        })
    }

    /**
     * Evaluate all rules for a business object
     */
    async function evaluateRules(
        objectCode: string,
        payload: RuleEvaluationRequest
    ): Promise<RuleEvaluationResult> {
        const response = await request({
            url: `${BASE_URL}/evaluate/${objectCode}/`,
            method: 'post',
            data: payload
        })
        return toData<RuleEvaluationResult>(response)
    }

    /**
     * Evaluate a single rule (for testing)
     */
    async function evaluateRule(
        objectCode: string,
        payload: RuleEvaluationRequest
    ): Promise<RuleEvaluationResult> {
        return evaluateRules(objectCode, payload)
    }

    /**
     * Validate only (run validation rules)
     */
    async function validateOnly(
        objectCode: string,
        payload: RuleEvaluationRequest
    ): Promise<{ is_valid: boolean; errors: any[] }> {
        const response = await request({
            url: `${BASE_URL}/validate/${objectCode}/`,
            method: 'post',
            data: payload
        })
        return toData<{ is_valid: boolean; errors: any[] }>(response)
    }

    /**
     * Get visibility states for fields
     */
    async function getVisibility(
        objectCode: string,
        payload: RuleEvaluationRequest
    ): Promise<Record<string, boolean>> {
        const response = await request({
            url: `${BASE_URL}/visibility/${objectCode}/`,
            method: 'post',
            data: payload
        })
        return toData<Record<string, boolean>>(response)
    }

    /**
     * Get rule execution logs
     */
    async function getExecutionLogs(params?: {
        rule?: string
        target_record_id?: string
        trigger_event?: string
        has_error?: boolean
    }): Promise<RuleExecution[]> {
        const response = await request({
            url: '/system/rule-executions/',
            method: 'get',
            params
        })
        return toPaginated<RuleExecution>(response).results
    }

    /**
     * Get execution logs for a specific record
     */
    async function getExecutionsByRecord(recordId: string): Promise<RuleExecution[]> {
        const response = await request({
            url: `/system/rule-executions/by-record/${recordId}/`,
            method: 'get'
        })
        return toPaginated<RuleExecution>(response).results
    }

    return {
        getRulesByObject,
        getRuleById,
        createRule,
        updateRule,
        deleteRule,
        evaluateRules,
        evaluateRule,
        validateOnly,
        getVisibility,
        getExecutionLogs,
        getExecutionsByRecord
    }
}

// Default export for backwards compatibility
export default {
    getRulesByObject: useBusinessRulesApi().getRulesByObject,
    getRuleById: useBusinessRulesApi().getRuleById,
    createRule: useBusinessRulesApi().createRule,
    updateRule: useBusinessRulesApi().updateRule,
    deleteRule: useBusinessRulesApi().deleteRule,
    evaluateRules: useBusinessRulesApi().evaluateRules,
    validateOnly: useBusinessRulesApi().validateOnly,
    getVisibility: useBusinessRulesApi().getVisibility,
    getExecutionLogs: useBusinessRulesApi().getExecutionLogs,
    getExecutionsByRecord: useBusinessRulesApi().getExecutionsByRecord
}
