import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from datetime import datetime, timedelta
from utils.session_manager import SESSION_TIMEOUT

class TestSessionIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        # Clear session state before each test
        if hasattr(st, 'session_state'):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

    @patch('streamlit.session_state', {})
    @patch('streamlit.warning')
    def test_admin_login_page_session(self, mock_warning):
        """Test session management in admin login page"""
        from pages import admin_login
        
        # Simulate logged-in admin
        st.session_state.user_email = "admin@example.com"
        st.session_state.role = "admin"
        st.session_state.last_activity = datetime.now()
        
        # Verify session is active
        self.assertIn('last_activity', st.session_state)
        self.assertEqual(st.session_state.role, "admin")

    @patch('streamlit.session_state', {})
    @patch('streamlit.warning')
    def test_registration_page_session(self, mock_warning):
        """Test session management in registration page"""
        from pages import registration
        
        # Simulate registered user
        st.session_state.user_email = "user@example.com"
        st.session_state.role = "user"
        st.session_state.last_activity = datetime.now()
        
        # Verify session is active
        self.assertIn('last_activity', st.session_state)
        self.assertEqual(st.session_state.role, "user")

    @patch('streamlit.session_state', {})
    @patch('streamlit.warning')
    @patch('streamlit.rerun')
    def test_page_navigation_session_update(self, mock_rerun, mock_warning):
        """Test session updates during page navigation"""
        # Simulate initial login
        st.session_state.user_email = "user@example.com"
        st.session_state.role = "user"
        st.session_state.last_activity = datetime.now()
        
        # Record initial activity time
        initial_time = st.session_state.last_activity
        
        # Simulate page navigation by importing different pages
        from pages import registration
        from pages import cast_vote
        
        # Verify last_activity was updated
        self.assertGreater(st.session_state.last_activity, initial_time)

    @patch('streamlit.session_state', {})
    @patch('streamlit.warning')
    @patch('streamlit.rerun')
    def test_session_timeout_across_pages(self, mock_rerun, mock_warning):
        """Test session timeout behavior across different pages"""
        # Simulate expired session
        st.session_state.user_email = "user@example.com"
        st.session_state.role = "user"
        st.session_state.last_activity = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        # Try accessing different pages
        from pages import cast_vote
        
        # Verify session was cleared
        self.assertNotIn('user_email', st.session_state)
        self.assertNotIn('role', st.session_state)
        mock_warning.assert_called()
        mock_rerun.assert_called()

    @patch('streamlit.session_state', {})
    @patch('streamlit.warning')
    def test_warning_behavior_across_pages(self, mock_warning):
        """Test warning behavior when approaching timeout across pages"""
        # Simulate near-timeout session
        st.session_state.user_email = "user@example.com"
        st.session_state.role = "user"
        st.session_state.last_activity = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        
        # Access different pages
        from pages import registration
        from pages import cast_vote
        
        # Verify warning was shown
        mock_warning.assert_called_with(
            "⚠️ Your session will expire in 1 minute due to inactivity. Please take action to stay logged in."
        )

    @patch('streamlit.session_state', {})
    def test_admin_only_pages_session(self):
        """Test session management for admin-only pages"""
        # Simulate admin session
        st.session_state.user_email = "admin@example.com"
        st.session_state.role = "admin"
        st.session_state.last_activity = datetime.now()
        
        # Try accessing admin pages
        from pages import mixnet
        from pages import tally
        
        # Verify session remains active
        self.assertIn('last_activity', st.session_state)
        self.assertEqual(st.session_state.role, "admin")

if __name__ == '__main__':
    unittest.main()