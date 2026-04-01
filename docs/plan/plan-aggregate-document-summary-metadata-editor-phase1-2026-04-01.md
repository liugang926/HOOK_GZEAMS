# Aggregate Document Summary Metadata Editor Phase 1 Plan

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-04-01 |
| 涉及阶段 | Phase 7.2.54 |
| 作者/Agent | Codex |

## 一、目标
- 将 aggregate document 的 `documentSummarySections` 从 `menu_config.py` 手工治理扩展到 Page Layout Designer 元数据编辑能力。
- 打通设计器 UI、`PageLayout.layout_config.workbench`、后端校验与 runtime 读取链路。

## 二、范围
- 后端：
  - `PageLayoutSerializer`
  - `validators.py`
  - 对应 serializer regression tests
- 前端：
  - `WysiwygLayoutDesigner`
  - 新增 `DesignerWorkbenchMetadataPanel`
  - designer metadata helper / type 补充
  - locale 与 Vitest 回归

## 三、实施拆分

### Step 1. 后端规范化与校验
- 统一规范 `layout_config.workbench.document_summary_sections`
- 兼容 camelCase 输入
- 校验 code / priority 枚举与重复值

### Step 2. 设计器元数据面板
- 在右侧属性区下方新增 aggregate document summary metadata 面板
- 支持顺序调整、priority 选择、恢复默认
- 接入 history / autosave / save / publish

### Step 3. 类型与多语言
- 补 `LayoutConfig.workbench`
- 补系统管理 designer i18n 文案

### Step 4. 回归验证
- 后端：`py_compile` + serializer tests
- 前端：Vitest 定向用例 + 触达文件 typecheck 筛选 + locale JSON 校验

## 四、验收标准
- 设计器可以编辑并保存 `documentSummarySections`
- 保存后的 payload 经后端规范化后可被 runtime 正确读取
- 非法 metadata 会在后端被拒绝
- 触达文件无新增 TypeScript 错误命中

## 五、风险与后续
- 当前只开放四个固定 section code，后续若 runtime 扩展 section，需要同步更新 designer helper 和后端校验枚举
- 下一阶段建议继续把 `defaultDocumentSurfaceTab` 等 document workbench metadata 也收敛到同一编辑面
