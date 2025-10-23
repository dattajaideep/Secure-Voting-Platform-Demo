# utils/data_masking.py
"""
Data Masking and Privacy Utility

Provides system-wide functionality to mask sensitive voter personally identifiable information (PII)
with "XXXXXX" and unmask it when authorized. This ensures privacy by default while allowing
controlled access to full data when needed.
"""

import re
from typing import Dict, List, Any, Union


# Constants for masking
MASK_VALUE = "XXXXXX"
SENSITIVE_FIELDS = {
    'voter_id',
    'name',
    'email',
    'phone',
    'address',
    'ssn',
    'user_email',
    'user_name',
}

# Fields that are safe to display without masking
PUBLIC_FIELDS = {
    'has_token',
    'has_voted',
    'token_hash',
    'signature',
    'ballot_id',
    'candidate',
    'id',
    'timestamp',
    'created_at',
    'updated_at',
    'role',
}


def mask_value(value: Any, always_mask: bool = False) -> str:
    """
    Mask a single value with XXXXXX if it contains sensitive data.
    
    Args:
        value: The value to potentially mask
        always_mask: If True, always return XXXXXX for non-None values
        
    Returns:
        Masked string or original value if it's safe
    """
    if value is None:
        return None
    
    if always_mask:
        return MASK_VALUE
    
    # Convert to string for display
    value_str = str(value)
    
    # Check if it looks like sensitive data (non-numeric or patterns that suggest PII)
    # For now, we mask most non-numeric values as they're likely names or IDs
    if len(value_str) > 0:
        return MASK_VALUE
    
    return value_str


def mask_dict(data: Dict[str, Any], unmask: bool = False, allowed_fields: set = None) -> Dict[str, Any]:
    """
    Mask all sensitive fields in a dictionary.
    
    Args:
        data: Dictionary containing potentially sensitive data
        unmask: If True, return unmasked data
        allowed_fields: Set of field names that are allowed to be shown unmasked.
                       If None, uses PUBLIC_FIELDS
        
    Returns:
        New dictionary with sensitive fields masked
    """
    if not data:
        return data
    
    if unmask:
        # Return unmasked data as-is
        return data
    
    if allowed_fields is None:
        allowed_fields = PUBLIC_FIELDS
    
    masked_data = {}
    for key, value in data.items():
        if key in allowed_fields:
            # Public field - don't mask
            masked_data[key] = value
        elif key.lower() in SENSITIVE_FIELDS or key.lower().endswith('_id') or key.lower().endswith('_name'):
            # Sensitive field - mask it
            masked_data[key] = MASK_VALUE
        else:
            # Unknown field - be conservative and mask
            masked_data[key] = MASK_VALUE if value is not None else None
    
    return masked_data


def mask_list(data_list: List[Dict[str, Any]], unmask: bool = False, allowed_fields: set = None) -> List[Dict[str, Any]]:
    """
    Mask sensitive fields in a list of dictionaries.
    
    Args:
        data_list: List of dictionaries containing potentially sensitive data
        unmask: If True, return unmasked data
        allowed_fields: Set of field names that are allowed to be shown unmasked
        
    Returns:
        New list with sensitive fields masked in each dictionary
    """
    if not data_list:
        return data_list
    
    return [mask_dict(item, unmask=unmask, allowed_fields=allowed_fields) for item in data_list]


def create_custom_mask_fields(*field_names: str) -> set:
    """
    Create a custom set of fields to consider sensitive.
    
    Args:
        *field_names: Variable length argument list of field names to mask
        
    Returns:
        Set of field names to mask
    """
    return set(field_names)


def is_masked(value: Any) -> bool:
    """Check if a value is masked."""
    return value == MASK_VALUE


def can_unmask(user_role: str) -> bool:
    """
    Determine if a user with the given role can unmask data.
    
    Args:
        user_role: The user's role (e.g., 'admin', 'voter', 'guest')
        
    Returns:
        True if the user can unmask data, False otherwise
    """
    # Only admins can view unmasked data
    return user_role == 'admin'


def can_voter_unmask_own_data(user_role: str) -> bool:
    """
    Determine if a user can unmask only their own voter data.
    
    Args:
        user_role: The user's role (e.g., 'admin', 'voter', 'guest')
        
    Returns:
        True if the user is a voter and can unmask their own data
    """
    # Voters can view their own unmasked data
    return user_role == 'voter'


def filter_voter_data(data_list: List[Dict[str, Any]], voter_id: str) -> List[Dict[str, Any]]:
    """
    Filter a list of voter data to return only the specified voter.
    
    Args:
        data_list: List of voter dictionaries
        voter_id: The voter_id to filter for
        
    Returns:
        List containing only the matching voter, or empty list if not found
    """
    if not data_list or not voter_id:
        return []
    
    matching_voters = [v for v in data_list if v.get('voter_id') == voter_id]
    return matching_voters


def mask_voter_for_self(voter_dict: Dict[str, Any], logged_in_voter_id: str, unmask: bool = False) -> Dict[str, Any]:
    """
    Apply masking rules for voter viewing their own data.
    Voters can unmask their own data only.
    
    Args:
        voter_dict: Dictionary with voter data
        logged_in_voter_id: The ID of the logged-in voter
        unmask: Whether to unmask (should be False by default for privacy)
        
    Returns:
        Masked or unmasked voter dictionary
    """
    # If this is the voter's own data, they can see it unmasked if they choose
    is_own_data = voter_dict.get('voter_id') == logged_in_voter_id
    
    if is_own_data and unmask:
        # Voter viewing their own data - allow unmasking
        return voter_dict
    else:
        # Default to masked
        return mask_dict(voter_dict, unmask=False)


def get_display_name(voter_dict: Dict[str, Any], unmask: bool = False) -> str:
    """
    Get a safe display name for a voter, with optional unmasking.
    
    Args:
        voter_dict: Dictionary with 'voter_id' and 'name' keys
        unmask: If True, return unmasked name
        
    Returns:
        Display name (either full or masked)
    """
    if unmask:
        return f"{voter_dict.get('name', 'Unknown')} (ID: {voter_dict.get('voter_id', 'N/A')})"
    else:
        return f"{MASK_VALUE} (ID: {MASK_VALUE})"


def apply_role_based_masking(data: Union[Dict, List], user_role: str, allow_unmask_override: bool = False) -> Union[Dict, List]:
    """
    Apply masking based on user role.
    
    Args:
        data: Dictionary or list of dictionaries to potentially mask
        user_role: The user's role
        allow_unmask_override: If True, checks for session state override
        
    Returns:
        Masked or unmasked data based on role
    """
    # Check if we should unmask (admin or authorized)
    should_unmask = can_unmask(user_role)
    
    # Optional: check for session state override (e.g., admin explicitly toggled unmask)
    if allow_unmask_override:
        try:
            import streamlit as st
            should_unmask = should_unmask and st.session_state.get('unmask_voter_data', False)
        except:
            pass
    
    if isinstance(data, list):
        return mask_list(data, unmask=should_unmask)
    else:
        return mask_dict(data, unmask=should_unmask)


def unmask_for_display(masked_dict: Dict[str, Any], original_dict: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convert a masked dictionary back to unmasked (useful if you have the original).
    
    Args:
        masked_dict: The masked dictionary (for reference)
        original_dict: The original unmasked dictionary (if available)
        
    Returns:
        The original dictionary if provided, otherwise returns the masked dict as-is
    """
    if original_dict:
        return original_dict
    
    # If no original, return masked dict (cannot recover masked data)
    return masked_dict


# Decorator for masking function outputs
def mask_output(allowed_fields: set = None, auto_unmask: bool = False):
    """
    Decorator to automatically mask the output of a function.
    
    Args:
        allowed_fields: Set of fields to not mask
        auto_unmask: If True, checks user role in session and unmasks for admins
        
    Example:
        @mask_output(allowed_fields={'id', 'timestamp'})
        def get_voter_data():
            return voter_repo.get_all_voters()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Determine if we should unmask
            should_unmask = False
            if auto_unmask:
                try:
                    import streamlit as st
                    from utils.roles import get_user_role
                    user_role = get_user_role()
                    should_unmask = can_unmask(user_role) and st.session_state.get('unmask_voter_data', False)
                except:
                    pass
            
            # Apply masking to result
            if isinstance(result, list):
                return mask_list(result, unmask=should_unmask, allowed_fields=allowed_fields)
            elif isinstance(result, dict):
                return mask_dict(result, unmask=should_unmask, allowed_fields=allowed_fields)
            else:
                return result
        
        return wrapper
    return decorator
