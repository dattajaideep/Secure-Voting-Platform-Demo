import re
from typing import Tuple

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
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
        
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
        
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
        
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
        
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
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