import streamlit as st
from streamlit_oauth import OAuth2Component
from dotenv import load_dotenv
from utils.roles import is_admin, is_logged_in, get_user_role, require_roles
from utils.data_masking import mask_list, mask_dict, get_display_name, MASK_VALUE, can_voter_unmask_own_data, filter_voter_data, mask_voter_for_self
import os
from datetime import datetime
from utils.session_manager import check_session_timeout, update_last_activity
from utils.logger import setup_logger


# --- Load environment variables ---
load_dotenv()

# OAuth credentials
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")

# Application settings from .env
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
STREAMLIT_SERVER_PORT = os.getenv("STREAMLIT_SERVER_PORT", "8501")

# Initialize logger
logger = setup_logger('voting_platform')

# --- Define Available Pages ---
VALID_PAGES = [
    "Home",
    "Register Voter",
    "Request Token",
    "Cast Vote",
    "Mix Network",
    "Tally Results",
    "Logs"
]


# --- Local project imports ---
from db.init_db import init_db
from db.connection import get_conn
from db.repositories.voter_repository import VoterRepository
from db.repositories.ballot_repository import BallotRepository
from db.repositories.mixnet_repository import MixNetRepository
from db.repositories.log_repository import LogRepository
from utils.logger import add_log
from utils.roles import is_admin, is_logged_in, get_user_role  # ← ADD THIS
from services.voting_authority import VotingAuthority
from services.voter_client import VoterClient
from services.mixnet import VerifiableMixNet


# --- 404 Error Handler Function ---
def handle_404_error():
    """Display 404 error page for invalid routes - no sensitive information disclosed"""
    st.error("❌ 404: Page Not Found", icon="🚫")
    st.markdown("""
    ### Oops! The requested page could not be found.
    
    Please select a valid page from the navigation menu on the left.
    """)
    
    st.markdown("### 📋 Available Pages:")
    cols = st.columns(2)
    for idx, page in enumerate(VALID_PAGES):
        with cols[idx % 2]:
            if st.button(f"Go to {page}", key=f"navigate_{idx}"):
                st.session_state["current_page"] = page
                st.rerun()
    
    st.markdown("---")
    st.info("💡 **Tip:** Use the sidebar radio menu to navigate between pages.")


# --- Initialize database tables automatically ---
init_db()

# --- Streamlit Config ---
st.set_page_config(page_title="Secure Voting System", page_icon="🗳️", layout="wide")

# Debug mode info
if DEBUG:
    st.sidebar.info(f"🔧 Debug Mode | Environment: {ENVIRONMENT} | Port: {STREAMLIT_SERVER_PORT}")
    logger.debug(f"Application started in {ENVIRONMENT} mode")

# Add custom CSS for timeout popup
st.markdown("""
<style>
    .timeout-popup {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0,0,0,0.2);
        z-index: 999;
        text-align: center;
    }
    .timeout-popup h3 {
        color: #ff4b4b;
        margin-bottom: 10px;
    }
    .timeout-popup p {
        margin: 10px 0;
    }
    .stButton button {
        margin: 10px auto;
    }
</style>
""", unsafe_allow_html=True)

st.title("Secure Voting System with Google OAuth + SQLite")

# --- Sidebar: Show login status and role ---
if is_logged_in():
    # Check for session timeout
    check_session_timeout()
    
    if is_admin():
        st.sidebar.success(f"🔑 Admin: {st.session_state.user_email}")
        # Add unmask toggle for admins to view unmasked voter data
        if st.sidebar.checkbox("🔓 Unmask Voter Data", value=st.session_state.get('unmask_voter_data', False)):
            st.session_state.unmask_voter_data = True
        else:
            st.session_state.unmask_voter_data = False
    elif get_user_role() == 'voter':
        st.sidebar.success(f"👤 Voter: {st.session_state.get('voter_id', 'Unknown')}")
        # Add unmask toggle for voters to view their own data unmasked
        if st.sidebar.checkbox("🔓 View My Details", value=st.session_state.get('unmask_own_voter_data', False)):
            st.session_state.unmask_own_voter_data = True
        else:
            st.session_state.unmask_own_voter_data = False
    else:
        st.sidebar.success(f"👤 User: {st.session_state.user_email}")
    
    # Update last activity timestamp
    update_last_activity()
    
    # Logout button (only show if logged in)
    if st.sidebar.button("Logout"):
        add_log(f"{st.session_state.user_email} logged out", "info")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
else:
    st.sidebar.info("Not logged in")

    
# --- Initialize core repositories and services ---
voter_repo = VoterRepository()
ballot_repo = BallotRepository()
log_repo = LogRepository()
mixnet_repo = MixNetRepository()

# Get database connection for services that require it
db_conn = get_conn()
authority = VotingAuthority(db_conn)
mixnet = VerifiableMixNet()


# --- Navigation Sidebar ---
# The navigation radio is intentionally disabled to make the sidebar non-interactive
# Users will still see the available pages but cannot change them from the sidebar.
try:
    # Newer Streamlit versions support the `disabled` parameter
    menu = st.sidebar.radio(
        "Navigate",
        VALID_PAGES,
        index=0,
        disabled=True
    )
except TypeError:
    # Fallback for older Streamlit versions that don't accept `disabled`
    # Use a read-only selectbox to display the same content without allowing changes
    menu = st.sidebar.selectbox(
        "Navigate",
        VALID_PAGES,
        index=0,
        disabled=True
    )




# --- Page render functions ---
@require_roles('voter', 'admin', 'guest')
def render_home():
    st.header("Welcome to the Secure Electronic Voting Demo")
    st.markdown("""
        This system shows how secure, transparent electronic voting can work.
        It uses Google OAuth for authentication and SQLite for secure data storage.
    """)


@require_roles('voter', 'admin')
def render_register_voter():
    st.header("Register Voter")
    st.markdown("""
    Register a new voter in the system. Each voter must have a unique ID and a valid name.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Voter Name", placeholder="Enter full name", help="The voter's full legal name")
    with col2:
        voter_id = st.text_input("Voter ID", placeholder="e.g., V001", help="Unique identifier for this voter")
    
    if st.button("Register Voter", type="primary"):
        if not name or not voter_id:
            st.error("❌ **Registration Failed**", icon="📋")
            st.markdown("""
            Please provide both pieces of information:
            - **Voter Name**: Required (cannot be empty)
            - **Voter ID**: Required (cannot be empty, must be unique)
            """)
        else:
            try:
                voter_repo.add_voter(voter_id, name)
                add_log(f"Registered voter: {name} ({voter_id})", "info")
                st.success(f"✅ **Registration Successful!**\n\nVoter **{name}** (ID: {voter_id}) has been registered in the system.")
            except Exception as e:
                st.error("❌ **Registration Error**", icon="⚠️")
                st.warning(f"Could not register voter. The Voter ID '{voter_id}' may already exist. Please use a unique ID.")
    
    st.markdown("---")
    voters = voter_repo.get_all_voters()
    if voters:
        # Apply data masking - unmask only if admin explicitly enabled it
        should_unmask = st.session_state.get('unmask_voter_data', False) and is_admin()
        masked_voters = mask_list(voters, unmask=should_unmask)
        st.subheader("📊 Registered Voters")
        st.dataframe(masked_voters, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No voters registered yet. Start by registering your first voter above.")


@require_roles('voter', 'admin')
def render_request_token():
    st.header("Request Voting Token")
    st.markdown("""
    Issue anonymous voting tokens to registered voters. Each voter can only receive one token,
    which they will use to cast their vote while maintaining ballot privacy.
    """)
    
    current_role = get_user_role()
    current_voter_id = st.session_state.get('voter_id', None)
    
    voters = voter_repo.get_all_voters()
    
    # If logged-in voter (not admin), show only their own data
    if current_role == 'voter' and current_voter_id:
        # Filter to show only this voter's data
        their_voters = [v for v in voters if v['voter_id'] == current_voter_id and not v["has_token"]]
        
        if their_voters:
            voter_data = their_voters[0]
            should_unmask = st.session_state.get('unmask_own_voter_data', False)
            
            # Show voter's own data with toggle
            col1, col2 = st.columns([3, 1])
            with col1:
                if should_unmask:
                    st.info(f"📋 **Your Voter ID:** {voter_data['voter_id']}")
                    st.write(f"**Name:** {voter_data['name']}")
                else:
                    st.info(f"📋 **Your Voter ID:** {MASK_VALUE}")
                    st.write(f"**Name:** {MASK_VALUE}")
            
            if st.button("Request Token", type="primary"):
                try:
                    client = VoterClient(authority)
                    token_hash, signature = client.create_blind_token(current_voter_id)
                    voter_repo.update_token_status(current_voter_id, True)
                    add_log(f"Voter {current_voter_id} requested token", "success")
                    st.success(f"✅ **Token Issued Successfully!**\n\nYou are now eligible to cast your vote.")
                except Exception as e:
                    st.error("❌ **Token Issuance Failed**", icon="⚠️")
                    st.warning("An error occurred while issuing your token. Please try again or contact an administrator.")
        else:
            st.warning("⚠️ **No Token Needed**", icon="🎯")
            st.markdown("""
            You already have a voting token or are not eligible at this time.
            Please proceed to the **Cast Vote** page to vote.
            """)
    
    # If admin, show all voters with masking controls
    else:
        voter_map = {v["voter_id"]: v["name"] for v in voters if not v["has_token"]}
        # Create display map with masking
        should_unmask = st.session_state.get('unmask_voter_data', False) and is_admin()
        display_map = {}
        for voter_id, name in voter_map.items():
            if should_unmask:
                display_map[voter_id] = f"{name} (ID: {voter_id})"
            else:
                display_map[voter_id] = f"{MASK_VALUE} (ID: {MASK_VALUE})"
        
        if voter_map:
            voter_id = st.selectbox("Select Voter", list(voter_map.keys()), format_func=lambda x: display_map.get(x, f"{MASK_VALUE} (ID: {MASK_VALUE})"))
            if st.button("Issue Token", type="primary"):
                try:
                    client = VoterClient(authority)
                    token_hash, signature = client.create_blind_token(voter_id)
                    voter_repo.update_token_status(voter_id, True)
                    add_log(f"Issued token to {voter_map[voter_id]}", "success")
                    st.success(f"✅ **Token Issued Successfully!**\n\nVoter **{voter_map[voter_id]}** is now eligible to cast their vote.")
                except Exception as e:
                    st.error("❌ **Token Issuance Failed**", icon="⚠️")
                    st.warning("An error occurred while issuing the token. Please try again or contact an administrator.")
        else:
            st.warning("⚠️ **No Voters Available**", icon="📋")
            st.markdown("""
            All registered voters already have voting tokens. To issue more tokens:
            1. Go to **Register Voter** and register new voters
            2. Return to this page to issue them tokens
            """)


@require_roles('voter')
def render_cast_vote():
    st.header("Cast Vote")
    st.markdown("""
    Cast your vote securely and anonymously. You can only vote once, so choose your candidate carefully.
    Your vote will be cryptographically protected and anonymized through the MixNet process.
    """)
    
    voters = voter_repo.get_all_voters()
    eligible = {v["voter_id"]: v["name"] for v in voters if v["has_token"] and not v["has_voted"]}
    # Create display map with masking for voters
    should_unmask = st.session_state.get('unmask_voter_data', False) and is_admin()
    eligible_display = {}
    for voter_id, name in eligible.items():
        if should_unmask:
            eligible_display[voter_id] = f"{name} (ID: {voter_id})"
        else:
            eligible_display[voter_id] = f"{MASK_VALUE} (ID: {MASK_VALUE})"
    candidates = ["Candidate A", "Candidate B", "Candidate C"]
    
    if eligible:
        col1, col2 = st.columns(2)
        with col1:
            voter_id = st.selectbox("Select Voter", list(eligible.keys()), format_func=lambda x: eligible_display.get(x, f"{MASK_VALUE} (ID: {MASK_VALUE})"))
        with col2:
            candidate = st.selectbox("Select Candidate", candidates)
        
        st.info("💡 **Reminder:** This action cannot be undone. Ensure you have selected the correct candidate.")
        
        if st.button("Submit Vote", type="primary"):
            try:
                client = VoterClient(authority)
                token_data = client.token_repo.get_token_by_voter(voter_id)
                signature = int(token_data["signature"], 16)
                token_hash = token_data["token_hash"]
                ballot_id = client.cast_vote(token_hash, signature, candidate)
                voter_repo.mark_voted(voter_id)
                add_log(f"{eligible[voter_id]} voted for {candidate}", "success")
                st.success(f"✅ **Vote Submitted Successfully!**\n\nYour vote for **{candidate}** has been recorded securely.")
            except Exception as e:
                st.error("❌ **Vote Submission Failed**", icon="⚠️")
                st.warning("An error occurred while processing your vote. Please try again or contact an administrator.")
    else:
        st.warning("⚠️ **No Eligible Voters**", icon="🗳️")
        st.markdown("""
        There are no voters available to cast votes. This could mean:
        1. No voters have been registered yet (go to **Register Voter**)
        2. No voters have received tokens (go to **Request Token**)
        3. All eligible voters have already cast their votes
        
        Please complete the necessary steps to enable voting.
        """)


# --- Page dispatch ---
if menu == "Home":
    render_home()
elif menu == "Register Voter":
    render_register_voter()
elif menu == "Request Token":
    render_request_token()
elif menu == "Cast Vote":
    render_cast_vote()
elif menu == "Mix Network":
    # Admin-only page
    if not is_admin():
        st.error("🚫 Access Denied: This page is only accessible to administrators")
        st.info("Please log in with admin credentials")
    else:
        st.header("Run MixNet to Anonymize Votes")
        ballots = ballot_repo.get_all_ballots()
        if st.button("Run MixNet"):
            mixed, proofs = mixnet.mix(ballots)
            st.session_state.mixed_ballots = mixed
            st.session_state.mix_proofs = proofs
            for p in proofs:
                mixnet_repo.save_proof(p)
                add_log(f"MixNet proof saved for layer {p['layer']}", "info")
            st.success("Mixing complete and proofs recorded.")
        if "mixed_ballots" in st.session_state:
            st.subheader("Mixed Ballots")
            st.table(st.session_state.mixed_ballots)
elif menu == "Tally Results":
    if not is_admin():
        st.error("🚫 Access Denied: This page is only accessible to administrators")
        st.info("Please log in with admin credentials")
    else:
        st.header("Tally Election Results")
        if "mixed_ballots" in st.session_state:
            tally = {}
            for b in st.session_state.mixed_ballots:
                tally[b["candidate"]] = tally.get(b["candidate"], 0) + 1
            st.subheader("Vote Totals")
            for c, count in tally.items():
                st.write(f"{c}: {count} votes")
        else:
            st.info("Run the MixNet first to anonymize ballots.")
elif menu == "Logs":
    if not is_admin():
        st.error("🚫 Access Denied: This page is only accessible to administrators")
        st.info("Please log in with admin credentials")
    else:
        st.header("System Activity Logs")
        logs = log_repo.get_all_logs()
        if logs:
            st.table(logs)
        else:
            st.info("No activity logs found.")
else:
    handle_404_error()