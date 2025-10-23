# pages/01_registration.py
import streamlit as st
from db.repositories import VoterRepository
from utils.logger import add_log
from auth.oauth import oauth2, OAUTH_REDIRECT_URI
from utils.otp_service import generate_otp, send_otp_email
from datetime import datetime, timedelta
from utils.session_manager import check_session_timeout, update_last_activity
from utils.validation import InputValidator, ValidationError

st.title("1️⃣ Voter Access Portal")

# Check for session timeout
check_session_timeout()

voter_repo = VoterRepository()

# Update activity timestamp if user is logged in
if 'user_email' in st.session_state:
    update_last_activity()

# --- Choose action: Register or Login ---
action = st.radio(
    "What would you like to do?",
    ["Register New Account", "Login to Existing Account"]
)

# ============================================
# REGISTRATION FLOW
# ============================================
if action == "Register New Account":
    st.subheader("Register New Voter")
    
    # Choose registration method
    method = st.radio(
        "Select Registration Method",
        ["Google OAuth", "Email + OTP"],
        key="register_method"
    )
    
    # --- Google OAuth Registration ---
    if method == "Google OAuth":
        result = oauth2.authorize_button(
            "Register with Google",
            OAUTH_REDIRECT_URI,
            "openid email profile"
        )

        if result:
            user_info = oauth2.get_user_info(result["access_token"])
            email = user_info.get("email")
            name = user_info.get("name", "Anonymous")

            voter_repo.add_voter(email, name)
            
            # Set session state for regular users
            st.session_state.user_email = email
            st.session_state.user_name = name
            st.session_state.role = "user"
            
            add_log(f"Google registration: {email}", "info")
            st.success(f"✅ {name} registered successfully via Google!")
    
    # --- Email + OTP Registration ---
    elif method == "Email + OTP":
        # Initialize session state variables before widgets
        if "reg_email" not in st.session_state:
            st.session_state.reg_email = ""
        if "reg_name" not in st.session_state:
            st.session_state.reg_name = ""
        
        email = st.text_input("Enter your email address", key="reg_email")
        name = st.text_input("Enter your full name", key="reg_name")

        # Step 1: Send OTP
        if st.button("Send OTP", key="send_reg_otp"):
            try:
                # Validate and sanitize inputs
                validated_data = InputValidator.validate_form_data(
                    {"email": email, "name": name},
                    {"email": "email", "name": "name"}
                )
                
                otp = generate_otp()
                if send_otp_email(validated_data["email"], otp):
                    st.session_state.reg_otp = otp
                    st.session_state.reg_otp_time = datetime.now()
                    st.success(f"✅ OTP sent to {validated_data['email']}")
                    add_log(f"OTP sent to {validated_data['email']}", "info")
                else:
                    st.error("Failed to send OTP. Check email configuration.")
            except ValidationError as e:
                st.error(f"❌ {str(e)}")
                add_log(f"Validation error in registration: {str(e)}", "warning")

        # Step 2: Verify OTP
        if "reg_otp" in st.session_state:
            otp_input = st.text_input("Enter the 6-digit OTP", type="password", max_chars=6, key="reg_otp_input")

            if st.button("Verify OTP and Register", key="verify_reg_otp"):
                try:
                    # Validate OTP format
                    InputValidator.validate_otp(otp_input)
                    
                    time_diff = datetime.now() - st.session_state.reg_otp_time
                    if time_diff > timedelta(minutes=5):
                        st.error("OTP expired. Please request a new one.")
                        del st.session_state.reg_otp
                    elif int(otp_input) == st.session_state.reg_otp:
                        # Register the voter
                        voter_repo.add_voter(st.session_state.reg_email, st.session_state.reg_name)
                        
                        # Set session state
                        st.session_state.user_email = st.session_state.reg_email
                        st.session_state.user_name = st.session_state.reg_name
                        st.session_state.role = "user"
                        
                        add_log(f"OTP registration: {st.session_state.reg_email}", "info")
                        st.success(f"✅ {st.session_state.reg_name} registered successfully!")
                        
                        # Clear OTP from session
                        del st.session_state.reg_otp
                        del st.session_state.reg_email
                        del st.session_state.reg_name
                        del st.session_state.reg_otp_time
                    else:
                        st.error("❌ Invalid OTP. Please try again.")
                except ValidationError as e:
                    st.error(f"❌ {str(e)}")
                    add_log(f"Validation error in OTP verification: {str(e)}", "warning")

# ============================================
# LOGIN FLOW
# ============================================
elif action == "Login to Existing Account":
    st.subheader("Login")
    
    # Choose login method
    method = st.radio(
        "Select Login Method",
        ["Google OAuth", "Email + OTP"],
        key="login_method"
    )
    
    # --- Google OAuth Login ---
    if method == "Google OAuth":
        result = oauth2.authorize_button(
            "Login with Google",
            OAUTH_REDIRECT_URI,
            "openid email profile"
        )

        if result:
            user_info = oauth2.get_user_info(result["access_token"])
            email = user_info.get("email")
            name = user_info.get("name", "Anonymous")
            
            # Set session state
            st.session_state.user_email = email
            st.session_state.user_name = name
            st.session_state.role = "user"
            
            add_log(f"{email} logged in via Google", "info")
            st.success(f"✅ Welcome back, {name}!")
    
    # --- Email + OTP Login ---
    elif method == "Email + OTP":
        email = st.text_input("Enter your registered email", key="login_email_input")

        # Step 1: Send OTP
        if st.button("Send Login OTP", key="send_login_otp"):
            try:
                # Validate email
                validated_data = InputValidator.validate_form_data(
                    {"email": email},
                    {"email": "email"}
                )
                
                otp = generate_otp()
                if send_otp_email(validated_data["email"], otp):
                    st.session_state.login_otp = otp
                    st.session_state.login_email_stored = validated_data["email"]
                    st.session_state.login_otp_time = datetime.now()
                    st.success(f"✅ OTP sent to {validated_data['email']}")
                    add_log(f"OTP login requested: {validated_data['email']}", "info")
                else:
                    st.error("Failed to send OTP. Check email configuration.")
            except ValidationError as e:
                st.error(f"❌ {str(e)}")
                add_log(f"Validation error in login: {str(e)}", "warning")

        # Step 2: Verify OTP
        if "login_otp" in st.session_state:
            otp_input = st.text_input("Enter the 6-digit OTP", type="password", max_chars=6, key="login_otp_input")

            if st.button("Verify Login", key="verify_login_otp"):
                try:
                    # Validate OTP format
                    InputValidator.validate_otp(otp_input)
                    
                    time_diff = datetime.now() - st.session_state.login_otp_time
                    if time_diff > timedelta(minutes=5):
                        st.error("OTP expired. Please request a new one.")
                        del st.session_state.login_otp
                    elif int(otp_input) == st.session_state.login_otp:
                        # Set session state
                        st.session_state.user_email = st.session_state.login_email_stored
                        st.session_state.user_name = "Voter"
                        st.session_state.role = "user"
                        
                        add_log(f"{st.session_state.login_email_stored} logged in via OTP", "info")
                        st.success("✅ Login successful!")
                        
                        # Clear OTP from session
                        del st.session_state.login_otp
                        del st.session_state.login_email_stored
                        del st.session_state.login_otp_time
                    else:
                        st.error("❌ Invalid OTP. Please try again.")
                except ValidationError as e:
                    st.error(f"❌ {str(e)}")
                    add_log(f"Validation error in OTP verification: {str(e)}", "warning")
# ============================================
# LIST REGISTERED VOTERS
# ============================================
st.divider()
st.subheader("Registered Voters")
voters = voter_repo.get_all_voters()
if voters:
    for v in voters:
        st.write(
            f"📧 {v['voter_id']} - {v['name']} | Token: {v['has_token']} | Voted: {v['has_voted']}"
        )
else:
    st.info("No voters registered yet.")