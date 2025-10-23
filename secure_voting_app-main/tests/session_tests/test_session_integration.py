import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import streamlit as st
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


class TestSessionIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        # Setup mock session state that supports both dict and attribute access
        self.mock_session_state = MockSessionState()
        self.patcher = patch('streamlit.session_state', self.mock_session_state)
        self.patcher.start()

    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()

    @patch('streamlit.warning')
    def test_session_timeout_in_admin_page(self, mock_warning):
        """Test session timeout behavior in admin page"""
        # Setup mock session
        st.session_state['user_email'] = "admin@example.com"
        st.session_state['role'] = "admin"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        with patch('streamlit.rerun'):
            check_session_timeout()
            
        # Verify session was cleared
        self.assertNotIn('user_email', st.session_state)
        self.assertNotIn('role', st.session_state)
        mock_warning.assert_called()

    @patch('streamlit.warning')
    def test_session_warning_in_voting_page(self, mock_warning):
        """Test session warning in voting page"""
        # Setup mock session
        st.session_state['user_email'] = "voter@example.com"
        st.session_state['role'] = "voter"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT - 0.5)
        
        check_session_timeout()
        
        # Verify warning was shown
        mock_warning.assert_called_with(
            "⚠️ Your session will expire in 1 minute due to inactivity. Please take action to stay logged in."
        )

    def test_session_activity_update_on_page_interaction(self):
        """Test session activity update on page interaction"""
        initial_time = datetime.now() - timedelta(minutes=1)
        st.session_state['last_activity'] = initial_time
        
        update_last_activity()
        
        self.assertGreater(st.session_state['last_activity'], initial_time)

    @patch('streamlit.button')
    @patch('streamlit.error')
    @patch('streamlit.container')
    @patch('streamlit.empty')
    @patch('streamlit.markdown')
    @patch('streamlit.warning')
    @patch('streamlit.rerun')
    def test_session_timeout_modal_display(self, mock_rerun, mock_warning, mock_markdown, 
                                           mock_empty, mock_container, mock_error, mock_button):
        """Test session timeout modal display"""
        # Setup mocks for context managers
        mock_empty_instance = MagicMock()
        mock_container_instance = MagicMock()
        mock_empty.return_value = mock_empty_instance
        mock_empty_instance.__enter__ = MagicMock(return_value=mock_empty_instance)
        mock_empty_instance.__exit__ = MagicMock(return_value=False)
        mock_container.return_value = mock_container_instance
        mock_container_instance.__enter__ = MagicMock(return_value=mock_container_instance)
        mock_container_instance.__exit__ = MagicMock(return_value=False)
        
        # Mock the button to return False (not clicked)
        mock_button.return_value = False
        
        st.session_state['user_email'] = "user@example.com"
        st.session_state['last_activity'] = datetime.now() - timedelta(minutes=SESSION_TIMEOUT + 1)
        
        check_session_timeout()
        
        self.assertTrue(st.session_state.get('show_timeout_popup'))
        mock_warning.assert_called()
        # Modal is displayed but rerun is not called until button is clicked
        mock_markdown.assert_called()
        mock_error.assert_called()

    def test_session_persistence_during_active_use(self):
        """Test session persistence during active use"""
        st.session_state['user_email'] = "user@example.com"
        st.session_state['role'] = "user"
        st.session_state['last_activity'] = datetime.now()
        
        original_activity = st.session_state['last_activity']
        
        # Simulate page interactions
        with patch('streamlit.warning'):
            check_session_timeout()
            update_last_activity()
        
        self.assertGreater(st.session_state['last_activity'], original_activity)
        self.assertEqual(st.session_state['user_email'], "user@example.com")
        self.assertEqual(st.session_state['role'], "user")

if __name__ == '__main__':
    unittest.main()