# Request voting token page
# pages/02_request_token.py
import streamlit as st
from services.voter_client import VoterClient
from services.voting_authority import VotingAuthority
from db.repositories import VoterRepository
from utils.logger import add_log
from db.connection import get_conn
from utils.session_manager import check_session_timeout, update_last_activity
from utils.data_masking import MASK_VALUE

st.title("2️⃣ Request Blind Token")

# Check for session timeout
check_session_timeout()

# ===== LOGIN VALIDATION =====
if 'user_email' not in st.session_state or st.session_state.get('role') != 'user':
    st.error("🚫 Access Denied: You must be logged in as a voter to access this page.")
    st.info("Please go back to the **Voter Access Portal** and log in first.")
    if st.button("Go to Login"):
        st.switch_page("pages/01_registration.py")
    st.stop()

# ===== VOTER FLOW ENFORCEMENT =====
if st.session_state.get('current_step') != 'request_token':
    if st.session_state.get('voted'):
        st.warning("✅ You have already voted. Logging you out...")
        st.session_state.clear()
        st.switch_page("pages/01_registration.py")
    elif st.session_state.get('current_step') == 'cast_vote':
        st.info("➡️ You already have a token. Proceeding to Cast Vote...")
        st.switch_page("pages/03_cast_vote.py")
    else:
        st.info("⏳ Please complete your voter registration first.")
        st.switch_page("pages/01_registration.py")

voter_repo = VoterRepository()
authority = VotingAuthority(get_conn())

# Update activity timestamp
update_last_activity()

st.markdown("""
🔐 **Request your anonymous voting token here.**

Your token will allow you to cast your vote while maintaining complete ballot privacy.
""")

# ===== EMAIL MASKING: Show only logged-in voter's email =====
current_voter_email = st.session_state.get('user_email')
current_voter_name = st.session_state.get('user_name')

# Initialize session state for voter self-unmasking
if 'unmask_own_email' not in st.session_state:
    st.session_state.unmask_own_email = False

# Display voter's own email with masking toggle
st.session_state.unmask_own_email = st.checkbox(
    "🔓 View My Email Before Requesting Token",
    value=st.session_state.unmask_own_email,
    help="Show your unmasked email address"
)

col1, col2 = st.columns([3, 1])
with col1:
    if st.session_state.unmask_own_email:
        st.info(f"📧 **Your Email:** {current_voter_email}")
        st.write(f"**Name:** {current_voter_name}")
    else:
        st.info(f"📧 **Your Email:** {MASK_VALUE}")
        st.write(f"**Name:** {MASK_VALUE}")

if st.button("Request Blind Token", type="primary", key="request_token_btn"):
    try:
        voter = voter_repo.get_voter_by_email(current_voter_email)
        
        if voter and voter.get("has_token"):
            st.warning("⚠️ You already have a voting token. Proceeding to Cast Vote...")
            st.session_state.current_step = "cast_vote"
            st.switch_page("pages/03_cast_vote.py")
        else:
            client = VoterClient(authority)
            token_hash, signature = client.create_blind_token(current_voter_email)
            voter_repo.update_token_status(current_voter_email, True)
            
            st.session_state.current_step = "cast_vote"
            st.session_state.token_hash = token_hash
            st.session_state.token_signature = signature
            
            add_log(f"Blind token issued: {current_voter_email}", "success")
            st.success(f"✅ **Token Issued Successfully!**\n\nYou can now proceed to cast your vote.")
            
            st.balloons()
            st.switch_page("pages/03_cast_vote.py")
    except Exception as e:
        st.error(f"❌ Error requesting token: {str(e)}")
        add_log(f"Error issuing token to {current_voter_email}: {str(e)}", "error")

# ===== Safety reminder =====
st.divider()
st.warning("⚠️ **Important:** After requesting your token, you will proceed directly to the voting page. You will only be able to vote once.")
