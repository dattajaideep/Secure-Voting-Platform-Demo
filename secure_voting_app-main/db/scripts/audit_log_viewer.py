"""
Audit Log Viewer Script

This script provides utilities for viewing and analyzing database audit logs.
It allows querying changes by table, operation type, date range, and more.

IMPORTANT: Audit log access is restricted to auditor role only.
Only users with 'auditor' or 'admin' role can access these functions.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connection import get_db_connection


# ==================== ACCESS CONTROL ====================

AUDIT_LOG_ALLOWED_ROLES = ['auditor', 'admin']  # Roles with audit_log access
AUDIT_LOG_READONLY_ROLES = ['auditor']  # Roles with read-only access


def check_audit_log_access(user_role: str, operation: str = 'SELECT') -> bool:
    """
    Verify user has permission to access audit logs.
    
    Args:
        user_role: The role of the user ('auditor', 'admin', 'voter', etc.)
        operation: The operation being performed ('SELECT', 'INSERT', 'UPDATE', 'DELETE')
    
    Returns:
        True if access is granted
        
    Raises:
        PermissionError: If user does not have access
    """
    if user_role not in AUDIT_LOG_ALLOWED_ROLES:
        raise PermissionError(
            f"Access Denied: Role '{user_role}' cannot access audit logs. "
            f"Only {AUDIT_LOG_ALLOWED_ROLES} roles are permitted."
        )
    
    # Auditors can only READ (SELECT)
    if user_role == 'auditor' and operation != 'SELECT':
        raise PermissionError(
            f"Access Denied: Auditors have read-only access to audit logs. "
            f"Operation '{operation}' not permitted."
        )
    
    return True


class AuditLogViewer:
    """View and analyze database audit logs."""

    def __init__(self, user_role: str = 'auditor'):
        """
        Initialize the audit log viewer with role-based access control.
        
        Args:
            user_role: The role of the user accessing the audit logs.
                      Must be 'auditor' or 'admin' to access audit logs.
        
        Raises:
            PermissionError: If user role does not have audit log access
        """
        # Check access before allowing initialization
        check_audit_log_access(user_role, 'SELECT')
        self.user_role = user_role

    def get_all_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the most recent audit log entries."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT audit_id, table_name, operation, record_id, old_values, new_values, timestamp, user
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return logs
        finally:
            conn.close()

    def get_audit_logs_by_table(self, table_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit logs for a specific table."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT audit_id, table_name, operation, record_id, old_values, new_values, timestamp, user
                FROM audit_log
                WHERE table_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (table_name, limit)
            )
            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return logs
        finally:
            conn.close()

    def get_audit_logs_by_operation(self, operation: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit logs for a specific operation (INSERT, UPDATE, DELETE)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT audit_id, table_name, operation, record_id, old_values, new_values, timestamp, user
                FROM audit_log
                WHERE operation = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (operation, limit)
            )
            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return logs
        finally:
            conn.close()

    def get_audit_logs_by_record(self, table_name: str, record_id: str) -> List[Dict[str, Any]]:
        """Get all changes to a specific record."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT audit_id, table_name, operation, record_id, old_values, new_values, timestamp, user
                FROM audit_log
                WHERE table_name = ? AND record_id = ?
                ORDER BY timestamp ASC
                """,
                (table_name, record_id)
            )
            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return logs
        finally:
            conn.close()

    def get_audit_logs_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs within a date range."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT audit_id, table_name, operation, record_id, old_values, new_values, timestamp, user
                FROM audit_log
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (start_date.isoformat(), end_date.isoformat(), limit)
            )
            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return logs
        finally:
            conn.close()

    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about audit logs."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Total audit log entries
            cursor.execute("SELECT COUNT(*) FROM audit_log")
            total_entries = cursor.fetchone()[0]

            # Entries by operation
            cursor.execute(
                "SELECT operation, COUNT(*) FROM audit_log GROUP BY operation"
            )
            operations = {row[0]: row[1] for row in cursor.fetchall()}

            # Entries by table
            cursor.execute(
                "SELECT table_name, COUNT(*) FROM audit_log GROUP BY table_name"
            )
            tables = {row[0]: row[1] for row in cursor.fetchall()}

            # Recent activity (last 24 hours)
            cursor.execute(
                """
                SELECT COUNT(*) FROM audit_log 
                WHERE timestamp > datetime('now', '-1 day')
                """
            )
            last_24h = cursor.fetchone()[0]

            return {
                "total_entries": total_entries,
                "operations": operations,
                "tables": tables,
                "last_24h_entries": last_24h,
            }
        finally:
            conn.close()

    def format_log_entry(self, log: Dict[str, Any]) -> str:
        """Format a single audit log entry for display."""
        output = f"\n{'='*70}\n"
        output += f"Audit ID: {log['audit_id']}\n"
        output += f"Table: {log['table_name']:.<20} Operation: {log['operation']}\n"
        output += f"Record ID: {log['record_id']}\n"
        output += f"Timestamp: {log['timestamp']}\n"
        output += f"User: {log['user']}\n"

        if log['old_values']:
            try:
                old_vals = json.loads(log['old_values'])
                output += f"\nOld Values:\n"
                for key, val in old_vals.items():
                    output += f"  {key}: {val}\n"
            except json.JSONDecodeError:
                output += f"\nOld Values: {log['old_values']}\n"

        if log['new_values']:
            try:
                new_vals = json.loads(log['new_values'])
                output += f"\nNew Values:\n"
                for key, val in new_vals.items():
                    output += f"  {key}: {val}\n"
            except json.JSONDecodeError:
                output += f"\nNew Values: {log['new_values']}\n"

        output += f"{'='*70}\n"
        return output

    def display_audit_logs(self, logs: List[Dict[str, Any]]):
        """Display a list of audit logs in a formatted way."""
        if not logs:
            print("No audit logs found.")
            return

        for log in logs:
            print(self.format_log_entry(log))

    def display_statistics(self):
        """Display audit log statistics."""
        stats = self.get_audit_statistics()
        
        print(f"\n{'='*70}\n")
        print("Database Audit Log Statistics")
        print(f"{'='*70}\n")
        
        print(f"Total Audit Entries: {stats['total_entries']}")
        print(f"Entries in Last 24 Hours: {stats['last_24h_entries']}\n")
        
        print("Entries by Operation:")
        for operation, count in stats['operations'].items():
            print(f"  {operation:.<20} {count:>6} entries")
        
        print("\nEntries by Table:")
        for table, count in sorted(stats['tables'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {table:.<30} {count:>6} entries")
        
        print(f"\n{'='*70}\n")


def main():
    """Main entry point for the audit log viewer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="View and analyze database audit logs (Auditor Role Required)"
    )
    parser.add_argument(
        "--role",
        default='auditor',
        choices=['auditor', 'admin'],
        help="User role for access control (default: auditor)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show audit log statistics"
    )
    parser.add_argument(
        "--recent",
        type=int,
        default=20,
        help="Show recent audit logs (default: 20)"
    )
    parser.add_argument(
        "--table",
        help="Filter by table name"
    )
    parser.add_argument(
        "--operation",
        choices=["INSERT", "UPDATE", "DELETE"],
        help="Filter by operation type"
    )
    parser.add_argument(
        "--record",
        nargs=2,
        metavar=("TABLE", "RECORD_ID"),
        help="Show all changes to a specific record"
    )
    parser.add_argument(
        "--hours",
        type=int,
        help="Show logs from the last N hours"
    )

    args = parser.parse_args()

    try:
        viewer = AuditLogViewer(user_role=args.role)
    except PermissionError as e:
        print(f"\n❌ ACCESS DENIED\n{e}\n")
        sys.exit(1)

    if args.stats:
        viewer.display_statistics()
    elif args.record:
        table, record_id = args.record
        logs = viewer.get_audit_logs_by_record(table, record_id)
        print(f"\nAudit history for {table}.{record_id}:\n")
        viewer.display_audit_logs(logs)
    elif args.operation:
        logs = viewer.get_audit_logs_by_operation(args.operation, limit=args.recent)
        print(f"\nRecent {args.operation} operations:\n")
        viewer.display_audit_logs(logs)
    elif args.table:
        logs = viewer.get_audit_logs_by_table(args.table, limit=args.recent)
        print(f"\nRecent changes in {args.table}:\n")
        viewer.display_audit_logs(logs)
    elif args.hours:
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=args.hours)
        logs = viewer.get_audit_logs_by_date_range(start_date, end_date, limit=args.recent)
        print(f"\nAudit logs from the last {args.hours} hours:\n")
        viewer.display_audit_logs(logs)
    else:
        logs = viewer.get_all_audit_logs(limit=args.recent)
        print(f"\n✓ Accessed as '{args.role}' role\n")
        print(f"Most recent {len(logs)} audit logs:\n")
        viewer.display_audit_logs(logs)


if __name__ == "__main__":
    main()
