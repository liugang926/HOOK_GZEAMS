const fs = require('fs');
let content = fs.readFileSync('src/views/dynamic/DynamicListPage.vue', 'utf8');

const targetRegex = /<div class="unified-search">[\s\S]*?<\/div>/;

const replacement = `<div class="unified-search">
          <el-select
            v-model="form.__unifiedField"
            class="unified-search-field"
            clearable
            :placeholder="t('common.select')"
          >
            <el-option
              :label="t('common.all')"
              value="__all"
            />
            <el-option
              v-for="option in unifiedSearchFieldOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-input
            v-model="form.__unifiedKeyword"
            class="unified-search-keyword"
            clearable
            :placeholder="t('common.selectors.searchKeyword')"
          />
        </div>`;

content = content.replace(targetRegex, replacement);

fs.writeFileSync('src/views/dynamic/DynamicListPage.vue', content, 'utf8');
console.log('Fixed unified-search');
