"""
Integration module constants and enums.

Defines system types, sync directions, status codes for ERP integration framework.
"""


class IntegrationSystemType:
    """Integration system type choices."""

    M18 = 'm18'
    SAP = 'sap'
    KINGDEE = 'kingdee'
    YONYOU = 'yonyou'
    ORACLE = 'oracle'
    ODOO = 'odoo'

    CHOICES = [
        (M18, '万达宝M18'),
        (SAP, 'SAP'),
        (KINGDEE, '金蝶'),
        (YONYOU, '用友'),
        (ORACLE, 'Oracle EBS'),
        (ODOO, 'Odoo'),
    ]


class IntegrationModuleType:
    """Integration module type choices."""

    PROCUREMENT = 'procurement'
    FINANCE = 'finance'
    INVENTORY = 'inventory'
    HR = 'hr'
    CRM = 'crm'

    CHOICES = [
        (PROCUREMENT, '采购管理'),
        (FINANCE, '财务核算'),
        (INVENTORY, '库存管理'),
        (HR, '人力资源'),
        (CRM, '客户关系'),
    ]


class SyncDirection:
    """Sync direction choices."""

    PULL = 'pull'
    PUSH = 'push'
    BIDIRECTIONAL = 'bidirectional'

    CHOICES = [
        (PULL, '拉取(第三方→本系统)'),
        (PUSH, '推送(本系统→第三方)'),
        (BIDIRECTIONAL, '双向同步'),
    ]


class SyncStatus:
    """Sync status choices."""

    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    PARTIAL_SUCCESS = 'partial_success'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

    CHOICES = [
        (PENDING, '待执行'),
        (RUNNING, '执行中'),
        (SUCCESS, '成功'),
        (PARTIAL_SUCCESS, '部分成功'),
        (FAILED, '失败'),
        (CANCELLED, '已取消'),
    ]


class HealthStatus:
    """Health status choices."""

    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'

    CHOICES = [
        (HEALTHY, '健康'),
        (DEGRADED, '降级'),
        (UNHEALTHY, '不可用'),
    ]
