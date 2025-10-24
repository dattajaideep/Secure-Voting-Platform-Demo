"""
Pytest configuration file for Secure Voting Platform tests.
This file sets up the Python path to include the project root.
"""

import sys
import os
import pytest

# Add the project root to sys.path so imports work correctly
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    """
    Initialize the database schema before running any tests.
    This ensures all tables (including encrypted_ballots) exist.
    Automatically used by all tests via autouse=True.
    """
    from db.init_db import init_db

    init_db()
