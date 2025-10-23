# Cast vote page
# pages/03_cast_vote.py
import streamlit as st
from services.voter_client import VoterClient
from services.voting_authority import VotingAuthority
from db.repositories import VoterRepository, TokenRepository, BallotRepository
from utils.logger import add_log
from db.connection import get_conn
from utils.session_manager import check_session_timeout, update_last_activity
from utils.data_masking import MASK_VALUE

st.title("3️⃣ Cast Vote")

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
if st.session_state.get('current_step') != 'cast_vote':
    st.warning("⚠️ You must request a token first before casting your vote.")
    st.switch_page("pages/02_request_token.py")

voter_repo = VoterRepository()
token_repo = TokenRepository()
ballot_repo = BallotRepository()
authority = VotingAuthority(get_conn())

# Update activity timestamp
update_last_activity()

current_voter_email = st.session_state.get('user_email')
current_voter_name = st.session_state.get('user_name')

st.info("💡 **Important:** You can only vote once. Please choose your candidate carefully.")

# ===== EMAIL MASKING: Show only logged-in voter's email =====
if 'unmask_own_email_vote' not in st.session_state:
    st.session_state.unmask_own_email_vote = False

# Display voter's own email with masking toggle
st.session_state.unmask_own_email_vote = st.checkbox(
    "🔓 View My Email Before Casting Vote",
    value=st.session_state.unmask_own_email_vote,
    help="Show your unmasked email address"
)

col1, col2 = st.columns([3, 1])
with col1:
    if st.session_state.unmask_own_email_vote:
        st.info(f"� **Your Email:** {current_voter_email}")
        st.write(f"**Name:** {current_voter_name}")
    else:
        st.info(f"📧 **Your Email:** {MASK_VALUE}")
        st.write(f"**Name:** {MASK_VALUE}")

# Candidate selection
candidates = ["Candidate A", "Candidate B", "Candidate C"]
selected_candidate = st.selectbox("Select Your Candidate", [""] + candidates, key="candidate_select")

if st.button("Cast Vote", key="cast_vote_btn", type="primary"):
    if not selected_candidate:
        st.error("❌ Please select a candidate")
    else:
        try:
            # Final check: Verify voter hasn't already voted (race condition prevention)
            voter = voter_repo.get_voter_by_email(current_voter_email)
            
            if voter and voter.get("has_voted"):
                st.error("❌ You have already cast your vote. Only one vote per voter is permitted.")
                add_log(f"Attempted multi-vote by {current_voter_email}", "warning")
                st.session_state.current_step = "logout"
                st.switch_page("pages/01_registration.py")
            else:
                client = VoterClient(authority)
                token = token_repo.get_token_by_voter(current_voter_email)
                
                if token is None:
                    st.error("❌ No token found for this voter")
                else:
                    # Convert signature from hex string to int if needed
                    signature = token.get("signature")
                    if isinstance(signature, str):
                        signature = int(signature, 16)
                    
                    # Cast vote
                    result = client.cast_vote(token.get("token_hash"), signature, selected_candidate)
                    
                    # Update voter as voted
                    voter_repo.update_vote_status(current_voter_email, True)
                    
                    # Update session state
                    st.session_state.voted = True
                    st.session_state.current_step = "logout"
                    
                    add_log(f"Vote cast by {current_voter_email}: {selected_candidate}", "success")
                    st.success(f"✅ **Vote Cast Successfully!**\n\nYour encrypted vote for **{selected_candidate}** has been securely recorded.")
                    st.balloons()
                    
                    # Auto-logout after 3 seconds
                    st.info("🔓 You will be automatically logged out in 3 seconds...")
                    import time
                    time.sleep(3)
                    
                    st.session_state.clear()
                    st.switch_page("pages/01_registration.py")
        except Exception as e:
            st.error(f"❌ Error casting vote: {str(e)}")
            add_log(f"Error casting vote for {current_voter_email}: {str(e)}", "error")

# ===== Safety reminder =====
st.divider()
st.warning("⚠️ **Important:** Your vote is encrypted and anonymous. After voting, you will be automatically logged out.")
