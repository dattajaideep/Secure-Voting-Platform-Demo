# Logs page
# pages/06_logs.py
import streamlit as st
from db.repositories import LogRepository


st.title("6️⃣ System Logs")
log_repo = LogRepository()
logs = log_repo.get_all_logs()
if logs:
    for log in logs:
        st.write(f"[{log['created_at']}] {log['log_type'].upper()} - {log['message']}")
else:
    st.info("No logs yet.")
