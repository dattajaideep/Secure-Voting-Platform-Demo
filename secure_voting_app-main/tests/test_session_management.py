import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import streamlit as st
from utils.session_manager import check_session_timeout, update_last_activity, SESSION_TIMEOUT
from utils.logger import add_log

class TestSessionManagement(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        # Clear session state before each test
        if hasattr(st, 'session_state'):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
    
    @patch('streamlit.session_state', {})
    def test_update_last_activity(self):
        """Test updating last activity timestamp"""
        update_last_activity()
        self.assertIn('last_activity', st.session_state)
        self.assertIsInstance(st.session_state.last_activity, datetime)

    @patch('streamlit.session_state', {})
    @patch('streamlit.warning')
    @patch('streamlit.rerun')
    def test_check_session_timeout_new_session(self, mock_rerun, mock_warning):
        """Test session timeout check for new session"""
        check_session_timeout()
        self.assertIn('last_activity', st.session_state)
        mock_warning.assert_not_called()
        mock_rerun.assert_not_called()

    @patch('streamlit.session_state')
    @patch('streamlit.warning')
    @patch('streamlit.rerun')
    def test_check_session_timeout_active_session(self, mock_rerun, mock_warning, mock_session_state):
        """Test session timeout check for active session"""
        # Setup mock session state
        mock_session_state.last_activity = datetime.now()
        mock_session_state.user_email = "test@example.com"
        
        check_session_timeout()
        mock_warning.assert_not_called()
        mock_rerun.assert_not_called()

    @patch('streamlit.session_state')
    @patch('streamlit.warning')
    @patch('streamlit.rerun')
    @patch('utils.logger.add_log')
    def test_check_session_timeout_expired_session(self, mock_add_log, mock_rerun, mock_warning, mock_session_state):
        """Test session timeout check for expired session"""
        # Setup mock session state with expired timestamp
        expired_time = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        mock_session_state.last_activity = expired_time
        mock_session_state.user_email = "test@example.com"
        
        check_session_timeout()
        mock_warning.assert_called()
        mock_add_log.assert_called_with("Session timeout for test@example.com", "info")
        mock_rerun.assert_called_once()

    @patch('streamlit.session_state')
    @patch('streamlit.warning')
    def test_check_session_timeout_warning(self, mock_warning, mock_session_state):
        """Test session timeout warning (1 minute before timeout)"""
        # Setup mock session state with near-timeout timestamp
        warning_time = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        mock_session_state.last_activity = warning_time
        mock_session_state.user_email = "test@example.com"
        
        check_session_timeout()
        mock_warning.assert_called_with("⚠️ Your session will expire in 1 minute due to inactivity. Please take action to stay logged in.")

    @patch('streamlit.session_state', {})
    def test_session_state_cleanup_on_timeout(self):
        """Test proper cleanup of session state on timeout"""
        # Setup session state with some data
        st.session_state.user_email = "test@example.com"
        st.session_state.role = "user"
        st.session_state.last_activity = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        check_session_timeout()
        
        # Verify only show_timeout_popup remains in session state
        self.assertNotIn('user_email', st.session_state)
        self.assertNotIn('role', st.session_state)
        self.assertIn('show_timeout_popup', st.session_state)

    @patch('streamlit.session_state')
    @patch('streamlit.warning')
    @patch('streamlit.rerun')
    def test_multiple_warning_suppression(self, mock_rerun, mock_warning, mock_session_state):
        """Test that warning is shown only once"""
        # Setup mock session state with near-timeout timestamp
        warning_time = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        mock_session_state.last_activity = warning_time
        mock_session_state.user_email = "test@example.com"
        
        # First check should show warning
        check_session_timeout()
        mock_warning.assert_called_once()
        
        # Second check should not show warning again
        mock_warning.reset_mock()
        check_session_timeout()
        mock_warning.assert_not_called()

if __name__ == '__main__':
    unittest.main()