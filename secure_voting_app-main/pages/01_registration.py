# pages/01_registration.py
import streamlit as st
from db.repositories import VoterRepository
from utils.logger import add_log
from auth.oauth import oauth2, OAUTH_REDIRECT_URI
from utils.otp_service import generate_otp, send_otp_email
from datetime import datetime, timedelta

st.title("1️⃣ Voter Registration")

voter_repo = VoterRepository()

# --- Choose registration method ---
choice = st.radio(
    "Select Registration Method",
    ["Google OAuth", "Email + OTP"]
)

# ============ GOOGLE OAUTH REGISTRATION ============
if choice == "Google OAuth":
    st.subheader("Sign in with Google to register")

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
        add_log(f"Google registration: {email}", "info")
        st.success(f"✅ {name} registered successfully via Google!")

# ============ EMAIL + OTP REGISTRATION ============
elif choice == "Email + OTP":
    st.subheader("Register with Email + OTP")

    email = st.text_input("Enter your email address")
    name = st.text_input("Enter your full name")

    # Step 1: Send OTP
    if st.button("Send OTP"):
        if not email or not name:
            st.error("Please enter both email and name")
        else:
            otp = generate_otp()
            if send_otp_email(email, otp):
                st.session_state.otp = otp
                st.session_state.otp_email = email
                st.session_state.otp_name = name
                st.session_state.otp_time = datetime.now()
                st.success(f"✅ OTP sent to {email}")
                add_log(f"OTP sent to {email}", "info")
            else:
                st.error("Failed to send OTP. Check email configuration.")

    # Step 2: Verify OTP
    if "otp" in st.session_state:
        otp_input = st.text_input("Enter the 6-digit OTP", type="password", max_chars=6)

        if st.button("Verify OTP and Register"):
            # Check if OTP expired (5 minutes)
            time_diff = datetime.now() - st.session_state.otp_time
            if time_diff > timedelta(minutes=5):
                st.error("OTP expired. Please request a new one.")
                del st.session_state.otp
            elif int(otp_input) == st.session_state.otp:
                # Register the voter
                voter_repo.add_voter(st.session_state.otp_email, st.session_state.otp_name)
                add_log(f"OTP registration: {st.session_state.otp_email}", "info")
                st.success(f"✅ {st.session_state.otp_name} registered successfully!")
                
                # Clear OTP from session
                del st.session_state.otp
                del st.session_state.otp_email
                del st.session_state.otp_name
                del st.session_state.otp_time
            else:
                st.error("❌ Invalid OTP. Please try again.")

# ============ LIST REGISTERED VOTERS ============
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
