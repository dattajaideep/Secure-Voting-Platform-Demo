# utils/roles.py
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# ==================== DATABASE ACCESS ROLES ====================
class DatabaseRole:
    """SQLite access control roles for the voting platform"""
    
    # Role identifiers
    VOTER_READ = "voter_read"
    ADMIN_FULL = "admin_full"
    
    # Allowed SQL operations per role
    ALLOWED_OPERATIONS = {
        VOTER_READ: ["SELECT"],
        ADMIN_FULL: ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"]
    }
    
    # Allowed tables per role
    ALLOWED_TABLES = {
        VOTER_READ: {
            "voters": ["SELECT"],
            "ballots": ["SELECT"],
            "tally_results": ["SELECT"],
            "logs": ["SELECT"]
        },
        ADMIN_FULL: {
            "voters": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "ballots": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "tokens": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "tally_results": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "logs": ["SELECT", "INSERT", "UPDATE", "DELETE"],
            "mixnet": ["SELECT", "INSERT", "UPDATE", "DELETE"]
        }
    }
    
    # Read-only tables for VOTER_READ
    VOTER_ACCESSIBLE_TABLES = {
        "voters": ["voter_id", "name", "has_token", "has_voted"],
        "ballots": ["ballot_id", "candidate", "encrypted_vote"],
        "tally_results": ["candidate", "vote_count", "percentage"]
    }


def get_db_role_for_user(user_role: str) -> str:
    """
    Map application user role to database access role
    
    Args:
        user_role: Application user role (e.g., "admin", "voter")
    
    Returns:
        Database role identifier
    """
    role_mapping = {
        "admin": DatabaseRole.ADMIN_FULL,
        "voter": DatabaseRole.VOTER_READ,
        "guest": DatabaseRole.VOTER_READ
    }
    return role_mapping.get(user_role, DatabaseRole.VOTER_READ)


def can_perform_operation(db_role: str, operation: str) -> bool:
    """
    Check if a database role can perform a specific SQL operation
    
    Args:
        db_role: Database role identifier
        operation: SQL operation (SELECT, INSERT, UPDATE, DELETE, etc.)
    
    Returns:
        True if operation is allowed, False otherwise
    """
    allowed_ops = DatabaseRole.ALLOWED_OPERATIONS.get(db_role, [])
    return operation.upper() in allowed_ops


def can_access_table(db_role: str, table_name: str) -> bool:
    """
    Check if a database role can access a specific table
    
    Args:
        db_role: Database role identifier
        table_name: Table name to access
    
    Returns:
        True if table access is allowed, False otherwise
    """
    allowed_tables = DatabaseRole.ALLOWED_TABLES.get(db_role, {})
    return table_name.lower() in allowed_tables


def get_allowed_operations_for_table(db_role: str, table_name: str) -> list:
    """
    Get list of allowed operations for a specific table and role
    
    Args:
        db_role: Database role identifier
        table_name: Table name
    
    Returns:
        List of allowed SQL operations
    """
    allowed_tables = DatabaseRole.ALLOWED_TABLES.get(db_role, {})
    return allowed_tables.get(table_name.lower(), [])


# ==================== APPLICATION AUTHENTICATION ROLES ====================

def is_admin():
    """Check if current user is admin"""
    return st.session_state.get("role") == "admin"


def is_logged_in():
    """Check if user is logged in (any role)"""
    return "user_email" in st.session_state


def get_user_role():
    """Get current user role"""
    return st.session_state.get("role", "guest")


def admin_login(email, password):
    """Verify admin credentials and set admin session"""
    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        st.session_state.user_email = email
        st.session_state.user_name = "Administrator"
        st.session_state.role = "admin"
        st.session_state.db_role = DatabaseRole.ADMIN_FULL
        return True
    return False


def voter_login(voter_id: str):
    """Set voter session with appropriate database role"""
    st.session_state.voter_id = voter_id
    st.session_state.user_name = f"Voter {voter_id}"
    st.session_state.role = "voter"
    st.session_state.db_role = DatabaseRole.VOTER_READ


def require_admin():
    """Guard function to restrict page access to admin only"""
    if not is_admin():
        st.error("🚫 Access Denied: Admin privileges required")
        st.info("Please log in with admin credentials via the Admin Login page")
        st.stop()


def get_current_db_role():
    """Get the current user's database role"""
    user_role = get_user_role()
    return get_db_role_for_user(user_role)