# pages/00_admin_login.py
import streamlit as st
import os
from dotenv import load_dotenv
from utils.roles import admin_login, is_admin
from utils.logger import add_log
from utils.session_manager import check_session_timeout, update_last_activity
from utils.validation import InputValidator, ValidationError
from utils.auth_security import check_login_attempts, record_login_attempt
from utils.password_validator import validate_password, mask_password

# Load environment variables
load_dotenv()

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

    # Display configured admin email
    configured_email = os.getenv("ADMIN_EMAIL", "admin@votingsystem.com")
    st.info(f"💡 Login with admin email: {configured_email}")
    
    with st.form("admin_login_form"):
        email = st.text_input("Admin Email", 
                             value=configured_email,
                             placeholder=configured_email)
        password = st.text_input("Admin Password", type="password")
        submit = st.form_submit_button("🔑 Login as Admin")
        
        if submit:
            try:
                # Validate and sanitize inputs
                validated_data = InputValidator.validate_form_data(
                    {"email": email, "password": password},
                    {"email": "email", "password": "password"}
                )
                
                # Check if account is locked out
                can_attempt, lockout_msg = check_login_attempts(validated_data["email"])
                if not can_attempt:
                    st.error(f"🔒 {lockout_msg}")
                    add_log(f"Locked out admin login attempt: {validated_data['email']}", "warning")
                    st.stop()
                
                # Validate email matches configured admin email
                if validated_data["email"] != configured_email:
                    is_locked, msg = record_login_attempt(validated_data["email"], False)
                    st.error("❌ Invalid admin email address")
                    add_log(f"Failed admin login attempt with wrong email: {validated_data['email']}", "warning")
                    st.stop()
                
                # Attempt login with configured credentials
                success = admin_login(validated_data["email"], validated_data["password"])
                is_locked, msg = record_login_attempt(validated_data["email"], success)
                
                if success:
                    add_log(f"Admin login successful: {validated_data['email']}", "info")
                    st.success("✅ Admin login successful!")
                    st.balloons()
                    st.rerun()
                else:
                    if is_locked:
                        st.error(f"🔒 {msg}")
                    else:
                        st.error("❌ Invalid admin password")
                    add_log(f"Failed admin login attempt with wrong password: {mask_password(validated_data['password'])}", "warning")
            except ValidationError as e:
                st.error(f"❌ {str(e)}")
                add_log(f"Validation error in admin login: {str(e)}", "warning")