import re
from typing import Optional, Dict, Any
import string

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class InputValidator:
    # Regex patterns
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'name': r'^[A-Za-z\s\'-]{2,50}$',
        'voter_id': r'^[A-Z0-9]{6,12}$',
        'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
        'token': r'^[A-Za-z0-9_-]{32,64}$',
        'candidate_name': r'^[A-Za-z\s\'-]{2,50}$',
        'otp': r'^\d{6}$',
        'date': r'^\d{4}-\d{2}-\d{2}$',
    }

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not re.match(InputValidator.PATTERNS['email'], email):
            raise ValidationError("Invalid email format")
        return True

    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate name format (letters, spaces, hyphens, apostrophes)"""
        if not re.match(InputValidator.PATTERNS['name'], name):
            raise ValidationError("Name must be 2-50 characters and contain only letters, spaces, hyphens, and apostrophes")
        return True

    @staticmethod
    def validate_voter_id(voter_id: str) -> bool:
        """Validate voter ID format (6-12 alphanumeric characters)"""
        if not re.match(InputValidator.PATTERNS['voter_id'], voter_id):
            raise ValidationError("Voter ID must be 6-12 characters and contain only uppercase letters and numbers")
        return True

    @staticmethod
    def validate_password(password: str) -> bool:
        """
        Validate password strength:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        if not re.match(InputValidator.PATTERNS['password'], password):
            raise ValidationError(
                "Password must be at least 8 characters and contain at least one uppercase letter, "
                "one lowercase letter, one number, and one special character"
            )
        return True

    @staticmethod
    def validate_token(token: str) -> bool:
        """Validate token format"""
        if not re.match(InputValidator.PATTERNS['token'], token):
            raise ValidationError("Invalid token format")
        return True

    @staticmethod
    def validate_candidate_name(name: str) -> bool:
        """Validate candidate name format"""
        if not re.match(InputValidator.PATTERNS['candidate_name'], name):
            raise ValidationError("Candidate name must be 2-50 characters and contain only letters, spaces, hyphens, and apostrophes")
        return True

    @staticmethod
    def validate_otp(otp: str) -> bool:
        """Validate OTP format (6 digits)"""
        if not re.match(InputValidator.PATTERNS['otp'], otp):
            raise ValidationError("OTP must be exactly 6 digits")
        return True

    @staticmethod
    def validate_date(date: str) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        if not re.match(InputValidator.PATTERNS['date'], date):
            raise ValidationError("Date must be in YYYY-MM-DD format")
        return True

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """
        Sanitize input by removing potentially dangerous characters
        while preserving valid input characters
        """
        # Define allowed characters (alphanumeric, basic punctuation)
        allowed_chars = string.ascii_letters + string.digits + string.punctuation + ' '
        return ''.join(c for c in input_str if c in allowed_chars)

    @staticmethod
    def validate_form_data(data: Dict[str, Any], required_fields: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate form data against required fields and their types
        
        Args:
            data: Dictionary of form data
            required_fields: Dictionary mapping field names to validation types
            
        Returns:
            Dictionary of sanitized and validated data
            
        Raises:
            ValidationError if validation fails
        """
        validated_data = {}
        
        for field, validation_type in required_fields.items():
            if field not in data or not data[field]:
                raise ValidationError(f"Missing required field: {field}")
            
            value = InputValidator.sanitize_input(str(data[field]))
            
            # Call appropriate validation method based on type
            validator_method = getattr(InputValidator, f"validate_{validation_type}", None)
            if validator_method:
                try:
                    validator_method(value)
                    validated_data[field] = value
                except ValidationError as e:
                    raise ValidationError(f"Invalid {field}: {str(e)}")
            else:
                validated_data[field] = value
                
        return validated_data