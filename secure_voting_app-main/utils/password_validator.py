"""
Password Validation Module

Provides password strength validation and masking utilities.
Enforces security requirements including minimum length, uppercase,
lowercase, numeric, and special character requirements.
"""

import re
from typing import Tuple

# ===== PASSWORD VALIDATION REQUIREMENTS =====
MIN_PASSWORD_LENGTH = 8
REQUIRED_UPPERCASE_PATTERN = r"[A-Z]"
REQUIRED_LOWERCASE_PATTERN = r"[a-z]"
REQUIRED_DIGIT_PATTERN = r"\d"
REQUIRED_SPECIAL_PATTERN = r"[!@#$%^&*(),.?\":{}|<>]"

def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength

    Args:
        password: Password to validate

    Returns:
        Tuple[bool, str]: (is_valid, message)
        - is_valid: True if password meets requirements
        - message: Error message if invalid, empty string if valid
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"

    if not re.search(REQUIRED_UPPERCASE_PATTERN, password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(REQUIRED_LOWERCASE_PATTERN, password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(REQUIRED_DIGIT_PATTERN, password):
        return False, "Password must contain at least one number"

    if not re.search(REQUIRED_SPECIAL_PATTERN, password):
        return False, "Password must contain at least one special character"

    return True, ""

def mask_password(password: str) -> str:
    """
    Mask a password for display or logging

    Args:
        password: Password to mask

    Returns:
        Masked password (e.g., "********")
    """
    return "*" * len(password)