import { ElMessage } from 'element-plus'

export function useAction() {

    const executeAction = async (action, context) => {
        if (!action) return;

        console.log('Executing Action:', action, 'Context:', context);

        try {
            switch (action.type) {
                case 'api':
                    await executeApiAction(action, context);
                    break;
                case 'script':
                    executeScriptAction(action, context);
                    break;
                case 'link':
                    executeLinkAction(action, context);
                    break;
                default:
                    ElMessage.warning(`Unknown action type: ${action.type}`);
            }
        } catch (error) {
            console.error('Action execution failed:', error);
            ElMessage.error(`Action failed: ${error.message}`);
        }
    }

    const executeApiAction = async (action, context) => {
        // Mock API call for now
        // In real implementation, this would use axios to call action.url
        ElMessage.info(`Calling API: ${action.url || '/api/mock'}`);
        return new Promise(resolve => setTimeout(resolve, 500));
    }

    const executeScriptAction = (action, context) => {
        // Safe script execution similar to validation
        // For Phase 3, we just log
        if (action.script) {
            try {
                // Simple logging for demo
                console.log("Script Output:", action.script);
                ElMessage.success('Script executed (check console)');
            } catch (e) {
                throw new Error('Script error');
            }
        }
    }

    const executeLinkAction = (action, context) => {
        if (action.url) {
            window.open(action.url, '_blank');
        }
    }

    return {
        executeAction
    }
}
