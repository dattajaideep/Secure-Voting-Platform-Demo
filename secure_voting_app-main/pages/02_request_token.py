# Request voting token page
# pages/02_request_token.py
import streamlit as st
from services.voter_client import VoterClient
from services.voting_authority import VotingAuthority
from db.repositories import VoterRepository
from utils.logger import add_log
from db.connection import get_conn


st.title("2️⃣ Request Blind Token")

voter_repo = VoterRepository()
authority = VotingAuthority(get_conn())

voters = voter_repo.get_all_voters()
voter_options = [v["voter_id"] for v in voters if not v["has_token"]]

selected_voter = st.selectbox("Select Voter", [""] + voter_options)

if st.button("Request Blind Token"):
    if not selected_voter:
        st.error("Please select a voter")
    else:
        client = VoterClient(authority)
        token_hash, signature = client.create_blind_token(selected_voter)
        st.success(f"Blind token issued for voter {selected_voter}")
        add_log(f"Blind token issued: {selected_voter}", "success")
        voter_repo.update_token_status(selected_voter, True)
