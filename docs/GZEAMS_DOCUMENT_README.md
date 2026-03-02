# GZEAMS 产品概览文档

## 文档文件

本目录包含 GZEAMS 产品概览文档的多种格式：

### 1. GZEAMS_PRODUCT_OVERVIEW.md
**Markdown 格式** - 原始文档
- 适合版本控制和编辑
- 可以直接在 GitHub 上预览

### 2. GZEAMS_PRODUCT_OVERVIEW.html
**HTML 格式** - 推荐查看方式
- 精美的排版设计
- 响应式布局，支持移动端
- 包含交互式导航
- 支持浏览器打印

**如何使用：**
```bash
# 直接用浏览器打开
start GZEAMS_PRODUCT_OVERVIEW.html

# 或者用默认浏览器打开
explorer GZEAMS_PRODUCT_OVERVIEW.html
```

### 3. 生成 PDF 文档

由于 pip 环境问题，请使用以下方法之一生成 PDF：

#### 方法一：浏览器打印（推荐）
1. 用浏览器打开 `GZEAMS_PRODUCT_OVERVIEW.html`
2. 按 `Ctrl + P` 或点击菜单中的"打印"
3. 选择"另存为 PDF"或"Microsoft Print to PDF"
4. 点击保存

#### 方法二：使用 Python 脚本
```bash
# 首先安装 reportlab（修复 pip 后）
pip install reportlab

# 然后运行生成器
python GZEAMS_PRODUCT_OVERVIEW_pdf_generator.py
```

## 文档内容

- **产品概述**: 产品定位、价值主张、适用场景
- **核心架构**: 技术架构图、元数据引擎、多租户隔离、事件驱动
- **功能模块**: Phase 1-7 所有模块详细说明
- **公共基类**: BaseModel 体系设计
- **技术规范**: 前后端开发规范
- **产品特色**: 竞品对比、差异化功能
- **实施路线图**: 各阶段实施状态

## 版本历史

| 版本 | 日期 | 变更说明 |
|-----|------|---------|
| v1.1.0 | 2026-01-22 | 新增 Phase 7 高级增强模块 |
| v1.0.0 | 2026-01-22 | 初始版本 |
