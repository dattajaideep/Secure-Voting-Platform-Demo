# Cast vote page
# pages/03_cast_vote.py
import streamlit as st
from services.voter_client import VoterClient
from services.voting_authority import VotingAuthority
from db.repositories import VoterRepository, TokenRepository, BallotRepository
from utils.logger import add_log
from db.connection import get_conn
from utils.session_manager import check_session_timeout, update_last_activity

st.title("3️⃣ Cast Vote")

# Check for session timeout
check_session_timeout()

voter_repo = VoterRepository()
token_repo = TokenRepository()
ballot_repo = BallotRepository()
authority = VotingAuthority(get_conn())

# Update activity timestamp if user is logged in
if 'user_email' in st.session_state:
    update_last_activity()

voters = [v for v in voter_repo.get_all_voters() if v["has_token"] and not v["has_voted"]]
voter_options = [v["voter_id"] for v in voters]

candidates = ["Candidate A", "Candidate B", "Candidate C"]

selected_voter = st.selectbox("Select Voter", [""] + voter_options)
selected_candidate = st.selectbox("Select Candidate", [""] + candidates)

if st.button("Cast Vote", key="cast_vote_btn"):
    if not selected_voter or not selected_candidate:
        st.error("Select both voter and candidate")
    else:
        try:
            client = VoterClient(authority)
            token = token_repo.get_token_by_voter(selected_voter)
            if token is None:
                st.error("No token found for this voter")
            else:
                # Convert signature from hex string to int
                signature_int = int(token["signature"], 16) if isinstance(token["signature"], str) else token["signature"]
                ballot_id = client.cast_vote(token["token_hash"], signature_int, selected_candidate)
                st.success(f"Vote cast successfully! Ballot ID: {ballot_id}")
                voter_repo.mark_voted(selected_voter)
                add_log(f"Vote cast by {selected_voter}, ballot {ballot_id}", "success")
        except Exception as e:
            st.error(f"Error casting vote: {str(e)}")
            add_log(f"Error casting vote for {selected_voter}: {str(e)}", "error")
