import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import streamlit as st
from utils.session_manager import check_session_timeout, update_last_activity, SESSION_TIMEOUT
from utils.logger import add_log

# Mock Streamlit session state with attribute-style access
class MockSessionState(dict):
    def __setattr__(self, name, value):
        self[name] = value
        
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None

# Mock Streamlit module
class MockStreamlit:
    def __init__(self):
        self.session_state = MockSessionState()
        self.warning_messages = []
        self.errors = []
        self.markdown_content = []
        self.containers = []
        
    def warning(self, message):
        self.warning_messages.append(message)
        
    def error(self, message):
        self.errors.append(message)
        
    def rerun(self):
        pass
        
    def markdown(self, content, unsafe_allow_html=False):
        self.markdown_content.append({
            'content': content,
            'unsafe_allow_html': unsafe_allow_html
        })
    
    def empty(self):
        container = MockContainer()
        self.containers.append(container)
        return container
    
    def container(self):
        container = MockContainer()
        self.containers.append(container)
        return container
        
    def button(self, label, key=None):
        return False

# Mock Container for Streamlit components
class MockContainer:
    def __init__(self):
        self.components = []
        self.errors = []
        self.warnings = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def empty(self):
        return self
        
    def container(self):
        return self
        
    def error(self, message):
        self.errors.append(message)
        
    def warning(self, message):
        self.warnings.append(message)
        
    def button(self, label, key=None):
        return False

# Mock Streamlit session state
class MockSessionState(dict):
    def __setattr__(self, key, value):
        self[key] = value
        
    def __getattr__(self, key):
        if key not in self:
            self[key] = None
        return self[key]

class TestSessionTimeout(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.mock_st = MockStreamlit()
        self.patcher = patch('utils.session_manager.st', self.mock_st)
        self.patcher.start()

    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()
    
    def test_update_last_activity(self):
        """Test updating last activity timestamp"""
        update_last_activity()
        self.assertIn('last_activity', self.mock_st.session_state)
        self.assertIsInstance(self.mock_st.session_state.last_activity, datetime)

    def test_check_session_timeout_new_session(self):
        """Test session timeout check for new session"""
        check_session_timeout()
        self.assertIn('last_activity', self.mock_st.session_state)
        self.assertEqual(len(self.mock_st.warning_messages), 0)

    def test_check_session_timeout_active_session(self):
        """Test session timeout check for active session"""
        self.mock_st.session_state.last_activity = datetime.now()
        self.mock_st.session_state.user_email = "test@example.com"
        
        check_session_timeout()
        self.assertEqual(len(self.mock_st.warning_messages), 0)

    @patch('utils.session_manager.add_log')
    def test_check_session_timeout_expired_session(self, mock_add_log):
        """Test session timeout check for expired session"""
        expired_time = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        self.mock_st.session_state.last_activity = expired_time
        self.mock_st.session_state.user_email = "test@example.com"
        
        check_session_timeout()
        
        # Verify warning was shown
        self.assertTrue(any("expired" in msg.lower() for msg in self.mock_st.warning_messages))
        
        # Verify log was added
        mock_add_log.assert_called_with("Session timeout for test@example.com", "info")

    def test_check_session_timeout_warning(self):
        """Test session timeout warning (1 minute before timeout)"""
        warning_time = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        self.mock_st.session_state.last_activity = warning_time
        self.mock_st.session_state.user_email = "test@example.com"
        
        check_session_timeout()
        
        expected_warning = "⚠️ Your session will expire in 1 minute due to inactivity. Please take action to stay logged in."
        self.assertTrue(any(expected_warning in msg for msg in self.mock_st.warning_messages))

    def test_session_state_cleanup_on_timeout(self):
        """Test proper cleanup of session state on timeout"""
        self.mock_st.session_state.user_email = "test@example.com"
        self.mock_st.session_state.role = "user"
        self.mock_st.session_state.last_activity = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        check_session_timeout()
        
        self.assertNotIn('user_email', self.mock_st.session_state)
        self.assertNotIn('role', self.mock_st.session_state)
        self.assertIn('show_timeout_popup', self.mock_st.session_state)

    def test_multiple_warning_suppression(self):
        """Test that warning is shown only once"""
        warning_time = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        self.mock_st.session_state.last_activity = warning_time
        self.mock_st.session_state.user_email = "test@example.com"
        
        # First check should show warning
        check_session_timeout()
        initial_warning_count = len(self.mock_st.warning_messages)
        
        # Second check should not show warning again
        check_session_timeout()
        self.assertEqual(len(self.mock_st.warning_messages), initial_warning_count)

if __name__ == '__main__':
    unittest.main()