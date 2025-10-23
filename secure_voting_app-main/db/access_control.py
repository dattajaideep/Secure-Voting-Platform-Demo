# db/access_control.py
"""
Database Access Control Module

Enforces role-based access control (RBAC) for SQLite operations.
Provides query validation and permission checking for database operations.
"""

import sqlite3
import streamlit as st
from typing import List, Optional, Dict, Any
from utils.roles import DatabaseRole, get_current_db_role, can_perform_operation, can_access_table
from utils.logger import add_log


class DatabaseAccessControl:
    """
    Enforces database access control policies based on user roles.
    Acts as a middleware between application and SQLite database.
    """
    
    def __init__(self, db_connection):
        """
        Initialize access control layer
        
        Args:
            db_connection: SQLite database connection
        """
        self.db = db_connection
        self.db_role = None
    
    def set_user_role(self, db_role: str):
        """Set the current user's database role"""
        if db_role in [DatabaseRole.VOTER_READ, DatabaseRole.ADMIN_FULL]:
            self.db_role = db_role
        else:
            raise ValueError(f"Invalid database role: {db_role}")
    
    def _extract_table_from_query(self, query: str) -> str:
        """
        Extract primary table name from SQL query
        
        Args:
            query: SQL query string
            
        Returns:
            Table name (best effort extraction)
        """
        query_upper = query.upper().strip()
        
        # Common patterns: INSERT INTO, UPDATE, DELETE FROM, SELECT ... FROM
        keywords = ["INSERT INTO", "UPDATE", "DELETE FROM", "FROM"]
        
        for keyword in keywords:
            if keyword in query_upper:
                parts = query_upper.split(keyword)[1].strip().split()
                return parts[0].lower()
        
        return None
    
    def _extract_operation(self, query: str) -> str:
        """
        Extract SQL operation type from query
        
        Args:
            query: SQL query string
            
        Returns:
            Operation type (SELECT, INSERT, UPDATE, DELETE, etc.)
        """
        query_upper = query.upper().strip()
        operations = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]
        
        for op in operations:
            if query_upper.startswith(op):
                return op
        
        return None
    
    def _validate_query_access(self, query: str) -> bool:
        """
        Validate if current user's role has permission for the query
        
        Args:
            query: SQL query string
            
        Returns:
            True if access is allowed, False otherwise
            
        Raises:
            PermissionError: If access is denied
        """
        if not self.db_role:
            raise PermissionError("No database role set for current user")
        
        operation = self._extract_operation(query)
        table_name = self._extract_table_from_query(query)
        
        if not operation:
            raise ValueError(f"Could not identify operation in query: {query}")
        
        # Check operation permission
        if not can_perform_operation(self.db_role, operation):
            raise PermissionError(
                f"Role '{self.db_role}' cannot perform '{operation}' operation. "
                f"Allowed operations: {DatabaseRole.ALLOWED_OPERATIONS[self.db_role]}"
            )
        
        # Check table access
        if table_name and not can_access_table(self.db_role, table_name):
            raise PermissionError(
                f"Role '{self.db_role}' cannot access table '{table_name}'. "
                f"Allowed tables: {list(DatabaseRole.ALLOWED_TABLES[self.db_role].keys())}"
            )
        
        return True
    
    def execute_with_access_control(self, query: str, params: tuple = ()) -> Any:
        """
        Execute a query with access control validation
        
        Args:
            query: SQL query string
            params: Query parameters (tuple)
            
        Returns:
            Query result (cursor or affected rows count)
            
        Raises:
            PermissionError: If user doesn't have access
        """
        try:
            # Validate access permissions
            self._validate_query_access(query)
            
            # Execute query
            cursor = self.db.cursor()
            cursor.execute(query, params)
            self.db.commit()
            
            # Log successful query execution for audit trail
            operation = self._extract_operation(query)
            table = self._extract_table_from_query(query)
            add_log(
                f"DB Access: {self.db_role} executed {operation} on {table}",
                "info"
            )
            
            return cursor
            
        except PermissionError as e:
            # Log access denial for security audit
            add_log(f"DB Access Denied: {str(e)}", "warning")
            raise
        except Exception as e:
            add_log(f"DB Execution Error: {str(e)}", "error")
            raise
    
    def select_with_role_filter(self, table: str, filters: Dict = None) -> List[Dict]:
        """
        Perform SELECT query with automatic role-based filtering
        For VOTER_READ role, only select allowed columns
        
        Args:
            table: Table name
            filters: WHERE clause conditions as dictionary
            
        Returns:
            List of result rows as dictionaries
        """
        if not can_access_table(self.db_role, table):
            raise PermissionError(f"Role '{self.db_role}' cannot access table '{table}'")
        
        # For VOTER_READ, restrict columns
        if self.db_role == DatabaseRole.VOTER_READ:
            allowed_cols = DatabaseRole.VOTER_ACCESSIBLE_TABLES.get(table, [])
            if allowed_cols:
                columns = ", ".join(allowed_cols)
            else:
                raise PermissionError(f"No column access defined for {table} in VOTER_READ role")
        else:
            columns = "*"
        
        # Build WHERE clause
        where_clause = ""
        params = []
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = " WHERE " + " AND ".join(conditions)
        
        query = f"SELECT {columns} FROM {table}{where_clause}"
        
        try:
            cursor = self.execute_with_access_control(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            add_log(f"SELECT error on {table}: {str(e)}", "error")
            raise
    
    def insert_with_access_control(self, table: str, data: Dict) -> bool:
        """
        Perform INSERT with access control
        
        Args:
            table: Table name
            data: Dictionary of column names to values
            
        Returns:
            True if insert successful
        """
        if self.db_role != DatabaseRole.ADMIN_FULL:
            raise PermissionError(f"Role '{self.db_role}' cannot INSERT into '{table}'")
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            self.execute_with_access_control(query, tuple(data.values()))
            add_log(f"Inserted row into {table} by {self.db_role}", "info")
            return True
        except Exception as e:
            add_log(f"INSERT error on {table}: {str(e)}", "error")
            raise
    
    def update_with_access_control(self, table: str, data: Dict, where: Dict) -> int:
        """
        Perform UPDATE with access control
        
        Args:
            table: Table name
            data: Dictionary of columns to update
            where: WHERE clause conditions
            
        Returns:
            Number of affected rows
        """
        if self.db_role != DatabaseRole.ADMIN_FULL:
            raise PermissionError(f"Role '{self.db_role}' cannot UPDATE '{table}'")
        
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = ?" for k in where.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        params = tuple(list(data.values()) + list(where.values()))
        
        try:
            cursor = self.execute_with_access_control(query, params)
            add_log(f"Updated rows in {table} by {self.db_role}", "info")
            return cursor.rowcount
        except Exception as e:
            add_log(f"UPDATE error on {table}: {str(e)}", "error")
            raise
    
    def delete_with_access_control(self, table: str, where: Dict) -> int:
        """
        Perform DELETE with access control
        
        Args:
            table: Table name
            where: WHERE clause conditions
            
        Returns:
            Number of deleted rows
        """
        if self.db_role != DatabaseRole.ADMIN_FULL:
            raise PermissionError(f"Role '{self.db_role}' cannot DELETE from '{table}'")
        
        where_clause = " AND ".join([f"{k} = ?" for k in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        try:
            cursor = self.execute_with_access_control(query, tuple(where.values()))
            add_log(f"Deleted rows from {table} by {self.db_role}", "info")
            return cursor.rowcount
        except Exception as e:
            add_log(f"DELETE error on {table}: {str(e)}", "error")
            raise
