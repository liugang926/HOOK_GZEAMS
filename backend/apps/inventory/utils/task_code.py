"""
Utility functions for inventory task code generation.
"""
from datetime import datetime
import random
import string


def generate_task_code() -> str:
    """
    Generate a unique inventory task code.

    Format: INV{YYYYMMDD}{4-char-random}
    Example: INV20250115A3B7

    Returns:
        Unique task code string
    """
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f'INV{date_str}{random_str}'


def validate_task_code(code: str) -> bool:
    """
    Validate inventory task code format.

    Args:
        code: Task code to validate

    Returns:
        True if valid, False otherwise
    """
    if not code or len(code) != 15:
        return False

    if not code.startswith('INV'):
        return False

    # Check date portion (8 digits after INV)
    date_part = code[3:11]
    if not date_part.isdigit():
        return False

    # Check random portion (4 characters)
    random_part = code[11:]
    if len(random_part) != 4:
        return False

    return True
