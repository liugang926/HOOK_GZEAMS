# GZEAMS + Claude Code 集成指南

本文档说明如何在 GZEAMS 项目中使用 Claude Code 的社区功能。

## 已配置的功能

### 1. 自定义命令 (Slash Commands)

在 Claude Code 中使用以下命令：

#### `/gzeams-review`
对代码更改进行 GZEAMS 标准审查：
- Backend: BaseModel 继承、BaseModelSerializer、BaseModelViewSetWithBatch 等
- Frontend: i18n 使用、错误处理规范
- 注释标准：必须使用英文注释

#### `/prd-validate`
验证 PRD 文档是否符合 GZEAMS 规范：
- 检查必需章节
- 验证公共模型引用声明表
- 检查 API 格式规范
- 验证 i18n 键覆盖

#### `/feature-start`
启动新功能开发流程：
1. 需求收集
2. 架构规划
3. 创建 PRD
4. 实施顺序
5. 执行

### 2. 自动化 Hooks

#### PreEdit Hook
在编辑文件前检查：
- Python 文件中的中文注释
- Vue/TS/JS 文件中的中文注释

#### PreCommit Hook
提交前验证：
- Django 类是否继承正确的基类
- Model → BaseModel
- Serializer → BaseModelSerializer
- ViewSet → BaseModelViewSetWithBatch
- Service → BaseCRUDService
- Filter → BaseModelFilter

#### PreToolUse Hook
执行 Bash 命令前验证：
- 危险命令检测 (rm -rf /, dd, etc.)
- Python manage.py 命令应使用 docker exec

### 3. MCP 服务器

已配置 zread MCP 服务器，用于：
- 查看其他 GitHub 仓库的代码结构
- 搜索项目文档

## 使用示例

### 代码审查

```
你: /gzeams-review
Claude: [分析当前更改的文件，检查 GZEAMS 规范]
```

### PRD 验证

```
你: /prd-validate docs/plans/my_feature.md
Claude: [验证 PRD 文档格式和内容]
```

### 开始新功能

```
你: /feature-start
Claude: [引导你完成功能开发流程]
```

### 查看其他项目

```
你: 查看 anthropics/claude-code 仓库的结构
Claude: [使用 zread MCP 获取仓库信息]
```

## 项目规范速查

### Backend (Django)

| 组件类型 | 必须继承 | 来源 |
|---------|---------|------|
| Model | `BaseModel` | `apps.common.models.BaseModel` |
| Serializer | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` |
| ViewSet | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` |
| Service | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` |
| Filter | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` |

### Frontend (Vue3)

- 所有用户文本使用 i18n: `$t('module.key')`
- 不使用 `alert()`，使用统一错误提示
- 使用 Composition API
- TypeScript 严格模式

### 注释规范

```
# ✅ 正确 - 英文注释
def get_active_assets(self):
    """Get all active assets for current organization."""
    return self.queryset.filter(is_deleted=False)

# ❌ 错误 - 中文注释
def get_active_assets(self):
    """获取当前组织的所有活跃资产"""
    return self.queryset.filter(is_deleted=False)
```

## 目录结构

```
.claude/
├── settings.local.json         # Claude Code 配置
└── plugins/
    └── gzeams-rules/           # GZEAMS 项目规则插件
        ├── plugin.json
        ├── README.md
        ├── commands/           # 自定义命令
        │   ├── gzeams-review.md
        │   ├── prd-validate.md
        │   └── feature-start.md
        ├── hooks/              # 自动化 hooks
        │   └── hooks.json
        └── services/           # Python 服务脚本
            ├── check_chinese_comments.py
            ├── validate_base_classes.py
            └── validate_bash.py
```

## 故障排查

### Hooks 不工作
确保 Python 可在终端中使用：
```bash
python --version
```

### MCP 服务器不工作
确保 Node.js 可用：
```bash
npx -y zread-mcp-server --version
```

### 命令不显示
重启 Claude Code：
```bash
# 关闭并重新打开 Claude Code
```

## 扩展

要添加新的命令或 hooks，参考 Claude Code 官方文档：
- https://github.com/anthropics/claude-code
- 或使用 MCP zread 服务器查看文档
