import re
import os

vue_file_path = r"c:\Users\ND\Desktop\Notting_Project\NEWSEAMS\frontend\src\components\common\BaseDetailPage.vue"
scss_file_path = r"c:\Users\ND\Desktop\Notting_Project\NEWSEAMS\frontend\src\components\common\detail\BaseDetailPage.scss"

with open(vue_file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the style block robustly
match = re.search(r'<style[^>]*>([\s\S]*?)</style>', content)
if match:
    css_content = match.group(1).strip()
    
    # Write to new SCSS file
    os.makedirs(os.path.dirname(scss_file_path), exist_ok=True)
    with open(scss_file_path, 'w', encoding='utf-8') as f:
        f.write(css_content + '\n')
    print(f"Successfully wrote {len(css_content)} chars to {scss_file_path}")
    
    # Replace in original file
    new_content = re.sub(
        r'<style[^>]*>[\s\S]*?</style>',
        '<style lang="scss" scoped>\n@import "./detail/BaseDetailPage.scss";\n</style>',
        content
    )
    
    with open(vue_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced style block with import in BaseDetailPage.vue")
else:
    print("Could not find <style> block")
