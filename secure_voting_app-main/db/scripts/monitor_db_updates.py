"""
Database Update Monitor Script

This script provides utilities for regularly monitoring and displaying database updates.
It tracks table changes, record counts, and recent modifications.
"""

import time
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connection import get_db_connection


class DBUpdateMonitor:
    """Monitor database updates and changes."""

    def __init__(self, check_interval: int = 60):
        """
        Initialize the database monitor.

        Args:
            check_interval: Time in seconds between update checks
        """
        self.check_interval = check_interval
        self.last_counts = {}
        self.update_history = []

    def get_table_names(self) -> List[str]:
        """Get list of all tables in the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        finally:
            conn.close()

    def get_table_record_count(self, table_name: str) -> int:
        """Get the number of records in a table."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            return count
        finally:
            conn.close()

    def get_all_table_counts(self) -> Dict[str, int]:
        """Get record counts for all tables."""
        tables = self.get_table_names()
        counts = {}
        for table in tables:
            try:
                counts[table] = self.get_table_record_count(table)
            except Exception as e:
                print(f"Error counting records in {table}: {e}")
                counts[table] = -1
        return counts

    def detect_changes(self, current_counts: Dict[str, int]) -> Dict[str, Dict[str, int]]:
        """
        Detect changes in table record counts.

        Returns:
            Dictionary with table names and their count changes
        """
        changes = {}
        for table, current_count in current_counts.items():
            previous_count = self.last_counts.get(table, 0)
            if current_count != previous_count:
                changes[table] = {
                    "previous": previous_count,
                    "current": current_count,
                    "change": current_count - previous_count,
                }
        return changes

    def format_update_report(self, changes: Dict[str, Dict[str, int]]) -> str:
        """Format changes into a readable report."""
        if not changes:
            return "No database changes detected."

        report = f"\n{'='*60}\n"
        report += f"Database Update Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"{'='*60}\n"

        for table, change_info in changes.items():
            direction = "↑" if change_info["change"] > 0 else "↓"
            report += f"\n📊 {table}:\n"
            report += f"   Previous: {change_info['previous']} records\n"
            report += f"   Current:  {change_info['current']} records\n"
            report += f"   Change:   {direction} {abs(change_info['change'])} records\n"

        report += f"\n{'='*60}\n"
        return report

    def display_all_table_status(self) -> str:
        """Display current status of all tables."""
        counts = self.get_all_table_counts()
        report = f"\n{'='*60}\n"
        report += f"Database Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"{'='*60}\n"

        for table, count in sorted(counts.items()):
            status = "✓" if count >= 0 else "✗"
            report += f"{status} {table:.<40} {count:>6} records\n"

        total_records = sum(c for c in counts.values() if c >= 0)
        report += f"\n{'Total':.<40} {total_records:>6} records\n"
        report += f"{'='*60}\n"
        return report

    def monitor_continuous(self):
        """Continuously monitor database for updates."""
        print("Starting database update monitor...")
        print(f"Check interval: {self.check_interval} seconds")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                current_counts = self.get_all_table_counts()
                changes = self.detect_changes(current_counts)

                if changes:
                    print(self.format_update_report(changes))
                    self.update_history.append(
                        {
                            "timestamp": datetime.now(),
                            "changes": changes,
                        }
                    )

                self.last_counts = current_counts
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            self.print_summary()

    def print_summary(self):
        """Print a summary of all recorded updates."""
        if not self.update_history:
            print("No updates were recorded during monitoring.")
            return

        print(f"\n{'='*60}\n")
        print(f"Monitoring Summary ({len(self.update_history)} updates detected)\n")
        print(f"{'='*60}\n")

        for i, update in enumerate(self.update_history, 1):
            print(f"Update #{i} - {update['timestamp'].strftime('%H:%M:%S')}")
            for table, change in update["changes"].items():
                direction = "↑" if change["change"] > 0 else "↓"
                print(f"  {table}: {direction} {abs(change['change'])} records")
            print()

    def get_recent_updates(self, minutes: int = 10) -> List[Dict[str, Any]]:
        """Get updates from the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent = [u for u in self.update_history if u["timestamp"] > cutoff_time]
        return recent


def main():
    """Main entry point for the monitoring script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor database updates in real-time"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current database status and exit",
    )

    args = parser.parse_args()

    monitor = DBUpdateMonitor(check_interval=args.interval)

    if args.status:
        print(monitor.display_all_table_status())
    else:
        monitor.monitor_continuous()


if __name__ == "__main__":
    main()
