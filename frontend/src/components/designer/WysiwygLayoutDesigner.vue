<!--
  WysiwygLayoutDesigner.vue - WYSIWYG Layout Designer
  What You See Is What You Get layout editor with real-time preview

  Key Features:
  - Left panel: Draggable field list organized by type
  - Center canvas: Real-time rendered form that IS the preview
  - Right panel: Property editor for selected elements
  - Inline editing: Click fields to select, drag to reorder
  - No separate preview mode - the design area IS the preview
-->

<template>
  <div
    class="wysiwyg-layout-designer"
    data-testid="layout-designer"
  >
    <!-- Toolbar -->
    <div class="designer-toolbar">
      <div class="toolbar-left">
        <el-button
          link
          @click="handleCancel"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-divider direction="vertical" />
        <span class="layout-info">{{ layoutName }} ({{ modeLabel }})</span>
        <el-tag
          v-if="!isDefault"
          type="warning"
          size="small"
        >
          自定义布局
        </el-tag>
      </div>
      <div class="toolbar-center">
        <el-button-group>
          <el-button
            data-testid="layout-undo-button"
            :disabled="!canUndo"
            @click="undo"
          >
            <el-icon><RefreshLeft /></el-icon>
            撤销
          </el-button>
          <el-button
            data-testid="layout-redo-button"
            :disabled="!canRedo"
            @click="redo"
          >
            <el-icon><RefreshRight /></el-icon>
            重做
          </el-button>
        </el-button-group>
      </div>
      <div class="toolbar-right">
        <el-button
          data-testid="layout-reset-button"
          @click="handleReset"
        >
          恢复默认
        </el-button>
        <el-button-group>
          <el-button
            size="small"
            data-testid="layout-preview-current-button"
            :disabled="previewLoading"
            :type="previewMode === 'current' ? 'primary' : 'default'"
            @click="setPreviewMode('current')"
          >
            自定义
          </el-button>
          <el-button
            size="small"
            data-testid="layout-preview-active-button"
            :loading="previewLoading && previewMode === 'active'"
            :disabled="previewLoading"
            :type="previewMode === 'active' ? 'primary' : 'default'"
            @click="setPreviewMode('active')"
          >
            预览
          </el-button>
        </el-button-group>
        <el-tag
          size="small"
          effect="plain"
        >
          {{ previewMode === 'active' ? '预览模式' : '自定义模式' }}
        </el-tag>
        <el-button
          :disabled="previewMode === 'active'"
          data-testid="layout-save-button"
          @click="handleSave"
        >
          保存草稿
        </el-button>
        <el-button
          type="success"
          :loading="publishing"
          :disabled="previewMode === 'active'"
          data-testid="layout-publish-button"
          @click="handlePublish"
        >
          发布
        </el-button>
      </div>
    </div>

    <!-- Main Area -->
    <div class="designer-main">
      <!-- Left Panel - Field List -->
      <div
        v-if="renderMode === 'design'"
        class="field-panel"
        data-testid="layout-field-panel"
      >
        <div class="panel-header">
          <el-input
            v-model="searchQuery"
            placeholder="搜索字段名称或编�?.."
            :prefix-icon="Search"
            size="small"
            clearable
          />
        </div>
        <div class="panel-content">
          <div
            v-for="group in filteredFieldGroups"
            :key="group.type"
            class="field-group"
          >
            <div
              class="group-header"
              @click="toggleGroup(group.type)"
            >
              <el-icon>
                <component :is="group.icon" />
              </el-icon>
              <span>{{ group.label }}</span>
              <el-tag size="small">
                {{ group.fields.length }}
              </el-tag>
              <el-icon
                class="expand-icon"
                :class="{ expanded: isGroupExpanded(group.type) }"
              >
                <ArrowRight />
              </el-icon>
            </div>
            <div
              v-show="isGroupExpanded(group.type)"
              class="group-fields"
            >
              <div
                v-for="field in group.fields"
                :key="field.code"
                class="field-item"
                :data-testid="`layout-palette-field-${field.code}`"
                :draggable="canAddField(field)"
                :title="getDisabledReason(field) || ''"
                :class="{
                  'is-selected': isFieldAdded(field.code),
                  'is-disabled': !canAddField(field)
                }"
                @dragstart="handleFieldDragStart($event, field)"
                @dragend="handleDragEnd"
                @click="handleFieldClick(field)"
              >
                <el-icon class="field-icon">
                  <Edit />
                </el-icon>
                <span class="field-label">{{ field.name }}</span>
                <span class="field-code">{{ field.code }}</span>
                <el-icon
                  v-if="isFieldAdded(field.code)"
                  class="added-icon"
                >
                  <Check />
                </el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Center Canvas - Real-time Preview Area -->
      <div
        class="canvas-area"
        data-testid="layout-canvas"
        :class="{ 'drag-over': isDragOverCanvas }"
        @drop="handleCanvasDrop"
        @dragover="handleCanvasDragOver"
        @dragleave="handleCanvasDragLeave"
      >
        <div class="canvas-header">
          <div class="canvas-header-left">
            <span v-if="renderMode === 'design'">布局设计画布（点击字段可编辑属性）</span>
            <span v-else-if="renderMode === 'edit'">编辑态渲染预览（与对象编辑页一致）</span>
            <span v-else>详情态渲染预览（与对象详情页一致）</span>
          </div>
          <div class="canvas-header-right">
            <el-radio-group
              :model-value="renderMode"
              size="small"
              @update:model-value="setRenderMode"
            >
              <el-radio-button label="design">
                设计态
              </el-radio-button>
              <el-radio-button label="edit">
                编辑态
              </el-radio-button>
              <el-radio-button label="detail">
                详情态
              </el-radio-button>
            </el-radio-group>
            <el-button
              v-if="renderMode === 'design'"
              size="small"
              text
              @click="addSection"
            >
              <el-icon><Plus /></el-icon>
              新增分区
            </el-button>
          </div>
        </div>
        <div
          ref="canvasContentRef"
          class="canvas-content"
        >
          <template v-if="renderMode === 'design'">
            <!-- Render the actual form using real components -->
            <div
              v-if="layoutConfig.sections && layoutConfig.sections.length > 0"
              class="form-renderer detail-layout-container"
              :class="{ 'has-sidebar': true }"
            >
              <!-- Main Column -->
              <div class="main-column">
                <el-form
                  :model="sampleData"
                  label-width="120px"
                  label-position="right"
                  class="designer-preview-form"
                >
                  <div
                    v-for="(section, sectionIndex) in mainSections"
                    :key="section.id"
                    class="layout-section"
                    data-testid="layout-section"
                    :class="{
                      'is-selected': selectedId === section.id,
                      'is-collapsed': section.collapsed
                    }"
                    :data-section-position="section.position"
                    :data-section-id="section.id"
                  >
                    <!-- Section Header -->
                    <div
                      class="section-header"
                      data-testid="layout-section-header"
                      @click.stop="selectSection(section.id)"
                    >
                      <div class="section-title">
                        <el-icon v-if="section.collapsible">
                          <component :is="section.collapsed ? 'ArrowRight' : 'ArrowDown'" />
                        </el-icon>
                        <span class="title-text">{{ section.title || 'Untitled Section' }}</span>
                      </div>
                      <div
                        v-if="selectedId === section.id"
                        class="section-actions"
                        @click.stop
                      >
                        <el-button
                          size="small"
                          text
                          @click="deleteSection(section.id)"
                        >
                          删除分区
                        </el-button>
                        <el-button
                          v-if="section.collapsible"
                          size="small"
                          text
                          @click="toggleSectionCollapse(section.id)"
                        >
                          {{ section.collapsed ? 'Expand' : 'Collapse' }}
                        </el-button>
                      </div>
                    </div>

                    <!-- Section Content -->
                    <div
                      v-show="!section.collapsed"
                      class="section-content"
                      :class="`columns-${getColumns(section)}`"
                      :data-section-id="section.id"
                      @drop="handleSectionDrop"
                      @dragover="handleSectionDragOver"
                      @dragleave="handleSectionDragLeave"
                    >
                      <!-- Render fields in this section -->
                      <template v-if="section.type === 'tab'">
                        <!-- Tab Section -->
                        <el-tabs
                          v-model="activeTabs[section.id]"
                          type="card"
                        >
                          <el-tab-pane
                            v-for="tab in section.tabs"
                            :key="tab.id"
                            :label="tab.title"
                            :name="tab.id"
                            class="tab-pane-content"
                            :data-tab-id="tab.id"
                            :data-section-id="section.id"
                            @drop="handleTabDrop"
                            @dragover="handleSectionDragOver"
                            @dragleave="handleSectionDragLeave"
                          >
                            <div
                              class="tab-fields designer-fields-container dynamic-form-section__fields"
                              :class="`columns-${getColumns(section)}`"
                              data-container-kind="tab"
                              :data-section-id="section.id"
                              :data-tab-id="tab.id"
                            >
                              <div
                                v-for="field in tab.fields"
                                :key="field.id"
                                class="field-renderer dynamic-form-section__field"
                                data-testid="layout-canvas-field"
                                :class="{
                                  'is-selected': selectedId === field.id
                                }"
                                :data-field-id="field.id"
                                :data-field-code="field.fieldCode"
                                :style="{ gridColumn: `span ${getGridSpan(field, section)} / ${getColumns(section)}` }"
                                @click.stop="selectField(field, section)"
                              >
                                <el-form-item
                                  :label="field.label"
                                  :prop="field.fieldCode"
                                  :required="!!field.required"
                                >
                                  <RuntimeFieldControl
                                    :field="fieldToFieldRenderer(field)"
                                    :model-value="sampleData[field.fieldCode] ?? getSampleValue(field)"
                                    :form-data="sampleData"
                                    :disabled="field.readonly || mode === 'readonly'"
                                    @update:model-value="handleFieldUpdate(field, $event)"
                                  />
                                </el-form-item>
                                <!-- Selection overlay -->
                                <div
                                  v-if="selectedId === field.id"
                                  class="field-overlay"
                                >
                                  <div class="overlay-label">
                                    {{ field.label }}
                                    <span
                                      v-if="field.fieldCode"
                                      class="overlay-code"
                                    >[{{ field.fieldCode }}]</span>
                                  </div>
                                  <div
                                    v-if="selectedId === field.id"
                                    class="overlay-actions"
                                  >
                                    <el-button
                                      size="small"
                                      circle
                                      data-testid="layout-remove-field-button"
                                      @click.stop="removeField(field.id, section.id, sectionIndex)"
                                    >
                                      <el-icon><Delete /></el-icon>
                                    </el-button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </el-tab-pane>
                        </el-tabs>
                      </template>

                      <template v-else-if="section.type === 'collapse'">
                        <!-- Collapse/Accordion Section -->
                        <el-collapse
                          v-model="activeCollapses[section.id]"
                          :accordion="false"
                        >
                          <el-collapse-item
                            v-for="item in section.items"
                            :key="item.id"
                            :name="item.id"
                            class="collapse-item-content"
                            :data-collapse-id="item.id"
                          >
                            <template #title>
                              <span>{{ item.title }}</span>
                            </template>
                            <div
                              class="collapse-fields designer-fields-container dynamic-form-section__fields"
                              :class="`columns-${getColumns(section)}`"
                              data-container-kind="collapse"
                              :data-section-id="section.id"
                              :data-collapse-id="item.id"
                              @drop="handleCollapseDrop"
                              @dragover="handleSectionDragOver"
                              @dragleave="handleSectionDragLeave"
                            >
                              <div
                                v-for="field in item.fields"
                                :key="field.id"
                                class="field-renderer dynamic-form-section__field"
                                data-testid="layout-canvas-field"
                                :class="{
                                  'is-selected': selectedId === field.id
                                }"
                                :data-field-id="field.id"
                                :data-field-code="field.fieldCode"
                                :style="{ gridColumn: `span ${getGridSpan(field, section)} / ${getColumns(section)}` }"
                                @click.stop="selectField(field, section)"
                              >
                                <el-form-item
                                  :label="field.label"
                                  :prop="field.fieldCode"
                                  :required="!!field.required"
                                >
                                  <RuntimeFieldControl
                                    :field="fieldToFieldRenderer(field)"
                                    :model-value="sampleData[field.fieldCode] ?? getSampleValue(field)"
                                    :form-data="sampleData"
                                    :disabled="field.readonly || mode === 'readonly'"
                                    @update:model-value="handleFieldUpdate(field, $event)"
                                  />
                                </el-form-item>
                                <div
                                  v-if="selectedId === field.id"
                                  class="field-overlay"
                                >
                                  <div class="overlay-label">
                                    {{ field.label }}
                                    <span
                                      v-if="field.fieldCode"
                                      class="overlay-code"
                                    >[{{ field.fieldCode }}]</span>
                                  </div>
                                  <div
                                    v-if="selectedId === field.id"
                                    class="overlay-actions"
                                  >
                                    <el-button
                                      size="small"
                                      circle
                                      data-testid="layout-remove-field-button"
                                      @click.stop="removeField(field.id, section.id, sectionIndex)"
                                    >
                                      <el-icon><Delete /></el-icon>
                                    </el-button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </el-collapse-item>
                        </el-collapse>
                      </template>

                      <template v-else>
                        <!-- Regular Section - Direct field rendering -->
                        <div
                          class="section-fields designer-fields-container dynamic-form-section__fields"
                          :class="`columns-${getColumns(section)}`"
                          data-container-kind="section"
                          :data-section-id="section.id"
                        >
                          <div
                            v-for="field in section.fields"
                            :key="field.id"
                            class="field-renderer dynamic-form-section__field"
                            data-testid="layout-canvas-field"
                            :class="{
                              'is-selected': selectedId === field.id
                            }"
                            :data-field-id="field.id"
                            :data-field-code="field.fieldCode"
                            :style="{ gridColumn: `span ${getGridSpan(field, section)} / ${getColumns(section)}` }"
                            @click.stop="selectField(field, section)"
                          >
                            <el-form-item
                              :label="field.label"
                              :prop="field.fieldCode"
                              :required="!!field.required"
                            >
                              <RuntimeFieldControl
                                :field="fieldToFieldRenderer(field)"
                                :model-value="sampleData[field.fieldCode] ?? getSampleValue(field)"
                                :form-data="sampleData"
                                :disabled="field.readonly || mode === 'readonly'"
                                @update:model-value="handleFieldUpdate(field, $event)"
                              />
                            </el-form-item>
                            <!-- Selection overlay -->
                            <div
                              v-if="selectedId === field.id"
                              class="field-overlay"
                            >
                              <div class="overlay-label">
                                {{ field.label }}
                                <span
                                  v-if="field.fieldCode"
                                  class="overlay-code"
                                >[{{ field.fieldCode }}]</span>
                                <el-tag
                                  v-if="field.required"
                                  type="danger"
                                  size="small"
                                >
                                  *
                                </el-tag>
                              </div>
                              <div
                                v-if="selectedId === field.id"
                                class="overlay-actions"
                              >
                                <el-button
                                  size="small"
                                  circle
                                  title="Remove field"
                                  data-testid="layout-remove-field-button"
                                  @click.stop="removeField(field.id, section.id, sectionIndex)"
                                >
                                  <el-icon><Delete /></el-icon>
                                </el-button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </template>
                    </div>
                  </div>
              
                  <!-- Placeholder for drag/drop when Main column is empty -->
                  <div
                    v-if="mainSections.length === 0"
                    class="empty-column-placeholder"
                    data-section-position="main"
                  >
                    Main Column (Drag sections here)
                  </div>
                </el-form>
              </div>

              <!-- Sidebar Column -->
              <div class="sidebar-column">
                <el-form
                  :model="sampleData"
                  label-position="top"
                  class="designer-preview-sidebar-form"
                >
                  <div
                    v-for="(section, sectionIndex) in sidebarSections"
                    :key="section.id"
                    class="sidebar-section-block layout-section"
                    data-testid="layout-sidebar-section"
                    :class="{
                      'is-selected': selectedId === section.id,
                      'is-collapsed': section.collapsed
                    }"
                    :data-section-position="section.position"
                    :data-section-id="section.id"
                  >
                    <div
                      class="section-header"
                      data-testid="layout-section-header"
                      @click.stop="selectSection(section.id)"
                    >
                      <div class="section-title">
                        <span class="title-text">{{ section.title || 'Untitled Section' }}</span>
                      </div>
                      <div
                        v-if="selectedId === section.id"
                        class="section-actions"
                        @click.stop
                      >
                        <el-button
                          size="small"
                          text
                          @click="deleteSection(section.id)"
                        >
                          删除分区
                        </el-button>
                      </div>
                    </div>

                    <!-- Sidebar Section Content -->
                    <div
                      v-show="!section.collapsed"
                      class="section-content"
                      :class="`columns-${getColumns(section)}`"
                      :data-section-id="section.id"
                      @drop="handleSectionDrop"
                      @dragover="handleSectionDragOver"
                      @dragleave="handleSectionDragLeave"
                    >
                      <div
                        class="section-fields designer-fields-container dynamic-form-section__fields"
                        :class="`columns-${getColumns(section)}`"
                        data-container-kind="section"
                        :data-section-id="section.id"
                      >
                        <div
                          v-for="field in section.fields"
                          :key="field.id"
                          class="field-renderer sidebar-field-col dynamic-form-section__field"
                          data-testid="layout-canvas-field"
                          :class="{ 'is-selected': selectedId === field.id }"
                          :data-field-id="field.id"
                          :data-field-code="field.fieldCode"
                          :style="{ gridColumn: `span ${getGridSpan(field, section)} / ${getColumns(section)}` }"
                          @click.stop="selectField(field, section)"
                        >
                          <div class="sidebar-field-item">
                            <div class="field-label">
                              {{ field.label }}
                              <span
                                v-if="field.required"
                                style="color: red"
                              >*</span>
                            </div>
                            <div class="field-value">
                              <RuntimeFieldControl
                                :field="fieldToFieldRenderer(field)"
                                :model-value="sampleData[field.fieldCode] ?? getSampleValue(field)"
                                :form-data="sampleData"
                                :disabled="field.readonly || mode === 'readonly'"
                                @update:model-value="handleFieldUpdate(field, $event)"
                              />
                            </div>
                          </div>

                          <!-- Selection overlay -->
                          <div
                            v-if="selectedId === field.id"
                            class="field-overlay"
                          >
                            <div class="overlay-actions">
                              <el-button
                                size="small"
                                circle
                                title="Remove field"
                                data-testid="layout-remove-field-button"
                                @click.stop="removeField(field.id, section.id, sectionIndex)"
                              >
                                <el-icon><Delete /></el-icon>
                              </el-button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <!-- Placeholder for drag/drop when Sidebar column is empty -->
                  <div
                    v-if="sidebarSections.length === 0"
                    class="empty-column-placeholder"
                    data-section-position="sidebar"
                  >
                    Sidebar Column (Configure 'Position' on a section to Sidebar)
                  </div>
                </el-form>
              </div>
            </div>

            <!-- Empty State -->
            <div
              v-else
              class="empty-canvas"
            >
              <el-empty description="Layout is empty. Add a section to start designing.">
                <el-button
                  type="primary"
                  @click="addSection"
                >
                  新增分区
                </el-button>
              </el-empty>
            </div>
          </template>
          <template v-else-if="renderMode === 'edit'">
            <div class="runtime-preview-card detail-mode-preview dynamic-detail-page">
              <BaseDetailPage
                v-model:form-data="sampleData"
                :title="layoutName"
                :sections="detailPreviewSections"
                :data="sampleData"
                :form-rules="previewFormRules"
                :audit-info="previewAuditInfo"
                :show-back="false"
                :show-edit="false"
                :show-delete="false"
                :show-related-objects="false"
                :edit-mode="true"
                :object-code="objectCode"
                :object-name="layoutName"
                @save="handleDetailPreviewSave"
                @cancel="handleDetailPreviewCancel"
              />
            </div>
          </template>
          <template v-else>
            <div class="runtime-preview-card detail-mode-preview dynamic-detail-page">
              <BaseDetailPage
                :title="layoutName"
                :sections="detailPreviewSections"
                :data="sampleData"
                :audit-info="previewAuditInfo"
                :show-back="false"
                :show-edit="false"
                :show-delete="false"
                :show-related-objects="false"
                :object-code="objectCode"
                :object-name="layoutName"
              />
            </div>
          </template>
        </div>
      </div>

      <!-- Right Panel - Property Editor -->
      <div
        v-if="renderMode === 'design'"
        class="property-panel"
        data-testid="layout-property-panel"
      >
        <div class="panel-header">
          <span>Properties</span>
        </div>
        <div class="panel-content">
          <!-- No Selection -->
          <div
            v-if="!selectedItem"
            class="no-selection"
          >
            <el-empty
              description="Select a field or section to edit its properties."
              :image-size="80"
            />
          </div>

          <!-- Field Properties -->
          <div
            v-else-if="elementType === 'field'"
            class="property-form"
          >
            <div class="property-header">
              <el-icon><Edit /></el-icon>
              <span>Field Properties</span>
              <el-tag size="small">
                {{ selectedItem.fieldCode }}
              </el-tag>
            </div>
            <FieldPropertyEditor
              v-model="fieldProps"
              data-testid="layout-field-property-editor"
              :field-type="fieldProps.fieldType"
              :mode="mode"
              :available-spans="availableSpans"
              :available-span-columns="availableSpanColumns"
              @update-property="handleFieldPropertyUpdate"
            />
          </div>

          <!-- Section Properties -->
          <div
            v-else-if="elementType === 'section'"
            class="property-form"
          >
            <div class="property-header">
              <el-icon><Grid /></el-icon>
              <span>Section Properties</span>
            </div>
            <SectionPropertyEditor
              v-model="sectionProps"
              data-testid="layout-section-property-editor"
              :section-type="sectionProps.type || 'section'"
              @update-property="handleSectionPropertyUpdate"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sortable from 'sortablejs'
import {
  ArrowLeft, ArrowRight, ArrowDown, Search, Plus, Delete, Check, RefreshLeft, RefreshRight,
  Edit, Grid, View, Hide, Lock, Unlock, Document, Histogram, Calendar, Timer,
  Message, Link, Connection, User, OfficeBuilding, Folder, Picture, Select,
  CircleCheck, Ticket, FolderOpened, Operation, Minus
} from '@element-plus/icons-vue'
import FieldPropertyEditor from '@/components/designer/FieldPropertyEditor.vue'
import SectionPropertyEditor from '@/components/designer/SectionPropertyEditor.vue'
import RuntimeFieldControl from '@/components/engine/RuntimeFieldControl.vue'
import BaseDetailPage, { type DetailSection, type DetailField } from '@/components/common/BaseDetailPage.vue'
import { adaptFieldDefinition, mergeRuntimeField } from '@/adapters/fieldAdapter'
import { normalizeSpan } from '@/adapters/layoutNormalizer'
import { dynamicApi } from '@/api/dynamic'
import { pageLayoutApi } from '@/api/system'
import { useLayoutHistory } from '@/composables/useLayoutHistory'
import { normalizeFieldType } from '@/utils/fieldType'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import { buildRenderSchema, type RenderSchema } from '@/platform/layout/renderSchema'
import { projectDetailSectionsFromRenderSchema } from '@/platform/layout/detailSchemaProjector'
import { canAddFieldInDesigner, getFieldDisabledReason } from '@/platform/layout/designerFieldGuard'
import { ensureLayoutConfigIds as ensurePersistLayoutConfigIds, preparePersistLayoutConfig } from '@/platform/layout/layoutPersistGuard'
import { mergeFieldSources } from '@/platform/layout/unifiedFieldOrder'
import { isSystemField } from '@/utils/transform'
import {
  getDefaultLayoutConfig,
  cloneLayoutConfig,
  generateId,
  type LayoutType
} from '@/utils/layoutValidation'
import { normalizeLayoutType } from '@/utils/layoutMode'
import type { LayoutFieldConfig } from '@/types/metadata'
import type { LayoutMode } from '@/types/layout'
import type { FieldDefinition as RuntimeFieldDefinition } from '@/types'

// ============================================================================
// Types
// ============================================================================

interface FieldDefinition {
  code: string
  name: string
  fieldType: string
  isRequired?: boolean
  isReadonly?: boolean
  isSystem?: boolean
  isSearchable?: boolean
  showInList?: boolean
  showInForm?: boolean
  showInDetail?: boolean
  // Field metadata for proper rendering
  options?: Array<{ value: any; label: string }>
  referenceObject?: string
  relatedObject?: string
  componentProps?: Record<string, any>
  dictionaryType?: string
  defaultValue?: any
  placeholder?: string
  helpText?: string
}

// Use LayoutFieldConfig from @/types/metadata for fields with full metadata
// This local interface is kept for backward compatibility but extends the concept
interface LayoutField extends Omit<LayoutFieldConfig, 'fieldType'> {
  fieldType?: string // Make fieldType optional for backward compatibility
  // Additional properties that may come from legacy layouts
  min_length?: number
  max_length?: number
  min_value?: number
  max_value?: number
  regex_pattern?: string
}

interface LayoutSection {
  id: string
  type: string
  title?: string
  collapsible?: boolean
  collapsed?: boolean
  border?: boolean
  columns?: number
  position?: 'main' | 'sidebar'
  fields?: LayoutField[]
  tabs?: LayoutTab[]
  items?: LayoutCollapseItem[]
}

interface LayoutTab {
  id: string
  title: string
  fields?: LayoutField[]
}

interface LayoutCollapseItem {
  id: string
  title: string
  fields?: LayoutField[]
}

interface LayoutConfig {
  sections?: LayoutSection[]
  columns?: any[]
  actions?: any[]
  modeOverrides?: Record<string, any>
  layoutOverrides?: Record<string, any>
}

interface FieldGroup {
  type: string
  label: string
  icon: string
  color?: string
  fields: FieldDefinition[]
}

// ============================================================================
// Props & Emits
// ============================================================================

interface Props {
  layoutId?: string
  mode?: LayoutMode
  objectCode?: string
  layoutName?: string
  businessObjectId?: string
  initialPreviewMode?: 'current' | 'active'
  layoutConfig?: LayoutConfig
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'edit',
  layoutName: '新建布局',
  objectCode: '',
  businessObjectId: '',
  initialPreviewMode: 'current',
  layoutConfig: () => ({ sections: [] })
})

const emit = defineEmits<{
  save: [data: Record<string, unknown>]
  cancel: []
  published: [data: Record<string, unknown>]
}>()

// ============================================================================
// State
// ============================================================================

const layoutConfig = ref<LayoutConfig>(
  normalizeAndEnsureLayoutConfig(getDefaultLayoutConfig(props.mode) as LayoutConfig)
)
const selectedId = ref<string>('')
const renderMode = ref<'design' | 'edit' | 'detail'>('design')
const previewMode = ref<'current' | 'active'>('current')
const currentLayoutSnapshot = ref<LayoutConfig | null>(null)
const previewLoading = ref(false)
const selectedSection = ref<LayoutSection | null>(null)
const saving = ref(false)
const publishing = ref(false)
const searchQuery = ref('')
const expandedGroups = ref<Set<string>>(new Set(['text', 'number', 'select']))

const isDefault = ref(false)
const isPublished = ref(false)
const layoutVersion = ref('1.0.0')
const sharedEditLayoutId = ref('')

// Track field drag source
const draggedField = ref<FieldDefinition | null>(null)
const isDragOverCanvas = ref(false)
const dragOverSection = ref<string | null>(null)

// Available fields
const availableFields = ref<FieldDefinition[]>([])

// Sample data for preview
const sampleData = ref<Record<string, any>>({})
const canvasContentRef = ref<HTMLElement | null>(null)

type ContainerKind = 'section' | 'tab' | 'collapse'
type ContainerMeta = {
  kind: ContainerKind
  sectionId: string
  tabId?: string
  collapseId?: string
}

let sortableInstances: Sortable[] = []

const destroySortables = () => {
  for (const inst of sortableInstances) inst.destroy()
  sortableInstances = []
}

const parseContainerMeta = (el: HTMLElement | null): ContainerMeta | null => {
  if (!el) return null
  const kind = (el.dataset.containerKind || '') as ContainerKind
  const sectionId = el.dataset.sectionId || ''

  if (!kind || !sectionId) return null
  if (kind === 'tab') {
    const tabId = el.dataset.tabId || ''
    if (!tabId) return null
    return { kind, sectionId, tabId }
  }
  if (kind === 'collapse') {
    const collapseId = el.dataset.collapseId || ''
    if (!collapseId) return null
    return { kind, sectionId, collapseId }
  }
  return { kind: 'section', sectionId }
}

const getFieldArrayRef = (config: LayoutConfig, meta: ContainerMeta): LayoutField[] | null => {
  const section = (config.sections || []).find((s) => s.id === meta.sectionId)
  if (!section) return null

  if (meta.kind === 'section') {
    section.fields = section.fields || []
    return section.fields
  }

  if (meta.kind === 'tab') {
    section.tabs = section.tabs || []
    const tab = (section.tabs || []).find((t) => t.id === meta.tabId)
    if (!tab) return null
    tab.fields = tab.fields || []
    return tab.fields
  }

  if (meta.kind === 'collapse') {
    section.items = section.items || []
    const item = (section.items || []).find((i) => i.id === meta.collapseId)
    if (!item) return null
    item.fields = item.fields || []
    return item.fields
  }

  return null
}

const applySortableMove = (evt: any) => {
  const fromMeta = parseContainerMeta(evt?.from as HTMLElement)
  const toMeta = parseContainerMeta(evt?.to as HTMLElement)
  const oldIndex = typeof evt?.oldIndex === 'number' ? evt.oldIndex : null
  const newIndex = typeof evt?.newIndex === 'number' ? evt.newIndex : null

  if (!fromMeta || !toMeta) return
  if (oldIndex === null || newIndex === null) return

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value)
  const fromArr = getFieldArrayRef(newConfig, fromMeta)
  const toArr = getFieldArrayRef(newConfig, toMeta)
  if (!fromArr || !toArr) return

  // Prefer index-based move (matches DOM order), fallback to id match for safety.
  const moved =
    fromArr[oldIndex] ||
    fromArr.find((f) => f?.id && (evt?.item as HTMLElement | undefined)?.dataset?.fieldId === f.id)

  if (!moved) return

  const removeIndex = fromArr.indexOf(moved)
  if (removeIndex >= 0) fromArr.splice(removeIndex, 1)

  const insertIndex = Math.max(0, Math.min(newIndex, toArr.length))
  toArr.splice(insertIndex, 0, moved)

  commitLayoutChange(newConfig, `Move field ${moved.fieldCode || moved.id}`, previousConfig)
}

const initSortables = async () => {
  if (renderMode.value !== 'design') {
    destroySortables()
    return
  }

  await nextTick()
  destroySortables()

  const root = canvasContentRef.value
  if (!root) return

  const containers = Array.from(root.querySelectorAll<HTMLElement>('.designer-fields-container'))
  for (const container of containers) {
    const inst = Sortable.create(container, {
      group: { name: 'layout-fields', pull: true, put: true },
      animation: 180,
      draggable: '.field-renderer',
      // Avoid grabbing from inputs; drag from labels/empty area instead.
      filter: 'input, textarea, button, select, option, .el-input, .el-textarea, .el-select, .el-date-editor',
      preventOnFilter: true,
      onEnd: applySortableMove
    })
    sortableInstances.push(inst)
  }
}

function handleFieldUpdate(field: any, value: any) {
  if (!field?.fieldCode) return
  sampleData.value[field.fieldCode] = value
}

function getColumns(section: any): number {
  return Number(section?.columns || section?.columnCount || section?.column || 2) || 2
}

function getGridSpan(field: any, section: any): number {
  return normalizeSpan(field?.span ?? 1, getColumns(section))
}

// Active tabs and collapses state
const activeTabs = ref<Record<string, string>>({})
const activeCollapses = ref<Record<string, string[]>>({})

// History management
const history = useLayoutHistory(layoutConfig, { maxHistory: 50 })
const { canUndo, canRedo, undo, redo, historyLength } = history

function commitLayoutChange(newConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) {
  if (historyLength.value === 0) {
    const baseline = cloneLayoutConfig(previousConfig || layoutConfig.value)
    history.push(baseline, 'Initial state')
  }
  layoutConfig.value = newConfig
  history.push(newConfig, description)
}

// Property form state
const fieldProps = ref<Partial<LayoutField>>({})
const sectionProps = ref<Partial<LayoutSection>>({})

// ============================================================================
// Computed
// ============================================================================

const modeLabel = computed(() => {
  const labels: Record<LayoutMode, string> = {
    edit: 'Edit Layout',
    readonly: 'Readonly Layout',
    search: 'Search Layout'
  }
  return labels[props.mode] || props.mode
})

const selectedItem = computed(() => {
  if (!selectedId.value) return null
  return findItemById(layoutConfig.value, selectedId.value)
})

const elementType = computed(() => {
  if (!selectedItem.value) return null
  if ('fieldCode' in selectedItem.value) return 'field'
  // Treat all non-field nodes in the canvas as section-like for property editing.
  // This covers regular sections as well as tab/collapse container sections.
  if ('columns' in selectedItem.value || 'fields' in selectedItem.value || 'tabs' in selectedItem.value || 'items' in selectedItem.value) return 'section'
  return 'section'
})

const availableSpanColumns = computed(() => {
  return selectedSection.value ? getColumns(selectedSection.value) : 2
})

const availableSpans = computed(() => {
  const columns = availableSpanColumns.value
  return Array.from({ length: columns }, (_, index) => index + 1)
})

const addedFieldCodes = computed(() => {
  const codes: string[] = []
  for (const section of layoutConfig.value.sections || []) {
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) {
        for (const field of tab.fields || []) {
          codes.push(field.fieldCode)
        }
      }
    } else if (section.type === 'collapse') {
      for (const item of section.items || []) {
        for (const field of item.fields || []) {
          codes.push(field.fieldCode)
        }
      }
    } else {
      for (const field of section.fields || []) {
        codes.push(field.fieldCode)
      }
    }
  }
  return codes
})

const mainSections = computed(() => {
  return (layoutConfig.value.sections || []).filter(s => s.position !== 'sidebar')
})

const sidebarSections = computed(() => {
  return (layoutConfig.value.sections || []).filter(s => s.position === 'sidebar')
})

// Group metadata for field types
const groupMetadata: Record<string, { label: string; icon: any; color: string }> = {
  text: { label: 'Text', icon: Edit, color: '#409eff' },
  textarea: { label: 'Textarea', icon: Document, color: '#409eff' },
  rich_text: { label: 'Rich Text', icon: Document, color: '#409eff' },
  number: { label: 'Number', icon: Histogram, color: '#67c23a' },
  boolean: { label: 'Boolean', icon: CircleCheck, color: '#67c23a' },
  date: { label: 'Date', icon: Calendar, color: '#e6a23c' },
  datetime: { label: 'DateTime', icon: Timer, color: '#e6a23c' },
  email: { label: 'Email', icon: Message, color: '#409eff' },
  url: { label: 'URL', icon: Link, color: '#409eff' },
  reference: { label: 'Reference', icon: Connection, color: '#909399' },
  user: { label: 'User', icon: User, color: '#f56c6c' },
  department: { label: 'Department', icon: OfficeBuilding, color: '#f56c6c' },
  file: { label: 'File', icon: Folder, color: '#e6a23c' },
  image: { label: 'Image', icon: Picture, color: '#e6a23c' },
  select: { label: 'Select', icon: Select, color: '#67c23a' },
  multi_select: { label: 'Multi Select', icon: Select, color: '#67c23a' },
  radio: { label: 'Radio', icon: CircleCheck, color: '#67c23a' },
  checkbox: { label: 'Checkbox', icon: Check, color: '#67c23a' },
  sub_table: { label: 'Sub Table', icon: FolderOpened, color: '#909399' },
  formula: { label: 'Formula', icon: Ticket, color: '#9c27b0' }
}

const fieldGroups = computed<FieldGroup[]>(() => {
  const groups: Record<string, FieldGroup> = {}

  availableFields.value.forEach(field => {
    let groupType = normalizeFieldType(field.fieldType || 'text')

    if (groupType === 'currency' || groupType === 'percent' || groupType === 'slider' || groupType === 'rate') {
      groupType = 'number'
    }
    if (groupType === 'year' || groupType === 'month' || groupType === 'time' || groupType === 'daterange') {
      groupType = 'date'
    }
    if (groupType === 'location' || groupType === 'asset') {
      groupType = 'reference'
    }

    const metadata = groupMetadata[groupType] || { label: groupType, icon: Edit, color: '#909399' }

    if (!groups[groupType]) {
      groups[groupType] = {
        type: groupType,
        label: metadata.label,
        icon: metadata.icon,
        color: metadata.color,
        fields: []
      }
    }
    groups[groupType].fields.push(field)
  })

  return Object.values(groups)
})

// Filter groups by search query
const filteredFieldGroups = computed(() => {
  if (!searchQuery.value) return fieldGroups.value

  const query = searchQuery.value.toLowerCase()
  return fieldGroups.value
    .map(group => ({
      ...group,
      fields: group.fields.filter(f =>
        f.name?.toLowerCase().includes(query) ||
        f.code?.toLowerCase().includes(query)
      )
    }))
    .filter(group => group.fields.length > 0)
})

// ============================================================================
// Methods
// ============================================================================

function findItemById(config: LayoutConfig, id: string): any {
  for (const section of config.sections || []) {
    if (section.id === id) return section
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) {
        if (tab.id === id) return tab
        for (const field of tab.fields || []) {
          if (field.id === id) return field
        }
      }
    } else if (section.type === 'collapse') {
      for (const item of section.items || []) {
        if (item.id === id) return item
        for (const field of item.fields || []) {
          if (field.id === id) return field
        }
      }
    } else {
      for (const field of section.fields || []) {
        if (field.id === id) return field
      }
    }
  }
  return null
}

function fieldToFieldRenderer(field: LayoutField): any {
  const fullField = availableFields.value.find(f => f.code === field.fieldCode)
  const base = fullField ? adaptFieldDefinition(fullField as any) : null

  const normalizedType = normalizeFieldType(field.fieldType || 'text')
  const mergedComponentProps = {
    ...(field.componentProps || {}),
    ...(field as any).component_props || {}
  }

  const override = {
    code: field.fieldCode,
    label: field.label,
    fieldType: normalizedType,
    field_type: normalizedType,
    required: field.required,
    readonly: field.readonly,
    hidden: field.visible === false,
    span: field.span,
    placeholder: field.placeholder,
    defaultValue: field.defaultValue,
    helpText: field.helpText,
    options: field.options,
    referenceObject: field.referenceObject || field.relatedObject,
    componentProps: mergedComponentProps,
    component_props: mergedComponentProps
  }

  const runtimeField = base ? mergeRuntimeField(base, override) : {
    code: field.fieldCode,
    label: field.label || field.fieldCode,
    fieldType: normalizedType,
    field_type: normalizedType,
    required: field.required,
    readonly: field.readonly,
    options: field.options,
    referenceObject: field.referenceObject || field.relatedObject,
    componentProps: mergedComponentProps,
    component_props: mergedComponentProps
  }

  return runtimeField
}

/**
 * Generate a sample value by canonical field type.
 */
function getSampleValue(field: LayoutField): any {
  const type = normalizeFieldType(field.fieldType || 'text')
  const label = field.label || ''
  const code = field.fieldCode || ''

  if (field.defaultValue !== undefined) return field.defaultValue

  const labelLower = label.toLowerCase()
  const codeLower = code.toLowerCase()

  if (codeLower.includes('name') || labelLower.includes('name')) {
    return 'Sample Name'
  }
  if (codeLower.includes('code') || labelLower.includes('code')) {
    return 'CODE001'
  }

  const sampleValues: Record<string, any> = {
    text: label || 'Sample Text',
    textarea: `${label || 'Sample'} details`,
    rich_text: `<p>${label || 'Sample rich text'}</p>`,
    number: 100,
    percent: 15.5,
    currency: 9999.99,
    boolean: true,
    date: '2024-01-15',
    datetime: '2024-01-15 14:30:00',
    time: '14:30:00',
    year: '2024',
    month: '2024-01',
    select: 'option-1',
    multi_select: ['option-1', 'option-2'],
    radio: 'option-1',
    checkbox: true,
    reference: null,
    user: null,
    department: null,
    location: null,
    asset: null,
    image: null,
    file: null,
    attachment: null,
    formula: 0,
    sub_table: []
  }

  return sampleValues[type] !== undefined ? sampleValues[type] : label || ''
}

const iterateLayoutFields = (config: LayoutConfig): LayoutField[] => {
  const out: LayoutField[] = []
  for (const section of config.sections || []) {
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) out.push(...(tab.fields || []))
      continue
    }
    if (section.type === 'collapse') {
      for (const item of section.items || []) out.push(...(item.fields || []))
      continue
    }
    out.push(...(section.fields || []))
  }
  return out.filter((field) => !!field?.fieldCode)
}

const previewFieldDefinitions = computed<RuntimeFieldDefinition[]>(() => {
  const map = new Map<string, RuntimeFieldDefinition>()

  const register = (code: string, seed: Partial<RuntimeFieldDefinition>) => {
    const normalizedCode = String(code || '').trim()
    if (!normalizedCode) return
    const current = map.get(normalizedCode)
    const next: RuntimeFieldDefinition = {
      code: normalizedCode,
      name: seed.name || seed.label || normalizedCode,
      label: seed.label || seed.name || normalizedCode,
      fieldType: normalizeFieldType((seed.fieldType as string) || 'text') as RuntimeFieldDefinition['fieldType'],
      isRequired: seed.isRequired ?? false,
      isReadonly: seed.isReadonly ?? false,
      isHidden: seed.isHidden ?? false,
      showInForm: seed.showInForm ?? true,
      showInDetail: seed.showInDetail ?? true,
      options: seed.options || [],
      span: seed.span,
      defaultValue: seed.defaultValue,
      placeholder: seed.placeholder,
      helpText: seed.helpText,
      referenceObject: seed.referenceObject,
      componentProps: seed.componentProps || {},
      ...(current || {})
    }
    map.set(normalizedCode, { ...next, ...(seed as RuntimeFieldDefinition) })
  }

  for (const field of availableFields.value) {
    register(field.code, {
      name: field.name,
      label: field.name,
      fieldType: field.fieldType as RuntimeFieldDefinition['fieldType'],
      isRequired: field.isRequired,
      isReadonly: field.isReadonly,
      showInForm: field.showInForm ?? true,
      showInDetail: field.showInDetail ?? true,
      options: field.options as any,
      defaultValue: field.defaultValue,
      placeholder: field.placeholder,
      helpText: field.helpText,
      referenceObject: field.referenceObject || field.relatedObject,
      componentProps: field.componentProps || {}
    })
  }

  for (const field of iterateLayoutFields(layoutConfig.value)) {
    register(field.fieldCode, {
      name: field.label || field.fieldCode,
      label: field.label || field.fieldCode,
      fieldType: normalizeFieldType(field.fieldType || 'text') as RuntimeFieldDefinition['fieldType'],
      isRequired: !!field.required,
      isReadonly: !!field.readonly,
      isHidden: field.visible === false,
      showInForm: field.visible !== false,
      showInDetail: field.visible !== false,
      options: (field.options || []) as any,
      span: field.span,
      defaultValue: field.defaultValue,
      placeholder: field.placeholder,
      helpText: field.helpText,
      referenceObject: field.referenceObject || field.relatedObject,
      componentProps: {
        ...(field.componentProps || {}),
        ...(field as any).component_props || {}
      }
    })
  }

  return Array.from(map.values())
})

const previewRenderSchema = computed<RenderSchema>(() => {
  return buildRenderSchema({
    mode: 'edit',
    layoutConfig: layoutConfig.value || { sections: [] },
    fields: previewFieldDefinitions.value as any[]
  })
})

const AUDIT_FIELD_CODES = new Set([
  'created_at',
  'created_by',
  'updated_at',
  'updated_by',
  'createdAt',
  'createdBy',
  'updatedAt',
  'updatedBy'
])

const isAuditFieldCode = (code: string) => AUDIT_FIELD_CODES.has(String(code || '').trim())

function shouldSkipPreviewDetailField(field: RuntimeFieldDefinition): boolean {
  const hidden = (field as any).isHidden ?? (field as any).is_hidden
  if (hidden) return true
  if (isSystemField(field)) return true
  const showInDetail = (field as any).showInDetail ?? (field as any).show_in_detail
  return showInDetail === false
}

function normalizeDetailSpan(rawSpan: any, rawColumns: any): number {
  const columns = Number(rawColumns) || 2
  const span = Number(rawSpan)

  if (!Number.isFinite(span) || span <= 0) return Math.max(1, Math.round(24 / columns))
  if (span <= columns) return Math.max(1, Math.min(24, Math.round((24 / columns) * span)))
  if (span <= 24) return Math.max(1, Math.min(24, Math.round(span)))
  return 24
}

function fieldToPreviewDetailField(field: RuntimeFieldDefinition): DetailField {
  const rawType = (field as any).fieldType || (field as any).field_type || (field as any).type || 'text'
  const normalizedType = normalizeFieldType(rawType)
  const options = (field as any).options || []

  const detailField: DetailField = {
    prop: field.code,
    label: field.label || field.name || field.code,
    span: field.span || 12,
    options
  }

  if (normalizedType === 'date' || normalizedType === 'datetime' || normalizedType === 'time') {
    detailField.type = normalizedType as DetailField['type']
    if (normalizedType === 'date') detailField.dateFormat = (field as any).dateFormat || 'YYYY-MM-DD'
    if (normalizedType === 'datetime') detailField.dateFormat = (field as any).dateFormat || 'YYYY-MM-DD HH:mm:ss'
    if (normalizedType === 'time') detailField.dateFormat = (field as any).dateFormat || 'HH:mm:ss'
  } else if (normalizedType === 'number' || normalizedType === 'currency') {
    detailField.type = normalizedType === 'currency' ? 'currency' : 'number'
    detailField.precision = (field as any).precision ?? (field as any).decimalPlaces ?? (field as any).decimal_places ?? 2
    detailField.currency = (field as any).currencySymbol || (field as any).currency || undefined
  } else if (normalizedType === 'percent') {
    detailField.type = 'percent'
    detailField.precision = (field as any).precision ?? (field as any).decimalPlaces ?? (field as any).decimal_places ?? 2
  } else if (normalizedType === 'image') {
    detailField.type = 'image'
    detailField.span = 24
  } else {
    detailField.type = 'text'
  }

  const shouldTag =
    normalizedType === 'status' ||
    normalizedType === 'enum' ||
    field.code === 'status' ||
    !!(field as any).tagTypeMapping ||
    options.some((opt: any) => opt?.color)

  if (shouldTag) {
    detailField.type = 'tag'
    detailField.tagType = (field as any).tagTypeMapping as Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'>
    detailField.defaultTagType = ((field as any).defaultTagType as any) || 'info'
  }

  return detailField
}

const detailPreviewSections = computed<DetailSection[]>(() => {
  return projectDetailSectionsFromRenderSchema(
    previewRenderSchema.value,
    previewFieldDefinitions.value as any[],
    {
      strictVisibility: true,
      isAuditFieldCode,
      mustSkipField: (field) => {
        if (isSystemField(field) || isAuditFieldCode(field.code)) return true
        const hidden = (field as any).isHidden ?? (field as any).is_hidden
        return hidden === true
      },
      shouldSkipField: (field) => shouldSkipPreviewDetailField(field as RuntimeFieldDefinition),
      fieldToDetailField: (field) => fieldToPreviewDetailField(field as RuntimeFieldDefinition) as DetailField,
      normalizeSpan: normalizeDetailSpan
    }
  ) as DetailSection[]
})

const previewAuditInfo = computed(() => ({
  createdBy: sampleData.value.createdBy || sampleData.value.created_by || 'System',
  createdAt: sampleData.value.createdAt || sampleData.value.created_at || '2026-03-01 10:00:00',
  updatedBy: sampleData.value.updatedBy || sampleData.value.updated_by || 'System',
  updatedAt: sampleData.value.updatedAt || sampleData.value.updated_at || '2026-03-01 12:30:00'
}))

const previewFormRules = computed<Record<string, any>>(() => {
  const rules: Record<string, any> = {}
  for (const field of previewFieldDefinitions.value) {
    if (!field.isRequired) continue
    const label = field.label || field.name || field.code
    rules[field.code] = [
      { required: true, message: `${label}不能为空`, trigger: ['blur', 'change'] }
    ]
  }
  return rules
})

function setRenderMode(mode: string | number) {
  const nextMode = mode === 'edit' || mode === 'detail' || mode === 'design'
    ? mode
    : 'design'
  renderMode.value = nextMode
}

function handleDetailPreviewSave(value: Record<string, any>) {
  sampleData.value = {
    ...sampleData.value,
    ...(value || {})
  }
  ElMessage.success('预览模式：示例数据已更新（未保存到后台）')
}

function handleDetailPreviewCancel() {
  ElMessage.info('预览模式：已取消编辑')
}

function isGroupExpanded(type: string): boolean {
  return expandedGroups.value.has(type)
}

function toggleGroup(type: string) {
  if (expandedGroups.value.has(type)) {
    expandedGroups.value.delete(type)
  } else {
    expandedGroups.value.add(type)
  }
}

function isFieldAdded(code: string): boolean {
  return addedFieldCodes.value.includes(code)
}

function getDisabledReason(field: FieldDefinition): string | null {
  return getFieldDisabledReason(field.fieldType, props.mode)
}

function canAddField(field: FieldDefinition): boolean {
  return canAddFieldInDesigner(field.fieldType, props.mode)
}

function notifyUnsupportedField(field: FieldDefinition): void {
  const reason = getDisabledReason(field)
  if (!reason) return
  ElMessage.warning(`Cannot add "${field.name}": ${reason}`)
}

function buildLayoutField(field: FieldDefinition): LayoutField {
  const fieldType = normalizeFieldType(field.fieldType || 'text')
  const componentProps = {
    ...(field.componentProps || {}),
    ...(field as any).component_props || {}
  }

  return {
    id: generateId('field'),
    fieldCode: field.code,
    label: field.name,
    span: 1,
    readonly: field.isReadonly || props.mode === 'readonly',
    visible: true,
    required: field.isRequired,
    fieldType,
    // Preserve complete metadata for proper rendering
    options: field.options,
    referenceObject: field.referenceObject || field.relatedObject,
    componentProps,
    dictionaryType: field.dictionaryType,
    defaultValue: field.defaultValue,
    placeholder: field.placeholder,
    helpText: field.helpText
  }
}

function addFieldToContainer(field: FieldDefinition, meta: ContainerMeta) {
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }

  if (isFieldAdded(field.code)) {
    ElMessage.warning('Field already added')
    return
  }

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value)
  const targetArr = getFieldArrayRef(newConfig, meta)
  if (!targetArr) return

  const newField = buildLayoutField(field)
  targetArr.push(newField)
  commitLayoutChange(newConfig, `Add field ${field.code}`, previousConfig)

  // Seed sample value so WYSIWYG preview is never blank.
  if (newField.fieldCode && sampleData.value[newField.fieldCode] === undefined) {
    sampleData.value[newField.fieldCode] = getSampleValue(newField)
  }

}

// Field selection from panel
function handleFieldClick(field: FieldDefinition) {
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }

  // Add to first section or create one if none exists
  if (!layoutConfig.value.sections || layoutConfig.value.sections.length === 0) {
    addSection()
  }

  // Check if already added
  if (isFieldAdded(field.code)) {
    ElMessage.warning('Field already added')
    return
  }

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value)
  const firstSection = newConfig.sections![0]
  if (!firstSection.fields) {
    firstSection.fields = []
  }

  const newField = buildLayoutField(field)
  firstSection.fields!.push(newField)
  if (newField.fieldCode && sampleData.value[newField.fieldCode] === undefined) {
    sampleData.value[newField.fieldCode] = getSampleValue(newField)
  }
  commitLayoutChange(newConfig, `Add field ${field.code}`, previousConfig)
}

function selectField(field: LayoutField, section: LayoutSection) {
  selectedId.value = field.id
  selectedSection.value = section
  fieldProps.value = { ...field }
}

function selectSection(id: string) {
  selectedId.value = id
  const section = findItemById(layoutConfig.value, id)
  selectedSection.value = section
  sectionProps.value = { ...section }
}

function deselect() {
  selectedId.value = ''
  selectedSection.value = null
  fieldProps.value = {}
  sectionProps.value = {}
}

// Drag handlers
function handleFieldDragStart(e: DragEvent, field: FieldDefinition) {
  if (!canAddField(field)) {
    e.preventDefault()
    notifyUnsupportedField(field)
    return
  }

  draggedField.value = field
  e.dataTransfer!.effectAllowed = 'copy'
  e.dataTransfer!.setData('field', JSON.stringify(field))
}

function handleCanvasFieldDragStart(e: DragEvent, field: LayoutField) {
  e.dataTransfer!.effectAllowed = 'move'
  e.dataTransfer!.setData('canvasField', JSON.stringify(field))
}

function handleDragEnd() {
  draggedField.value = null
  isDragOverCanvas.value = false
  dragOverSection.value = null
}

function handleCanvasDragOver(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  isDragOverCanvas.value = true
}

function handleCanvasDragLeave(e: DragEvent) {
  if (renderMode.value !== 'design') return
  isDragOverCanvas.value = false
}

function handleCanvasDrop(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  isDragOverCanvas.value = false

  const data = e.dataTransfer!.getData('field')
  if (!data) return

  const field: FieldDefinition = JSON.parse(data)
  handleFieldClick(field)
}

function handleSectionDragOver(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  e.stopPropagation()
}

function handleSectionDragLeave(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.stopPropagation()
}

function handleSectionDrop(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  e.stopPropagation()

  const data = e.dataTransfer?.getData('field')
  if (!data) return

  const sectionId = (e.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
  if (!sectionId) return

  const field: FieldDefinition = JSON.parse(data)
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }
  addFieldToContainer(field, { kind: 'section', sectionId })
}

function handleTabDrop(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  e.stopPropagation()

  const data = e.dataTransfer?.getData('field')
  if (!data) return

  const tabId = (e.currentTarget as HTMLElement | null)?.dataset?.tabId || ''
  const sectionId = (e.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
  if (!sectionId || !tabId) return

  const field: FieldDefinition = JSON.parse(data)
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }
  addFieldToContainer(field, { kind: 'tab', sectionId, tabId })
}

function handleCollapseDrop(e: DragEvent) {
  if (renderMode.value !== 'design') return
  e.preventDefault()
  e.stopPropagation()

  const data = e.dataTransfer?.getData('field')
  if (!data) return

  const sectionId = (e.currentTarget as HTMLElement | null)?.dataset?.sectionId || ''
  const collapseId = (e.currentTarget as HTMLElement | null)?.dataset?.collapseId || ''
  if (!sectionId || !collapseId) return

  const field: FieldDefinition = JSON.parse(data)
  if (!canAddField(field)) {
    notifyUnsupportedField(field)
    return
  }
  addFieldToContainer(field, { kind: 'collapse', sectionId, collapseId })
}

// Field update
function updateField(key: string, value: any) {
  if (!selectedId.value || elementType.value !== 'field') return

  if (key === 'fieldType') {
    const nextType = normalizeFieldType(value || 'text')
    const reason = getFieldDisabledReason(nextType, props.mode)
    if (reason) {
      ElMessage.warning(`Cannot switch field type: ${reason}`)
      const current = findItemById(layoutConfig.value, selectedId.value)
      if (current) {
        fieldProps.value = {
          ...fieldProps.value,
          fieldType: normalizeFieldType(current.fieldType || 'text')
        }
      }
      return
    }
  }

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value)
  const item = findItemById(newConfig, selectedId.value)
  if (item) {
    item[key] = key === 'fieldType' ? normalizeFieldType(value || 'text') : value
    commitLayoutChange(newConfig, `Update field ${key}`, previousConfig)
  }
}

function handleFieldPropertyUpdate(payload: { key: string; value: any }) {
  updateField(payload.key, payload.value)
}

function updateSection(key: string, value: any) {
  if (!selectedId.value || elementType.value !== 'section') return

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value)
  const item = findItemById(newConfig, selectedId.value)
  if (item) {
    item[key] = value

    // Auto-bootstrap tabs array if switching to tab mode and empty
    if (key === 'type' && value === 'tab') {
      if (!Array.isArray(item.tabs) || item.tabs.length === 0) {
        const tabId = `tab_${Date.now()}`
        item.tabs = [{
          id: tabId,
          title: 'Tab 1',
          name: tabId,
          fields: []
        }]
        // Initialize the v-model as well
        activeTabs.value[item.id] = tabId
      }
    }

    commitLayoutChange(newConfig, `Update section ${key}`, previousConfig)
  }
}

function handleSectionPropertyUpdate(payload: { key: string; value: any }) {
  updateSection(payload.key, payload.value)
}

function updateFieldProps() {
  if (selectedItem.value && elementType.value === 'field') {
    Object.assign(selectedItem.value, fieldProps.value)
  }
}

function updateSectionProps() {
  if (selectedItem.value && elementType.value === 'section') {
    Object.assign(selectedItem.value, sectionProps.value)
  }
}

function removeField(fieldId: string, sectionId: string, sectionIndex?: number) {
  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value)
  
  const section = newConfig.sections?.find(s => s.id === sectionId)
  if (!section) return

  if (section.type === 'tab') {
    // Find in tabs
    for (const tab of section.tabs || []) {
      tab.fields = tab.fields?.filter(f => f.id !== fieldId) || []
    }
  } else if (section.type === 'collapse') {
    for (const item of section.items || []) {
      item.fields = item.fields?.filter(f => f.id !== fieldId) || []
    }
  } else {
    section.fields = section.fields?.filter(f => f.id !== fieldId) || []
  }

  commitLayoutChange(newConfig, `Remove field ${fieldId}`, previousConfig)
  selectedId.value = ''
}

function deleteSection(sectionId: string) {
  ElMessageBox.confirm('Delete this section? Fields in this section will be removed.', 'Delete section', {
    type: 'warning'
  }).then(() => {
    const previousConfig = cloneLayoutConfig(layoutConfig.value)
    const newConfig = cloneLayoutConfig(layoutConfig.value)
    newConfig.sections = newConfig.sections?.filter(s => s.id !== sectionId) || []
    commitLayoutChange(newConfig, `Delete section ${sectionId}`, previousConfig)
    selectedId.value = ''
    ElMessage.success('Section deleted')
  }).catch(() => {})
}

function addSection() {
  const newSection: LayoutSection = {
    id: generateId('section'),
    type: 'section',
    title: 'New Section',
    collapsible: true,
    collapsed: false,
    columns: 2,
    border: true,
    fields: []
  }

  const previousConfig = cloneLayoutConfig(layoutConfig.value)
  const newConfig = cloneLayoutConfig(layoutConfig.value)
  if (!newConfig.sections) {
    newConfig.sections = []
  }

  newConfig.sections.push(newSection)
  commitLayoutChange(newConfig, 'Add section', previousConfig)
  selectedId.value = newSection.id
}

function toggleSectionCollapse(sectionId: string) {
  const section = findItemById(layoutConfig.value, sectionId)
  if (section && section.collapsible !== undefined) {
    section.collapsed = !section.collapsed
  }
}

const resolveLayoutType = (): LayoutType => {
  return normalizeLayoutType(props.mode) as LayoutType
}

const isReadonlyMode = computed(() => props.mode === 'readonly')

function normalizeAndEnsureLayoutConfig(rawConfig: LayoutConfig): LayoutConfig {
  return ensurePersistLayoutConfigIds(rawConfig || { sections: [] }) as LayoutConfig
}

function extractConfigPayload(raw: any): LayoutConfig {
  const payload = (raw?.data ?? raw) as any
  const config = payload?.layoutConfig || payload?.layout_config || payload?.layout || { sections: [] }
  return normalizeAndEnsureLayoutConfig(config as LayoutConfig)
}

function buildReadonlyModeOverride(sharedBase: LayoutConfig, readonlyConfig: LayoutConfig): LayoutConfig {
  const next = cloneLayoutConfig(normalizeAndEnsureLayoutConfig(sharedBase || { sections: [] })) as any
  const normalizedReadonly = normalizeAndEnsureLayoutConfig(readonlyConfig || { sections: [] })
  const existingOverrides = (next.modeOverrides || next.mode_overrides || {}) as Record<string, any>

  next.modeOverrides = {
    ...existingOverrides,
    readonly: {
      sections: normalizedReadonly.sections || [],
      actions: normalizedReadonly.actions || []
    }
  }

  return next as LayoutConfig
}

async function resolveSharedEditLayout(readonlySeed?: LayoutConfig): Promise<any> {
  if (!props.objectCode) {
    throw new Error('Missing objectCode')
  }

  // Reuse resolved target when possible to avoid redundant queries.
  if (sharedEditLayoutId.value) {
    const existing = await pageLayoutApi.detail(sharedEditLayoutId.value)
    if ((existing as any)?.id) return existing
  }

  let activeEdit: any = null
  try {
    activeEdit = await pageLayoutApi.byObjectAndMode(props.objectCode, 'edit')
  } catch {
    activeEdit = null
  }

  const normalizedEdit = ((activeEdit as any)?.data ?? activeEdit) as any
  if (normalizedEdit?.id && !normalizedEdit?.isDefault) {
    sharedEditLayoutId.value = String(normalizedEdit.id)
    return normalizedEdit
  }

  // If current active edit layout is system default, create a custom edit layout
  // and store readonly override in that custom shared layout.
  const sourceBusinessObject =
    normalizedEdit?.businessObject ||
    normalizedEdit?.business_object ||
    props.businessObjectId

  let baseLayoutConfig: LayoutConfig | null = null
  if (normalizedEdit?.layoutConfig || normalizedEdit?.layout_config) {
    baseLayoutConfig = extractConfigPayload(normalizedEdit)
  } else {
    try {
      const defaultEdit = await pageLayoutApi.getDefault(props.objectCode, 'edit')
      baseLayoutConfig = extractConfigPayload(defaultEdit)
    } catch {
      baseLayoutConfig = null
    }
  }

  const fallbackSeed = normalizeAndEnsureLayoutConfig(readonlySeed || { sections: [] })
  const createPayload = {
    layoutCode: `${props.objectCode}_edit_shared_${Date.now()}`,
    layoutName: `${props.objectCode} Edit Shared`,
    mode: 'edit',
    business_object: sourceBusinessObject || props.businessObjectId,
    status: 'draft',
    isDefault: false,
    layoutConfig: baseLayoutConfig || fallbackSeed
  }

  const created = await pageLayoutApi.create(createPayload as any)
  const normalizedCreated = ((created as any)?.data ?? created) as any
  if (!normalizedCreated?.id) {
    if (props.layoutId) {
      const legacy = await pageLayoutApi.detail(props.layoutId)
      const normalizedLegacy = ((legacy as any)?.data ?? legacy) as any
      if (normalizedLegacy?.id) {
        sharedEditLayoutId.value = String(normalizedLegacy.id)
        return normalizedLegacy
      }
    }
    throw new Error('Failed to resolve shared edit layout')
  }
  sharedEditLayoutId.value = String(normalizedCreated.id)
  return normalizedCreated
}

async function saveReadonlyToSharedLayout(readonlyConfig: LayoutConfig, publish = false) {
  const targetLayout = await resolveSharedEditLayout(readonlyConfig)
  const targetLayoutId = String(targetLayout.id)
  const targetMode = String(targetLayout?.mode || '').toLowerCase()
  const targetType = String(targetLayout?.layoutType || targetLayout?.layout_type || '').toLowerCase()
  const isEditTarget = targetMode === 'edit' || targetType === 'form'
  const mergedConfig = isEditTarget
    ? buildReadonlyModeOverride(extractConfigPayload(targetLayout), readonlyConfig)
    : normalizeAndEnsureLayoutConfig(readonlyConfig)

  await pageLayoutApi.partialUpdate(targetLayoutId, {
    layoutConfig: mergedConfig,
    status: 'draft'
  })

  if (publish) {
    await pageLayoutApi.publish(targetLayoutId, {
      change_summary: 'Publish readonly override on shared edit layout'
    })
  }

  sharedEditLayoutId.value = targetLayoutId
  return {
    id: targetLayoutId,
    layoutConfig: mergedConfig
  }
}

const prepareLayoutConfig = (): LayoutConfig | null => {
  try {
    const availableFieldCodes = availableFields.value.map((item) => String(item.code || '').trim()).filter(Boolean)
    const prepared = preparePersistLayoutConfig(layoutConfig.value || { sections: [] }, {
      layoutType: resolveLayoutType(),
      availableFieldCodes
    }) as LayoutConfig
    layoutConfig.value = prepared
    return prepared
  } catch (error: any) {
    ElMessage.error(error?.message || 'Layout configuration is invalid')
    return null
  }
}

// Save and publish
async function handleSave() {
  saving.value = true
  try {
    const sanitizedConfig = prepareLayoutConfig()
    if (!sanitizedConfig) return
    const data: Record<string, any> = {
      layoutConfig: sanitizedConfig,
      status: 'draft'
    }

    if (isReadonlyMode.value && props.objectCode) {
      const result = await saveReadonlyToSharedLayout(sanitizedConfig, false)
      data.sharedLayoutId = result.id
      // Compatibility sync: keep legacy readonly layout snapshot updated when editing from a readonly layout row.
      if (props.layoutId && props.layoutId !== result.id) {
        try {
          await pageLayoutApi.partialUpdate(props.layoutId, {
            layoutConfig: sanitizedConfig,
            status: 'draft'
          } as any)
        } catch {
          // ignore legacy sync failure; shared edit layout is source of truth.
        }
      }
    } else if (props.layoutId) {
      await pageLayoutApi.partialUpdate(props.layoutId, data as any)
    } else {
      await pageLayoutApi.create({
        ...data,
        layoutCode: `${props.objectCode}_${props.mode}_${Date.now()}`,
        layoutName: props.layoutName,
        mode: props.mode,
        business_object: props.businessObjectId
      })
    }

    ElMessage.success('Layout saved')
    emit('save', data)
  } catch (error: any) {
    console.error('Save failed:', error)
    ElMessage.error(error.response?.data?.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

async function handlePublish() {
  publishing.value = true
  try {
    const sanitizedConfig = prepareLayoutConfig()
    if (!sanitizedConfig) return

    if (isReadonlyMode.value && props.objectCode) {
      const result = await saveReadonlyToSharedLayout(sanitizedConfig, true)
      // Compatibility sync for legacy readonly layout records.
      if (props.layoutId && props.layoutId !== result.id) {
        try {
          await pageLayoutApi.partialUpdate(props.layoutId, {
            layoutConfig: sanitizedConfig,
            status: 'draft'
          } as any)
          await pageLayoutApi.publish(props.layoutId, {
            change_summary: 'Sync readonly snapshot from shared edit layout'
          })
        } catch {
          // ignore legacy sync failure; shared edit layout is source of truth.
        }
      }
    } else if (props.layoutId) {
      // Persist latest draft before publish to avoid publishing stale server-side config.
      await pageLayoutApi.partialUpdate(props.layoutId, {
        layoutConfig: sanitizedConfig,
        status: 'draft'
      })
      await pageLayoutApi.publish(props.layoutId, {
        change_summary: 'Publish layout'
      })
    } else {
      // Create as draft first, then publish to keep lifecycle consistent.
      const createResult = await pageLayoutApi.create({
        layoutConfig: sanitizedConfig,
        layoutCode: `${props.objectCode}_${props.mode}_${Date.now()}`,
        layoutName: props.layoutName,
        mode: props.mode,
        business_object: props.businessObjectId,
        status: 'draft'
      })
      await pageLayoutApi.publish(createResult.id, {
        change_summary: 'Publish layout',
        set_as_default: true
      })
    }

    isPublished.value = true
    ElMessage.success('Layout published')
    emit('published', layoutConfig.value)
  } catch (error: any) {
    console.error('Publish failed:', error)
    ElMessage.error(error.response?.data?.message || 'Publish failed')
  } finally {
    publishing.value = false
  }
}

/**
 * Reset layout to system default
 * Fetches the auto-generated default layout from backend which includes all fields
 */
async function handleReset() {
  try {
    await ElMessageBox.confirm(
      'Reset layout to system default? Unsaved changes will be lost.',
      'Reset confirmation',
      { type: 'warning' }
    )
  } catch {
    return // User cancelled
  }

  try {
    if (!props.objectCode) throw new Error('Missing objectCode')

    // Single source of truth: default layout endpoint (supports mode/type normalization).
    const layoutType = normalizeLayoutType(props.mode)
    const result = await pageLayoutApi.getDefault(props.objectCode, layoutType)
    const payload = ((result as any)?.data ?? result) as any
    const backendConfig =
      payload?.layoutConfig ||
      payload?.layout_config ||
      payload?.layout ||
      null

    if (
      backendConfig &&
      (
        (Array.isArray(backendConfig.sections) && backendConfig.sections.length > 0) ||
        (Array.isArray(backendConfig.columns) && backendConfig.columns.length > 0) ||
        Object.keys(backendConfig).length > 0
      )
    ) {
      // Normalize and use the backend-generated default layout
      layoutConfig.value = normalizeAndEnsureLayoutConfig(backendConfig as LayoutConfig)
      await loadAvailableFields()
      populateSampleData()
      console.log('[LayoutDesigner Reset] Applied normalized layout:', layoutConfig.value)
    } else {
      // Fallback: generate a layout with all available fields
      console.warn('[LayoutDesigner Reset] No default layout from backend, generating from available fields')
      await loadAvailableFields()
      
      const defaultSection = {
        id: `section-${Date.now()}`,
        type: 'section',
        title: 'Basic Information',
        collapsible: true,
        collapsed: false,
        columns: 2,
        border: false,
        fields: availableFields.value.map((field, index) => ({
          id: `field-${Date.now()}-${index}`,
          fieldCode: field.code,
          label: field.name || (field as any).displayName || field.code,
          fieldType: normalizeFieldType((field as any).fieldType || (field as any).field_type || (field as any).type || 'text'),
          span: 12,
          required: field.isRequired || false,
          options: field.options,
          referenceObject: field.referenceObject || field.relatedObject,
          componentProps: field.componentProps,
          dictionaryType: field.dictionaryType
        }))
      }
      
      layoutConfig.value = {
        sections: [defaultSection],
        actions: [
          { code: 'submit', label: 'Submit', type: 'primary', position: 'bottom-right' },
          { code: 'cancel', label: 'Cancel', type: 'default', position: 'bottom-right' }
        ]
      }
      populateSampleData()
    }
    
    selectedId.value = ''
    history.clear()
    ElMessage.success('Reset to system default layout')
  } catch (error) {
    console.error('[LayoutDesigner Reset] Failed:', error)
    ElMessage.error('Reset failed, please refresh and try again')
  }
}

function handleCancel() {
  emit('cancel')
}

/**
 * Populate sampleData with sample values for all fields in the layout
 * This ensures the canvas preview displays sample text instead of empty fields
 */
function populateSampleData() {
  const data: Record<string, any> = {}

  // Iterate through all sections and fields to collect field codes
  for (const section of layoutConfig.value.sections || []) {
    if (section.type === 'tab') {
      // Tab section - iterate through tabs
      for (const tab of section.tabs || []) {
        for (const field of tab.fields || []) {
          data[field.fieldCode] = getSampleValue(field)
        }
      }
    } else if (section.type === 'collapse') {
      // Collapse section - iterate through items
      for (const item of section.items || []) {
        for (const field of item.fields || []) {
          data[field.fieldCode] = getSampleValue(field)
        }
      }
    } else {
      // Regular section
      for (const field of section.fields || []) {
        data[field.fieldCode] = getSampleValue(field)
      }
    }
  }

  sampleData.value = data
}

function normalizeAvailableFields(fields: any[]): FieldDefinition[] {
  return (fields || []).map((field: any) => ({
    ...field,
    code: String(field.code || field.fieldCode || field.field_code || field.fieldName || '').trim(),
    name: String(field.name || field.label || field.displayName || field.display_name || field.code || field.fieldName || '').trim(),
    fieldType: normalizeFieldType(field.fieldType || field.field_type || field.type || 'text')
  }))
}

function applyResolvedLayoutToDesigner(resolved: any): boolean {
  const combinedFields = Array.isArray(resolved?.fields) ? resolved.fields : []
  if (combinedFields.length > 0 && availableFields.value.length === 0) {
    availableFields.value = normalizeAvailableFields(combinedFields)
  }

  const activeConfig = resolved?.layoutConfig || null
  if (!activeConfig) return false

  if (!(activeConfig.sections?.length || activeConfig.columns?.length)) return false

  layoutConfig.value = normalizeAndEnsureLayoutConfig({ ...activeConfig } as LayoutConfig)
  return true
}

async function loadActiveLayoutPreview(): Promise<boolean> {
  if (!props.objectCode) return false
  try {
    const resolved = await resolveRuntimeLayout(props.objectCode, props.mode || 'edit', {
      includeRelations: true
    })
    if (applyResolvedLayoutToDesigner(resolved)) {
      populateSampleData()
      return true
    }
  } catch (error) {
    // ignore and keep current canvas
  }
  return false
}

async function setPreviewMode(mode: 'current' | 'active') {
  if (previewLoading.value) return
  if (previewMode.value === mode) return

  if (mode === 'current') {
    previewMode.value = mode
    if (currentLayoutSnapshot.value) {
      layoutConfig.value = cloneLayoutConfig(currentLayoutSnapshot.value)
      populateSampleData()
    }
    ElMessage.info('已切换到自定义模式')
    return
  }

  previewLoading.value = true
  currentLayoutSnapshot.value = cloneLayoutConfig(layoutConfig.value)

  try {
    previewMode.value = mode
    const ok = await loadActiveLayoutPreview()
    if (!ok) {
      previewMode.value = 'current'
      if (currentLayoutSnapshot.value) {
        layoutConfig.value = cloneLayoutConfig(currentLayoutSnapshot.value)
        populateSampleData()
      }
      ElMessage.warning('未获取到可预览布局，已回退到自定义模式')
      return
    }
    ElMessage.success('已切换到预览模式')
  } finally {
    previewLoading.value = false
  }
}

async function loadLayout() {

  previewMode.value = 'current'
  currentLayoutSnapshot.value = null
  previewLoading.value = false

  // Otherwise, load from API if layoutId is provided
  if (props.layoutId && !isReadonlyMode.value) {
    try {
      const layout = await pageLayoutApi.detail(props.layoutId)
      const rawConfig = layout.layoutConfig || getDefaultLayoutConfig(props.mode)
      // Normalize the layout config to handle backend API format (field -> fieldCode)
      layoutConfig.value = normalizeAndEnsureLayoutConfig(rawConfig as LayoutConfig)
      isDefault.value = layout.isDefault
      isPublished.value = layout.status === 'published'
      layoutVersion.value = layout.version
      // Populate sample data with values from the loaded layout
      await loadAvailableFields()
      populateSampleData()
      return
    } catch (error) {
      console.error('Failed to load layout:', error)
    }
  }

  // If no specific layoutId, load the active layout to match the real detail page
  if (props.objectCode) {
    try {
      const resolved = await resolveRuntimeLayout(props.objectCode, props.mode || 'edit', {
        includeRelations: true
      })
      applyResolvedLayoutToDesigner(resolved)
      await loadAvailableFields()
      isDefault.value = !!resolved?.isDefault
      isPublished.value = resolved?.layoutStatus === 'published'
      layoutVersion.value = resolved?.layoutVersion || layoutVersion.value

      populateSampleData()
      return
    } catch (error) {
      // Ignore and fall back to default
    }
  }

  // Fall back to layoutConfig prop if provided
  if (props.layoutConfig && (props.layoutConfig.sections?.length || props.layoutConfig.columns?.length)) {
    layoutConfig.value = normalizeAndEnsureLayoutConfig({ ...props.layoutConfig } as LayoutConfig)
    populateSampleData()
    return
  }

  // Final fallback: backend default layout for this object/mode
  if (props.objectCode) {
    try {
      const defaultLayout = await pageLayoutApi.getDefault(props.objectCode, normalizeLayoutType(props.mode))
      const defaultData: any = (defaultLayout as any)?.data ?? defaultLayout
      const backendConfig = defaultData?.layoutConfig || defaultData?.layout_config
      if (backendConfig && (backendConfig.sections?.length || backendConfig.columns?.length)) {
        layoutConfig.value = normalizeAndEnsureLayoutConfig({ ...backendConfig } as LayoutConfig)
        populateSampleData()
        return
      }
    } catch (error) {
      // fall through
    }
  }

  return
}

/**
 * Load available fields using businessObjectApi for authenticated requests
 * Refactored to use unified API layer instead of native fetch()
 */
async function loadAvailableFields() {
  if (!props.objectCode) {
    console.warn('[LayoutDesigner] No objectCode provided, cannot load fields')
    return
  }

  try {
    const [runtimeResult, metadataResult] = await Promise.allSettled([
      resolveRuntimeLayout(props.objectCode, props.mode || 'edit', {
        includeRelations: true
      }),
      dynamicApi.getMetadata(props.objectCode)
    ])

    const runtimeFields =
      runtimeResult.status === 'fulfilled' && Array.isArray(runtimeResult.value?.fields)
        ? runtimeResult.value.fields
        : []

    const metadataPayload =
      metadataResult.status === 'fulfilled'
        ? ((metadataResult.value as any)?.data ?? metadataResult.value)
        : null
    const metadataFields = Array.isArray(metadataPayload?.fields) ? metadataPayload.fields : []

    // Runtime fields preserve active layout semantics; metadata fills gaps for full designer palette.
    const combined = mergeFieldSources(runtimeFields, metadataFields)
    if (combined.length > 0) {
      availableFields.value = normalizeAvailableFields(combined)
      return
    }

    console.warn('[LayoutDesigner] No fields returned from runtime/metadata endpoints, keeping current fields')
  } catch (error) {
    console.error('Failed to load fields:', error)
    // Only set fallback mock data if availableFields is empty
    if (availableFields.value.length === 0) {
      console.log('[LayoutDesigner] Using fallback mock data')
      availableFields.value = [
        { code: 'name', name: 'Name', fieldType: 'text', isRequired: true },
        { code: 'code', name: 'Code', fieldType: 'text', isRequired: true },
        { code: 'status', name: 'Status', fieldType: 'select', isRequired: false },
        { code: 'description', name: 'Description', fieldType: 'textarea', isRequired: false }
      ]
    }
  }
}

// Update properties when selection changes
watch(selectedId, () => {
  const item = selectedItem.value
  if (!item) {
    fieldProps.value = {}
    sectionProps.value = {}
    return
  }

  if (elementType.value === 'field') {
    fieldProps.value = {
      ...item,
      fieldType: normalizeFieldType((item as any).fieldType || (item as any).field_type || 'text')
    }
  } else if (elementType.value === 'section') {
    sectionProps.value = { ...item }
  }
})

const dndSignature = computed(() => {
  const sections = layoutConfig.value.sections || []
  return JSON.stringify(
    {
      renderMode: renderMode.value,
      sections: sections.map((s) => ({
        id: s.id,
        type: s.type,
        tabs: s.type === 'tab' ? (s.tabs || []).map((t) => t.id) : [],
        items: s.type === 'collapse' ? (s.items || []).map((i) => i.id) : []
      }))
    }
  )
})

function syncContainerStates() {
  const sections = layoutConfig.value.sections || []
  const nextTabs = { ...(activeTabs.value || {}) }
  const nextCollapses = { ...(activeCollapses.value || {}) }
  let tabsChanged = false
  let collapsesChanged = false

  for (const section of sections) {
    const sectionId = section.id
    if (!sectionId) continue

    if (section.type === 'tab') {
      const tabIds = (section.tabs || []).map((tab) => tab.id).filter(Boolean) as string[]
      if (tabIds.length === 0) {
        if (nextTabs[sectionId] !== undefined) {
          delete nextTabs[sectionId]
          tabsChanged = true
        }
      } else {
        const current = nextTabs[sectionId]
        if (!current || !tabIds.includes(current)) {
          nextTabs[sectionId] = tabIds[0]
          tabsChanged = true
        }
      }
    }

    if (section.type === 'collapse') {
      const itemIds = (section.items || []).map((item) => item.id).filter(Boolean) as string[]
      if (itemIds.length === 0) {
        if (nextCollapses[sectionId] !== undefined) {
          delete nextCollapses[sectionId]
          collapsesChanged = true
        }
      } else {
        const current = Array.isArray(nextCollapses[sectionId]) ? nextCollapses[sectionId] : []
        const filtered = current.filter((id) => itemIds.includes(id))
        const target = filtered.length > 0 ? filtered : [itemIds[0]]
        if (JSON.stringify(current) !== JSON.stringify(target)) {
          nextCollapses[sectionId] = target
          collapsesChanged = true
        }
      }
    }
  }

  if (tabsChanged) {
    activeTabs.value = nextTabs
  }
  if (collapsesChanged) {
    activeCollapses.value = nextCollapses
  }
}

watch(
  dndSignature,
  async () => {
    syncContainerStates()
    await initSortables()
  },
  { immediate: true }
)

watch(renderMode, (mode) => {
  if (mode === 'design') return
  deselect()
  isDragOverCanvas.value = false
  dragOverSection.value = null
})

// Lifecycle
onMounted(() => {
  loadLayout().finally(() => {
    if (props.initialPreviewMode === 'active') {
      void setPreviewMode('active')
    }
  })
  // Expand first group by default
  expandedGroups.value.add('text')
})

onUnmounted(() => {
  destroySortables()
})

// Watch for prop changes
watch(() => props.mode, (newType) => {
  layoutConfig.value = normalizeAndEnsureLayoutConfig(getDefaultLayoutConfig(newType) as LayoutConfig)
  loadLayout()
})
</script>

<style scoped lang="scss">
.wysiwyg-layout-designer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.designer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  row-gap: 8px;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    flex: 1 1 auto;

    .layout-info {
      display: inline-block;
      max-width: 420px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 16px;
      font-weight: 500;
      color: #303133;
    }
  }

  .toolbar-center {
    flex: 0 0 auto;
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 8px;
    flex: 0 0 auto;
  }
}

.designer-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

// Left Panel - Field List
.field-panel {
  width: 260px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;

  .panel-header {
    padding: 12px 16px;
    border-bottom: 1px solid #e4e7ed;
  }

  .panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }
}

.field-group {
  margin-bottom: 8px;

  .group-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    cursor: pointer;
    border-radius: 6px;
    transition: background 0.2s;

    &:hover {
      background: #f5f7fa;
    }

    .expand-icon {
      margin-left: auto;
      transition: transform 0.2s;

      &.expanded {
        transform: rotate(90deg);
      }
    }
  }

  .group-fields {
    padding: 0 8px 8px;
  }
}

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;

  .field-icon {
    color: #909399;
  }

  .field-label {
    flex: 1;
    font-size: 14px;
    color: #303133;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .field-code {
    font-size: 12px;
    color: #909399;
  }

  .added-icon {
    margin-left: auto;
    color: #67c23a;
  }

  &:hover {
    background: #f0f9ff;
    border-color: #409eff;
  }

  &.is-selected {
    background: #ecf5ff;
    border-color: #409eff;
  }

  &.is-disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// Center Canvas
.canvas-area {
  flex: 1;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .canvas-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 20px;
    background: white;
    border-bottom: 1px solid #e4e7ed;
    font-size: 14px;
    color: #606266;

    .canvas-header-left {
      min-width: 0;
      flex: 1;
    }

    .canvas-header-right {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }
  }

  .canvas-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  &.drag-over {
    background: #ecf5ff;
  }
}

.form-renderer {
  max-width: 1200px; /* expanded to accommodate two columns */
  margin: 0 auto;

  .designer-preview-form {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: flex-start;
  }
}

.layout-section {
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  overflow: hidden;

  /* Default (Main Activity) takes up full remaining width but max 860 roughly */
  flex: 1 1 600px;
  max-width: 100%;

  &.is-sidebar-position {
    /* Sidebar blocks are constrained */
    flex: 0 0 320px;
    max-width: 320px;

    /* A visual hint that it is a sidebar in design mode */
    border-top: 3px solid #64748b;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #f5f7fa;
    border-bottom: 1px solid #e4e7ed;
    cursor: pointer;

    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;
      color: #303133;
    }
  }

  &.is-selected {
    border-color: #409eff;
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
  }

  &.is-collapsed {
    .section-content {
      display: none;
    }
  }
}

.empty-column-placeholder {
  padding: 30px;
  text-align: center;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  color: #909399;
  font-size: 14px;
}

.section-content {
  padding: 16px;
}

.designer-fields-container {
  display: grid;
  gap: 12px;

  &.columns-1 {
    grid-template-columns: 1fr;
  }

  &.columns-2 {
    grid-template-columns: repeat(2, 1fr);
  }

  &.columns-3 {
    grid-template-columns: repeat(3, 1fr);
  }

  &.columns-4 {
    grid-template-columns: repeat(4, 1fr);
  }
}

.field-renderer {
  position: relative;
  min-width: 0;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  cursor: move;

  &:hover {
    background: #f0f9ff;
  }

  &.is-selected {
    background: #ecf5ff;
    border: 1px dashed #409eff;
    border-radius: 4px;
  }

}

.designer-field-label {
  font-size: 12px;
  color: #303133;
  margin: 2px 0 6px;
}

.designer-field-code {
  margin-left: 6px;
  font-size: 11px;
  color: #909399;
}

.field-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;

  .overlay-label {
    position: absolute;
    top: 2px;
    left: 8px;
    font-size: 12px;
    color: #409eff;
    background: rgba(255, 255, 255, 0.9);
    padding: 2px 6px;
    border-radius: 3px;
  }
  .overlay-code {
    margin-left: 6px;
    font-size: 11px;
    color: #909399;
  }

  .overlay-actions {
    position: absolute;
    top: 50%;
    right: 4px;
    transform: translateY(-50%);
    pointer-events: auto;
    display: flex;
    gap: 4px;
  }
}

// Right Panel - Property Editor
.property-panel {
  width: 280px;
  background: white;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;

  .panel-header {
    padding: 12px 16px;
    border-bottom: 1px solid #e4e7ed;
    font-weight: 500;
    color: #303133;
  }

  .panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
  }
}

.property-form {
  .property-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e4e7ed;

    .el-icon {
      color: #409eff;
    }
  }
}

.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.empty-canvas {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

.runtime-preview-card {
  width: 100%;
  margin: 0;
  padding: 0;
}

.detail-mode-preview {
  min-height: 100%;

  :deep(.base-detail-page) {
    background: transparent;
  }
}
</style>


