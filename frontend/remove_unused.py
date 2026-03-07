import re

vue_file = r"c:\Users\ND\Desktop\Notting_Project\NEWSEAMS\frontend\src\components\common\BaseDetailPage.vue"

with open(vue_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove getSectionDisplayTitle
content = re.sub(r"const getSectionDisplayTitle \= \(section\: DetailSection\)\: string \=\> \{[\s\S]*?return \`\$\{baseTitle\} \/ \$\{tabTitle\}\`\n\}", "", content)

# Remove getFieldItemStyle
content = re.sub(r"const getFieldItemStyle \= \(field\: DetailField\)\: Record\<string\, string\> \=\> \{[\s\S]*?return \{ minHeight\: \`\$\{Math\.round\(minHeight\)\}px\` \}\n\}", "", content)

# Remove getDetailSectionColumns
content = re.sub(r"const getDetailSectionColumns \= \(section\: DetailSection\)\: number \=\> \{[\s\S]*?return section\.columns \|\| specifiedColumns \|\| 2\n\}", "", content)

# Remove getSectionCanvasStyle
content = re.sub(r"/\*\*[\s\S]*?CSS Grid variables\.[\s\S]*?\*/\nconst getSectionCanvasStyle \= \(section\: DetailSection\)\: Record\<string\, string\> \=\> \{[\s\S]*?\}\n\}", "", content)

# Remove getFieldColStyle
content = re.sub(r"const getFieldColStyle \= \(field\: DetailField\, section\: DetailSection\)\: Record\<string\, string\> \=\> \{[\s\S]*?return toCanvasGridStyle\(\{ span\, rowSpan\: field\.rowSpan \}\)\n\}", "", content)

# Remove getFieldPlacementAttrs
content = re.sub(r"const getFieldPlacementAttrs \= \(field\: DetailField\)\: Record\<string\, string\> \=\> \{[\s\S]*?\}", "", content)

# Remove handleSectionHeaderClick
content = re.sub(r"const handleSectionHeaderClick \= \(section\: DetailSection\) \=\> \{[\s\S]*?\}\n\}", "", content)

with open(vue_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed unused functions")
