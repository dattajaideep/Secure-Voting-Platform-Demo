# Mixnet shuffle page
# services/mixnet.py
# pages/04_mixnet.py
import streamlit as st
from services.mixnet import VerifiableMixNet
from db.repositories import BallotRepository, MixNetRepository
from utils.logger import add_log


st.title("4️⃣ MixNet Anonymization")

ballot_repo = BallotRepository()
mixnet_repo = MixNetRepository()
ballots = ballot_repo.get_all_ballots()
if not ballots:
    st.info("No ballots to mix yet.")

if st.button("Run MixNet"):
    mixnet = VerifiableMixNet(layers=3)
    mixed, proofs = mixnet.mix(ballots)
    for proof in proofs:
        mixnet_repo.save_proof(proof)
        add_log(f"Mix layer {proof['layer']} verified", "success")
    st.success("MixNet completed! Ballots anonymized.")
    st.write(mixed)
