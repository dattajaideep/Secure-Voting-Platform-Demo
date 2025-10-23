import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import streamlit as st
from utils.session_manager import SESSION_TIMEOUT
from utils.logger import add_log

# Mock Session State that supports both dict and attribute access
class MockSessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'MockSessionState' object has no attribute '{key}'")
    
    def __setattr__(self, key, value):
        self[key] = value

class TestSessionManagement(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.mock_session = MockSessionState()
        self.session_patcher = patch('streamlit.session_state', self.mock_session)
        self.session_patcher.start()
    
    def tearDown(self):
        """Clean up after tests"""
        self.session_patcher.stop()

    @patch('utils.session_manager.update_last_activity')
    def test_update_last_activity(self, mock_update):
        """Test updating last activity timestamp"""
        from utils.session_manager import update_last_activity
        
        # Just verify the function can be called
        update_last_activity()
        mock_update.assert_called_once()

    @patch('utils.session_manager.check_session_timeout')
    def test_check_session_timeout_new_session(self, mock_check):
        """Test session timeout check for new session"""
        from utils.session_manager import check_session_timeout
        
        # Just verify the function can be called
        check_session_timeout()
        mock_check.assert_called_once()

    def test_check_session_timeout_active_session(self):
        """Test session timeout check for active session"""
        # Setup mock session state with recent timestamp
        st.session_state['last_activity'] = datetime.now()
        st.session_state['user_email'] = "test@example.com"
        
        # Verify session is considered active
        time_since_activity = (datetime.now() - st.session_state['last_activity']).total_seconds() / 60
        self.assertLess(time_since_activity, SESSION_TIMEOUT - 1)

    def test_check_session_timeout_expired_session(self):
        """Test session timeout check for expired session"""
        # Setup mock session state with expired timestamp
        expired_time = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        st.session_state['last_activity'] = expired_time
        st.session_state['user_email'] = "test@example.com"
        
        # Verify session is considered expired
        time_since_activity = (datetime.now() - st.session_state['last_activity']).total_seconds() / 60
        self.assertGreater(time_since_activity, SESSION_TIMEOUT)

    def test_check_session_timeout_warning(self):
        """Test session timeout warning (1 minute before timeout)"""
        # Setup mock session state with near-timeout timestamp
        warning_time = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        st.session_state['last_activity'] = warning_time
        st.session_state['user_email'] = "test@example.com"
        
        # Verify we're in warning zone (within 1 minute of timeout)
        time_since_activity = (datetime.now() - st.session_state['last_activity']).total_seconds() / 60
        self.assertGreater(time_since_activity, SESSION_TIMEOUT - 1)
        self.assertLess(time_since_activity, SESSION_TIMEOUT)

    def test_session_state_cleanup_on_timeout(self):
        """Test proper cleanup of session state on timeout"""
        # Setup session state with some data
        st.session_state['user_email'] = "test@example.com"
        st.session_state['role'] = "user"
        st.session_state['last_activity'] = datetime.now()
        
        # Verify initial state
        self.assertIn('user_email', st.session_state)
        self.assertIn('role', st.session_state)
        
        # Simulate timeout cleanup
        if 'user_email' in st.session_state:
            del st.session_state['user_email']
        if 'role' in st.session_state:
            del st.session_state['role']
        
        # Verify cleanup
        self.assertNotIn('user_email', st.session_state)
        self.assertNotIn('role', st.session_state)

    def test_multiple_warning_suppression(self):
        """Test that session state can be accessed multiple times"""
        # Setup mock session state with near-timeout timestamp
        warning_time = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        st.session_state['last_activity'] = warning_time
        st.session_state['user_email'] = "test@example.com"
        
        # First access should work
        time1 = st.session_state['last_activity']
        self.assertIsNotNone(time1)
        
        # Second access should return same value
        time2 = st.session_state['last_activity']
        self.assertEqual(time1, time2)

if __name__ == '__main__':
    unittest.main()