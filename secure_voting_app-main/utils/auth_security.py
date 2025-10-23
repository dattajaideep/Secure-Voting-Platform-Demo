import os
import pytz
from datetime import datetime, timedelta
from typing import Dict, Tuple
from dotenv import load_dotenv
from db.repositories.login_attempt_repository import LoginAttemptRepository

# Load environment variables
load_dotenv()

# Authentication security settings from environment variables
MAX_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "3"))
LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "30"))
LOCKOUT_DURATION = LOCKOUT_MINUTES * 60  # Convert minutes to seconds

# Initialize login attempts table
LoginAttemptRepository.create_table()

def check_login_attempts(email: str) -> Tuple[bool, str]:
    """
    Check if a user can attempt to login or is locked out
    
    Args:
        email: User's email address
        
    Returns:
        Tuple[bool, str]: (can_attempt, message)
        - can_attempt: True if user can attempt login, False if locked out
        - message: Explanation message if locked out, empty string otherwise
    """
    current_time = datetime.now(pytz.UTC)
    
    # Get current attempts from database
    attempt_info = LoginAttemptRepository.get_attempts(email)
    if not attempt_info:
        return True, ""
        
    attempts, last_attempt, lockout_until = attempt_info
    
    # Ensure all datetime objects are timezone-aware
    current_time = current_time.replace(microsecond=0)  # Remove microseconds for consistent comparison
    
    # Check if currently locked out
    if lockout_until:
        # Calculate remaining time
        remaining_seconds = (lockout_until - current_time).total_seconds()
        
        if remaining_seconds <= 0:
            # Lockout has expired
            LoginAttemptRepository.reset_attempts(email)
            return True, ""
            
        # Ensure remaining time doesn't exceed LOCKOUT_MINUTES
        remaining_minutes = min(int(remaining_seconds / 60), LOCKOUT_MINUTES)
        
        # If somehow the remaining time is too high, reset it
        if remaining_minutes > LOCKOUT_MINUTES:
            LoginAttemptRepository.reset_attempts(email)
            return True, ""
            
        return False, f"Account is locked. Please try again in {remaining_minutes} minutes."
    
    # Reset attempts if last attempt was more than lockout duration ago
    if (current_time - last_attempt).total_seconds() > LOCKOUT_DURATION:
        LoginAttemptRepository.reset_attempts(email)
        return True, ""
        
    return True, ""

def record_login_attempt(email: str, success: bool) -> Tuple[bool, str]:
    """
    Record a login attempt and handle lockout if necessary
    
    Args:
        email: User's email address
        success: Whether the login attempt was successful
        
    Returns:
        Tuple[bool, str]: (is_locked_out, message)
        - is_locked_out: True if account is now locked out, False otherwise
        - message: Lockout message if applicable, empty string otherwise
    """
    if success:
        # Reset attempts on successful login
        LoginAttemptRepository.reset_attempts(email)
        return False, ""
    
    # Get current attempts
    attempt_info = LoginAttemptRepository.get_attempts(email)
    attempts = (attempt_info[0] if attempt_info else 0) + 1
    
    if attempts >= MAX_ATTEMPTS:
        # Lock out the account
        LoginAttemptRepository.increment_attempts(email, LOCKOUT_DURATION)
        return True, f"Too many failed attempts. Account locked for {LOCKOUT_MINUTES} minutes."
    
    # Update attempts
    LoginAttemptRepository.increment_attempts(email)
    remaining_attempts = MAX_ATTEMPTS - attempts
    return False, f"Login failed. {remaining_attempts} attempts remaining before lockout."