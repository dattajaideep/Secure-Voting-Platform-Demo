import unittest
from utils.password_utils import (
    generate_salt,
    hash_password,
    verify_password,
    encode_hash_salt,
    decode_hash_salt
)

class TestPasswordUtils(unittest.TestCase):
    def test_generate_salt(self):
        """Test salt generation"""
        salt = generate_salt()
        self.assertIsNotNone(salt)
        self.assertIsInstance(salt, bytes)
        self.assertTrue(len(salt) > 0)
        
        # Generate another salt and verify it's different
        salt2 = generate_salt()
        self.assertNotEqual(salt, salt2)

    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password123"
        
        # Test with auto-generated salt
        hashed1, salt1 = hash_password(password)
        self.assertIsNotNone(hashed1)
        self.assertIsNotNone(salt1)
        self.assertIsInstance(hashed1, bytes)
        self.assertIsInstance(salt1, bytes)
        
        # Test with provided salt
        salt2 = generate_salt()
        hashed2, salt2_returned = hash_password(password, salt2)
        self.assertEqual(salt2, salt2_returned)
        
        # Verify different salts produce different hashes
        self.assertNotEqual(hashed1, hashed2)

    def test_verify_password(self):
        """Test password verification"""
        password = "test_password123"
        wrong_password = "wrong_password123"
        
        # Hash the password
        hashed, salt = hash_password(password)
        
        # Test correct password
        self.assertTrue(verify_password(password, hashed, salt))
        
        # Test wrong password
        self.assertFalse(verify_password(wrong_password, hashed, salt))

    def test_encode_decode_hash_salt(self):
        """Test encoding and decoding of hash and salt"""
        password = "test_password123"
        hashed, salt = hash_password(password)
        
        # Encode
        encoded_hash, encoded_salt = encode_hash_salt(hashed, salt)
        self.assertIsInstance(encoded_hash, str)
        self.assertIsInstance(encoded_salt, str)
        
        # Decode
        decoded_hash, decoded_salt = decode_hash_salt(encoded_hash, encoded_salt)
        self.assertEqual(hashed, decoded_hash)
        self.assertEqual(salt, decoded_salt)
        
        # Verify the decoded values still work for verification
        self.assertTrue(verify_password(password, decoded_hash, decoded_salt))

    def test_password_strength(self):
        """Test different password strengths and types"""
        passwords = [
            "short",  # Short password
            "LongPasswordWithNumbers123",  # Complex password
            "!@#$%^&*()",  # Special characters
            "    spaces    ",  # Spaces
            "🔒unicode🔑"  # Unicode characters
        ]
        
        for password in passwords:
            hashed, salt = hash_password(password)
            self.assertTrue(verify_password(password, hashed, salt))
            self.assertFalse(verify_password(password + "wrong", hashed, salt))

    def test_error_cases(self):
        """Test error cases and edge conditions"""
        # Empty password
        hashed, salt = hash_password("")
        self.assertTrue(verify_password("", hashed, salt))
        
        # None password should raise TypeError
        with self.assertRaises(TypeError):
            hash_password(None)
        
        # Invalid salt
        with self.assertRaises(ValueError):
            hash_password("password", b"invalid_salt")
            
        # Invalid encoded strings
        with self.assertRaises(Exception):
            decode_hash_salt("invalid_base64", "invalid_base64")

if __name__ == '__main__':
    unittest.main()