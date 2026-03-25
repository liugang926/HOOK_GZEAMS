"""
Validate bash commands before execution.

Checks for:
- Dangerous commands (rm -rf, etc.)
- Commands that might break the system
- Commands that should use docker exec instead
"""

import sys
import re

DANGEROUS_PATTERNS = [
    (r'rm\s+-rf\s+/', 'CRITICAL: Attempting to delete root directory!'),
    (r'rm\s+-rf\s+\.', 'CRITICAL: Attempting to delete current directory!'),
    (r'>\s*/dev/sda', 'CRITICAL: Attempting to write to disk directly!'),
    (r'dd\s+if=', 'CRITICAL: Disk destruction command!'),
    (r':(){:\s*:};\s*:', 'WARNING: Fork bomb pattern'),
]

SAFE_PREFIXES = [
    'docker-compose exec backend',
    'docker exec gzeams-backend',
    'cd ',
    'echo ',
    'git ',
]

def validate_command(command):
    """Validate a bash command for safety."""
    # Remove leading 'Bash(' wrapper if present
    command = re.sub(r'^Bash\(([^)]+)\)', r'\1', command)

    # Strip quotes
    command = command.strip('"').strip("'")

    issues = []

    # Check against dangerous patterns
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            issues.append((pattern, message))

    # Check for python manage.py commands (should use docker exec)
    if 'python manage.py' in command and 'docker exec' not in command and 'docker-compose exec' not in command:
        issues.append(('python manage.py', 'WARNING: python manage.py should run inside Docker container. Use: docker-compose exec backend python manage.py ...'))

    return issues

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(0)

    command = sys.argv[1]
    issues = validate_command(command)

    if issues:
        print("⚠️  Command Safety Warning:")
        for pattern, message in issues:
            print(f"  {message}")
            print(f"    Pattern: {pattern}")
        print("\nProceed with caution!")
        sys.exit(1)
    else:
        sys.exit(0)
