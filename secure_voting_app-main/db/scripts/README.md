# Database Scripts

This folder contains utility scripts for monitoring and managing database updates.

## Features

### Automatic Audit Logging
The database now includes automatic audit logging via SQLite triggers. Every INSERT, UPDATE, and DELETE operation on the following tables is automatically recorded:
- `voters`
- `encrypted_ballots`
- `tokens`
- `ballots`
- `login_attempts`

All audit records are stored in the `audit_log` table with the following information:
- `table_name`: Which table was modified
- `operation`: Type of change (INSERT, UPDATE, DELETE)
- `record_id`: ID of the affected record
- `old_values`: Previous values (JSON format, for UPDATE/DELETE)
- `new_values`: New values (JSON format, for INSERT/UPDATE)
- `timestamp`: When the change occurred
- `user`: Who made the change (defaults to 'system')

## Scripts

### `monitor_db_updates.py`

Real-time database update monitor that tracks changes to table record counts.

**Features:**
- Real-time monitoring of all database tables
- Automatic change detection (inserts/deletes)
- Formatted update reports
- Update history tracking
- Quick status checks

**Usage:**

```bash
# Continuous monitoring (checks every 60 seconds)
python monitor_db_updates.py

# Continuous monitoring with custom interval (30 seconds)
python monitor_db_updates.py --interval 30

# Show current database status and exit
python monitor_db_updates.py --status
```

**Output Example:**
```
============================================================
Database Update Report - 2025-10-24 14:30:45
============================================================

📊 users:
   Previous: 42 records
   Current:  43 records
   Change:   ↑ 1 records

📊 votes:
   Previous: 156 records
   Current:  157 records
   Change:   ↑ 1 records

============================================================
```

### `audit_log_viewer.py`

View and analyze database audit logs with detailed change history.

**Features:**
- View all database changes with complete history
- Filter by table name
- Filter by operation type (INSERT, UPDATE, DELETE)
- Track specific record changes over time
- View changes within a date range
- Display audit statistics
- JSON-formatted old/new values for easy analysis

**Usage:**

```bash
# Show recent 20 audit logs
python audit_log_viewer.py

# Show last 50 audit logs
python audit_log_viewer.py --recent 50

# Show audit statistics
python audit_log_viewer.py --stats

# Show recent changes to voters table
python audit_log_viewer.py --table voters

# Show all INSERT operations
python audit_log_viewer.py --operation INSERT

# Track all changes to a specific record
python audit_log_viewer.py --record voters voter_123

# Show changes from the last 12 hours
python audit_log_viewer.py --hours 12
```

**Output Example:**
```
======================================================================
Audit ID: 42
Table: voters              Operation: UPDATE
Record ID: voter_001
Timestamp: 2025-10-24 14:30:45
User: system

Old Values:
  has_token: 0
  has_voted: 0

New Values:
  has_token: 1
  has_voted: 0

======================================================================
```

**Statistics Output:**
```
======================================================================
Database Audit Log Statistics
======================================================================

Total Audit Entries: 1,250
Entries in Last 24 Hours: 156

Entries by Operation:
  INSERT:............................ 520 entries
  UPDATE:............................ 680 entries
  DELETE:............................ 50 entries

Entries by Table:
  encrypted_ballots................. 320 entries
  voters............................. 450 entries
  tokens............................. 250 entries
  ballots............................ 180 entries
  login_attempts..................... 50 entries

======================================================================
```

## Requirements

- Python 3.7+
- SQLite database connection configured via `db.connection.get_db_connection()`

## Integration

To integrate these scripts into your application:

1. Run the monitor in a separate process
2. Use the `DBUpdateMonitor` class directly in Python code
3. Check database status regularly during system maintenance

## Future Scripts

- `backup_db.py` - Automated database backups
- `cleanup_old_records.py` - Archive and clean old data
- `export_statistics.py` - Export database statistics
- `integrity_check.py` - Database integrity verification
