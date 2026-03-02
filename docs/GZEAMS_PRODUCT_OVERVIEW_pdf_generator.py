"""
GZEAMS Product Overview PDF Generator
Creates a professional PDF document with tables and diagrams
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether, Preformatted
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

# Document metadata
DOC_TITLE = "GZEAMS 钩子固定资产 - 产品概览文档"
DOC_VERSION = "v1.1.0"
DOC_DATE = "2026-01-22"


def create_pdf(output_path="GZEAMS_PRODUCT_OVERVIEW.pdf"):
    """Create the PDF document"""

    # Setup document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Container for story elements
    story = []

    # Styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=0.5*cm,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=1.5*cm,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=0.8*cm,
        spaceAfter=0.3*cm,
        fontName='Helvetica-Bold'
    )

    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#334155'),
        spaceBefore=0.5*cm,
        spaceAfter=0.2*cm,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#334155'),
        spaceAfter=0.3*cm,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontSize=8,
        textColor=colors.white,
        backColor=colors.HexColor('#1e293b'),
        spaceBefore=0.3*cm,
        spaceAfter=0.3*cm,
        leftIndent=0.5*cm,
        fontName='Courier'
    )

    # ============================================================================
    # COVER PAGE
    # ============================================================================

    # Title
    story.append(Paragraph(DOC_TITLE, title_style))
    story.append(Spacer(1, 0.3*cm))

    # Version badge
    version_data = [[
        Paragraph(f"<font name='Helvetica-Bold'>Version:</font> {DOC_VERSION}", normal_style),
        Paragraph(f"<font name='Helvetica-Bold'>Updated:</font> {DOC_DATE}", normal_style),
    ]]
    version_table = Table(version_data, colWidths=[4*cm, 4*cm])
    version_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PAD', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#475569')),
    ]))
    story.append(version_table)
    story.append(Spacer(1, 1*cm))

    # Subtitle
    story.append(Paragraph(
        "企业级固定资产低代码管理平台<br/>"
        "元数据驱动 + 多组织隔离 + 事件驱动解耦",
        subtitle_style
    ))
    story.append(Spacer(1, 2*cm))

    # Info cards
    info_data = [
        ["产品名称", "GZEAMS (钩子固定资产)"],
        ["产品定位", "企业级固定资产低代码管理平台"],
        ["核心架构", "元数据驱动 + 多组织隔离 + 事件驱动"],
        ["技术栈", "Django 5.0 + Vue 3 + PostgreSQL + Redis + Celery"],
    ]

    info_table = Table(info_data, colWidths=[3.5*cm, 12*cm], hAlign='LEFT')
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('PAD', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(info_table)

    story.append(PageBreak())

    # ============================================================================
    # SECTION 1: 产品概述
    # ============================================================================

    story.append(Paragraph("一、产品概述", heading_style))

    story.append(Paragraph("产品定位", subheading_style))
    story.append(Paragraph(
        "<b>GZEAMS (Hook Fixed Assets)</b> 是一款基于 <b>元数据驱动低代码架构</b> 的企业级"
        "固定资产管理平台。产品核心设计理念是<b>\"业务与流程分离\"</b>，通过可视化配置快速适配"
        "不同企业的资产管理需求，无需修改代码即可实现业务流程定制。",
        normal_style
    ))

    story.append(Paragraph("核心价值主张", subheading_style))

    value_data = [
        ["价值维度", "传统方案痛点", "GZEAMS 解决方案"],
        ["实施效率", "需求变更需重新开发，周期长", "元数据驱动，配置即可生效"],
        ["组织适配", "单组织设计，集团化管理困难", "多租户架构，支持集团/公司/部门三级隔离"],
        ["流程灵活性", "流程硬编码，调整困难", "可视化工作流设计器，拖拽式配置"],
        ["数据一致性", "盘点期间数据变动导致差异", "快照机制，保证盘点数据准确性"],
        ["系统集成", "财务数据需手工录入", "标准化ERP适配器，自动同步凭证"],
        ["移动办公", "PC为主，现场操作不便", "移动端PWA，支持离线盘点"],
    ]

    value_table = Table(value_data, colWidths=[3*cm, 5*cm, 5*cm])
    value_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PAD', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
    ]))
    story.append(value_table)

    story.append(Paragraph("适用场景", subheading_style))

    scenario_data = [
        ["🏢 集团型企业", "多公司、多部门统一管理，独立核算"],
        ["📦 中大型企业", "资产数量大、种类多、流转频繁"],
        ["🏛️ 监管严格行业", "需要完整审计链和合规性报告（金融、医疗、政府）"],
        ["🚀 快速成长企业", "组织架构和业务流程频繁调整"],
    ]

    scenario_table = Table(scenario_data, colWidths=[4*cm, 11*cm])
    scenario_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PAD', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(scenario_table)

    story.append(PageBreak())

    # ============================================================================
    # SECTION 2: 核心架构
    # ============================================================================

    story.append(Paragraph("二、核心架构设计", heading_style))

    story.append(Paragraph("元数据驱动引擎", subheading_style))
    story.append(Paragraph("产品的核心竞争力在于元数据驱动架构，实现\"零代码\"业务定制：", normal_style))

    metadata_data = [
        ["组件", "功能", "存储结构"],
        ["BusinessObject", "定义可配置的业务实体", "PostgreSQL 表"],
        ["FieldDefinition", "动态字段定义（类型、验证、公式）", "PostgreSQL 表"],
        ["PageLayout", "表单/列表页面的布局配置", "JSONB 字段"],
        ["DynamicForm", "前端动态表单渲染引擎", "Vue 3 组件"],
    ]

    metadata_table = Table(metadata_data, colWidths=[4*cm, 5*cm, 4*cm])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PAD', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(metadata_table)

    story.append(Paragraph("多租户数据隔离", subheading_style))

    tenant_diagram = """
┌─────────────────────────────────────────────────────────┐
│                    Group (集团)                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ Company A  │  │ Company B  │  │ Company C  │        │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │
│        │               │               │                │
│   ┌────┴────┐     ┌────┴────┐     ┌────┴────┐           │
│   │ 部门树   │     │ 部门树   │     │ 部门树   │           │
│   └─────────┘     └─────────┘     └─────────┘           │
└─────────────────────────────────────────────────────────┘

自动隔离机制:
• TenantMiddleware: 从 JWT 提取 company_id
• TenantManager: 所有查询自动添加 org 过滤
• BaseModel: 所有业务模型继承，自动获得隔离能力
"""

    story.append(Preformatted(tenant_diagram, code_style))

    story.append(PageBreak())

    # ============================================================================
    # SECTION 3: 功能模块
    # ============================================================================

    story.append(Paragraph("三、产品功能模块", heading_style))

    # Phase overview
    phase_data = [
        ["Phase", "模块名称", "状态", "子模块数量"],
        ["1", "基础资产核心", "✅ 已完成", "9"],
        ["2", "组织与权限", "✅ 已完成", "5"],
        ["3", "工作流引擎", "✅ 已完成", "2"],
        ["4", "盘点管理", "✅ 已完成", "5"],
        ["5", "财务集成", "✅ 已完成", "5"],
        ["6", "用户门户", "🚧 开发中", "4"],
        ["7", "高级增强", "📋 规划中", "4"],
    ]

    phase_table = Table(phase_data, colWidths=[1.5*cm, 4*cm, 3*cm, 3*cm])
    phase_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PAD', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(phase_table)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Phase 1: 基础资产核心", subheading_style))

    phase1_data = [
        ["模块", "功能描述", "核心模型"],
        ["1.1 资产分类体系", "树形分类，支持国标6大类，折旧方法配置", "AssetCategory"],
        ["1.2 多组织架构", "租户数据隔离，集团/公司/部门三级管理", "Organization, Department"],
        ["1.3 元数据引擎", "低代码配置，动态字段定义，页面布局", "BusinessObject, FieldDefinition"],
        ["1.4 资产CRUD", "资产卡片管理，二维码生成，标签打印", "Asset, AssetAttachment"],
        ["1.5 资产操作", "领用/调拨/借用/退库四类单据", "AssetPickup, AssetTransfer"],
        ["1.6 低值易耗", "批次管理，库存预警，成本统计", "Consumable, ConsumableStock"],
        ["1.7 生命周期", "采购→入库→领用→维护→处置全流程", "PurchaseRequest, DisposalRequest"],
        ["1.8 移动端增强", "离线数据库，智能同步，移动审批", "MobileDevice, SyncQueue"],
        ["1.9 统一通知", "多渠道通知（站内/邮件/短信/企微）", "Notification, NotificationTemplate"],
    ]

    phase1_table = Table(phase1_data, colWidths=[2.5*cm, 8*cm, 4.5*cm])
    phase1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('PAD', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(phase1_table)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Phase 7: 高级增强 (新增)", subheading_style))

    phase7_data = [
        ["模块", "功能描述", "核心模型"],
        ["7.1 借用外借增强", "内部/外部借用，押金管理，逾期计费，信用管理", "AssetLoan, LoanDeposit, BorrowerCredit"],
        ["7.2 资产项目管理", "项目资产分配，成本核算，项目结项回收", "AssetProject, ProjectAsset, ProjectCost"],
        ["7.3 资产标签系统", "多维度标签，灵活分类，快速筛选", "TagGroup, AssetTag, AssetTagRelation"],
        ["7.4 智能搜索增强", "Elasticsearch全文搜索，拼音匹配，搜索建议", "SearchHistory, SavedSearch"],
    ]

    phase7_table = Table(phase7_data, colWidths=[2.5*cm, 8*cm, 4.5*cm])
    phase7_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('PAD', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(phase7_table)

    story.append(PageBreak())

    # ============================================================================
    # SECTION 4: 公共基类体系
    # ============================================================================

    story.append(Paragraph("四、公共基类体系", heading_style))

    story.append(Paragraph(
        "GZEAMS 的核心设计理念是<b>\"约定优于配置\"</b>，所有业务模块必须继承公共基类，"
        "自动获得标准功能。",
        normal_style
    ))

    baseclass_data = [
        ["组件类型", "基类", "引用路径", "自动获得功能"],
        ["Model", "BaseModel", "apps.common.models.BaseModel", "组织隔离、软删除、审计字段、custom_fields"],
        ["Serializer", "BaseModelSerializer", "apps.common.serializers.base.BaseModelSerializer", "公共字段序列化、custom_fields处理"],
        ["ViewSet", "BaseModelViewSetWithBatch", "apps.common.viewsets.base.BaseModelViewSetWithBatch", "组织过滤、软删除、批量操作"],
        ["Filter", "BaseModelFilter", "apps.common.filters.base.BaseModelFilter", "时间范围过滤、用户过滤"],
        ["Service", "BaseCRUDService", "apps.common.services.base_crud.BaseCRUDService", "统一CRUD方法、组织隔离"],
    ]

    baseclass_table = Table(baseclass_data, colWidths=[2.5*cm, 4*cm, 7*cm, 4.5*cm])
    baseclass_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('PAD', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(baseclass_table)

    story.append(PageBreak())

    # ============================================================================
    # SECTION 5: 技术规范
    # ============================================================================

    story.append(Paragraph("五、技术规范", heading_style))

    story.append(Paragraph("后端开发规范", subheading_style))

    backend_std_data = [
        ["规范项", "要求", "说明"],
        ["代码注释", "✅ 强制英文", "所有注释必须是英文"],
        ["模型继承", "✅ 必须继承 BaseModel", "自动获得组织隔离等功能"],
        ["软删除", "✅ 禁止物理删除", "使用 soft_delete() 方法"],
        ["异步任务", "Celery 分级队列", "高/中/低优先级队列"],
        ["事件驱动", "Django Signals", "业务代码发出事件，监听器处理副作用"],
        ["API文档", "drf-spectacular", "自动生成 OpenAPI 文档"],
    ]

    backend_std_table = Table(backend_std_data, colWidths=[3*cm, 4.5*cm, 6*cm])
    backend_std_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PAD', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(backend_std_table)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("前端开发规范", subheading_style))

    frontend_std_data = [
        ["规范项", "要求", "说明"],
        ["框架", "Vue 3 Composition API", "禁用 Options API"],
        ["组件库", "Element Plus", "统一UI风格"],
        ["命名", "camelCase", "后端 snake_case 自动转换"],
        ["状态管理", "Pinia", "全局状态管理"],
        ["错误处理", "统一拦截器", "禁用 alert()"],
    ]

    frontend_std_table = Table(frontend_std_data, colWidths=[3*cm, 5*cm, 5.5*cm])
    frontend_std_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PAD', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(frontend_std_table)

    story.append(PageBreak())

    # ============================================================================
    # SECTION 6: 产品特色
    # ============================================================================

    story.append(Paragraph("六、产品特色", heading_style))

    story.append(Paragraph("与竞品对比", subheading_style))

    compare_data = [
        ["特性", "GZEAMS", "传统固定资产系统", "SaaS固定资产产品"],
        ["定制能力", "元数据驱动，零代码定制", "需二次开发", "固定功能"],
        ["部署方式", "私有化部署/云端", "私有化部署", "仅云端"],
        ["数据所有权", "客户完全拥有", "客户完全拥有", "托管在供应商"],
        ["工作流", "可视化设计器", "硬编码", "有限定制"],
        ["财务集成", "标准适配器", "定制开发", "有限集成"],
        ["盘点方案", "二维码+RFID双模", "单一方案", "单一方案"],
    ]

    compare_table = Table(compare_data, colWidths=[2.5*cm, 4*cm, 3.5*cm, 3.5*cm])
    compare_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('PAD', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(compare_table)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("核心差异化功能", subheading_style))

    feature_data = [
        ["📸", "快照盘点机制", "业界首创，确保盘点期间数据变动不影响盘点结果"],
        ["🔄", "双模盘点", "二维码精准盘点 + RFID批量盘点，适应不同场景"],
        ["⚙️", "元数据驱动", "无需代码修改即可扩展字段和表单"],
        ["🔌", "事件驱动架构", "业务与流程完全解耦，易于扩展"],
        ["🏢", "多租户原生", "从底层设计就支持多组织数据隔离"],
    ]

    feature_table = Table(feature_data, colWidths=[1.5*cm, 3.5*cm, 9*cm])
    feature_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PAD', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(feature_table)

    story.append(PageBreak())

    # ============================================================================
    # SECTION 7: 实施路线图
    # ============================================================================

    story.append(Paragraph("七、实施路线图", heading_style))

    roadmap_diagram = """
Phase 1: 基础资产核心 [已完成]
├── 1.1 资产分类体系
├── 1.2 多组织架构
├── 1.3 元数据引擎
├── 1.4 资产CRUD
├── 1.5 资产操作
├── 1.6 低值易耗
├── 1.7 生命周期
├── 1.8 移动端增强
└── 1.9 统一通知

Phase 2: 组织与权限 [已完成]
├── 2.1 企业微信SSO
├── 2.2 组织同步
├── 2.3 通知中心
├── 2.4 组织增强
└── 2.5 权限增强

Phase 3: 工作流引擎 [已完成]
├── 3.1 LogicFlow设计器
└── 3.2 执行引擎

Phase 4: 盘点管理 [已完成]
├── 4.1 二维码盘点
├── 4.2 RFID批量盘点
├── 4.3 快照差异
├── 4.4 任务分配
└── 4.5 业务链条

Phase 5: 财务集成 [已完成]
├── 5.0 集成框架
├── 5.1 M18适配器
├── 5.2 凭证集成
├── 5.3 折旧计算
└── 5.4 财务报表

Phase 6: 用户门户 [开发中]
├── 6.1 我的资产
├── 6.2 我的申请
├── 6.3 我的待办
└── 6.4 移动PWA

Phase 7: 高级增强 [规划中]
├── 7.1 借用外借增强
│   ├── 内部/外部借用支持
│   ├── 押金管理
│   ├── 逾期计费
│   └── 信用评分系统
├── 7.2 资产项目管理
│   ├── 项目资产分配
│   ├── 成本核算
│   ├── 项目结项回收
│   └── 跨项目调拨
├── 7.3 资产标签系统
│   ├── 标签分组管理
│   ├── 多维度标签
│   ├── 组合筛选
│   └── 自动打标签
└── 7.4 智能搜索增强
    ├── Elasticsearch集成
    ├── 中文分词+拼音
    ├── 搜索建议
    └── 搜索历史收藏
"""

    story.append(Preformatted(roadmap_diagram, code_style))

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("技术债务与持续改进", subheading_style))

    improvement_data = [
        ["•", "完善 E2E 测试覆盖"],
        ["•", "性能优化与压力测试"],
        ["•", "国际化支持 (i18n)"],
        ["•", "更多ERP适配器 (SAP, Oracle, Kingdee)"],
        ["•", "AI 辅助盘点 (图像识别)"],
    ]

    improvement_table = Table(improvement_data, colWidths=[1*cm, 15*cm])
    improvement_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PAD', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(improvement_table)

    story.append(PageBreak())

    # ============================================================================
    # FOOTER
    # ============================================================================

    story.append(Paragraph("联系与支持", heading_style))

    contact_data = [
        ["GitHub", "https://github.com/liugang926/HOOK_GZEAMS.git"],
        ["参考标杆", "https://yzcweixin.niimbot.com/"],
        ["问题反馈", "GitHub Issues"],
    ]

    contact_table = Table(contact_data, colWidths=[3*cm, 12*cm])
    contact_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PAD', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(contact_table)

    story.append(Spacer(1, 2*cm))

    story.append(Paragraph(
        f"<font name='Helvetica' size='8' color='#64748b'>"
        f"本文档由 GZEAMS 项目团队维护，最后更新于 {DOC_DATE}<br/>"
        f"版本: {DOC_VERSION}"
        f"</font>",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
    ))

    # Build the PDF
    doc.build(story)
    print(f"PDF created successfully: {output_path}")


if __name__ == "__main__":
    output_file = os.path.join(os.path.dirname(__file__), "GZEAMS_PRODUCT_OVERVIEW.pdf")
    create_pdf(output_file)
