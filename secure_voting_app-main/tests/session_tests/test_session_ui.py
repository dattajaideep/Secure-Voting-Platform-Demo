import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from datetime import datetime, timedelta
from utils.session_manager import check_session_timeout, update_last_activity, SESSION_TIMEOUT

class TestSessionUI(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.mock_session_state = {}
        self.patcher = patch('streamlit.session_state', self.mock_session_state)
        self.patcher.start()

    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()

    @patch('streamlit.markdown')
    def test_timeout_popup_style_injection(self, mock_markdown):
        """Test that timeout popup styles are properly injected"""
        st.session_state['user_email'] = "user@example.com"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        with patch('streamlit.warning'), patch('streamlit.rerun'):
            check_session_timeout()
        
        mock_markdown.assert_called()
        style_call = mock_markdown.call_args_list[0]
        self.assertIn('timeout-modal', str(style_call))
        self.assertIn('position: fixed', str(style_call))

    @patch('streamlit.empty')
    @patch('streamlit.container')
    def test_timeout_modal_container_creation(self, mock_container, mock_empty):
        """Test that timeout modal container is properly created"""
        st.session_state['user_email'] = "user@example.com"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        with patch('streamlit.warning'), patch('streamlit.rerun'):
            check_session_timeout()
        
        mock_empty.assert_called()
        mock_container.assert_called()

    @patch('streamlit.error')
    @patch('streamlit.warning')
    def test_timeout_modal_content(self, mock_warning, mock_error):
        """Test that timeout modal displays correct content"""
        st.session_state['user_email'] = "user@example.com"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        with patch('streamlit.rerun'):
            check_session_timeout()
        
        mock_error.assert_called_with("⚠️ Session Timeout")
        mock_warning.assert_called_with("Your session has expired due to 5 minutes of inactivity.")

    @patch('streamlit.warning')
    def test_warning_message_content(self, mock_warning):
        """Test that warning message shows correct content"""
        st.session_state['user_email'] = "user@example.com"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        
        check_session_timeout()
        
        mock_warning.assert_called_with(
            "⚠️ Your session will expire in 1 minute due to inactivity. Please take action to stay logged in."
        )

if __name__ == '__main__':
    unittest.main()