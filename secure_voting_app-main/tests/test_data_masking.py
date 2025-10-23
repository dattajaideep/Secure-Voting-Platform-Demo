# tests/test_data_masking.py
"""
Unit tests for the data masking utility module.
Verifies that voter PII is properly masked and unmasked.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.data_masking import (
    mask_value,
    mask_dict,
    mask_list,
    get_display_name,
    is_masked,
    can_unmask,
    MASK_VALUE,
    PUBLIC_FIELDS,
    SENSITIVE_FIELDS,
)


def test_mask_value():
    """Test masking of individual values."""
    # Test that values are masked with XXXXXX
    assert mask_value("John Doe", always_mask=True) == MASK_VALUE
    assert mask_value("V001", always_mask=True) == MASK_VALUE
    assert mask_value(None) is None
    print("✓ test_mask_value passed")


def test_mask_dict():
    """Test masking of dictionaries."""
    voter = {
        "voter_id": "V001",
        "name": "John Doe",
        "has_token": True,
        "has_voted": False,
    }
    
    # Test masked output
    masked = mask_dict(voter, unmask=False)
    assert masked["voter_id"] == MASK_VALUE
    assert masked["name"] == MASK_VALUE
    assert masked["has_token"] == True  # Public field
    assert masked["has_voted"] == False  # Public field
    print("✓ test_mask_dict (masked) passed")
    
    # Test unmasked output
    unmasked = mask_dict(voter, unmask=True)
    assert unmasked["voter_id"] == "V001"
    assert unmasked["name"] == "John Doe"
    assert unmasked["has_token"] == True
    print("✓ test_mask_dict (unmasked) passed")


def test_mask_list():
    """Test masking of lists."""
    voters = [
        {"voter_id": "V001", "name": "John Doe", "has_token": True},
        {"voter_id": "V002", "name": "Jane Smith", "has_token": False},
    ]
    
    # Test masked output
    masked = mask_list(voters, unmask=False)
    assert len(masked) == 2
    assert masked[0]["voter_id"] == MASK_VALUE
    assert masked[0]["name"] == MASK_VALUE
    assert masked[0]["has_token"] == True
    assert masked[1]["voter_id"] == MASK_VALUE
    print("✓ test_mask_list (masked) passed")
    
    # Test unmasked output
    unmasked = mask_list(voters, unmask=True)
    assert unmasked[0]["voter_id"] == "V001"
    assert unmasked[1]["name"] == "Jane Smith"
    print("✓ test_mask_list (unmasked) passed")


def test_get_display_name():
    """Test display name generation."""
    voter = {"voter_id": "V001", "name": "John Doe"}
    
    # Masked
    masked_name = get_display_name(voter, unmask=False)
    assert masked_name == f"{MASK_VALUE} (ID: {MASK_VALUE})"
    print("✓ test_get_display_name (masked) passed")
    
    # Unmasked
    unmasked_name = get_display_name(voter, unmask=True)
    assert unmasked_name == "John Doe (ID: V001)"
    print("✓ test_get_display_name (unmasked) passed")


def test_is_masked():
    """Test detection of masked values."""
    assert is_masked(MASK_VALUE) == True
    assert is_masked("John Doe") == False
    assert is_masked(None) == False
    print("✓ test_is_masked passed")


def test_can_unmask():
    """Test role-based unmask permissions."""
    assert can_unmask("admin") == True
    assert can_unmask("voter") == False
    assert can_unmask("guest") == False
    print("✓ test_can_unmask passed")


def test_public_and_sensitive_fields():
    """Test field categorization."""
    # Check that public fields are not masked
    voter = {
        "id": "1",
        "voter_id": "V001",
        "name": "John",
        "has_token": True,
        "has_voted": False,
        "timestamp": "2025-10-23",
    }
    
    masked = mask_dict(voter, unmask=False)
    
    # Public fields should remain unchanged
    assert masked["id"] == "1"
    assert masked["has_token"] == True
    assert masked["has_voted"] == False
    assert masked["timestamp"] == "2025-10-23"
    
    # Sensitive fields should be masked
    assert masked["voter_id"] == MASK_VALUE
    assert masked["name"] == MASK_VALUE
    print("✓ test_public_and_sensitive_fields passed")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Running Data Masking Unit Tests")
    print("="*60 + "\n")
    
    test_mask_value()
    test_mask_dict()
    test_mask_list()
    test_get_display_name()
    test_is_masked()
    test_can_unmask()
    test_public_and_sensitive_fields()
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60 + "\n")
