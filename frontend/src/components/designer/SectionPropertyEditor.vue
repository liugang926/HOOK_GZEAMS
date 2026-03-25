<template>
  <el-form
    :model="modelDraft"
    label-position="top"
    size="small"
    class="section-property-editor"
  >
    <template
      v-for="section in sections"
      :key="section"
    >
      <section
        v-if="groupedSchema[section]?.length > 0"
        class="property-section-card"
        :data-section-group="section"
      >
        <header class="property-section-card__header">
          <DesignerPropertySectionHeading
            :label="sectionLabels[section]"
            :count="groupedSchema[section].length"
          />
        </header>
        <div class="property-section-card__content">
          <el-form-item
            v-for="item in groupedSchema[section]"
            :key="item.key"
            :label="resolveSchemaLabel(item)"
            :data-property-key="item.key"
          >
            <div :data-testid="item.inputType !== 'select' ? `section-prop-${item.key}` : undefined">
              <div
                v-if="item.inputType === 'switch'"
                :data-testid="`section-prop-${item.key}`"
              >
                <el-switch
                  :model-value="switchValue(item.key)"
                  @change="handleSwitchChange(item.key, $event)"
                />
              </div>

              <el-radio-group
                v-else-if="item.key === 'columns'"
                :data-testid="`section-prop-${item.key}`"
                :model-value="Number(propertyValue(item.key) ?? 2)"
                class="section-column-choice"
                size="small"
                @change="handleSelectChange(item.key, $event)"
              >
                <el-radio-button
                  v-for="option in item.options || []"
                  :key="option.value"
                  :label="option.value"
                >
                  {{ resolveOptionLabel(option) }}
                </el-radio-button>
              </el-radio-group>

              <template v-else-if="item.inputType === 'select'">
                <el-select
                  :data-testid="`section-prop-${item.key}`"
                  :model-value="propertyValue(item.key)"
                  popper-class="section-property-editor__select-popper"
                  style="width: 100%"
                  @change="handleSelectChange(item.key, $event)"
                >
                  <el-option
                    v-for="option in item.options || []"
                    :key="option.value"
                    :label="resolveOptionLabel(option)"
                    :value="option.value"
                  />
                </el-select>
                <div
                  v-if="item.key === 'relationCode' && selectedDetailRegion"
                  class="detail-region-meta"
                  data-testid="detail-region-meta"
                >
                  <span>{{ tr('system.pageLayout.designer.hints.detailRegionField', 'Field') }}: {{ detailRegionFieldCode }}</span>
                  <span>{{ tr('system.pageLayout.designer.hints.detailRegionTarget', 'Target Object') }}: {{ detailRegionTargetObject }}</span>
                </div>
                <div
                  v-if="item.key === 'relationCode' && selectedDetailRegion && detailRegionSectionPresetOptions.length > 0"
                  class="detail-region-template-presets"
                  data-testid="detail-region-section-presets"
                  @mouseleave="clearDetailRegionSectionPresetPreview()"
                  @focusout="handleDetailRegionSectionPresetPreviewFocusOut($event)"
                >
                  <div class="detail-region-template-presets__header">
                    <span class="detail-region-template-presets__label">
                      {{ tr('system.pageLayout.designer.detailRegionConfigurator.sectionPreset', 'Section Template') }}
                    </span>
                    <span
                      v-if="resolvedDetailRegionSectionPresetLabel"
                      class="detail-region-template-presets__current"
                    >
                      {{ resolvedDetailRegionSectionPresetLabel }}
                    </span>
                  </div>
                  <div class="detail-region-template-presets__actions">
                    <button
                      v-for="preset in detailRegionSectionPresetOptions"
                      :key="preset.value"
                      type="button"
                      class="detail-region-template-presets__trigger"
                      :class="detailRegionSectionPresetButtonClasses(preset.value)"
                      :data-testid="`detail-region-section-preset-trigger-${preset.value}`"
                      :aria-pressed="resolvedDetailRegionSectionPresetCode === preset.value"
                      @mousedown.prevent
                      @mouseenter="setDetailRegionSectionPresetPreview(preset.value)"
                      @focus="setDetailRegionSectionPresetPreview(preset.value)"
                      @click.stop.prevent="applyDetailRegionSectionPresetSelection(preset.value)"
                    >
                      {{ preset.label }}
                    </button>
                  </div>
                  <div
                    v-if="activeDetailRegionSectionPresetDescription"
                    class="detail-region-template-presets__description"
                    data-testid="detail-region-section-preset-description"
                  >
                    {{ activeDetailRegionSectionPresetDescription }}
                  </div>
                  <div
                    v-if="detailRegionSectionPresetPreviewHint"
                    class="detail-region-template-presets__hint"
                    data-testid="detail-region-section-preset-hint"
                  >
                    {{ detailRegionSectionPresetPreviewHint }}
                  </div>
                  <div
                    v-if="activeDetailRegionSectionPresetPreviewItems.length > 0"
                    class="detail-region-template-presets__preview"
                    data-testid="detail-region-section-preset-preview"
                  >
                    <span class="detail-region-template-presets__preview-label">
                      {{ tr('system.pageLayout.designer.detailRegionConfigurator.preview', 'Preview') }}
                    </span>
                    <span
                      v-for="item in activeDetailRegionSectionPresetPreviewItems"
                      :key="item"
                      class="detail-region-template-presets__preview-chip"
                    >
                      {{ item }}
                    </span>
                  </div>
                </div>
              </template>

              <div
                v-else-if="item.key === 'relatedFields' && availableDetailRegionFields.length > 0"
                :data-testid="`section-prop-${item.key}`"
                class="detail-region-field-picker"
              >
                <el-select
                  :model-value="selectedRelatedFieldCodes"
                  multiple
                  filterable
                  collapse-tags
                  style="width: 100%"
                  @change="handleRelatedFieldsSelectionChange"
                >
                  <el-option
                    v-for="fieldOption in availableDetailRegionFields"
                    :key="fieldOption.code"
                    :label="fieldOption.label"
                    :value="fieldOption.code"
                  />
                </el-select>
                <div
                  v-if="selectedRelatedFieldConfigs.length > 0"
                  class="detail-region-configurator"
                  data-testid="detail-region-relatedFields-configurator"
                >
                  <div
                    v-for="fieldConfig in selectedRelatedFieldConfigs"
                    :key="resolveConfiguredFieldKey(fieldConfig)"
                    class="detail-region-configurator__item"
                    :class="configuredFieldItemClasses('relatedFields', resolveConfiguredFieldKey(fieldConfig))"
                    :data-testid="`detail-region-relatedFields-item-${resolveConfiguredFieldKey(fieldConfig)}`"
                    draggable="true"
                    @dragstart="handleConfiguredFieldDragStart('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                    @dragover.prevent="handleConfiguredFieldDragOver('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                    @drop="handleConfiguredFieldDrop('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                    @dragend="handleConfiguredFieldDragEnd"
                  >
                    <div class="detail-region-configurator__meta">
                      <span
                        class="detail-region-configurator__drag-handle"
                        aria-hidden="true"
                      >
                        ::
                      </span>
                      <span class="detail-region-configurator__label">
                        {{ resolveConfiguredFieldLabel(fieldConfig) }}
                      </span>
                    </div>
                    <div class="detail-region-configurator__controls">
                      <label
                        class="detail-region-configurator__width"
                        :data-testid="`detail-region-relatedFields-width-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.columnWidth', 'Width') }}</span>
                        <el-input
                          :model-value="configuredFieldWidth(fieldConfig)"
                          @input="updateConfiguredFieldWidth('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <label
                        class="detail-region-configurator__width"
                        :data-testid="`detail-region-relatedFields-min-width-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.minColumnWidth', 'Min Width') }}</span>
                        <el-input
                          :model-value="configuredFieldMinWidth(fieldConfig)"
                          @input="updateConfiguredFieldMinWidth('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <label
                        class="detail-region-configurator__align"
                        :data-testid="`detail-region-relatedFields-align-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.columnAlign', 'Align') }}</span>
                        <el-select
                          :model-value="configuredFieldAlign(fieldConfig)"
                          @change="updateConfiguredFieldAlign('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <el-option
                            v-for="option in detailRegionAlignOptions"
                            :key="String(option.value)"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                      </label>
                      <label
                        class="detail-region-configurator__align"
                        :data-testid="`detail-region-relatedFields-fixed-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.fixedColumn', 'Fixed') }}</span>
                        <el-select
                          :model-value="configuredFieldFixed(fieldConfig)"
                          @change="updateConfiguredFieldFixed('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <el-option
                            v-for="option in detailRegionFixedOptions"
                            :key="String(option.value)"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                      </label>
                      <label
                        class="detail-region-configurator__switch"
                        :data-testid="`detail-region-relatedFields-ellipsis-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.ellipsis', 'Ellipsis') }}</span>
                        <el-switch
                          :model-value="configuredFieldEllipsis(fieldConfig)"
                          @change="updateConfiguredFieldEllipsis('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <label
                        class="detail-region-configurator__align"
                        :data-testid="`detail-region-relatedFields-preset-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.preset', 'Preset') }}</span>
                        <el-select
                          :model-value="configuredFieldPreset(fieldConfig)"
                          @change="applyConfiguredFieldPreset('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <el-option
                            v-for="option in configuredFieldPresetOptions(fieldConfig)"
                            :key="String(option.value)"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                        <div
                          v-if="configuredFieldPreviewCandidates(fieldConfig).length > 0"
                          class="detail-region-configurator__preset-actions"
                          :data-testid="`detail-region-relatedFields-preset-actions-${resolveConfiguredFieldKey(fieldConfig)}`"
                          @mouseleave="clearConfiguredFieldPresetPreview('relatedFields', resolveConfiguredFieldKey(fieldConfig))"
                          @focusout="handleConfiguredFieldPresetPreviewFocusOut('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <span class="detail-region-configurator__preset-preview-label">
                            {{ tr('system.pageLayout.designer.detailRegionConfigurator.tryPresets', 'Try presets') }}
                          </span>
                          <button
                            v-for="preset in configuredFieldPreviewCandidates(fieldConfig)"
                            :key="String(preset.value)"
                            type="button"
                            class="detail-region-configurator__preset-trigger"
                            :class="configuredFieldPresetButtonClasses('relatedFields', resolveConfiguredFieldKey(fieldConfig), fieldConfig, preset.value)"
                            :data-testid="`detail-region-relatedFields-preset-trigger-${resolveConfiguredFieldKey(fieldConfig)}-${preset.value}`"
                            :aria-pressed="configuredFieldPreset(fieldConfig) === preset.value"
                            @mousedown.prevent
                            @mouseenter="setConfiguredFieldPresetPreview('relatedFields', resolveConfiguredFieldKey(fieldConfig), preset.value)"
                            @focus="setConfiguredFieldPresetPreview('relatedFields', resolveConfiguredFieldKey(fieldConfig), preset.value)"
                            @click.stop.prevent="applyConfiguredFieldPreset('relatedFields', resolveConfiguredFieldKey(fieldConfig), preset.value)"
                          >
                            {{ preset.label }}
                          </button>
                        </div>
                        <div
                          v-if="configuredFieldPresetDescription('relatedFields', resolveConfiguredFieldKey(fieldConfig), fieldConfig)"
                          class="detail-region-configurator__preset-description"
                          :data-testid="`detail-region-relatedFields-preset-description-${resolveConfiguredFieldKey(fieldConfig)}`"
                        >
                          {{ configuredFieldPresetDescription('relatedFields', resolveConfiguredFieldKey(fieldConfig), fieldConfig) }}
                        </div>
                        <div
                          v-if="configuredFieldPresetPreviewHint('relatedFields', resolveConfiguredFieldKey(fieldConfig))"
                          class="detail-region-configurator__preset-hint"
                          :data-testid="`detail-region-relatedFields-preset-hint-${resolveConfiguredFieldKey(fieldConfig)}`"
                        >
                          {{ configuredFieldPresetPreviewHint('relatedFields', resolveConfiguredFieldKey(fieldConfig)) }}
                        </div>
                        <div
                          v-if="configuredFieldPresetPreviewItems('relatedFields', resolveConfiguredFieldKey(fieldConfig), fieldConfig).length > 0"
                          class="detail-region-configurator__preset-preview"
                          :data-testid="`detail-region-relatedFields-preset-preview-${resolveConfiguredFieldKey(fieldConfig)}`"
                        >
                          <span class="detail-region-configurator__preset-preview-label">
                            {{ tr('system.pageLayout.designer.detailRegionConfigurator.preview', 'Preview') }}
                          </span>
                          <span
                            v-for="item in configuredFieldPresetPreviewItems('relatedFields', resolveConfiguredFieldKey(fieldConfig), fieldConfig)"
                            :key="item"
                            class="detail-region-configurator__preset-chip"
                          >
                            {{ item }}
                          </span>
                        </div>
                        <div
                          v-else-if="configuredFieldRecommendedPresetText('relatedFields', resolveConfiguredFieldKey(fieldConfig), fieldConfig)"
                          class="detail-region-configurator__preset-recommendation"
                          :data-testid="`detail-region-relatedFields-preset-recommendation-${resolveConfiguredFieldKey(fieldConfig)}`"
                        >
                          {{ configuredFieldRecommendedPresetText('relatedFields', resolveConfiguredFieldKey(fieldConfig), fieldConfig) }}
                        </div>
                      </label>
                      <label
                        class="detail-region-configurator__align"
                        :data-testid="`detail-region-relatedFields-formatter-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.formatter', 'Formatter') }}</span>
                        <el-select
                          :model-value="configuredFieldFormatter(fieldConfig)"
                          @change="updateConfiguredFieldFormatter('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <el-option
                            v-for="option in detailRegionFormatterOptions"
                            :key="String(option.value)"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                      </label>
                      <label
                        class="detail-region-configurator__text"
                        :data-testid="`detail-region-relatedFields-empty-text-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.emptyText', 'Empty Text') }}</span>
                        <el-input
                          :model-value="configuredFieldEmptyText(fieldConfig)"
                          @input="updateConfiguredFieldEmptyText('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <label
                        class="detail-region-configurator__text"
                        :data-testid="`detail-region-relatedFields-tooltip-template-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.tooltipTemplate', 'Tooltip Template') }}</span>
                        <el-input
                          :model-value="configuredFieldTooltipTemplate(fieldConfig)"
                          @input="updateConfiguredFieldTooltipTemplate('relatedFields', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <div class="detail-region-configurator__actions">
                        <el-button
                          link
                          size="small"
                          :data-testid="`detail-region-relatedFields-move-up-${resolveConfiguredFieldKey(fieldConfig)}`"
                          @click="moveConfiguredField('relatedFields', resolveConfiguredFieldKey(fieldConfig), -1)"
                        >
                          {{ tr('system.pageLayout.designer.detailRegionConfigurator.moveUp', 'Up') }}
                        </el-button>
                        <el-button
                          link
                          size="small"
                          :data-testid="`detail-region-relatedFields-move-down-${resolveConfiguredFieldKey(fieldConfig)}`"
                          @click="moveConfiguredField('relatedFields', resolveConfiguredFieldKey(fieldConfig), 1)"
                        >
                          {{ tr('system.pageLayout.designer.detailRegionConfigurator.moveDown', 'Down') }}
                        </el-button>
                        <el-button
                          link
                          size="small"
                          :data-testid="`detail-region-relatedFields-remove-${resolveConfiguredFieldKey(fieldConfig)}`"
                          @click="removeConfiguredField('relatedFields', resolveConfiguredFieldKey(fieldConfig))"
                        >
                          {{ tr('system.pageLayout.designer.detailRegionConfigurator.remove', 'Remove') }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div
                v-else-if="item.key === 'lookupColumns' && availableDetailRegionFields.length > 0"
                :data-testid="`section-prop-${item.key}`"
                class="detail-region-field-picker"
              >
                <el-select
                  :model-value="selectedLookupColumnKeys"
                  multiple
                  filterable
                  collapse-tags
                  style="width: 100%"
                  @change="handleLookupColumnsSelectionChange"
                >
                  <el-option
                    v-for="fieldOption in availableDetailRegionFields"
                    :key="fieldOption.code"
                    :label="fieldOption.label"
                    :value="fieldOption.code"
                  />
                </el-select>
                <div
                  v-if="selectedLookupColumnConfigs.length > 0"
                  class="detail-region-configurator"
                  data-testid="detail-region-lookupColumns-configurator"
                >
                  <div
                    v-for="fieldConfig in selectedLookupColumnConfigs"
                    :key="resolveConfiguredFieldKey(fieldConfig)"
                    class="detail-region-configurator__item"
                    :class="configuredFieldItemClasses('lookupColumns', resolveConfiguredFieldKey(fieldConfig))"
                    :data-testid="`detail-region-lookupColumns-item-${resolveConfiguredFieldKey(fieldConfig)}`"
                    draggable="true"
                    @dragstart="handleConfiguredFieldDragStart('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                    @dragover.prevent="handleConfiguredFieldDragOver('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                    @drop="handleConfiguredFieldDrop('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                    @dragend="handleConfiguredFieldDragEnd"
                  >
                    <div class="detail-region-configurator__meta">
                      <span
                        class="detail-region-configurator__drag-handle"
                        aria-hidden="true"
                      >
                        ::
                      </span>
                      <span class="detail-region-configurator__label">
                        {{ resolveConfiguredFieldLabel(fieldConfig) }}
                      </span>
                    </div>
                    <div class="detail-region-configurator__controls">
                      <label
                        class="detail-region-configurator__width"
                        :data-testid="`detail-region-lookupColumns-width-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.columnWidth', 'Width') }}</span>
                        <el-input
                          :model-value="configuredFieldWidth(fieldConfig)"
                          @input="updateConfiguredFieldWidth('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <label
                        class="detail-region-configurator__width"
                        :data-testid="`detail-region-lookupColumns-min-width-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.minColumnWidth', 'Min Width') }}</span>
                        <el-input
                          :model-value="configuredFieldMinWidth(fieldConfig)"
                          @input="updateConfiguredFieldMinWidth('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <label
                        class="detail-region-configurator__align"
                        :data-testid="`detail-region-lookupColumns-align-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.columnAlign', 'Align') }}</span>
                        <el-select
                          :model-value="configuredFieldAlign(fieldConfig)"
                          @change="updateConfiguredFieldAlign('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <el-option
                            v-for="option in detailRegionAlignOptions"
                            :key="String(option.value)"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                      </label>
                      <label
                        class="detail-region-configurator__align"
                        :data-testid="`detail-region-lookupColumns-fixed-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.fixedColumn', 'Fixed') }}</span>
                        <el-select
                          :model-value="configuredFieldFixed(fieldConfig)"
                          @change="updateConfiguredFieldFixed('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <el-option
                            v-for="option in detailRegionFixedOptions"
                            :key="String(option.value)"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                      </label>
                      <label
                        class="detail-region-configurator__switch"
                        :data-testid="`detail-region-lookupColumns-ellipsis-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.ellipsis', 'Ellipsis') }}</span>
                        <el-switch
                          :model-value="configuredFieldEllipsis(fieldConfig)"
                          @change="updateConfiguredFieldEllipsis('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <label
                        class="detail-region-configurator__align"
                        :data-testid="`detail-region-lookupColumns-preset-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.preset', 'Preset') }}</span>
                        <el-select
                          :model-value="configuredFieldPreset(fieldConfig)"
                          @change="applyConfiguredFieldPreset('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <el-option
                            v-for="option in configuredFieldPresetOptions(fieldConfig)"
                            :key="String(option.value)"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                        <div
                          v-if="configuredFieldPreviewCandidates(fieldConfig).length > 0"
                          class="detail-region-configurator__preset-actions"
                          :data-testid="`detail-region-lookupColumns-preset-actions-${resolveConfiguredFieldKey(fieldConfig)}`"
                          @mouseleave="clearConfiguredFieldPresetPreview('lookupColumns', resolveConfiguredFieldKey(fieldConfig))"
                          @focusout="handleConfiguredFieldPresetPreviewFocusOut('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <span class="detail-region-configurator__preset-preview-label">
                            {{ tr('system.pageLayout.designer.detailRegionConfigurator.tryPresets', 'Try presets') }}
                          </span>
                          <button
                            v-for="preset in configuredFieldPreviewCandidates(fieldConfig)"
                            :key="String(preset.value)"
                            type="button"
                            class="detail-region-configurator__preset-trigger"
                            :class="configuredFieldPresetButtonClasses('lookupColumns', resolveConfiguredFieldKey(fieldConfig), fieldConfig, preset.value)"
                            :data-testid="`detail-region-lookupColumns-preset-trigger-${resolveConfiguredFieldKey(fieldConfig)}-${preset.value}`"
                            :aria-pressed="configuredFieldPreset(fieldConfig) === preset.value"
                            @mousedown.prevent
                            @mouseenter="setConfiguredFieldPresetPreview('lookupColumns', resolveConfiguredFieldKey(fieldConfig), preset.value)"
                            @focus="setConfiguredFieldPresetPreview('lookupColumns', resolveConfiguredFieldKey(fieldConfig), preset.value)"
                            @click.stop.prevent="applyConfiguredFieldPreset('lookupColumns', resolveConfiguredFieldKey(fieldConfig), preset.value)"
                          >
                            {{ preset.label }}
                          </button>
                        </div>
                        <div
                          v-if="configuredFieldPresetDescription('lookupColumns', resolveConfiguredFieldKey(fieldConfig), fieldConfig)"
                          class="detail-region-configurator__preset-description"
                          :data-testid="`detail-region-lookupColumns-preset-description-${resolveConfiguredFieldKey(fieldConfig)}`"
                        >
                          {{ configuredFieldPresetDescription('lookupColumns', resolveConfiguredFieldKey(fieldConfig), fieldConfig) }}
                        </div>
                        <div
                          v-if="configuredFieldPresetPreviewHint('lookupColumns', resolveConfiguredFieldKey(fieldConfig))"
                          class="detail-region-configurator__preset-hint"
                          :data-testid="`detail-region-lookupColumns-preset-hint-${resolveConfiguredFieldKey(fieldConfig)}`"
                        >
                          {{ configuredFieldPresetPreviewHint('lookupColumns', resolveConfiguredFieldKey(fieldConfig)) }}
                        </div>
                        <div
                          v-if="configuredFieldPresetPreviewItems('lookupColumns', resolveConfiguredFieldKey(fieldConfig), fieldConfig).length > 0"
                          class="detail-region-configurator__preset-preview"
                          :data-testid="`detail-region-lookupColumns-preset-preview-${resolveConfiguredFieldKey(fieldConfig)}`"
                        >
                          <span class="detail-region-configurator__preset-preview-label">
                            {{ tr('system.pageLayout.designer.detailRegionConfigurator.preview', 'Preview') }}
                          </span>
                          <span
                            v-for="item in configuredFieldPresetPreviewItems('lookupColumns', resolveConfiguredFieldKey(fieldConfig), fieldConfig)"
                            :key="item"
                            class="detail-region-configurator__preset-chip"
                          >
                            {{ item }}
                          </span>
                        </div>
                        <div
                          v-else-if="configuredFieldRecommendedPresetText('lookupColumns', resolveConfiguredFieldKey(fieldConfig), fieldConfig)"
                          class="detail-region-configurator__preset-recommendation"
                          :data-testid="`detail-region-lookupColumns-preset-recommendation-${resolveConfiguredFieldKey(fieldConfig)}`"
                        >
                          {{ configuredFieldRecommendedPresetText('lookupColumns', resolveConfiguredFieldKey(fieldConfig), fieldConfig) }}
                        </div>
                      </label>
                      <label
                        class="detail-region-configurator__align"
                        :data-testid="`detail-region-lookupColumns-formatter-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.formatter', 'Formatter') }}</span>
                        <el-select
                          :model-value="configuredFieldFormatter(fieldConfig)"
                          @change="updateConfiguredFieldFormatter('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        >
                          <el-option
                            v-for="option in detailRegionFormatterOptions"
                            :key="String(option.value)"
                            :label="option.label"
                            :value="option.value"
                          />
                        </el-select>
                      </label>
                      <label
                        class="detail-region-configurator__text"
                        :data-testid="`detail-region-lookupColumns-empty-text-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.emptyText', 'Empty Text') }}</span>
                        <el-input
                          :model-value="configuredFieldEmptyText(fieldConfig)"
                          @input="updateConfiguredFieldEmptyText('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <label
                        class="detail-region-configurator__text"
                        :data-testid="`detail-region-lookupColumns-tooltip-template-${resolveConfiguredFieldKey(fieldConfig)}`"
                      >
                        <span>{{ tr('system.pageLayout.designer.detailRegionConfigurator.tooltipTemplate', 'Tooltip Template') }}</span>
                        <el-input
                          :model-value="configuredFieldTooltipTemplate(fieldConfig)"
                          @input="updateConfiguredFieldTooltipTemplate('lookupColumns', resolveConfiguredFieldKey(fieldConfig), $event)"
                        />
                      </label>
                      <div class="detail-region-configurator__actions">
                        <el-button
                          link
                          size="small"
                          :data-testid="`detail-region-lookupColumns-move-up-${resolveConfiguredFieldKey(fieldConfig)}`"
                          @click="moveConfiguredField('lookupColumns', resolveConfiguredFieldKey(fieldConfig), -1)"
                        >
                          {{ tr('system.pageLayout.designer.detailRegionConfigurator.moveUp', 'Up') }}
                        </el-button>
                        <el-button
                          link
                          size="small"
                          :data-testid="`detail-region-lookupColumns-move-down-${resolveConfiguredFieldKey(fieldConfig)}`"
                          @click="moveConfiguredField('lookupColumns', resolveConfiguredFieldKey(fieldConfig), 1)"
                        >
                          {{ tr('system.pageLayout.designer.detailRegionConfigurator.moveDown', 'Down') }}
                        </el-button>
                        <el-button
                          link
                          size="small"
                          :data-testid="`detail-region-lookupColumns-remove-${resolveConfiguredFieldKey(fieldConfig)}`"
                          @click="removeConfiguredField('lookupColumns', resolveConfiguredFieldKey(fieldConfig))"
                        >
                          {{ tr('system.pageLayout.designer.detailRegionConfigurator.remove', 'Remove') }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div
                v-else-if="item.inputType === 'tabs'"
                :data-testid="`section-prop-${item.key}`"
                class="tabs-manager"
              >
                <div
                  v-for="(tab, index) in getTabsValue()"
                  :key="tab.id"
                  class="tab-item-row"
                >
                  <el-input
                    v-model="tab.title"
                    size="small"
                    @change="handleTabsChange"
                  />
                  <el-button
                    type="danger"
                    link
                    size="small"
                    icon="Delete"
                    :disabled="getTabsValue().length <= 1"
                    @click="removeTab(index)"
                  />
                </div>
                <el-button
                  type="primary"
                  plain
                  size="small"
                  icon="Plus"
                  class="add-tab-btn"
                  @click="addTab"
                >
                  {{ tr('system.pageLayout.designer.actions.addTabPage', 'Add Tab Page') }}
                </el-button>
              </div>

              <el-input
                v-else-if="item.inputType === 'json'"
                :data-testid="`section-prop-${item.key}`"
                :model-value="jsonValue(item.key)"
                type="textarea"
                :rows="4"
                @input="handleJsonChange(item.key, $event)"
              />

              <el-input
                v-else
                :data-testid="`section-prop-${item.key}`"
                :model-value="stringValue(item.key)"
                @input="handleTextChange(item.key, $event)"
              />
            </div>
          </el-form-item>
        </div>
      </section>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import DesignerPropertySectionHeading from '@/components/designer/DesignerPropertySectionHeading.vue'
import {
  applyDetailRegionColumnPreset,
  getDetailRegionColumnPresetDefinition,
  resolveDetailRegionColumnPreset
} from '@/components/designer/detailRegionColumnPresets'
import {
  buildConfiguredFieldPresetDescription,
  buildConfiguredFieldPresetOptions,
  buildConfiguredFieldPresetPreviewHint,
  buildConfiguredFieldPresetPreviewItems,
  buildConfiguredFieldPreviewCandidates,
  buildConfiguredFieldRecommendedPresetText,
  buildDetailRegionSectionPresetPreviewHint,
  buildDetailRegionSectionPresetPreviewItems,
} from '@/components/designer/detailRegionPresetPreview'
import {
  buildDetailRegionOptionLabel,
  localizeDetailRegionTarget,
} from '@/components/designer/detailRegionMetadata'
import {
  buildDetailRegionSectionPresetPatch,
  getDetailRegionSectionPresetDefinition,
  getDetailRegionSectionPresetDefinitions,
  resolveDetailRegionSectionPreset,
  type DetailRegionSectionPresetCode
} from '@/components/designer/detailRegionSectionPresets'
import {
  buildLookupColumnConfigs,
  buildRelatedFieldConfigs,
  extractLookupColumnKeys,
  extractRelatedFieldCodes,
  type DetailRegionFieldOption
} from '@/components/designer/detailRegionFieldOptions'
import {
  useConfiguredDetailRegionFields,
  type ConfiguredFieldGroup,
} from '@/components/designer/useConfiguredDetailRegionFields'
import { getSectionPropertySchema } from '@/composables/useSectionPropertySchema'
import { usePropertyEditorDraft } from '@/components/designer/usePropertyEditorDraft'
import type { RuntimeAggregateDetailRegion } from '@/types/runtime'

interface Props {
  modelValue?: Record<string, any>
  sectionType?: string
  isCompactMode?: boolean
  detailRegionOptions?: RuntimeAggregateDetailRegion[]
  detailRegionFieldOptions?: Record<string, DetailRegionFieldOption[]>
}

type SectionPreviewPropertyPayload =
  | { key: string; value: any }
  | { values: Record<string, any> }

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({}),
  sectionType: 'section',
  isCompactMode: false,
  detailRegionOptions: () => [],
  detailRegionFieldOptions: () => ({})
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'update-property', payload: { key: string; value: any }): void
  (e: 'update-properties', payload: Record<string, any>): void
  (e: 'preview-property', payload: SectionPreviewPropertyPayload | null): void
}>()
const { t, locale } = useI18n()

const tr = (key: string, fallback: string) => {
  const text = t(key, {})
  return text === key ? fallback : text
}
const trf = (key: string, fallback: string, params: Record<string, string | number>) => {
  const text = t(key, params)
  if (text !== key) return text
  return Object.entries(params).reduce((output, [token, value]) => {
    return output.replace(new RegExp(`\\{${token}\\}`, 'g'), String(value))
  }, fallback)
}
const {
  modelDraft,
  updateDraft,
  propertyValue,
  stringValue,
  booleanValue
} = usePropertyEditorDraft(() => props.modelValue)

const normalizedLocale = computed<'zh-CN' | 'en-US'>(() => {
  const raw = String(locale.value || 'zh-CN').toLowerCase()
  return raw.startsWith('en') ? 'en-US' : 'zh-CN'
})

const detailRegionSelectOptions = computed(() => {
  return (props.detailRegionOptions || [])
    .filter((region) => typeof region?.relationCode === 'string' && region.relationCode.trim())
    .map((region) => ({
      label: buildDetailRegionOptionLabel(region, normalizedLocale.value),
      value: region.relationCode
    }))
})

const hasMetadataBackedDetailRegions = computed(() => {
  return props.sectionType === 'detail-region' && detailRegionSelectOptions.value.length > 0
})

const selectedDetailRegion = computed(() => {
  const relationCode = String(propertyValue('relationCode') || propertyValue('relation_code') || '').trim()
  if (!relationCode) return null
  return (props.detailRegionOptions || []).find((region) => region.relationCode === relationCode) || null
})

const detailRegionSectionPresetOptions = computed(() => {
  return getDetailRegionSectionPresetDefinitions().map((preset) => ({
    label: tr(preset.labelKey, preset.fallbackLabel),
    value: preset.code
  }))
})

const detailRegionFieldCode = computed(() => {
  return (
    String(selectedDetailRegion.value?.fieldCode || propertyValue('fieldCode') || propertyValue('field_code') || '').trim() ||
    '-'
  )
})

const detailRegionTargetObject = computed(() => {
  if (selectedDetailRegion.value) {
    return (
      localizeDetailRegionTarget(selectedDetailRegion.value, normalizedLocale.value) ||
      selectedDetailRegion.value.targetObjectCode ||
      '-'
    )
  }
  return String(propertyValue('targetObjectCode') || propertyValue('target_object_code') || '').trim() || '-'
})

const activeDetailRegionCode = computed(() => {
  return String(propertyValue('relationCode') || propertyValue('relation_code') || '').trim()
})

const availableDetailRegionFields = computed<DetailRegionFieldOption[]>(() => {
  const relationCode = activeDetailRegionCode.value
  if (!relationCode) return []
  return props.detailRegionFieldOptions?.[relationCode] || []
})

const selectedRelatedFieldCodes = computed(() => {
  return extractRelatedFieldCodes(propertyValue('relatedFields') || propertyValue('related_fields'))
})

const selectedLookupColumnKeys = computed(() => {
  return extractLookupColumnKeys(propertyValue('lookupColumns') || propertyValue('lookup_columns'))
})

const selectedRelatedFieldConfigs = computed<Record<string, any>[]>(() => {
  return buildRelatedFieldConfigs(
    selectedRelatedFieldCodes.value,
    availableDetailRegionFields.value,
    propertyValue('relatedFields') || propertyValue('related_fields')
  )
})

const selectedLookupColumnConfigs = computed<Record<string, any>[]>(() => {
  return buildLookupColumnConfigs(
    selectedLookupColumnKeys.value,
    availableDetailRegionFields.value,
    propertyValue('lookupColumns') || propertyValue('lookup_columns')
  )
})

const schema = computed(() => {
  let base = getSectionPropertySchema(props.sectionType || 'section')
  if (hasMetadataBackedDetailRegions.value) {
    base = base
      .filter((item) => item.key !== 'fieldCode' && item.key !== 'targetObjectCode')
      .map((item) => {
        if (item.key !== 'relationCode') return item
        return {
          ...item,
          inputType: 'select' as const,
          options: detailRegionSelectOptions.value
        }
      })
  }
  if (!props.isCompactMode) return base
  // In Compact mode: filter out tab/collapse from type options, keep only 'section'
  return base.map(item => {
    if (item.key === 'type' && item.options) {
      return {
        ...item,
        options: item.options.filter((opt: { value: unknown }) => opt.value === 'section')
      }
    }
    // Hide tab management in compact mode
    if (item.key === 'tabs') return null
    return item
  }).filter(Boolean) as typeof base
})

const sectionLabels = computed<Record<string, string>>(() => ({
  basic: tr('common.labels.basic', 'Basic'),
  display: tr('common.labels.display', 'Display'),
  advanced: tr('common.labels.advanced', 'Advanced')
}))
const sections = ['basic', 'display', 'advanced'] as const
const detailRegionAlignOptions = computed(() => ([
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.alignOptions.default', 'Default'),
    value: ''
  },
  {
    label: tr('system.pageLayout.designer.sectionProperties.options.labelPosition.left', 'Left Aligned'),
    value: 'left'
  },
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.alignOptions.center', 'Center'),
    value: 'center'
  },
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.alignOptions.right', 'Right'),
    value: 'right'
  }
]))
const detailRegionFixedOptions = computed(() => ([
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.fixedOptions.default', 'Default'),
    value: ''
  },
  {
    label: tr('system.pageLayout.designer.sectionProperties.options.labelPosition.left', 'Left Aligned'),
    value: 'left'
  },
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.fixedOptions.right', 'Right'),
    value: 'right'
  }
]))
const detailRegionFormatterOptions = computed(() => ([
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.formatterOptions.default', 'Default'),
    value: ''
  },
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.formatterOptions.uppercase', 'Uppercase'),
    value: 'uppercase'
  },
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.formatterOptions.lowercase', 'Lowercase'),
    value: 'lowercase'
  },
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.formatterOptions.number', 'Number'),
    value: 'number'
  },
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.formatterOptions.date', 'Date'),
    value: 'date'
  },
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.formatterOptions.datetime', 'DateTime'),
    value: 'datetime'
  },
  {
    label: tr('system.pageLayout.designer.detailRegionConfigurator.formatterOptions.boolean', 'Boolean'),
    value: 'boolean'
  }
]))
const previewingDetailRegionSectionPreset = ref<DetailRegionSectionPresetCode | ''>('')
const previewingConfiguredFieldPreset = ref<{
  group: ConfiguredFieldGroup
  key: string
  presetCode: string
} | null>(null)

const groupedSchema = computed(() => {
  const map: Record<string, Array<{ key: string; label: string; labelKey?: string; inputType: string; options?: Array<{ label: string; labelKey?: string; value: any }> }>> = {
    basic: [],
    display: [],
    advanced: []
  }
  for (const item of schema.value) {
    map[item.section].push(item)
  }
  return map
})

const emitUpdate = (key: string, value: any) => {
  const next = updateDraft((draft) => ({ ...draft, [key]: value }))
  previewingDetailRegionSectionPreset.value = ''
  previewingConfiguredFieldPreset.value = null
  emit('preview-property', null)
  emit('update:modelValue', next)
  emit('update-property', { key, value })
}

const emitPatchUpdate = (patch: Record<string, any>) => {
  if (!patch || typeof patch !== 'object') return
  const entries = Object.entries(patch)
  if (entries.length === 0) return

  const next = updateDraft((draft) => ({ ...draft, ...patch }))
  previewingDetailRegionSectionPreset.value = ''
  previewingConfiguredFieldPreset.value = null
  emit('preview-property', null)
  emit('update:modelValue', next)
  emit('update-properties', patch)
}

const emitPreviewProperty = (payload: SectionPreviewPropertyPayload | null) => {
  emit('preview-property', payload)
}

const handleSwitchChange = (key: string, value: unknown) => emitUpdate(key, Boolean(value))
const handleSelectChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleTextChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleJsonChange = (key: string, value: unknown) => emitJsonUpdate(key, value)
const handleRelatedFieldsSelectionChange = (value: unknown) => {
  emitUpdate(
    'relatedFields',
    buildRelatedFieldConfigs(
      Array.isArray(value) ? value.map((item) => String(item || '').trim()).filter(Boolean) : [],
      availableDetailRegionFields.value,
      propertyValue('relatedFields') || propertyValue('related_fields')
    )
  )
}
const handleLookupColumnsSelectionChange = (value: unknown) => {
  emitUpdate(
    'lookupColumns',
    buildLookupColumnConfigs(
      Array.isArray(value) ? value.map((item) => String(item || '').trim()).filter(Boolean) : [],
      availableDetailRegionFields.value,
      propertyValue('lookupColumns') || propertyValue('lookup_columns')
    )
  )
}

const buildDetailRegionSectionPresetValue = (
  presetCode: unknown
): Record<string, any> | null => {
  if (!selectedDetailRegion.value) return null
  return buildDetailRegionSectionPresetPatch(selectedDetailRegion.value, presetCode) as Record<string, any> | null
}

const resolvedDetailRegionSectionPresetCode = computed<DetailRegionSectionPresetCode | ''>(() => {
  if (previewingDetailRegionSectionPreset.value) return previewingDetailRegionSectionPreset.value
  return resolveDetailRegionSectionPreset(modelDraft.value, selectedDetailRegion.value)
})

const resolvedDetailRegionSectionPresetLabel = computed(() => {
  const definition = getDetailRegionSectionPresetDefinition(resolvedDetailRegionSectionPresetCode.value)
  if (!definition) return ''
  return tr(definition.labelKey, definition.fallbackLabel)
})

const activeDetailRegionSectionPresetDescription = computed(() => {
  const definition = getDetailRegionSectionPresetDefinition(resolvedDetailRegionSectionPresetCode.value)
  if (!definition) return ''
  return tr(definition.descriptionKey, definition.fallbackDescription)
})

const activeDetailRegionSectionPresetPreviewItems = computed(() => {
  return buildDetailRegionSectionPresetPreviewItems(
    buildDetailRegionSectionPresetValue(resolvedDetailRegionSectionPresetCode.value),
    tr,
    trf
  )
})

const detailRegionSectionPresetPreviewHint = computed(() => {
  return buildDetailRegionSectionPresetPreviewHint(
    previewingDetailRegionSectionPreset.value,
    tr,
    trf
  )
})

const detailRegionSectionPresetButtonClasses = (presetCode: unknown) => {
  const normalized = String(presetCode || '').trim()
  return {
    'is-applied': resolveDetailRegionSectionPreset(modelDraft.value, selectedDetailRegion.value) === normalized,
    'is-previewing': previewingDetailRegionSectionPreset.value === normalized
  }
}

const setDetailRegionSectionPresetPreview = (presetCode: unknown) => {
  const normalized = String(presetCode || '').trim() as DetailRegionSectionPresetCode
  if (!getDetailRegionSectionPresetDefinition(normalized)) {
    clearDetailRegionSectionPresetPreview()
    return
  }

  const patch = buildDetailRegionSectionPresetValue(normalized)
  if (!patch) {
    clearDetailRegionSectionPresetPreview()
    return
  }

  previewingConfiguredFieldPreset.value = null
  previewingDetailRegionSectionPreset.value = normalized
  emitPreviewProperty({ values: patch })
}

const clearDetailRegionSectionPresetPreview = () => {
  if (!previewingDetailRegionSectionPreset.value) return
  previewingDetailRegionSectionPreset.value = ''
  emitPreviewProperty(null)
}

const handleDetailRegionSectionPresetPreviewFocusOut = (event: FocusEvent) => {
  const current = event.currentTarget
  const nextTarget = event.relatedTarget
  if (!(current instanceof HTMLElement)) {
    clearDetailRegionSectionPresetPreview()
    return
  }
  if (nextTarget instanceof Node && current.contains(nextTarget)) return
  clearDetailRegionSectionPresetPreview()
}

const applyDetailRegionSectionPresetSelection = (presetCode: unknown) => {
  const patch = buildDetailRegionSectionPresetValue(presetCode)
  if (!patch) return
  emitPatchUpdate(patch)
}

const resolveConfiguredFieldKey = (value: unknown): string => {
  if (!value || typeof value !== 'object') return ''
  const record = value as Record<string, any>
  return String(record.key || record.code || record.fieldCode || record.field_code || '').trim()
}

const {
  getConfiguredFieldList,
  configuredFieldItemClasses,
  handleConfiguredFieldDragStart,
  handleConfiguredFieldDragOver,
  handleConfiguredFieldDragEnd,
  handleConfiguredFieldDrop,
  moveConfiguredField,
  updateConfiguredFieldWidth,
  updateConfiguredFieldMinWidth,
  updateConfiguredFieldAlign,
  updateConfiguredFieldFixed,
  updateConfiguredFieldEllipsis,
  updateConfiguredFieldFormatter,
  updateConfiguredFieldEmptyText,
  updateConfiguredFieldTooltipTemplate,
  applyConfiguredFieldPreset,
  removeConfiguredField,
} = useConfiguredDetailRegionFields({
  selectedRelatedFieldConfigs,
  selectedLookupColumnConfigs,
  resolveConfiguredFieldKey,
  emitUpdate,
})

const resolveConfiguredFieldLabel = (value: unknown): string => {
  if (!value || typeof value !== 'object') return '-'
  const record = value as Record<string, any>
  const key = resolveConfiguredFieldKey(record)
  return String(record.label || record.name || key || '-').trim() || '-'
}

const configuredFieldWidth = (value: unknown): string => {
  if (!value || typeof value !== 'object') return ''
  const width = Number((value as Record<string, any>).width)
  return Number.isFinite(width) && width > 0 ? String(Math.round(width)) : ''
}

const configuredFieldMinWidth = (value: unknown): string => {
  if (!value || typeof value !== 'object') return ''
  const minWidth = Number((value as Record<string, any>).minWidth ?? (value as Record<string, any>).min_width)
  return Number.isFinite(minWidth) && minWidth > 0 ? String(Math.round(minWidth)) : ''
}

const configuredFieldAlign = (value: unknown): string => {
  if (!value || typeof value !== 'object') return ''
  const align = String((value as Record<string, any>).align || '').trim().toLowerCase()
  return ['left', 'center', 'right'].includes(align) ? align : ''
}

const configuredFieldFixed = (value: unknown): string => {
  if (!value || typeof value !== 'object') return ''
  const fixed = String((value as Record<string, any>).fixed || '').trim().toLowerCase()
  return ['left', 'right'].includes(fixed) ? fixed : ''
}

const configuredFieldEllipsis = (value: unknown): boolean => {
  if (!value || typeof value !== 'object') return false
  const record = value as Record<string, any>
  return record.ellipsis === true || record.showOverflowTooltip === true || record.show_overflow_tooltip === true
}

const configuredFieldFormatter = (value: unknown): string => {
  if (!value || typeof value !== 'object') return ''
  const formatter = String((value as Record<string, any>).formatter || (value as Record<string, any>).displayFormatter || '').trim().toLowerCase()
  return ['uppercase', 'lowercase', 'number', 'date', 'datetime', 'boolean'].includes(formatter) ? formatter : ''
}

const configuredFieldEmptyText = (value: unknown): string => {
  if (!value || typeof value !== 'object') return ''
  return String((value as Record<string, any>).emptyText ?? (value as Record<string, any>).empty_text ?? '').trim()
}

const configuredFieldTooltipTemplate = (value: unknown): string => {
  if (!value || typeof value !== 'object') return ''
  return String((value as Record<string, any>).tooltipTemplate ?? (value as Record<string, any>).tooltip_template ?? '').trim()
}

const configuredFieldPreset = (value: unknown): string => {
  return resolveDetailRegionColumnPreset(value)
}

const resolvePreviewingConfiguredFieldPreset = (
  key: ConfiguredFieldGroup,
  configKey: string
): string => {
  return (
    previewingConfiguredFieldPreset.value?.group === key &&
    previewingConfiguredFieldPreset.value?.key === configKey
  )
    ? previewingConfiguredFieldPreset.value.presetCode
    : ''
}

const buildConfiguredFieldPresetPreviewValue = (
  key: ConfiguredFieldGroup,
  configKey: string,
  presetCode: string
): Record<string, any>[] => {
  return getConfiguredFieldList(key).map((item) => {
    if (resolveConfiguredFieldKey(item) !== configKey) return item
    return applyDetailRegionColumnPreset(item, presetCode)
  })
}

const setConfiguredFieldPresetPreview = (
  key: ConfiguredFieldGroup,
  configKey: string,
  presetCode: unknown
) => {
  const normalized = String(presetCode || '').trim()
  if (!configKey || !getDetailRegionColumnPresetDefinition(normalized)) {
    clearConfiguredFieldPresetPreview(key, configKey)
    return
  }
  previewingConfiguredFieldPreset.value = {
    group: key,
    key: configKey,
    presetCode: normalized
  }
  previewingDetailRegionSectionPreset.value = ''
  emitPreviewProperty({
    key,
    value: buildConfiguredFieldPresetPreviewValue(key, configKey, normalized)
  })
}

const clearConfiguredFieldPresetPreview = (
  key?: ConfiguredFieldGroup,
  configKey?: string
) => {
  if (!previewingConfiguredFieldPreset.value) return
  if (key && previewingConfiguredFieldPreset.value.group !== key) return
  if (configKey && previewingConfiguredFieldPreset.value.key !== configKey) return
  previewingConfiguredFieldPreset.value = null
  emitPreviewProperty(null)
}

const handleConfiguredFieldPresetPreviewFocusOut = (
  key: ConfiguredFieldGroup,
  configKey: string,
  event: FocusEvent
) => {
  const current = event.currentTarget
  const nextTarget = event.relatedTarget
  if (!(current instanceof HTMLElement)) {
    clearConfiguredFieldPresetPreview(key, configKey)
    return
  }
  if (nextTarget instanceof Node && current.contains(nextTarget)) return
  clearConfiguredFieldPresetPreview(key, configKey)
}

const resolveConfiguredFieldType = (value: unknown): string => {
  if (value && typeof value === 'object') {
    const directType = String(
      (value as Record<string, any>).fieldType ||
      (value as Record<string, any>).field_type ||
      ''
    ).trim()
    if (directType) return directType
  }

  const key = resolveConfiguredFieldKey(value)
  if (!key) return ''
  const option = availableDetailRegionFields.value.find((field) => field.code === key)
  return String(option?.fieldType || '').trim()
}

const configuredFieldPresetOptions = (value: unknown) => {
  return buildConfiguredFieldPresetOptions(resolveConfiguredFieldType(value), tr)
}

const configuredFieldPreviewCandidates = (value: unknown) => {
  return buildConfiguredFieldPreviewCandidates(resolveConfiguredFieldType(value), tr)
}

const resolveConfiguredFieldActivePreset = (
  key: ConfiguredFieldGroup,
  configKey: string,
  value: unknown
): string => {
  return resolvePreviewingConfiguredFieldPreset(key, configKey) || configuredFieldPreset(value)
}

const configuredFieldPresetDescription = (
  key: ConfiguredFieldGroup,
  configKey: string,
  value: unknown
): string => {
  return buildConfiguredFieldPresetDescription(
    resolveConfiguredFieldActivePreset(key, configKey, value),
    tr
  )
}

const configuredFieldPresetPreviewHint = (
  key: ConfiguredFieldGroup,
  configKey: string
): string => {
  return buildConfiguredFieldPresetPreviewHint(
    resolvePreviewingConfiguredFieldPreset(key, configKey),
    tr,
    trf
  )
}

const configuredFieldPresetPreviewItems = (
  key: ConfiguredFieldGroup,
  configKey: string,
  value: unknown
): string[] => {
  return buildConfiguredFieldPresetPreviewItems(
    resolveConfiguredFieldActivePreset(key, configKey, value),
    tr,
    trf
  )
}

const configuredFieldRecommendedPresetText = (
  key: ConfiguredFieldGroup,
  configKey: string,
  value: unknown
): string => {
  return buildConfiguredFieldRecommendedPresetText(
    resolveConfiguredFieldActivePreset(key, configKey, value),
    configuredFieldPresetOptions(value),
    trf
  )
}

const configuredFieldPresetButtonClasses = (
  key: ConfiguredFieldGroup,
  configKey: string,
  value: unknown,
  presetCode: unknown
) => ({
  'is-applied': configuredFieldPreset(value) === String(presetCode || '').trim(),
  'is-previewing': resolvePreviewingConfiguredFieldPreset(key, configKey) === String(presetCode || '').trim()
})

const switchValue = (key: string): boolean => booleanValue(key)

const resolveSchemaLabel = (item: { label: string; labelKey?: string }) => {
  if (item.labelKey) {
    return tr(item.labelKey, item.label)
  }
  return item.label
}

const resolveOptionLabel = (option: { label: string; labelKey?: string }) => {
  if (option.labelKey) {
    return tr(option.labelKey, option.label)
  }
  return option.label
}

const emitJsonUpdate = (key: string, value: unknown) => {
  let parsed: unknown = value
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) {
      parsed = ''
    } else {
      try {
        parsed = JSON.parse(trimmed)
      } catch {
        parsed = value
      }
    }
  }
  emitUpdate(key, parsed)
}

const jsonValue = (key: string): string => {
  const value = propertyValue(key)
  if (typeof value === 'string') return value
  if (value === null || value === undefined) return ''
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

const getTabsValue = () => {
  const tabs = propertyValue('tabs') || []
  return Array.isArray(tabs) ? tabs as Array<{ id: string, title: string, name?: string, fields: any[] }> : []
}

const handleTabsChange = () => {
  emitUpdate('tabs', [...getTabsValue()])
}

const addTab = () => {
  const currentTabs = [...getTabsValue()]
  const newId = `tab_${Date.now()}`
  currentTabs.push({
    id: newId,
    title: tr('system.pageLayout.designer.defaults.newTab', 'New Tab'),
    name: newId,
    fields: []
  })
  emitUpdate('tabs', currentTabs)
}

const removeTab = (index: number) => {
  const currentTabs = [...getTabsValue()]
  if (currentTabs.length > 1) {
    currentTabs.splice(index, 1)
    emitUpdate('tabs', currentTabs)
  }
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.section-property-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;

  :deep(.el-form-item) {
    margin-bottom: 10px;
  }

  :deep(.el-form-item:last-child) {
    margin-bottom: 0;
  }

  :deep(.el-form-item__label) {
    padding-bottom: 3px;
    color: #5b6472;
    font-size: 12px;
    font-weight: 600;
    line-height: 1.35;
  }

  :deep(.el-input),
  :deep(.el-select),
  :deep(.el-input-number) {
    width: 100%;
  }

  :deep(.section-column-choice) {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    width: 100%;
    gap: 6px;
  }

  :deep(.section-column-choice .el-radio-button) {
    width: 100%;
  }

  :deep(.section-column-choice .el-radio-button__inner) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 32px;
    padding: 0 10px;
    border: 1px solid rgba(15, 23, 42, 0.12);
    border-radius: 10px;
    box-shadow: none;
    font-size: 12px;
    font-weight: 700;
  }

  :deep(.section-column-choice .el-radio-button__original-radio:checked + .el-radio-button__inner) {
    border-color: #2563eb;
    background: rgba(37, 99, 235, 0.1);
    color: #1d4ed8;
  }

  :deep(.section-column-choice .el-radio-button:first-child .el-radio-button__inner),
  :deep(.section-column-choice .el-radio-button:last-child .el-radio-button__inner) {
    border-radius: 10px;
  }

  :deep(.section-property-editor__select-popper.el-zoom-in-top-leave-active),
  :deep(.section-property-editor__select-popper.el-zoom-in-top-leave-from),
  :deep(.section-property-editor__select-popper.el-zoom-in-top-leave-to) {
    pointer-events: none !important;
  }

  .property-section-card {
    overflow: hidden;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 14px;
    background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    box-shadow: 0 10px 18px rgba(15, 23, 42, 0.04);
  }

  .property-section-card__header {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(15, 23, 42, 0.08);
    background: rgba(248, 250, 252, 0.92);
  }

  .property-section-card__content {
    padding: 10px 12px 12px;
  }

  .tabs-manager {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;

    .tab-item-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 8px;
      padding: 8px;
      border: 1px solid rgba(15, 23, 42, 0.08);
      border-radius: 10px;
      background: #f8fafc;
    }

    .add-tab-btn {
      width: 100%;
      margin-top: 2px;
    }
  }

  .detail-region-field-picker {
    width: 100%;
  }

  .detail-region-configurator {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 10px;
  }

  .detail-region-configurator__item {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 10px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 12px;
    background: #f8fafc;
    cursor: move;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
  }

  .detail-region-configurator__item.is-dragging {
    opacity: 0.58;
    border-color: rgba(37, 99, 235, 0.22);
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08);
  }

  .detail-region-configurator__item.is-drag-over-before::before,
  .detail-region-configurator__item.is-drag-over-after::after {
    content: '';
    position: absolute;
    left: 10px;
    right: 10px;
    height: 2px;
    border-radius: 999px;
    background: #2563eb;
  }

  .detail-region-configurator__item.is-drag-over-before::before {
    top: -1px;
  }

  .detail-region-configurator__item.is-drag-over-after::after {
    bottom: -1px;
  }

  .detail-region-configurator__meta {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .detail-region-configurator__drag-handle {
    flex-shrink: 0;
    color: #94a3b8;
    font-family: monospace;
    font-size: 12px;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -1px;
    user-select: none;
  }

  .detail-region-configurator__label {
    color: #0f172a;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.4;
  }

  .detail-region-configurator__controls {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    gap: 8px;
  }

  .detail-region-configurator__width {
    display: grid;
    gap: 4px;
    min-width: 120px;
    flex: 0 0 140px;
    color: #475569;
    font-size: 12px;
    line-height: 1.4;
  }

  .detail-region-configurator__align {
    display: grid;
    gap: 4px;
    min-width: 120px;
    flex: 0 0 140px;
    color: #475569;
    font-size: 12px;
    line-height: 1.4;
  }

  .detail-region-configurator__text {
    display: grid;
    gap: 4px;
    min-width: 180px;
    flex: 1 1 220px;
    color: #475569;
    font-size: 12px;
    line-height: 1.4;
  }

  .detail-region-configurator__switch {
    display: grid;
    gap: 8px;
    min-width: 96px;
    color: #475569;
    font-size: 12px;
    line-height: 1.4;
  }

  .detail-region-configurator__preset-description,
  .detail-region-configurator__preset-recommendation {
    margin-top: 6px;
    color: #64748b;
    font-size: 11px;
    line-height: 1.5;
  }

  .detail-region-configurator__preset-hint {
    margin-top: 6px;
    color: #1d4ed8;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.5;
  }

  .detail-region-configurator__preset-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
  }

  .detail-region-configurator__preset-trigger {
    appearance: none;
    border: 1px solid rgba(148, 163, 184, 0.38);
    border-radius: 999px;
    background: #ffffff;
    color: #334155;
    cursor: pointer;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.4;
    min-height: 24px;
    padding: 0 10px;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease, color 0.18s ease;
  }

  .detail-region-configurator__preset-trigger:hover,
  .detail-region-configurator__preset-trigger:focus-visible {
    outline: none;
    border-color: rgba(37, 99, 235, 0.3);
    background: rgba(239, 246, 255, 0.92);
    color: #1d4ed8;
  }

  .detail-region-configurator__preset-trigger.is-previewing {
    border-color: rgba(14, 165, 233, 0.34);
    background: rgba(224, 242, 254, 0.9);
    color: #0369a1;
    box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.12);
  }

  .detail-region-configurator__preset-trigger.is-applied {
    border-color: rgba(37, 99, 235, 0.28);
    background: rgba(219, 234, 254, 0.92);
    color: #1d4ed8;
  }

  .detail-region-configurator__preset-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 6px;
  }

  .detail-region-configurator__preset-preview-label {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.8;
  }

  .detail-region-configurator__preset-chip {
    display: inline-flex;
    align-items: center;
    min-height: 22px;
    padding: 0 8px;
    border: 1px solid rgba(37, 99, 235, 0.12);
    border-radius: 999px;
    background: rgba(239, 246, 255, 0.8);
    color: #1d4ed8;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.4;
  }

  .detail-region-configurator__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .detail-region-meta {
    display: grid;
    gap: 4px;
    margin-top: 8px;
    padding: 8px 10px;
    border: 1px solid rgba(37, 99, 235, 0.12);
    border-radius: 10px;
    background: rgba(239, 246, 255, 0.72);
    color: #475569;
    font-size: 12px;
    line-height: 1.5;
  }

  .detail-region-template-presets {
    margin-top: 10px;
    padding: 10px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 12px;
    background: #f8fafc;
  }

  .detail-region-template-presets__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 8px;
  }

  .detail-region-template-presets__label,
  .detail-region-template-presets__current {
    color: #475569;
    font-size: 11px;
    font-weight: 700;
    line-height: 1.4;
  }

  .detail-region-template-presets__current {
    color: #1d4ed8;
  }

  .detail-region-template-presets__actions,
  .detail-region-template-presets__preview {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .detail-region-template-presets__trigger {
    appearance: none;
    border: 1px solid rgba(148, 163, 184, 0.38);
    border-radius: 999px;
    background: #ffffff;
    color: #334155;
    cursor: pointer;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.4;
    min-height: 26px;
    padding: 0 10px;
    transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease, color 0.18s ease;
  }

  .detail-region-template-presets__trigger:hover,
  .detail-region-template-presets__trigger:focus-visible {
    outline: none;
    border-color: rgba(37, 99, 235, 0.3);
    background: rgba(239, 246, 255, 0.92);
    color: #1d4ed8;
  }

  .detail-region-template-presets__trigger.is-previewing {
    border-color: rgba(14, 165, 233, 0.34);
    background: rgba(224, 242, 254, 0.9);
    color: #0369a1;
    box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.12);
  }

  .detail-region-template-presets__trigger.is-applied {
    border-color: rgba(37, 99, 235, 0.28);
    background: rgba(219, 234, 254, 0.92);
    color: #1d4ed8;
  }

  .detail-region-template-presets__description,
  .detail-region-template-presets__hint {
    margin-top: 8px;
    font-size: 11px;
    line-height: 1.5;
  }

  .detail-region-template-presets__description {
    color: #64748b;
  }

  .detail-region-template-presets__hint {
    color: #1d4ed8;
    font-weight: 600;
  }

  .detail-region-template-presets__preview {
    margin-top: 8px;
  }

  .detail-region-template-presets__preview-label {
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.8;
  }

  .detail-region-template-presets__preview-chip {
    display: inline-flex;
    align-items: center;
    min-height: 22px;
    padding: 0 8px;
    border: 1px solid rgba(37, 99, 235, 0.12);
    border-radius: 999px;
    background: rgba(239, 246, 255, 0.8);
    color: #1d4ed8;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.4;
  }
}
</style>
