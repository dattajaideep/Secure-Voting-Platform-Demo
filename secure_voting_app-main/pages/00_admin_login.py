# pages/00_admin_login.py
import streamlit as st
from utils.roles import admin_login, is_admin
from utils.logger import add_log
from utils.session_manager import check_session_timeout, update_last_activity
from utils.validation import InputValidator, ValidationError

st.title("🔐 Admin Login")

# Check for session timeout
check_session_timeout()

# If already logged in as admin, show status
if is_admin():
    update_last_activity()
    st.success(f"✅ Already logged in as Administrator")
    st.info("Navigate to admin pages using the sidebar")
else:
    st.info("⚠️ This page is for administrators only")

    with st.form("admin_login_form"):
        email = st.text_input("Admin Email", placeholder="admin@votingsystem.com")
        password = st.text_input("Admin Password", type="password")
        submit = st.form_submit_button("🔑 Login as Admin")
        
        if submit:
            try:
                # Validate and sanitize inputs
                validated_data = InputValidator.validate_form_data(
                    {"email": email, "password": password},
                    {"email": "email", "password": "password"}
                )
                
                if admin_login(validated_data["email"], validated_data["password"]):
                    add_log(f"Admin login successful: {validated_data['email']}", "info")
                    st.success("✅ Admin login successful!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Invalid admin credentials")
                    add_log(f"Failed admin login attempt: {validated_data['email']}", "warning")
            except ValidationError as e:
                st.error(f"❌ {str(e)}")
                add_log(f"Validation error in admin login: {str(e)}", "warning")