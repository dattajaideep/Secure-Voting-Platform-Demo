# Tally votes page
# pages/05_tally.py
import streamlit as st
from db.repositories import BallotRepository
from utils.logger import add_log
from utils.roles import require_admin  # ← ADD THIS IMPORT

# ← ADD THIS LINE (must be first, before any other st. commands)
require_admin()

st.title("5️⃣ Tally Results")
ballot_repo = BallotRepository()
ballots = ballot_repo.get_all_ballots()
if not ballots:
    st.info("No ballots to tally.")

tally = {}
for b in ballots:
    tally[b["candidate"]] = tally.get(b["candidate"], 0) + 1

st.subheader("Election Results")
for candidate, votes in tally.items():
    st.write(f"{candidate}: {votes} votes")
add_log("Election results tallied", "success")
