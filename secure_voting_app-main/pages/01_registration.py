# pages/01_registration.py
import streamlit as st
from db.repositories import VoterRepository
from utils.logger import add_log
from auth.oauth import oauth2, OAUTH_REDIRECT_URI
from utils.otp_service import generate_otp, send_otp_email
from datetime import datetime, timedelta
from utils.session_manager import check_session_timeout, update_last_activity
from utils.validation import InputValidator, ValidationError
from utils.data_masking import mask_dict, mask_list, MASK_VALUE

st.title("1️⃣ Voter Access Portal")

# Check for session timeout
check_session_timeout()

voter_repo = VoterRepository()

# Update activity timestamp if user is logged in
if 'user_email' in st.session_state:
    update_last_activity()

# --- Redirect already logged-in voters to next step ---
if 'user_email' in st.session_state and st.session_state.get('role') == 'user':
    st.info("✅ You are already logged in. Redirecting to Request Token...")
    st.switch_page("pages/02_request_token.py")

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

            voters_emails = [v[1] for v in voter_repo.get_all_voters()]
            
            if email not in voters_emails:
                # New voter - register them
                voter_repo.add_voter(email, name)
                
                # Mark as newly registered so voter can see themselves in the list
                st.session_state.newly_registered_email = email
                st.session_state.newly_registered_name = name
                
                add_log(f"Google OAuth registration: {email}", "info")
                st.success(f"✅ Welcome! You have been registered.")
                st.info("👇 Your voter information appears below. You can unmask your email before logging in.")
                st.rerun()
            else:
                # Existing voter - allow login
                st.session_state.user_email = email
                st.session_state.voter_id = email
                st.session_state.user_name = name
                st.session_state.role = "user"
                st.session_state.voted = False
                st.session_state.current_step = "request_token"
                
                add_log(f"Google OAuth login: {email}", "info")
                st.success(f"✅ Welcome back, {name}!")
                st.info("🔒 You are locked into the voting flow: Request Token → Cast Vote → Logout")
                st.switch_page("pages/02_request_token.py")
    
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
                        
                        # Mark as newly registered so voter can see themselves in the list
                        st.session_state.newly_registered_email = st.session_state.reg_email
                        st.session_state.newly_registered_name = st.session_state.reg_name
                        
                        add_log(f"OTP registration: {st.session_state.reg_email}", "info")
                        st.success(f"✅ {st.session_state.reg_name} registered successfully!")
                        st.info("� Your voter information appears below. You can unmask your email before logging in.")
                        
                        # Clear OTP from session
                        del st.session_state.reg_otp
                        del st.session_state.reg_email
                        del st.session_state.reg_name
                        del st.session_state.reg_otp_time
                        
                        # Rerun to show the voter list with the newly registered voter
                        st.rerun()
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
            
            # Check if voter is registered
            voter = voter_repo.get_voter_by_email(email)
            if voter:
                # Set session state for logged-in voter
                st.session_state.user_email = email
                st.session_state.voter_id = email
                st.session_state.user_name = voter.get("name", "Anonymous")
                st.session_state.role = "user"
                st.session_state.voted = voter.get("has_voted", False)
                
                # Determine current step in voter flow
                if st.session_state.voted:
                    st.session_state.current_step = "logout"
                elif voter.get("has_token", False):
                    st.session_state.current_step = "cast_vote"
                else:
                    st.session_state.current_step = "request_token"
                
                add_log(f"Google login: {email}", "info")
                st.success(f"✅ Welcome back, {st.session_state.user_name}!")
                st.info("🔒 You are locked into the voting flow based on your current status.")
                
                st.balloons()
                st.switch_page("pages/02_request_token.py")
            else:
                st.error("❌ Voter not registered. Please register first.")
                add_log(f"Login attempt with unregistered email: {email}", "warning")
    
    # --- Email + OTP Login ---
    elif method == "Email + OTP":
        # Initialize session state variables before widgets
        if "login_email_stored" not in st.session_state:
            st.session_state.login_email_stored = ""
            st.session_state.login_otp = None
            st.session_state.login_otp_time = None

        # Step 1: Request OTP
        login_email = st.text_input("Enter your registered email", key="login_email_input")

        # Step 1: Send OTP
        if st.button("Send Login OTP", key="send_login_otp"):
            try:
                # Validate email
                validated_data = InputValidator.validate_form_data(
                    {"email": login_email},
                    {"email": "email"}
                )
                
                # Check if email is registered
                voter = voter_repo.get_voter_by_email(validated_data["email"])
                if not voter:
                    st.error("❌ Email not registered. Please register first.")
                    add_log(f"Login attempt with unregistered email: {validated_data['email']}", "warning")
                else:
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
        if "login_otp" in st.session_state and st.session_state.login_otp:
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
                        # Login voter
                        voter = voter_repo.get_voter_by_email(st.session_state.login_email_stored)
                        
                        st.session_state.user_email = st.session_state.login_email_stored
                        st.session_state.voter_id = st.session_state.login_email_stored
                        st.session_state.user_name = voter.get("name", "Anonymous")
                        st.session_state.role = "user"
                        st.session_state.voted = voter.get("has_voted", False)
                        
                        # Determine current step in voter flow
                        if st.session_state.voted:
                            st.session_state.current_step = "logout"
                        elif voter.get("has_token", False):
                            st.session_state.current_step = "cast_vote"
                        else:
                            st.session_state.current_step = "request_token"
                        
                        add_log(f"OTP login: {st.session_state.login_email_stored}", "info")
                        st.success("✅ Login successful!")
                        st.info("🔒 You are locked into the voting flow based on your current status.")
                        
                        # Clear OTP from session
                        del st.session_state.login_otp
                        del st.session_state.login_email_stored
                        del st.session_state.login_otp_time
                        
                        st.balloons()
                        st.switch_page("pages/02_request_token.py")
                    else:
                        st.error("❌ Invalid OTP. Please try again.")
                except ValidationError as e:
                    st.error(f"❌ {str(e)}")
                    add_log(f"Validation error in OTP verification: {str(e)}", "warning")
# ============================================
# LIST REGISTERED VOTERS
# ============================================
# st.divider()
# st.subheader("Registered Voters")

# voters = voter_repo.get_all_voters()

# # Check if there's a newly registered voter
# is_newly_registered = 'newly_registered_email' in st.session_state

# if voters:
#     # For newly registered voters, show the voter list with their own data unmasked
#     if is_newly_registered:
#         st.info(f"✅ Welcome! Here's your voter profile. You can unmask your email to confirm your registration:")
        
#         # Create columns for unmask toggle
#         col1, col2 = st.columns([3, 1])
#         with col2:
#             show_unmask = st.checkbox("Unmask Email", key="unmask_own_email")
        
#         # Display all voters
#         for v in voters:
#             voter_id_display = v.get('voter_id', MASK_VALUE)
#             name_display = v.get('name', MASK_VALUE)
#             has_token = v.get('has_token', False)
#             has_voted = v.get('has_voted', False)
            
#             # If this is the newly registered voter and unmask is enabled, show their real email
#             if v.get('voter_id') == st.session_state.newly_registered_email and show_unmask:
#                 voter_id_display = st.session_state.newly_registered_email
#             elif v.get('voter_id') == st.session_state.newly_registered_email:
#                 voter_id_display = MASK_VALUE
            
#             # Highlight the newly registered voter
#             if v.get('voter_id') == st.session_state.newly_registered_email:
#                 st.write(f"👤 **{voter_id_display}** - {name_display} | Token: {has_token} | Voted: {has_voted}")
#             else:
#                 st.write(f"📧 {voter_id_display} - {name_display} | Token: {has_token} | Voted: {has_voted}")

#         # Show login button to proceed with voting flow
#         # if st.button("✅ Proceed to Login & Request Token", key="proceed_after_registration"):
#         #     st.session_state.user_email = st.session_state.newly_registered_email
#         #     st.session_state.voter_id = st.session_state.newly_registered_email
#         #     st.session_state.user_name = st.session_state.newly_registered_name
#         #     st.session_state.role = "user"
#         #     st.session_state.voted = False
#         #     st.session_state.current_step = "request_token"
            
#         #     # Clear registration flags
#         #     del st.session_state.newly_registered_email
#         #     del st.session_state.newly_registered_name
            
#         #     add_log(f"Voter confirmed registration and proceeding: {st.session_state.user_email}", "info")
#         #     st.success("✅ Registration confirmed! Proceeding to voting flow...")
#         #     st.switch_page("pages/02_request_token.py")
    
#     # For admins or other viewers, show all voters
#     elif 'is_admin' in st.session_state and st.session_state.is_admin:
#         col1, col2 = st.columns([3, 1])
#         with col2:
#             unmask_all = st.checkbox("Unmask All", key="unmask_all_voters")
        
#         for v in voters:
#             voter_id_display = v.get('voter_id', MASK_VALUE) if not unmask_all else v.get('voter_id', MASK_VALUE)
#             name_display = v.get('name', MASK_VALUE) if not unmask_all else v.get('name', MASK_VALUE)
#             has_token = v.get('has_token', False)
#             has_voted = v.get('has_voted', False)
            
#             if unmask_all:
#                 voter_id_display = v.get('voter_id', MASK_VALUE)
#                 name_display = v.get('name', MASK_VALUE)
#             else:
#                 voter_id_display = MASK_VALUE
#                 name_display = MASK_VALUE
            
#             st.write(
#                 f"📧 {voter_id_display} - {name_display} | Token: {has_token} | Voted: {has_voted}"
#             )
#     else:
#         st.info("📋 Register above or log in with your credentials to proceed.")
# else:
#     st.info("No voters registered yet.")