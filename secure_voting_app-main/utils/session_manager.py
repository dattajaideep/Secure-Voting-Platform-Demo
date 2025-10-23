import streamlit as st
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.logger import add_log

# Load environment variables
load_dotenv()

# Session timeout duration from .env (in seconds, default 30 minutes)
SESSION_TIMEOUT_SECONDS = int(os.getenv('SESSION_TIMEOUT', '1800'))
SESSION_TIMEOUT = SESSION_TIMEOUT_SECONDS // 60  # Convert to minutes for display
SESSION_SECRET = os.getenv('SESSION_SECRET', 'default_session_secret')

def update_last_activity():
    """Update the last activity timestamp in the session state"""
    st.session_state.last_activity = datetime.now()

def check_session_timeout():
    """Check if the session has timed out and clear it if necessary"""
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()
        return

    # Calculate time difference
    time_diff = datetime.now() - st.session_state.last_activity
    timeout_duration = timedelta(seconds=SESSION_TIMEOUT_SECONDS)
    warning_duration = timedelta(seconds=SESSION_TIMEOUT_SECONDS - 60)  # Warning 1 minute before timeout

    if time_diff > timeout_duration:
        # Session has expired
        user_email = st.session_state.get('user_email', 'Unknown user')
        
        # Log the timeout first
        add_log(f"Session timeout for {user_email}", "info")
        
        # Store timeout info for popup
        st.session_state.show_timeout_popup = True
        st.session_state.timeout_user = user_email
        
        # Clear session state except timeout info
        for key in list(st.session_state.keys()):
            if key not in ['show_timeout_popup', 'timeout_user']:
                del st.session_state[key]
        
        # Create a modal dialog for timeout notification
        st.markdown(
            """
            <style>
                .timeout-modal {
                    display: flex;
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background-color: white;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.5);
                    z-index: 1000;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Show modal dialog
        modal_container = st.empty()
        with modal_container.container():
            st.error("⚠️ Session Timeout")
            st.warning(f"Your session has expired due to {SESSION_TIMEOUT} minutes of inactivity.")
            if st.button("OK", key="timeout_ok"):
                modal_container.empty()
                st.rerun()
    
    elif time_diff > warning_duration and 'warning_shown' not in st.session_state:
        # Show warning 1 minute before timeout
        st.warning("⚠️ Your session will expire in 1 minute due to inactivity. Please take action to stay logged in.")
        st.session_state.warning_shown = True
    else:
        # Update last activity time
        update_last_activity()