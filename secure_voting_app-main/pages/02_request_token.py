# Request voting token page
# pages/02_request_token.py
import streamlit as st
from services.voter_client import VoterClient
from services.voting_authority import VotingAuthority
from db.repositories import VoterRepository
from utils.logger import add_log
from db.connection import get_conn
from utils.session_manager import check_session_timeout, update_last_activity


st.title("2️⃣ Request Blind Token")

# Check for session timeout
check_session_timeout()

voter_repo = VoterRepository()
authority = VotingAuthority(get_conn())

# Update activity timestamp if user is logged in
if 'user_email' in st.session_state:
    update_last_activity()

voters = voter_repo.get_all_voters()
voter_options = [v["voter_id"] for v in voters if not v["has_token"]]

selected_voter = st.selectbox("Select Voter", [""] + voter_options)

if st.button("Request Blind Token", key="request_token_btn"):
    if not selected_voter:
        st.error("Please select a voter")
    else:
        try:
            client = VoterClient(authority)
            token_hash, signature = client.create_blind_token(selected_voter)
            st.success(f"Blind token issued for voter {selected_voter}")
            add_log(f"Blind token issued: {selected_voter}", "success")
            voter_repo.update_token_status(selected_voter, True)
        except Exception as e:
            st.error(f"Error issuing token: {str(e)}")
            add_log(f"Error issuing token to {selected_voter}: {str(e)}", "error")
