"""
Database Audit System Documentation

This document explains the comprehensive audit logging system implemented for the database.
"""

# AUDIT_SYSTEM.md

## Overview

The Secure Voting Platform Database now includes a comprehensive audit logging system that automatically records every change (INSERT, UPDATE, DELETE) to critical database tables using SQLite triggers.

## Architecture

### Audit Table Schema

The `audit_log` table stores all database changes:

```sql
CREATE TABLE audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,           -- Which table was modified
    operation TEXT NOT NULL,             -- INSERT, UPDATE, or DELETE
    record_id TEXT,                      -- ID of the affected record
    old_values TEXT,                     -- JSON object with previous values
    new_values TEXT,                     -- JSON object with new values
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user TEXT DEFAULT 'system'           -- Who made the change
)
```

### SQLite Triggers

Automatic triggers have been created for the following tables:

1. **voters table**
   - `voters_insert_audit`: Records new voter registrations
   - `voters_update_audit`: Records updates to voter status (e.g., token issued, vote cast)
   - `voters_delete_audit`: Records voter deletions

2. **encrypted_ballots table**
   - `encrypted_ballots_insert_audit`: Records encrypted vote submissions
   - `encrypted_ballots_update_audit`: Records any updates to encrypted votes
   - `encrypted_ballots_delete_audit`: Records vote deletions (if applicable)

3. **tokens table**
   - `tokens_insert_audit`: Records token generation
   - `tokens_delete_audit`: Records token invalidation

4. **ballots table**
   - `ballots_insert_audit`: Records candidate additions
   - `ballots_update_audit`: Records candidate updates
   - `ballots_delete_audit`: Records candidate deletions

5. **login_attempts table**
   - `login_attempts_insert_audit`: Records login attempt records
   - `login_attempts_update_audit`: Records lockout status changes

## Data Format

### JSON Value Storage

Old and new values are stored as JSON objects for easy parsing and analysis:

**Example INSERT operation:**
```json
{
  "new_values": "{\"voter_id\": \"voter_001\", \"name\": \"John Doe\", \"has_token\": 0, \"has_voted\": 0}"
}
```

**Example UPDATE operation:**
```json
{
  "old_values": "{\"has_token\": 0, \"has_voted\": 0}",
  "new_values": "{\"has_token\": 1, \"has_voted\": 0}"
}
```

## Usage

### Initialization

The audit system is automatically initialized when `db/init_db.py` is run. The audit table and all triggers are created automatically:

```python
from db.init_db import init_db
init_db()  # Creates audit_log table and all triggers
```

### Viewing Audit Logs

Use the `audit_log_viewer.py` script to query and analyze audit logs:

```bash
# Recent changes
python db/scripts/audit_log_viewer.py --recent 50

# Changes to specific table
python db/scripts/audit_log_viewer.py --table voters

# All INSERT operations
python db/scripts/audit_log_viewer.py --operation INSERT

# Track a specific record
python db/scripts/audit_log_viewer.py --record voters voter_001

# Changes in last 12 hours
python db/scripts/audit_log_viewer.py --hours 12

# Statistics summary
python db/scripts/audit_log_viewer.py --stats
```

### Direct SQL Queries

You can also query the audit log directly:

```sql
-- All changes to voter_001
SELECT * FROM audit_log 
WHERE table_name='voters' AND record_id='voter_001'
ORDER BY timestamp;

-- All INSERT operations
SELECT * FROM audit_log 
WHERE operation='INSERT'
ORDER BY timestamp DESC;

-- Changes in last 24 hours
SELECT * FROM audit_log 
WHERE timestamp > datetime('now', '-1 day')
ORDER BY timestamp DESC;

-- Changes by table
SELECT table_name, operation, COUNT(*) 
FROM audit_log 
GROUP BY table_name, operation;
```

## Security Considerations

1. **Immutable Records**: Audit logs should never be modified or deleted
2. **Access Control**: Consider restricting `audit_log` table access to auditors only
3. **Regular Backups**: Back up the database regularly to protect audit history
4. **Data Retention**: Define and implement data retention policies for audit logs
5. **Integrity Verification**: Periodically verify audit log integrity for compliance

## Performance Impact

- **Negligible overhead**: SQLite triggers execute efficiently in-process
- **Disk usage**: Plan for ~2-3KB per audit log entry over time
- **Query performance**: Minimal impact on main database operations
- **Index optimization**: Consider adding indexes to `audit_log` for high-volume queries

```sql
-- Optional: Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_operation ON audit_log(operation);
```

## Compliance

This audit system supports compliance requirements for:
- **Data Integrity**: Complete history of database changes
- **Accountability**: Tracking who made what changes and when
- **Non-repudiation**: Permanent record of all modifications
- **Audit Trails**: Complete audit history for regulatory compliance

## Monitoring

Use the `monitor_db_updates.py` script for real-time monitoring of database changes:

```bash
# Monitor with 60-second interval
python db/scripts/monitor_db_updates.py

# Monitor with 30-second interval
python db/scripts/monitor_db_updates.py --interval 30

# Quick status check
python db/scripts/monitor_db_updates.py --status
```

## Best Practices

1. **Regular Audits**: Review audit logs regularly for suspicious activity
2. **Data Sanitization**: Ensure sensitive data (passwords, etc.) is never logged
3. **Automated Alerts**: Set up alerts for critical operations (vote casting, token generation)
4. **Archive Strategy**: Archive old audit logs to prevent database bloat
5. **Documentation**: Keep documentation of audit procedures for compliance audits

## Troubleshooting

### Audit logs not appearing?

1. Verify the `audit_log` table exists:
   ```sql
   PRAGMA table_info(audit_log);
   ```

2. Check that triggers are created:
   ```sql
   SELECT * FROM sqlite_master WHERE type='trigger' AND name LIKE '%audit';
   ```

3. Verify data is being modified (check with monitor_db_updates.py)

### Performance degradation?

1. Check audit log size:
   ```sql
   SELECT COUNT(*) FROM audit_log;
   ```

2. Add indexes (see Performance Impact section)

3. Consider archiving old logs (create new table with year prefix)

## Future Enhancements

- [ ] Automated audit log archival
- [ ] Encryption of sensitive audit fields
- [ ] Real-time alerting for critical changes
- [ ] Audit log export to external systems
- [ ] Integration with compliance reporting tools
- [ ] Audit log compression for long-term storage
