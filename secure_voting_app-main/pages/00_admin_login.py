# pages/00_admin_login.py
import streamlit as st
from utils.roles import admin_login, is_admin
from utils.logger import add_log

st.title("🔐 Admin Login")

# If already logged in as admin, show status
if is_admin():
    st.success(f"✅ Already logged in as Administrator")
    st.info("Navigate to admin pages using the sidebar")
else:
    st.info("⚠️ This page is for administrators only")
    
    with st.form("admin_login_form"):
        email = st.text_input("Admin Email", placeholder="admin@votingsystem.com")
        password = st.text_input("Admin Password", type="password")
        submit = st.form_submit_button("🔑 Login as Admin")
        
        if submit:
            if not email or not password:
                st.error("Please enter both email and password")
            elif admin_login(email, password):
                add_log(f"Admin login successful: {email}", "info")
                st.success("✅ Admin login successful!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials")
                add_log(f"Failed admin login attempt: {email}", "warning")