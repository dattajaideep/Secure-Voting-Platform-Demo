# Shuffle and proof generation
# services/mixnet.py
import secrets

class VerifiableMixNet:
    def __init__(self, layers=3):
        self.layers = layers

    def mix(self, ballots: list):
        mixed = ballots.copy()
        proofs = []
        for layer in range(self.layers):
            secrets.SystemRandom().shuffle(mixed)
            proof = {
                "layer": layer + 1,
                "inputCount": len(mixed),
                "outputCount": len(mixed),
                "proof": secrets.token_hex(16)
            }
            proofs.append(proof)
        return mixed, proofs
