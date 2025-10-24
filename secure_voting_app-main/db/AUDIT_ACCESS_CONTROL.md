"""
Audit Log Access Control Enforcement

This document specifies how the audit_log table access is restricted to auditor role only.
"""

# AUDIT_ACCESS_CONTROL.md

## Overview

The `audit_log` table is restricted to **auditor role only** for security and compliance reasons. 
This ensures that only designated auditors can view the complete history of database changes.

## Role-Based Access Control (RBAC)

### Database Roles and Permissions

#### Admin Role
- **Audit Log Access**: Full access (SELECT, INSERT, UPDATE, DELETE)
- **Purpose**: System administration and emergency access
- **Limitation**: Should rarely access audit logs directly; changes should be audited separately

#### Voter Role
- **Audit Log Access**: NO ACCESS
- **Purpose**: Cast votes and participate in voting
- **Rationale**: Voters should not see audit logs for privacy reasons

#### Auditor Role ⭐ (PRIMARY ACCESS)
- **Audit Log Access**: SELECT ONLY (Read-only)
- **Purpose**: Complete audit trail review and compliance verification
- **Rationale**: Auditors need full visibility into all database changes without modification ability

## Access Control Implementation

### Database Permission Model

```python
DB_ROLES = {
    "admin": {
        "audit_log": ["SELECT", "INSERT", "UPDATE", "DELETE"]  # Full access
    },
    "voter": {
        # audit_log NOT INCLUDED - NO ACCESS
    },
    "auditor": {
        "audit_log": ["SELECT"]  # Read-only EXCLUSIVE ACCESS
    }
}
```

### Enforcement Methods

#### 1. Role-Based Access Control (RBAC)
The application should enforce these permissions at the application layer:

```python
# Example: Checking audit_log access
from db.access_control import check_permission

# This will return False for non-auditors
has_access = check_permission(user_role, 'audit_log', 'SELECT')
if not has_access:
    raise PermissionError("Only auditors can access audit logs")
```

#### 2. Database-Level Constraints
Implement SQLite PRAGMA restrictions or Python wrapper functions:

```python
def query_audit_log(user_role, query):
    """Query audit log with role-based access control."""
    if user_role != 'auditor' and user_role != 'admin':
        raise PermissionError(f"Role '{user_role}' cannot access audit_log")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()
```

#### 3. Audit Log Queries
Only auditors should execute these queries:

```sql
-- Restricted to auditor role
SELECT * FROM audit_log WHERE operation = 'INSERT';
SELECT * FROM audit_log WHERE table_name = 'voters';
SELECT * FROM audit_log WHERE timestamp > datetime('now', '-1 day');
```

## Access Control Scenarios

### ✅ Allowed Operations

**Auditor Role:**
```python
# View all audit logs
logs = viewer.get_all_audit_logs()

# Filter by table
logs = viewer.get_audit_logs_by_table('voters')

# Filter by operation
logs = viewer.get_audit_logs_by_operation('INSERT')

# Track specific records
logs = viewer.get_audit_logs_by_record('voters', 'voter_001')

# View statistics
stats = viewer.get_audit_statistics()
```

**Admin Role:**
```python
# Admin can also view, but should be limited for security
logs = viewer.get_all_audit_logs()
```

### ❌ Blocked Operations

**Voter Role:**
```python
# DENIED - Voter cannot access audit logs
logs = viewer.get_all_audit_logs()  # PermissionError
```

**Non-Authenticated Users:**
```python
# DENIED - Unauthenticated users cannot access audit logs
logs = viewer.get_all_audit_logs()  # PermissionError
```

## Compliance Requirements

### 1. Immutability
- Only auditors can READ audit logs
- No one except admins can MODIFY audit logs
- Changes to audit logs should themselves be logged

### 2. Non-Repudiation
- Auditors can review complete change history
- Trace all modifications back to their source
- Verify system integrity and compliance

### 3. Accountability
- Who made changes? (tracked in audit_log.user)
- When did changes occur? (tracked in audit_log.timestamp)
- What changed? (tracked in audit_log.old_values, new_values)

## Implementation Checklist

- [x] Add `audit_log` to auditor role permissions (SELECT only)
- [x] Exclude `audit_log` from voter role permissions
- [x] Include `audit_log` in admin role permissions (full access)
- [ ] Implement application-level access control checks
- [ ] Add authorization validation in audit_log_viewer.py
- [ ] Create audit logs for access violations
- [ ] Document access policies in security documentation
- [ ] Regular audit trail reviews by designated auditors
- [ ] Alert system for unauthorized access attempts

## Code Integration

### Updating Access Control Module

Add to `db/access_control.py`:

```python
AUDIT_LOG_RESTRICTED = True  # Flag indicating audit_log is restricted

def check_audit_log_access(user_role):
    """Check if user role has access to audit logs."""
    allowed_roles = ['auditor', 'admin']
    if user_role not in allowed_roles:
        raise PermissionError(
            f"Role '{user_role}' cannot access audit_log. "
            f"Only {allowed_roles} roles are permitted."
        )
    return True
```

### Updating Audit Log Viewer

Add authorization check in `db/scripts/audit_log_viewer.py`:

```python
class AuditLogViewer:
    def __init__(self, user_role='system'):
        """Initialize with role-based access control."""
        self.user_role = user_role
        self._check_access()
    
    def _check_access(self):
        """Verify user has audit_log access."""
        allowed_roles = ['auditor', 'admin']
        if self.user_role not in allowed_roles:
            raise PermissionError(
                f"Insufficient permissions: {self.user_role} cannot access audit logs"
            )
```

## Audit Logging Policies

### When to Review Audit Logs
- Daily compliance checks
- After system maintenance
- During security incidents
- Before and after voting periods
- Quarterly compliance audits

### What to Look For
- Unexpected DELETE operations
- Unusual UPDATE patterns
- Failed login attempts
- Token generation anomalies
- Data access patterns

### Retention Policy
- Keep audit logs for minimum 1 year
- Archive logs older than 6 months
- Never delete audit logs (delete operations should be logged separately)
- Encrypt archived audit logs

## Security Considerations

1. **Access Logging**: Log every access to audit logs by auditors
2. **Session Management**: Ensure auditor sessions are secure and time-limited
3. **Network Security**: Restrict audit log access to secure networks
4. **Data Protection**: Protect audit logs from tampering or deletion
5. **User Management**: Maintain strict auditor user list and access credentials

## Troubleshooting

### "Permission Denied" Error
Verify user role is set to 'auditor' or 'admin':
```python
from db.access_control import get_user_role
role = get_user_role(user_id)
print(f"Current role: {role}")
```

### Audit Logs Not Appearing
1. Check that triggers are created (see AUDIT_SYSTEM.md)
2. Verify INSERT operations are actually happening
3. Check database connection and permissions

### Unauthorized Access Attempts
Monitor for these patterns:
- Multiple failed access attempts
- Non-auditor roles attempting audit_log queries
- Unusual access times or patterns

## Future Enhancements

- [ ] Multi-factor authentication for auditor access
- [ ] IP address whitelisting for auditor access
- [ ] Time-based access restrictions (business hours only)
- [ ] Automated alerts for audit log access
- [ ] Audit log signing with digital signatures
- [ ] Integration with external audit systems
