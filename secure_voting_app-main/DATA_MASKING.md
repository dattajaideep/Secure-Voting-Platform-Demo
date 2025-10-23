# Voter Data Masking & Privacy System

## Overview

The Secure Voting Platform implements a **system-wide voter data masking feature** to protect personally identifiable information (PII) by default. All voter sensitive data is masked with "XXXXXX" during display, and can only be unmasked by authorized administrators when explicitly needed.

## Architecture

### Core Components

1. **Data Masking Utility** (`utils/data_masking.py`)
   - Core masking/unmasking functions
   - Role-based access control for data visibility
   - Support for individual values, dictionaries, and lists

2. **Integration Points** (in `streamlit_app.py`)
   - Voter list display (Register Voter page)
   - Voter selection dropdowns (Request Token & Cast Vote pages)
   - Admin-only pages with unmasking toggle

3. **Session State Management**
   - `unmask_voter_data` flag in `st.session_state`
   - Only available to admin users
   - Toggle via checkbox in sidebar

## How It Works

### Role-Based Unmasking

The system supports three types of users with different unmasking capabilities:

1. **Admin Users**: Can unmask ALL voter data via the sidebar toggle "🔓 Unmask Voter Data"
2. **Logged-In Voters**: Can unmask ONLY their OWN voter data via the sidebar toggle "🔓 View My Details"
3. **Guests**: Cannot unmask any data (always see masked)

### Default Behavior (Masked)

By default, all voter PII is masked:

```
Original: {"voter_id": "V001", "name": "John Doe", "has_token": true}
Masked:   {"voter_id": "XXXXXX", "name": "XXXXXX", "has_token": true}
```

### Public vs. Sensitive Fields

**Sensitive Fields (Always Masked):**
- `voter_id`
- `name`
- `email`
- `phone`
- `address`
- `ssn`
- `user_email`
- `user_name`

**Public Fields (Never Masked):**
- `has_token`
- `has_voted`
- `token_hash`
- `signature`
- `ballot_id`
- `candidate`
- `id`
- `timestamp`
- `created_at`
- `updated_at`
- `role`

### Admin Unmasking

Administrators can unmask data by:

1. Logging in as admin (via Admin Login page)
2. Toggling the **"🔓 Unmask Voter Data"** checkbox in the sidebar
3. Viewing unmasked voter data in displays and dropdowns

When unmasked is OFF: `Voter displays as "XXXXXX (ID: XXXXXX)"`
When unmasked is ON: `Voter displays as "John Doe (ID: V001)"`

### Voter Self-Unmasking (Request Token Page)

When a voter logs in and navigates to the **Request Token** page:

1. They see ONLY their own voter information (not other voters)
2. By default, their voter ID and name are masked: `"XXXXXX"`
3. They can toggle the **"🔓 View My Details"** checkbox in the sidebar to unmask their own data
4. When unmasked, they see: `"Your Voter ID: V001"` and `"Name: John Doe"`
5. They can then click "Request Token" to issue themselves a voting token

**Key Privacy Feature**: Voters cannot see or unmask other voters' data—only their own.

## Usage Guide

### For Developers

#### Import and Use the Masking Utility

```python
from utils.data_masking import mask_dict, mask_list, get_display_name, MASK_VALUE

# Mask a single voter dictionary
voter = {"voter_id": "V001", "name": "John Doe", "has_token": True}
masked_voter = mask_dict(voter, unmask=False)  # Returns masked version

# Mask a list of voters
voters = [...]
masked_voters = mask_list(voters, unmask=False)

# Get masked display name
display_name = get_display_name(voter, unmask=False)  # Returns "XXXXXX (ID: XXXXXX)"
```

def can_unmask(user_role: str) -> bool:
    """Check if admin can unmask all data"""
    return user_role == 'admin'

def can_voter_unmask_own_data(user_role: str) -> bool:
    """Check if voter can unmask their own data"""
    return user_role == 'voter'

def filter_voter_data(data_list, voter_id: str):
    """Get only the specified voter from a list"""
    return [v for v in data_list if v.get('voter_id') == voter_id]

def mask_voter_for_self(voter_dict, logged_in_voter_id: str, unmask: bool):
    """Apply masking rules for voter viewing own data"""
    is_own_data = voter_dict.get('voter_id') == logged_in_voter_id
    if is_own_data and unmask:
        return voter_dict  # Unmasked own data
    else:
        return mask_dict(voter_dict, unmask=False)  # Masked
```

#### Check Role-Based Permissions

```python
from utils.data_masking import can_unmask, can_voter_unmask_own_data
from utils.roles import get_user_role

user_role = get_user_role()

# For admins viewing all data
if can_unmask(user_role):
    # Show unmasked data
    pass

# For voters viewing own data
if can_voter_unmask_own_data(user_role):
    # Voter can toggle to see own data
    pass
```

#### Voter-Specific Unmasking

```python
import streamlit as st
from utils.data_masking import filter_voter_data, mask_voter_for_self

def render_request_token():
    current_voter_id = st.session_state.get('voter_id')
    voters = voter_repo.get_all_voters()
    
    # Show only this voter's data
    their_voters = filter_voter_data(voters, current_voter_id)
    
    if their_voters:
        voter_data = their_voters[0]
        should_unmask = st.session_state.get('unmask_own_voter_data', False)
        
        # Apply voter-specific masking
        display_data = mask_voter_for_self(voter_data, current_voter_id, should_unmask)
        
        if should_unmask:
            st.info(f"Your Voter ID: {display_data['voter_id']}")
        else:
            st.info(f"Your Voter ID: XXXXXX")
```

#### Adding Masking to New Pages

```python
import streamlit as st
from utils.data_masking import mask_list
from utils.roles import is_admin

# In your page render function:
def render_new_page():
    voters = voter_repo.get_all_voters()
    
    # Check if admin wants to see unmasked data
    should_unmask = st.session_state.get('unmask_voter_data', False) and is_admin()
    
    # Apply masking
    display_voters = mask_list(voters, unmask=should_unmask)
    
    # Display
    st.dataframe(display_voters)
```

#### Using the Masking Decorator

```python
from utils.data_masking import mask_output

@mask_output(allowed_fields={'id', 'timestamp'})
def get_voter_data():
    return voter_repo.get_all_voters()
    # Returns automatically masked data based on user role
```

### For End Users

#### As a Voter
- Your data is always masked by default
- You cannot unmask voter data (only admins can)
- In dropdowns and lists, you'll see "XXXXXX (ID: XXXXXX)"

#### As an Admin
- Your data is masked by default for privacy
- You can toggle "🔓 Unmask Voter Data" in the sidebar when needed
- Unmasked data only appears after toggling the checkbox
- All audit logs still record the true voter IDs for security

## Security Considerations

1. **Masking is Display-Level**: Masking only affects UI display. Database records remain unchanged.
2. **Admin Audit Trail**: All admin actions that access unmasked data are logged with their email and timestamp.
3. **Session-Scoped**: The unmask toggle is per-session and resets when the admin logs out.
4. **Role-Based Enforcement**: Only users with `role == 'admin'` can unmask data.

## Configuration

### Customize Sensitive Fields

To add custom sensitive fields:

```python
# In utils/data_masking.py, update SENSITIVE_FIELDS:
SENSITIVE_FIELDS = {
    'voter_id',
    'name',
    'email',
    # ... add custom fields
    'custom_pii_field',
}
```

### Customize Masking Value

Change the mask character(s):

```python
# In utils/data_masking.py:
MASK_VALUE = "***REDACTED***"  # Instead of "XXXXXX"
```

## Testing

Run the masking tests:

```bash
cd secure_voting_app-main
python tests/test_data_masking.py
```

Expected output:
```
============================================================
Running Data Masking Unit Tests
============================================================

✓ test_mask_value passed
✓ test_mask_dict (masked) passed
✓ test_mask_dict (unmasked) passed
✓ test_mask_list (masked) passed
✓ test_mask_list (unmasked) passed
✓ test_get_display_name (masked) passed
✓ test_get_display_name (unmasked) passed
✓ test_is_masked passed
✓ test_can_unmask passed
✓ test_public_and_sensitive_fields passed

============================================================
✅ All tests passed!
============================================================
```

## Pages with Masking Integration

### ✅ Already Integrated
- **Register Voter**: Voter list displays masked data by default
- **Request Token**: 
  - **For Admins**: Voter dropdown shows masked names (can unmask with sidebar toggle)
  - **For Voters**: Shows ONLY their own voter info with toggle to unmask own details
- **Cast Vote**: Voter selection dropdown shows masked identities

### Manual Toggle Available
- **Admin Sidebar**: "🔓 Unmask Voter Data" checkbox controls all masked displays site-wide
- **Voter Sidebar**: "🔓 View My Details" checkbox allows voters to view their own unmasked information

## Future Enhancements

1. **Granular Permissions**: Allow selective unmasking of specific voter fields
2. **Audit Logging**: Log all unmasking actions with admin email and timestamp
3. **Expiring Unmask**: Auto-mask data after a timeout period
4. **Field-Level Masking**: Different masking rules for different fields
5. **Encryption at Rest**: Encrypted storage of sensitive fields in database
6. **GDPR Compliance**: Automatic data retention and deletion policies

## Examples

### Example 1: Displaying Masked Voters

```python
# Page: Register Voter
voters = voter_repo.get_all_voters()
should_unmask = st.session_state.get('unmask_voter_data', False) and is_admin()
masked_voters = mask_list(voters, unmask=should_unmask)
st.dataframe(masked_voters)

# Output when masked:
# voter_id | name    | has_token | has_voted
# XXXXXX   | XXXXXX  | true      | false
# XXXXXX   | XXXXXX  | true      | true

# Output when unmasked:
# voter_id | name      | has_token | has_voted
# V001     | John Doe  | true      | false
# V002     | Jane Smith| true      | true
```

### Example 2: Admin Workflow

1. Admin logs in
2. Navigates to "Register Voter" page
3. By default, sees masked list: "XXXXXX (ID: XXXXXX)"
4. Toggles "🔓 Unmask Voter Data" checkbox
5. Now sees full names and IDs: "John Doe (ID: V001)"
6. Logs out
7. New admin session starts with data masked by default

### Example 3: Voter Workflow (Request Token Page)

1. Voter logs in with their voter ID
2. Navigates to "Request Token" page
3. Sees ONLY their own information (not a dropdown with all voters)
4. By default, sees masked: "Your Voter ID: XXXXXX" and "Name: XXXXXX"
5. Toggles "🔓 View My Details" checkbox in sidebar
6. Now sees: "Your Voter ID: V001" and "Name: John Doe"
7. Clicks "Request Token" to issue themselves a voting token
8. Logs out
9. New voter session starts with own data masked by default

## References

- **Utility Module**: `secure_voting_app-main/utils/data_masking.py`
- **Integration Points**: `secure_voting_app-main/streamlit_app.py` (render functions)
- **Tests**: `secure_voting_app-main/tests/test_data_masking.py`
- **Role Management**: `secure_voting_app-main/utils/roles.py`
