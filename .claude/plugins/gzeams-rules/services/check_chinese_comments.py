"""
Check for Chinese comments in source files.

GZEAMS Standard: ALL code comments MUST be in English.
"""

import sys
import re

# Chinese character ranges
CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fff]+')

def check_file(filepath):
    """Check a file for Chinese characters in comments."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        return True  # Skip files that can't be read

    issues = []

    for i, line in enumerate(lines, 1):
        # Skip strings, only check comments
        # Python comments
        if '#' in line and '"' not in line.split('#')[0]:
            comment_part = line.split('#', 1)[1]
            if CHINESE_PATTERN.search(comment_part):
                issues.append((i, line.strip(), comment_part))

        # JS/TS/TSX/Vue comments (// and /* */ style)
        if '//' in line:
            comment_part = line.split('//', 1)[1]
            if CHINESE_PATTERN.search(comment_part):
                issues.append((i, line.strip(), comment_part))

    return issues

def format_issue(issue):
    """Format a single issue for display."""
    line_num, full_line, comment = issue
    # Remove the comment from display to focus on the Chinese text
    return f"  Line {line_num}: {comment.strip()}"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_chinese_comments.py <file>")
        sys.exit(0)

    filepath = sys.argv[1]
    issues = check_file(filepath)

    if issues:
        print(f"⚠️  WARNING: Chinese comments found in {filepath}")
        print("GZEAMS Standard: ALL code comments MUST be in English.")
        print("\nFound at lines:")
        for issue in issues:
            print(format_issue(issue))
        print("\nPlease rewrite these comments in English.")
        sys.exit(1)
    else:
        sys.exit(0)
