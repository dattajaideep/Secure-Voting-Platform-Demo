import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from datetime import datetime, timedelta
from utils.session_manager import check_session_timeout, update_last_activity, SESSION_TIMEOUT


# Mock Session State class that supports both dict and attribute access
class MockSessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None
    
    def __setattr__(self, key, value):
        self[key] = value


class TestSessionUI(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.mock_session_state = MockSessionState()
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
        
        with patch('streamlit.warning'), patch('streamlit.rerun'), \
             patch('streamlit.empty'), patch('streamlit.container'), \
             patch('streamlit.error'), patch('streamlit.button', return_value=False):
            check_session_timeout()
        
        mock_markdown.assert_called()
        # Check that markdown was called with CSS containing timeout-modal
        calls_str = str(mock_markdown.call_args_list)
        self.assertIn('timeout-modal', calls_str)


    @patch('streamlit.button')
    @patch('streamlit.error')
    @patch('streamlit.empty')
    def test_timeout_modal_container_creation(self, mock_empty, mock_error, mock_button):
        """Test that timeout modal container is properly created"""
        # Setup mocks for context managers
        mock_empty_instance = MagicMock()
        mock_container_instance = MagicMock()
        mock_empty.return_value = mock_empty_instance
        mock_empty_instance.container = MagicMock(return_value=mock_container_instance)
        mock_container_instance.__enter__ = MagicMock(return_value=mock_container_instance)
        mock_container_instance.__exit__ = MagicMock(return_value=False)
        mock_button.return_value = False
        
        st.session_state['user_email'] = "user@example.com"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        with patch('streamlit.warning'), patch('streamlit.rerun'), \
             patch('streamlit.markdown'):
            check_session_timeout()
        
        mock_empty.assert_called()
        mock_empty_instance.container.assert_called()

    @patch('streamlit.button')
    @patch('streamlit.error')
    @patch('streamlit.container')
    @patch('streamlit.empty')
    @patch('streamlit.warning')
    def test_timeout_modal_content(self, mock_warning, mock_empty, mock_container, 
                                   mock_error, mock_button):
        """Test that timeout modal displays correct content"""
        # Setup mocks for context managers
        mock_empty_instance = MagicMock()
        mock_container_instance = MagicMock()
        mock_empty.return_value = mock_empty_instance
        mock_empty_instance.__enter__ = MagicMock(return_value=mock_empty_instance)
        mock_empty_instance.__exit__ = MagicMock(return_value=False)
        mock_container.return_value = mock_container_instance
        mock_container_instance.__enter__ = MagicMock(return_value=mock_container_instance)
        mock_container_instance.__exit__ = MagicMock(return_value=False)
        mock_button.return_value = False
        
        st.session_state['user_email'] = "user@example.com"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        with patch('streamlit.rerun'), patch('streamlit.markdown'):
            check_session_timeout()
        
        mock_error.assert_called_with("⚠️ Session Timeout")
        mock_warning.assert_called_with(f"Your session has expired due to {SESSION_TIMEOUT} minutes of inactivity.")

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