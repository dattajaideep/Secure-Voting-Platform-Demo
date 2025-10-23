import streamlit as st
from streamlit_oauth import OAuth2Component
from dotenv import load_dotenv
from utils.roles import is_admin, is_logged_in, get_user_role
import os
from datetime import datetime


# --- Load environment variables (Google OAuth credentials) ---
load_dotenv()
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")


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


# --- Initialize database tables automatically ---
init_db()

# --- Streamlit Config ---
st.set_page_config(page_title="Secure Voting System", page_icon="🗳️", layout="wide")
st.title("Secure Voting System with Google OAuth + SQLite")

# --- Sidebar: Show login status and role ---
if is_logged_in():
    if is_admin():
        st.sidebar.success(f"🔑 Admin: {st.session_state.user_email}")
    else:
        st.sidebar.success(f"👤 User: {st.session_state.user_email}")
    
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
menu = st.sidebar.radio(
    "Navigate",
    ["Home", "Register Voter", "Request Token", "Cast Vote", "Mix Network", "Tally Results", "Logs"]
)


# --- Page: Home ---
if menu == "Home":
    st.header("Welcome to the Secure Electronic Voting Demo")
    st.markdown("""
        This system shows how secure, transparent electronic voting can work.
        It uses Google OAuth for authentication and SQLite for secure data storage.
    """)


# --- Page: Register Voter ---
elif menu == "Register Voter":
    st.header("Register Voter")
    name = st.text_input("Voter Name")
    voter_id = st.text_input("Voter ID")
    if st.button("Register"):
        if name and voter_id:
            voter_repo.add_voter(voter_id, name)
            add_log(f"Registered voter: {name} ({voter_id})", "info")
            st.success(f"Voter {name} registered successfully!")
        else:
            st.error("Please fill in both name and voter ID.")
    voters = voter_repo.get_all_voters()
    if voters:
        st.subheader("Current Voters")
        st.table(voters)
    else:
        st.info("No voters registered yet.")


# --- Page: Request Token ---
elif menu == "Request Token":
    st.header("Request Voting Token")
    voters = voter_repo.get_all_voters()
    voter_map = {v["voter_id"]: v["name"] for v in voters if not v["has_token"]}
    if voter_map:
        voter_id = st.selectbox("Select Voter", list(voter_map.keys()), format_func=lambda x: voter_map[x])
        if st.button("Request Token"):
            client = VoterClient(authority)
            token_hash, signature = client.create_blind_token(voter_id)
            voter_repo.update_token_status(voter_id, True)
            add_log(f"Issued token to {voter_map[voter_id]}", "success")
            st.success(f"Token issued for {voter_map[voter_id]}")
    else:
        st.info("No eligible voters without tokens.")


# --- Page: Cast Vote ---
elif menu == "Cast Vote":
    st.header("Cast Vote")
    voters = voter_repo.get_all_voters()
    eligible = {v["voter_id"]: v["name"] for v in voters if v["has_token"] and not v["has_voted"]}
    candidates = ["Candidate A", "Candidate B", "Candidate C"]
    if eligible:
        voter_id = st.selectbox("Select Voter", list(eligible.keys()), format_func=lambda x: eligible[x])
        candidate = st.selectbox("Select Candidate", candidates)
        if st.button("Submit Vote"):
            client = VoterClient(authority)
            token_data = client.token_repo.get_token_by_voter(voter_id)
            signature = int(token_data["signature"], 16)
            token_hash = token_data["token_hash"]
            ballot_id = client.cast_vote(token_hash, signature, candidate)
            voter_repo.mark_voted(voter_id)
            add_log(f"{eligible[voter_id]} voted for {candidate}", "success")
            st.success(f"Vote recorded for {candidate} successfully.")
    else:
        st.info("No eligible voters available to vote.")


# --- Page: Mix Network (Admin Only) ---
elif menu == "Mix Network":
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


# --- Page: Tally Results (Admin Only) ---
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


# --- Page: Logs (Admin Only) ---
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