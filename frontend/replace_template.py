import re
import os

vue_file = r"c:\Users\ND\Desktop\Notting_Project\NEWSEAMS\frontend\src\components\common\BaseDetailPage.vue"
template_file = r"c:\Users\ND\Desktop\Notting_Project\NEWSEAMS\frontend\new_template.txt"

with open(vue_file, 'r', encoding='utf-8') as f:
    content = f.read()

with open(template_file, 'r', encoding='utf-8') as f:
    new_template = f.read()

# Replace everything from </script>\n\n<template> to </template>\n\n<style scoped lang="scss">
# Regex pattern blocks:
pattern = re.compile(r"(</script>\s*)(<template>[\s\S]*?</template>)(\s*<style scoped lang=\"scss\">)", re.MULTILINE)

def replacer(match):
    return match.group(1) + new_template + match.group(3)

new_content = pattern.sub(replacer, content)

with open(vue_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully replaced template block")
