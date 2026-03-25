# 布局设计器增强 Backlog

关联文档:

- `docs/prd/prd-layout-designer-enhancement-2026-03-11.md`

本文档用于把修订后的 PRD 拆成可执行开发任务，默认按 Epic > Story > Task 组织。

---

## Epic 1 - Layout Field Model Unification

目标: 统一布局字段模型，降低设计器、运行时和持久化链路之间的适配成本。

### Story 1.1 - 统一字段配置主格式

验收:

- 内部处理路径只保留一套主格式。
- 保存、发布、回读后规则字段不丢失。
- 旧数据仍可兼容读取。

前端任务:

- 梳理 `LayoutField` 的真实持久化字段集合。
- 明确 `min_length/max_length/regex_pattern/validation_message` 与 camelCase 字段映射。
- 在 `designerLayoutAdapters.ts` 增加 normalize / denormalize 工具。
- 在 `useDesignerPersistenceActions.ts` 保存前统一序列化。
- 在加载链路统一反序列化。

后端任务:

- 确认 `layout_config` 对新增字段不做丢弃式清洗。
- 评估是否需要在 serializer 层补文档或兼容说明。

测试任务:

- 增加 layout save/load contract test。
- 覆盖“旧 layout 数据 + 新字段保存后回读”场景。

建议文件:

- `frontend/src/components/designer/designerTypes.ts`
- `frontend/src/components/designer/designerLayoutAdapters.ts`
- `frontend/src/components/designer/useDesignerPersistenceActions.ts`
- `frontend/src/types/metadata.ts`
- `backend/apps/system/serializers_modules/business_object.py`

### Story 1.2 - 明确 view_mode 行为覆盖策略

验收:

- `edit / readonly / detail` 的字段行为覆盖关系有固定规则。
- shared edit layout 不因新规则配置被破坏。

前端任务:

- 梳理 `saveReadonlyToSharedLayout` 的行为边界。
- 明确哪些配置写 shared base，哪些写 readonly override。
- 为 visibility / validation 规则补 mode-aware merge 说明和实现。

后端任务:

- 如有必要，为 `layout_config.modeOverrides` 增补字段示例文档。

测试任务:

- 覆盖 readonly 保存、发布、回读、回滚。
- 覆盖 edit 和 readonly 互不串规则。

建议文件:

- `frontend/src/components/designer/useDesignerPersistenceActions.ts`
- `frontend/src/views/system/PageLayoutDesigner.vue`

---

## Epic 2 - Runtime Validation And Visibility

目标: 让设计器里配置的字段行为在运行时真正生效。

### Story 2.1 - 运行时 validation rules 生成

验收:

- required、长度、数值范围、正则可在 edit runtime 生效。
- 自定义错误文案生效。
- 隐藏字段不参与校验。

前端任务:

- 在字段投影阶段生成 field rule descriptor。
- 在 `BaseDetailPage` 注入 `formRules`。
- 根据字段类型区分 `blur` / `change` 触发时机。
- 对只读字段跳过交互型校验。

后端任务:

- 输出说明: 本期后端是否同步校验，若不同步需在 PRD 标注前端范围。

测试任务:

- 单元测试覆盖 text/number/select/date 基本规则。
- E2E 覆盖设计器保存后到详情编辑页校验生效。

建议文件:

- `frontend/src/components/common/useBaseDetailPageFields.ts`
- `frontend/src/components/common/BaseDetailPage.vue`
- `frontend/src/components/common/BaseDetailSectionCard.vue`

### Story 2.2 - 轻量 visibility rule 设计器配置

验收:

- 可在属性面板配置单条件显隐。
- 配置可保存、回读、编辑。

前端任务:

- 在属性面板增加 visibility rule 编辑区。
- 提供字段选择、运算符、值输入三元配置。
- 限制当前版本只支持单条件规则。
- 为后续升级 JSON Logic 预留结构。

后端任务:

- 确认 `layout_config` 原样存储 visibility 字段。

测试任务:

- 单元测试覆盖空规则、合法规则、删除规则。

建议文件:

- `frontend/src/components/designer/FieldPropertyEditor.vue`
- `frontend/src/components/designer/designerTypes.ts`

### Story 2.3 - 运行时 visibility 求值

验收:

- 依赖字段变化时目标字段实时显隐。
- 隐藏字段不参与前端校验。
- 隐藏后再次显示，字段值仍可恢复显示。

前端任务:

- 在详情页字段投影阶段计算 hidden 状态。
- 监听 `formData` 变化重新求值。
- 定义 `eq/neq/in/notIn` 的求值规则。

后端任务:

- 无强依赖。
- 可选: 评估后续是否与 `Rule Engine` 对齐。

测试任务:

- 单元测试覆盖 4 类运算符。
- E2E 覆盖字段 A 改值触发字段 B 显隐。

建议文件:

- `frontend/src/components/common/useBaseDetailPageFields.ts`
- `frontend/src/components/common/BaseDetailSectionCard.vue`

---

## Epic 3 - Designer Experience Gap Closure

目标: 把已有能力补齐到稳定可交付状态。

### Story 3.1 - 统计栏接线

验收:

- 画布底部显示字段数、必填数、Section 数。
- 新增、删除、撤销、重做后统计实时更新。

前端任务:

- 在 `WysiwygLayoutDesigner.vue` 计算 totalFields / requiredFields / sectionCount。
- 透传到 `DesignerCanvas.vue`。

测试任务:

- 单元测试覆盖统计值计算。

建议文件:

- `frontend/src/components/designer/WysiwygLayoutDesigner.vue`
- `frontend/src/components/designer/DesignerCanvas.vue`

### Story 3.2 - 字段面板分配进度

验收:

- 字段面板顶部显示已分配进度。
- 未分配字段有高亮标识。

前端任务:

- 计算已使用字段编码集合。
- 显示 `assigned/total` 进度。
- 为未分配字段增加视觉标识。

测试任务:

- 单元测试覆盖字段增删后的进度变化。

建议文件:

- `frontend/src/components/designer/DesignerFieldPanel.vue`
- `frontend/src/components/designer/WysiwygLayoutDesigner.vue`

### Story 3.3 - 字段真实预览补差

验收:

- 常见字段在设计器中的表现接近运行时。
- reference / related_object / sub_table 有明确降级策略。

前端任务:

- 梳理不可预览字段列表。
- 定义各字段类型的设计态显示标准。
- 修复 disabled 态样式不一致问题。

测试任务:

- 回归 text/switch/date/select/reference 五类字段预览。

建议文件:

- `frontend/src/components/designer/DesignerFieldCard.vue`
- `frontend/src/components/engine/FieldRenderer.vue`
- `frontend/src/components/engine/fields/*.vue`

### Story 3.4 - 属性面板收口

验收:

- 只显示当前字段类型适用配置。
- 分组顺序一致。
- 系统字段的只读锁不可取消。

前端任务:

- 清理 schema 展示顺序。
- 优化字段类型相关项显隐。
- 为系统字段加入禁用态和提示文案。

测试任务:

- 单元测试覆盖 text/number/reference/sub_table 几类 schema。

建议文件:

- `frontend/src/components/designer/FieldPropertyEditor.vue`
- `frontend/src/platform/layout/propertySchema.ts`

---

## Epic 4 - Drag Feedback And Productivity

目标: 增强设计器操作反馈和高频编辑效率。

### Story 4.1 - 插入位置指示

验收:

- 拖拽过程中有明确插入位置反馈。
- 跨容器拖拽位置反馈稳定。

前端任务:

- 明确使用 `sortable-ghost` 还是单独插入线方案。
- 修正不同容器中的样式表现。

测试任务:

- E2E 覆盖同 Section 和跨 Section 拖拽。

建议文件:

- `frontend/src/components/designer/useDesignerDragInteractions.ts`
- `frontend/src/components/designer/WysiwygLayoutDesigner.scss`

### Story 4.2 - 拖拽 ghost 预览

验收:

- 桌面端拖拽源有更清晰的 ghost。
- 移动端自动降级。

前端任务:

- 实现 `setDragImage` 或 custom ghost。
- 补 user-agent / pointer capability 降级逻辑。

测试任务:

- 手工回归桌面端 Chrome/Edge。

建议文件:

- `frontend/src/components/designer/DesignerFieldPanel.vue`
- `frontend/src/components/designer/useDesignerDragInteractions.ts`

### Story 4.3 - 放置动画接线

验收:

- 字段成功放置后有短时反馈动画。

前端任务:

- 在 drop / onEnd 之后为新节点打 `field-just-dropped` 类。
- 动画结束后清理类名。

测试任务:

- 手工回归为主。

建议文件:

- `frontend/src/components/designer/useDesignerDragInteractions.ts`
- `frontend/src/components/designer/WysiwygLayoutDesigner.scss`

### Story 4.4 - 双击快编 Label

验收:

- 双击字段标题进入 inline edit。
- Enter 确认，Esc 取消。

前端任务:

- 为 `DesignerFieldCard` 增加轻量 inline edit 状态。
- 接入历史记录和撤销链路。

测试任务:

- 单元测试覆盖提交和取消。

建议文件:

- `frontend/src/components/designer/DesignerFieldCard.vue`
- `frontend/src/components/designer/useDesignerHistory.ts`

### Story 4.5 - 可选高级项

候选:

- 右键菜单
- Section 排序

说明:

- 这两项建议在核心范围完成后单独排期。
- Section 排序必须额外评估历史、回滚、空容器和跨模式一致性。

---

## Sprint 建议

### Sprint 1

- Story 1.1
- Story 2.1
- Story 3.1
- Story 3.2

### Sprint 2

- Story 1.2
- Story 2.2
- Story 2.3
- Story 3.3
- Story 3.4

### Sprint 3

- Story 4.1
- Story 4.2
- Story 4.3
- Story 4.4

### Backlog Parking Lot

- Story 4.5

---

## Definition Of Done

- 代码通过现有 lint / typecheck / 相关单元测试。
- 至少补 1 组设计器保存到运行时生效的端到端验证。
- PR 描述包含:
  - 改动范围
  - 风险点
  - 回归清单
  - 是否涉及单布局模型行为变化
