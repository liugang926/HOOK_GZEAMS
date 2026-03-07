import re

vue_file_path = r"c:\Users\ND\Desktop\Notting_Project\NEWSEAMS\frontend\src\components\common\BaseDetailPage.vue"

with open(vue_file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Pattern to rip out the data processing logic between availableActions and validation
pattern = r'(/\*\*\s*Visible reverse relations \(not hidden\)\s*\*/[\s\S]*?)// ============================================================================\s*// Expose'

replacement = """import { toRefs } from 'vue'
import { useDetailData } from '@/composables/useDetailData'

const { data: dataRef, formData: formDataRef, sections: sectionsRef, reverseRelations: reverseRelationsRef, showRelatedObjects: showRelatedObjectsRef, objectCode: objectCodeRef } = toRefs(props)

const {
  groupedReverseRelationSections,
  editDrawerProxyFields,
  getFieldValue,
  getEditFieldValue,
  toInlineEditRuntimeField,
  updateFormData
} = useDetailData({
  data: dataRef,
  formData: formDataRef,
  sections: sectionsRef,
  reverseRelations: reverseRelationsRef,
  showRelatedObjects: showRelatedObjectsRef,
  objectCode: objectCodeRef,
  activeTabs
}, emit)

// ============================================================================
// Expose"""

new_text = re.sub(pattern, replacement, text)

# We also need to remove the duplicate watch blocks for objectCode/locale at the end of the script, 
# and the duplicate fetchRuntimeRelations calls, and runtimeRelations declarations.
new_text = re.sub(r'const runtimeRelations = ref<ReverseRelationField\[\]>\(\[\]\)\s*', '', new_text)

new_text = re.sub(r'watch\(\s*\(\) => props\.objectCode,\s*\(\) => \{\s*fetchRuntimeRelations\(\)\s*\},[\s\S]*?immediate: true \}\s*\)', '', new_text)
new_text = re.sub(r'watch\(\s*\(\) => locale\.value,\s*\(\) => \{\s*fetchRuntimeRelations\(\)\s*\}\s*\)', '', new_text)

with open(vue_file_path, 'w', encoding='utf-8') as f:
    f.write(new_text)

print("BaseDetailPage.vue script logic successfully ripped and replaced.")
