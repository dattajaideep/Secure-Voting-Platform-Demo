"""
Pytest configuration file for Secure Voting Platform tests.
This file sets up the Python path to include the project root.
"""

import sys
import os

# Add the project root to sys.path so imports work correctly
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
