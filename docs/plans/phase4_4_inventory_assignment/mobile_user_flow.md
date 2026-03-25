# Phase 4.4: 移动端盘点任务操作流程

## 概述

本文档详细描述盘点执行人如何在移动端接收和处理盘点任务的完整流程。

---

## 1. 完整操作流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        移动端盘点任务操作流程                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
  │  任务通知  │  -->  │  我的任务  │  -->  │  执行盘点  │  -->  │  提交完成  │
  │ Notification│       │ MyTasks  │       │  ScanPage │       │  Complete │
  └──────────┘       └──────────┘       └──────────┘       └──────────┘
         │                   │                   │                   │
         ▼                   ▼                   ▼                   ▼
    [推送/消息]         [任务列表]          [扫码/填单]         [结果确认]
    点击进入          选择任务开始         扫描二维码          提交盘点结果
```

---

## 2. 页面流程详解

### 2.1 任务通知入口

当盘点任务发布后，执行人通过以下方式接收通知：

#### 方式一：企业微信/钉钉消息推送

```
┌─────────────────────────────────────┐
│  企业微信消息通知                    │
├─────────────────────────────────────┤
│  [图标] 盘点任务通知                 │
│                                     │
│  您有新的盘点任务                   │
│  任务名称：2024年6月资产盘点        │
│  待盘资产：150项                    │
│  截止日期：2024-06-20               │
│                                     │
│  [查看详情]  [稍后提醒]             │
└─────────────────────────────────────┘
```

#### 方式二：App内消息中心

```
┌─────────────────────────────────────┐
│  消息中心                           │
├─────────────────────────────────────┤
│  📋 待办事项 (3)                     │
│  └─ 新增盘点任务                    │
│     2024年6月资产盘点               │
│     2分钟前                        │
└─────────────────────────────────────┘
```

### 2.2 我的任务列表页 (`MyTasks.vue`)

**页面功能：**
- 展示当前用户的所有盘点任务
- 显示任务进度统计（待盘/已盘）
- 筛选任务状态（全部/待执行/进行中/已完成）
- 支持点击进入任务详情

```
┌─────────────────────────────────────────────────────────────┐
│  我的盘点任务                                  [_搜索框_]      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📊 今日统计                                         │   │
│  │                                                    │   │
│  │  ┌─────┐  ┌─────┐  ┌─────┐                          │   │
│  │  │ 120 │  │  30 │  │  3  │                          │   │
│  │  │待盘 │  │已盘 │  │任务 │                          │   │
│  │  └─────┘  └─────┘  └─────┘                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [全部] [待执行] [进行中] [已完成]                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 任务名称: 2024年6月资产盘点         [待执行] [标签]    │   │
│  │ 任务编号: PD20240615001                              │   │
│  │ 盘点模式: 部门自盘                                    │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 30/150 (20%)          │   │
│  │ 截止日期: 2024-06-20                                  │   │
│  │                                      [开始盘点]        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 任务名称: 办公设备抽查               [进行中] [标签]    │   │
│  │ 任务编号: PD20240610002                              │   │
│  │ 盘点模式: 随机抽查                                    │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8/10 (80%)           │   │
│  │ 截止日期: 2024-06-18                                  │   │
│  │                                      [继续盘点]        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 任务详情页 (`TaskDetail.vue`)

点击任务卡片后进入任务详情，显示：
- 任务基本信息
- 待盘资产列表
- 已盘资产列表
- 进度统计

```
┌─────────────────────────────────────────────────────────────┐
│  <- 任务详情                               [更多操作]        │
├─────────────────────────────────────────────────────────────┤
│  任务名称: 2024年6月资产盘点                                │
│  任务编号: PD20240615001                                    │
│  盘点类型: 部门自盘                                          │
│  开始时间: 2024-06-15 09:00                                 │
│  截止时间: 2024-06-20 18:00                                 │
│                                                             │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                        │
│  │ 120 │  │ 30 │  │ 5  │  │ 85 │  异常: 5项            │
│  │总数 │  │待盘 │  │已盘│  │完成│                        │
│  └─────┘  └─────┘  └─────┘  └─────┘                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  筛选: [全部] [待盘] [已盘] [异常]                   │   │
│  │  排序: [编码] [名称] [地点]                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📦 ZC202406001001                                   │   │
│  │     MacBook Pro 16寸                                │   │
│  │     3楼A区 / 张三                                   │   │
│  │                    [扫码盘点]  [标记异常]              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📦 ZC202406001002  ✅                               │   │
│  │     Dell 显示器 27寸                                │   │
│  │     3楼A区 / 李四                                   │   │
│  │                    [查看详情]                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [                    开始批量扫码                        ]   │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 扫码盘点页 (`ScanPage.vue`)

这是核心操作页面，支持：
- 扫描资产二维码
- 查看资产快照信息
- 选择盘点状态（正常/位置变更/损坏/缺失）
- 拍照记录
- 手动输入编码

```
┌─────────────────────────────────────────────────────────────┐
│  扫码盘点                              [_完成_/_待盘_]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ╔═════════════════════════════════════════════════════════╗   │
│  ║                   📹 扫描区域                          ║   │
│  ║                                                       ║   │
│  ║                     ┌─────────┐                        ║   │
│  ║                     │ ██████ │                        ║   │
│  ║                     │ ██████ │                        ║   │
│  ║                     └─────────┘                        ║   │
│  ║                   将二维码放入框内                        ║   │
│  ║                                                       ║   │
│  ╚═════════════════════════════════════════════════════════╝   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  快速操作:                                         │   │
│  │  [📷 拍照]  [✏️ 手动输入]  [💡 开灯]               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  最近扫描:                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ✅ ZC202406001001  MacBook Pro                      │   │
│  │  ✅ ZC202406001002  Dell 显示器                      │   │
│  │  ⏳ ZC202406001003  扫描中...                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**扫描结果确认页：**

```
┌─────────────────────────────────────────────────────────────┐
│  扫描结果                                                     │
├─────────────────────────────────────────────────────────────┤
│  [<] 返回                                                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  资产编码: ZC202406001001                            │   │
│  │  资产名称: MacBook Pro 16寸                           │   │
│  │  资产快照: 3楼A区 / 正常使用                           │   │
│  │  保管人: 张三                                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  请选择盘点状态:                                     │   │
│  │                                                     │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐│   │
│  │  │   ✓    │  │   📍    │  │   ⚠️    │  │   ❌    ││   │
│  │  │  正常  │  │位置变更 │  │   损坏  │  │   缺失  ││   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘│   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │ 当前状态: 正常 ⭐️                               │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  备注 (可选)                                       │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │                                             │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [📷 添加照片]                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [ 重扫 ]              [ 确认提交 ]                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.5 盘点完成页 (`CompletePage.vue`)

当所有资产盘点完成后显示：

```
┌─────────────────────────────────────────────────────────────┐
│                         🎉                                    │
│                      盘点完成！                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  本次盘点统计                                       │   │
│  │                                                     │   │
│  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐         │   │
│  │  │ 150 │ │ 145 │ │  3  │ │  2  │ │  1  │         │   │
│  │  │总数 │ │已盘 │ │待盘 │ │正常 │ │异常 │         │   │
│  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  异常资产清单                                       │   │
│  │                                                     │   │
│  │  📦 ZC202406001050  [位置变更]  未在指定位置           │   │
│  │  📦 ZC202406001078  [损坏]      屏幕有裂痕           │   │
│  │  📦 ZC202406001088  [缺失]      未找到资产           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [查看明细]  [返回任务列表]  [退出]                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 核心交互细节

### 3.1 连续扫码模式

适用于快速盘点场景：

```
┌─────────────────────────────────────────────────────────────┐
│  连续扫码模式                      [_退出连续模式_]      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                      扫描中...                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                             │
│  本次已扫描: 120项                                           │
│  剩余待盘: 30项                                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  最近5秒扫描:                                     │   │
│  │  • ✅ ZC202406001115  扫描成功                      │   │
│  │  • ✅ ZC202406001116  扫描成功                      │   │
│  │  • ✅ ZC202406001117  扫描成功                      │   │
│  │  • ✅ ZC202406001118  扫描成功                      │   │
│  │  • ⏳ 正在扫描...                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  💡 提示: 扫描后会自动使用"正常"状态，如需修改请点击资产    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 离线暂存模式

网络不佳时的处理：

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ 网络连接不稳定，已启用离线模式                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • 扫描结果会暂存在本地                                   │
│  • 网络恢复后自动上传                                     │
│  • 已暂存: 25条记录                                       │
│                                                             │
│  [查看暂存数据]  [立即同步]                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 异常处理流程

当扫描到异常情况时：

```
┌─────────────────────────────────────────────────────────────┐
│  发现异常                                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  资产: ZC202406001050                                 │   │
│  │  名称: ThinkPad X1 Carbon                             │   │
│  │  快照位置: 3楼A区                                     │   │
│  │  当前位置: 3楼B区                                     │   │
│  │                                                     │   │
│  │  ⚠️ 位置不一致，请确认:                              │   │
│  │                                                     │   │
│  │  [以快照为准]  [以当前为准]  [位置变更]               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  位置变更说明:                                       │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │ 资产已移至3楼B区会议室                         │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  │  [拍照留证]  [确认提交]                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [返回]  [跳过此项]                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. API交互序列

### 4.1 开始盘点流程

```
User                    App                    API                  Database
 │                       │                       │                       │
 │── 点击"开始盘点" ────>│                       │                       │
 │                       │── POST /start ──────>│                       │
 │                       │                       │── INSERT scan_log│
 │                       │<──── 200 OK ────────│                       │
 │                       │                       │                       │
 │── 进入扫码页 ────────>│                       │                       │
 │                       │                       │                       │
 │── 扫描二维码 ────────>│                       │                       │
 │                       │── POST /scan ───────>│                       │
 │                       │                       │── UPDATE scan_log │
 │                       │<──── 资产信息 ───────│                       │
 │                       │                       │                       │
 │── 确认提交 ──────────>│                       │                       │
 │                       │── POST /confirm ─────>│                       │
 │                       │                       │── UPDATE result    │
 │                       │<──── 200 OK ────────│                       │
 │                       │                       │                       │
 │── 继续下一个 ────────>│                       │                       │
```

### 4.2 批量扫码流程

```
User                    App                    API                  Database
 │                       │                       │                       │
 │── 开启连续扫码 ─────>│                       │                       │
 │                       │── POST /batch_start │                       │
 │                       │                       │                       │
 │── 扫描 #1 ──────────>│── POST /scan (状态=正常,自动提交)                 │
 │                       │<──── 200 OK ────────│                       │
 │                       │── 更新计数器: 1/150                          │
 │                       │                       │                       │
 │── 扫描 #2 ──────────>│── POST /scan                                  │
 │                       │<──── 200 OK ────────│                       │
 │                       │── 更新计数器: 2/150                          │
 │                       │                       │                       │
 │  ...                   │  ...                    │  ...                    │
 │                       │                       │                       │
 │── 扫描 #150 ─────────>│── POST /scan                                  │
 │                       │<──── 200 OK ────────│                       │
 │                       │── 更新计数器: 150/150 ✓                     │
 │                       │                       │                       │
 │── 自动完成 ─────────>│── 显示完成页面                                 │
 │                       │── POST /complete ────>│── 更新任务状态     │
 │                       │                       │── 创建盘点报告     │
```

---

## 5. 状态定义

### 5.1 任务状态

| 状态 | 说明 | 可操作 |
|------|------|--------|
| `pending` | 待执行 | 开始盘点 |
| `in_progress` | 进行中 | 继续盘点 |
| `completed` | 已完成 | 查看报告 |
| `cancelled` | 已取消 | - |
| `expired` | 已逾期 | - |

### 5.2 资产盘点状态

| 状态 | 说明 | 需补充信息 |
|------|------|------------|
| `normal` | 正常 | 无 |
| `location_changed` | 位置变更 | 实际位置 |
| `damaged` | 损坏 | 损坏描述+照片 |
| `lost` | 缺失 | 备注说明 |
| `extra_found` | 盘盈 | 资产信息 |

---

## 6. 关键UI组件

### 6.1 进度卡片组件

```vue
<template>
  <div class="progress-card">
    <div class="progress-header">
      <span class="task-name">{{ taskName }}</span>
      <el-tag :type="statusType">{{ statusLabel }}</el-tag>
    </div>
    <div class="progress-stats">
      <div class="stat">
        <span class="value">{{ progress }}%</span>
        <span class="label">完成度</span>
      </div>
      <div class="stat">
        <span class="value">{{ scannedCount }}/{{ totalCount }}</span>
        <span class="label">已扫/总数</span>
      </div>
    </div>
    <el-progress
      :percentage="progress"
      :stroke-width="12"
      :show-text="false"
    />
    <div class="progress-actions">
      <el-button
        v-if="status === 'pending'"
        type="primary"
        block
        @click="start"
      >
        开始盘点
      </el-button>
      <el-button
        v-else-if="status === 'in_progress'"
        type="primary"
        block
        @click="continue"
      >
        继续盘点
      </el-button>
      <el-button
        v-else
        block
        @click="viewReport"
      >
        查看报告
      </el-button>
    </div>
  </div>
</template>
```

### 6.2 扫描结果确认组件

```vue
<template>
  <div class="scan-result">
    <!-- 资产信息卡片 -->
    <div class="asset-card">
      <div class="card-header">
        <el-icon><Box /></el-icon>
        <span>{{ asset.asset_code }}</span>
        <el-tag type="success" size="small">已扫描</el-tag>
      </div>
      <div class="card-body">
        <div class="field">
          <span class="label">资产名称</span>
          <span class="value">{{ asset.asset_name }}</span>
        </div>
        <div class="field">
          <span class="label">快照位置</span>
          <span class="value">{{ asset.snapshot_location }}</span>
        </div>
        <div class="field" v-if="asset.custodian">
          <span class="label">保管人</span>
          <span class="value">{{ asset.custodian }}</span>
        </div>
      </div>
    </div>

    <!-- 状态选择器 -->
    <div class="status-selector">
      <h4 class="selector-title">盘点状态</h4>
      <div class="options-grid">
        <div
          v-for="option in statusOptions"
          :key="option.value"
          class="status-option"
          :class="{ active: localStatus === option.value }"
          @click="localStatus = option.value"
        >
          <div class="option-icon" :style="{ background: option.color }">
            <el-icon><component :is="option.icon" /></el-icon>
          </div>
          <span class="option-label">{{ option.label }}</span>
        </div>
      </div>
    </div>

    <!-- 条件输入区 -->
    <div v-if="localStatus === 'location_changed'" class="condition-input">
      <el-form-item label="实际位置">
        <el-input
          v-model="actualLocation"
          placeholder="请输入或扫描实际位置"
        >
          <template #append>
            <el-button :icon="Location">扫码</el-button>
          </template>
        </el-input>
      </el-form-item>
    </div>

    <div v-if="localStatus === 'damaged'" class="condition-input">
      <el-form-item label="损坏描述">
        <el-input
          v-model="damageDesc"
          type="textarea"
          placeholder="请描述损坏情况"
          :rows="3"
        />
      </el-form-item>
      <el-form-item label="照片证明">
        <ImageUploader v-model="damagePhotos" :max="3" />
      </el-form-item>
    </div>

    <!-- 备注 -->
    <div class="remark-section">
      <el-input
        v-model="remark"
        type="textarea"
        placeholder="添加备注信息（可选）"
        :rows="3"
      />
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="reset">
        <el-icon><RefreshLeft /></el-icon> 重扫
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="confirmScan"
      >
        <el-icon><Check /></el-icon> 确认提交
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Box, Check, RefreshLeft, Location,
  CircleCheck, Warning, CircleClose
} from '@element-plus/icons-vue'

const props = defineProps<{
  asset: any
}>()

const emit = defineEmits<{
  confirm: [data: any]
  reset: []
  next: []
}>()

const localStatus = ref('normal')
const actualLocation = ref('')
const damageDesc = ref('')
const remark = ref('')
const submitting = ref(false)

const statusOptions = [
  { value: 'normal', label: '正常', icon: CircleCheck, color: '#67c23a' },
  { value: 'location_changed', label: '位置变更', icon: Location, color: '#409eff' },
  { value: 'damaged', label: '损坏', icon: Warning, color: '#e6a23c' },
  { value: 'lost', label: '缺失', icon: CircleClose, color: '#f56c6c' }
]

const confirmScan = () => {
  submitting.value = true
  emit('confirm', {
    asset_id: props.asset.snapshot_id,
    scan_status: localStatus.value,
    actual_location: actualLocation.value,
    damage_desc: damageDesc.value,
    remark: remark.value
  })
}

const reset = () => {
  emit('reset')
}
</script>

<style scoped>
.scan-result {
  padding: 16px;
}

.asset-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
}

.field {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f5f7fa;
}

.field .label {
  color: #909399;
  font-size: 14px;
}

.field .value {
  font-weight: 500;
  color: #303133;
}

.status-selector {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.selector-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.status-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.status-option.active {
  border-color: var(--option-color, #409eff);
  background: #ecf5ff;
}

.option-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 4px;
}

.option-label {
  font-size: 12px;
  color: #606266;
}

.condition-input {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.remark-section {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.action-buttons .el-button {
  flex: 1;
}
</style>
```

### 6.3 连续扫码模式组件

```vue
<template>
  <div class="continuous-scan">
    <!-- 扫描区域 -->
    <div class="scan-area" :class="{ active: isScanning }">
      <video ref="videoRef" class="scan-video" autoplay playsinline muted></video>
      <canvas ref="canvasRef" style="display:none"></canvas>

      <!-- 扫描框 -->
      <div class="scan-frame" v-show="isScanning">
        <div class="scan-line"></div>
        <div class="scan-tip">已扫码: {{ scannedCount }} / {{ totalCount }}</div>
      </div>

      <!-- 启动提示 -->
      <div class="scan-prompt" v-else>
        <el-icon :size="48"><VideoCamera /></el-icon>
        <p>点击按钮启动连续扫码</p>
      </div>
    </div>

    <!-- 控制栏 -->
    <div class="control-bar">
      <el-button
        v-if="!isScanning"
        type="primary"
        size="large"
        @click="startScan"
      >
        <el-icon><VideoCamera /></el-icon>
        开始扫码
      </el-button>
      <template v-else>
        <el-button size="large" @click="pauseScan">
          <el-icon><VideoPause /></el-icon>
          暂停
        </el-button>
        <el-button size="large" type="danger" @click="stopScan">
          <el-icon><Close /></el-icon>
          结束
        </el-button>
      </template>
    </div>

    <!-- 最近扫描列表 -->
    <div class="recent-scans" v-if="recentScans.length > 0">
      <h4 class="section-title">最近扫描 ({{ recentScans.length }})</h4>
      <div class="scan-list">
        <transition-group name="scan-item">
          <div
            v-for="item in recentScans"
            :key="item.id"
            class="scan-item"
          >
            <el-icon class="status-icon" :color="getStatusColor(item.status)">
              <component :is="getStatusIcon(item.status)" />
            </el-icon>
            <span class="scan-code">{{ item.asset_code }}</span>
            <span class="scan-name">{{ item.asset_name }}</span>
            <span class="scan-time">{{ formatTime(item.scanned_at) }}</span>
          </div>
        </transition-group>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { VideoCamera, VideoPause, Close, Check, Warning, CircleClose } from '@element-plus/icons-vue'
import { BrowserMultiFormatReader } from '@zxing/library'

const props = defineProps<{
  assignmentId: string
  totalCount: number
}>()

const emit = defineEmits<{
  scan: [data: any]
  complete: []
}>()

const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()
const isScanning = ref(false)
const isPaused = ref(false)
const codeReader = ref<BrowserMultiFormatReader>()
const recentScans = ref<any[]>([])

const scannedCount = computed(() => recentScans.value.length)

let lastScanTime = 0
const SCAN_DEBOUNCE = 1000 // 1秒防抖

const startScan = async () => {
  isScanning.value = true
  isPaused.value = false

  codeReader.value = new BrowserMultiFormatReader()
  await codeReader.value.decodeFromVideoDevice(
    undefined,
    videoRef.value!,
    (result) => {
      if (result) {
        handleScanResult(result.text)
      }
    }
  )
}

const pauseScan = () => {
  isPaused.value = true
  if (codeReader.value) {
    codeReader.value.reset()
  }
}

const stopScan = () => {
  isScanning.value = false
  if (codeReader.value) {
    codeReader.value.reset()
  }

  // 检查是否完成
  if (scannedCount.value >= props.totalCount) {
    emit('complete')
  }
}

const handleScanResult = async (qrData: string) => {
  const now = Date.now()
  if (now - lastScanTime < SCAN_DEBOUNCE) {
    return // 防抖处理
  }
  lastScanTime = now

  try {
    // 震动反馈
    if (navigator.vibrate) {
      navigator.vibrate(50)
    }

    // 播放提示音
    playBeep()

    // 处理扫描结果
    const data = JSON.parse(qrData)
    const scanData = {
      ...data,
      scan_status: 'normal',
      scanned_at: new Date().toISOString()
    }

    // 添加到最近列表
    recentScans.value.unshift(scanData)
    if (recentScans.value.length > 5) {
      recentScans.value.pop()
    }

    // 触发扫描事件
    emit('scan', scanData)

    // 自动继续扫描
    if (scannedCount.value >= props.totalCount) {
      stopScan()
    }

  } catch (error) {
    console.error('扫描解析失败:', error)
  }
}

const playBeep = () => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)()
  const oscillator = audioContext.createOscillator()
  const gainNode = audioContext.createGain()

  oscillator.connect(gainNode)
  gainNode.connect(audioContext.destination)

  oscillator.frequency.value = 1000
  oscillator.type = 'sine'

  gainNode.gain.setValueAtTime(0.1, audioContext.currentTime)
  oscillator.start()
  oscillator.stop(audioContext.currentTime + 0.1)
}

const getStatusColor = (status: string) => {
  const colors = {
    'normal': '#67c23a',
    'location_changed': '#409eff',
    'damaged': '#e6a23c',
    'lost': '#f56c6c'
  }
  return colors[status] || '#909399'
}

const getStatusIcon = (status: string) => {
  const icons = {
    'normal': Check,
    'location_changed': Location,
    'damaged': Warning,
    'lost': CircleClose
  }
  return icons[status] || Check
}

const formatTime = (time: string) => {
  const date = new Date(time)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

onUnmounted(() => {
  if (codeReader.value) {
    codeReader.value.reset()
  }
})
</script>

<style scoped>
.continuous-scan {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.scan-area {
  flex: 1;
  position: relative;
  background: #000;
  overflow: hidden;
}

.scan-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scan-frame {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  height: 60%;
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #409eff, transparent);
  animation: scan 2s linear infinite;
}

@keyframes scan {
   0% { top: 0; }
  100% { top: 100%; }
}

.scan-tip {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  color: white;
  font-size: 16px;
  text-align: center;
}

.scan-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(255, 255, 255, 0.7);
}

.control-bar {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #1f1f1f;
}

.recent-scans {
  padding: 16px;
  background: #1f1f1f;
}

.section-title {
  margin: 0 0 12px 0;
  color: white;
  font-size: 14px;
}

.scan-list {
  max-height: 200px;
  overflow-y: auto;
}

.scan-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #2a2a2a;
  border-radius: 8px;
  margin-bottom: 8px;
}

.scan-item-enter-active,
.scan-item-leave-active {
  transition: all 0.3s ease;
}

.scan-item-enter-from,
.scan-item-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.scan-code {
  color: #409eff;
  font-family: monospace;
}

.scan-name {
  flex: 1;
  color: white;
}

.scan-time {
  color: #909399;
  font-size: 12px;
}
</style>
```

---

## 7. 离线处理

### 7.1 离线数据结构

```typescript
// IndexedDB 存储结构
interface OfflineScanRecord {
  id: string
  assignment_id: string
  snapshot_id: string
  asset_code: string
  asset_name: string
  scan_status: 'normal' | 'location_changed' | 'damaged' | 'lost'
  actual_location?: string
  damage_desc?: string
  photos?: string[]  // base64
  remark?: string
  scanned_at: string
  synced: boolean
}

interface OfflineTaskCache {
  task_id: string
  task_name: string
  total_count: number
  scanned_count: number
  records: OfflineScanRecord[]
}
```

### 7.2 离线同步逻辑

```typescript
// 离线同步服务
class OfflineSyncService {
  private db: IDBDatabase
  private syncQueue: ScanRecord[] = []

  // 添加离线扫描记录
  async addOfflineScan(record: OfflineScanRecord) {
    await this.db.offlineScans.add({
      ...record,
      synced: false,
      created_at: new Date().toISOString()
    })
    this.updateSyncBadge()
  }

  // 批量同步离线数据
  async syncOfflineData() {
    const records = await this.db.offlineScans
      .where('synced').equals(false)
      .toArray()

    for (const record of records) {
      try {
        await api.post('/api/inventory/my/record-scan/', record)
        await this.db.offlineScans.update(record.id, { synced: true })
      } catch (error) {
        console.error('同步失败:', record.id, error)
      }
    }

    this.updateSyncBadge()
    ElMessage.success(`成功同步 ${records.length} 条记录`)
  }

  // 更新同步徽章
  updateSyncBadge() {
    const count = await this.db.offlineScans
      .where('synced').equals(false)
      .count()

    if (count > 0) {
      navigator.setAppBadge?.(count)
    } else {
      navigator.setAppBadge?.(0)
    }
  }

  // 检查并提示同步
  checkAndPromptSync() {
    this.db.offlineScans
      .where('synced').equals(false)
      .count()
      .then(count => {
        if (count > 0) {
          ElNotification({
            title: '有离线数据待同步',
            message: `您有 ${count} 条盘点记录尚未同步`,
            type: 'warning',
            duration: 0
          })
        }
      })
  }
}
```

---

## 8. 权限验证

在移动端操作时需要验证：

```typescript
// 权限验证 API
interface PermissionCheckResponse {
  has_permission: boolean
  permission_type: 'full' | 'assigned_only' | 'view_only'
  can_edit: boolean
  can_delete: boolean
  allowed_assets: string[]  // 允许操作的资产ID列表
}

// 验证权限
async function validatePermission(assignmentId: string, assetId: string) {
  const { data } = await api.get<PermissionCheckResponse>(
    `/api/inventory/my/check-permission/`,
    { assignment_id: assignmentId, asset_id: assetId }
  )

  if (!data.has_permission) {
    ElMessage.error('您没有权限操作此资产')
    return false
  }

  if (data.permission_type === 'assigned_only' &&
      !data.allowed_assets.includes(assetId)) {
    ElMessage.error('此资产不在您的盘点范围内')
    return false
  }

  return true
}
```

---

## 9. 常见问题处理

### 9.1 二维码无法识别

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ 无法识别此二维码                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  可能的原因:                                               │
│  • 二维码不是本系统资产二维码                               │
│  • 二维码模糊或损坏                                         │
│  • 光线过暗或反光                                           │
│                                                              │
│  [重新扫描]  [手动输入编码]  [跳过此资产]                  │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 资产不在任务范围内

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ 此资产不在您的盘点任务中                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  资产编码: ZC202406001999                                 │
│  资产名称: 测试打印机                                       │
│                                                             │
│  [确认这是误扫]  [联系管理员分配此资产]                     │
└─────────────────────────────────────────────────────────────┘
```

### 9.3 重复扫描提示

```
┌─────────────────────────────────────────────────────────────┐
│  ℹ️ 此资产已扫描过                                         │
│                                                             │
│  上次扫描时间: 2024-06-15 14:30                           │
│  上次扫描状态: 正常                                         │
│                                                             │
│  [查看上次记录]  [更新扫描结果]                            │
└─────────────────────────────────────────────────────────────┘
```
