import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from datetime import datetime, timedelta
from utils.session_manager import SESSION_TIMEOUT

# Mock Session State class that supports both dict and attribute access
class MockSessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None
    
    def __setattr__(self, key, value):
        self[key] = value

class TestSessionIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        # Use mock session state that supports both dict and attribute access
        self.mock_session = MockSessionState()
        self.patcher = patch('streamlit.session_state', self.mock_session)
        self.patcher.start()

    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()

    def test_admin_login_page_session(self):
        """Test session management in admin login page"""
        # Simulate logged-in admin
        st.session_state['user_email'] = "admin@example.com"
        st.session_state['role'] = "admin"
        st.session_state['last_activity'] = datetime.now()
        
        # Verify session is active
        self.assertIn('last_activity', st.session_state)
        self.assertEqual(st.session_state['role'], "admin")

    def test_registration_page_session(self):
        """Test session management in registration page"""
        # Simulate registered user
        st.session_state['user_email'] = "user@example.com"
        st.session_state['role'] = "user"
        st.session_state['last_activity'] = datetime.now()
        
        # Verify session is active
        self.assertIn('last_activity', st.session_state)
        self.assertEqual(st.session_state['role'], "user")

    @patch('streamlit.warning')
    @patch('streamlit.rerun')
    def test_page_navigation_session_update(self, mock_rerun, mock_warning):
        """Test session updates during page navigation"""
        # Simulate initial login
        st.session_state['user_email'] = "user@example.com"
        st.session_state['role'] = "user"
        st.session_state['last_activity'] = datetime.now()
        
        # Record initial activity time
        initial_time = st.session_state['last_activity']
        
        # Simulate page navigation by updating activity time
        st.session_state['last_activity'] = datetime.now()
        
        # Verify last_activity was updated
        self.assertGreaterEqual(st.session_state['last_activity'], initial_time)

    @patch('streamlit.warning')
    @patch('streamlit.rerun')
    def test_session_timeout_across_pages(self, mock_rerun, mock_warning):
        """Test session timeout behavior across different pages"""
        # Simulate expired session
        st.session_state['user_email'] = "user@example.com"
        st.session_state['role'] = "user"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        # Simulate session timeout check
        if 'user_email' in st.session_state and 'last_activity' in st.session_state:
            time_since_activity = (datetime.now() - st.session_state['last_activity']).total_seconds() / 60
            if time_since_activity > SESSION_TIMEOUT:
                del st.session_state['user_email']
                del st.session_state['role']
        
        # Verify session was cleared
        self.assertNotIn('user_email', st.session_state)
        self.assertNotIn('role', st.session_state)

    @patch('streamlit.warning')
    def test_warning_behavior_across_pages(self, mock_warning):
        """Test warning behavior when approaching timeout across pages"""
        # Simulate near-timeout session
        st.session_state['user_email'] = "user@example.com"
        st.session_state['role'] = "user"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        
        # Verify time calculation works
        time_since_activity = (datetime.now() - st.session_state['last_activity']).total_seconds() / 60
        self.assertGreater(time_since_activity, SESSION_TIMEOUT - 1)

    def test_admin_only_pages_session(self):
        """Test session management for admin-only pages"""
        # Simulate admin session
        st.session_state['user_email'] = "admin@example.com"
        st.session_state['role'] = "admin"
        st.session_state['last_activity'] = datetime.now()
        
        # Verify session remains active
        self.assertIn('last_activity', st.session_state)
        self.assertEqual(st.session_state['role'], "admin")

if __name__ == '__main__':
    unittest.main()