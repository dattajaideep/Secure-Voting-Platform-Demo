# Logs page
# pages/06_logs.py
import streamlit as st
from db.repositories import LogRepository
from utils.roles import require_admin
from utils.session_manager import check_session_timeout, update_last_activity

# Check for session timeout before requiring admin
check_session_timeout()

# Require admin access
require_admin()

st.title("6️⃣ System Logs")

# Update activity timestamp if user is logged in
if 'user_email' in st.session_state:
    update_last_activity()
log_repo = LogRepository()
logs = log_repo.get_all_logs()
if logs:
    for log in logs:
        st.write(f"[{log['created_at']}] {log['log_type'].upper()} - {log['message']}")
else:
    st.info("No logs yet.")
