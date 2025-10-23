# secure_voting_app

secure_voting_app_basic

## Running PostgreSQL in GitHub Codespaces

GitHub Codespaces does not support running Docker containers directly inside the codespace. Instead, use the built-in PostgreSQL service provided by Codespaces, or connect to a remote/local PostgreSQL instance.

### Option 1: Use Codespaces PostgreSQL Dev Service

1. Open the Codespaces configuration (gear icon > "Add Dev Service").
2. Add the PostgreSQL service and configure:
   - Username: `postgres`
   - Password: `password`
   - Database: `voting_db`
   - Port: `5432`
3. Update your `.env` file if needed:
   ```env
   DATABASE_URL=postgresql://postgres:password@localhost:5432/voting_db
   ```

### Option 2: Connect to a Remote or Local PostgreSQL

If you have PostgreSQL running on your local machine or a remote server, update your `.env` file with the correct host and credentials.

### Option 3: Use a Managed PostgreSQL Service

You can use cloud providers like AWS RDS, Azure Database, or Google Cloud SQL. Update your `.env` file with the connection string provided by your service.

---

## Docker Installation (Debian-based Linux)

To install Docker, run the following commands:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
	"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
	$(lsb_release -cs) stable" | \
	sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

After installation, verify Docker is installed:

```bash
docker --version
```

## Project overview (detailed)

This is a small demo secure voting system with:

- Frontend UI: Streamlit app (`streamlit_app.py` + `pages/*`) providing six pages (Registration, Request Token, Cast Vote, Mix Network, Tally, Logs).
- Services: core crypto and protocol logic in `services` (RSA, `VotingAuthority`, `VoterClient`, `MixNet`).
- Database layer: simple repository wrappers in `db/repositories` using `db.connection.get_conn()` (Postgres).
- Utilities: cryptographic helpers and logging helpers in `utils`.
- DB schema initializer: `.devcontainer/init-db.sql`.

The system demonstrates blind-signature token issuance, casting votes with blinded tokens, a simple mixnet shuffle, and tallying.

Below is an in-depth walk-through.

### High-level architecture and components

- **UI layer (Streamlit)**
  - `streamlit_app.py` is the main UI glue. It initializes repositories, services, and session state, and exposes a sidebar navigation among pages.
  - `pages/*.py` contain page components (optionally used in a multipage Streamlit layout). They call services/repositories.
- **Services**
  - `voting_authority.py`: central authority holding RSA keys and methods to issue blind signatures and verify tokens when casting ballots. Also inserts ballots into DB via `BallotRepository`.
  - `voter_client.py`: client-side logic for voters to create blind tokens and unblind signatures; interacts with `VotingAuthority` to obtain blind signature and with `TokenRepository` to store tokens.
  - `secure_rsa.py`: RSA implementation (key generation, `mod_pow`, sign/verify, blind/unblind). Custom implementation (non-library).
  - `mixnet.py`: mixnet simulator that shuffles ballots and generates commitment-bound proof hashes. Can optionally persist proofs via a repository.
- **Database & repositories**
  - `connection.py` reads `DATABASE_URL` and returns a psycopg2 connection with `RealDictCursor`.
  - Repositories: `VoterRepository`, `TokenRepository`, `BallotRepository`, `MixNetRepository`, `LogRepository` — thin wrappers around SQL operations (INSERT/SELECT/UPDATE). Each opens a connection, makes a single change or query, commits, and closes.
- **Utilities**
  - `crypto.py` — `sha256_hex` helper.
  - `logger.py` — wrapper around `LogRepository.add_log()` to centralize logging.
- **DB initializer**: `.devcontainer/init-db.sql` creates tables (`voters`, `tokens`, `ballots`, `mixnet_proofs`, `logs`).

### Data shapes and DB schema mapping

- **Voter (table `voters`)**:
  - columns: `voter_id TEXT PRIMARY KEY`, `name TEXT`, `has_token BOOLEAN`, `has_voted BOOLEAN`
- **Token (table `tokens`)**:
  - columns: `voter_id TEXT PRIMARY KEY REFERENCES voters(voter_id)`, `token_hash TEXT`, `signature TEXT`
  - `token_hash` is hex SHA-256 of the token; `signature` is hex string produced by RSA blind-signature protocol.
- **Ballot (table `ballots`)**:
  - columns: `ballot_id TEXT PRIMARY KEY`, `candidate TEXT`, `token_hash TEXT`, `encrypted BOOLEAN DEFAULT TRUE`
- **Mixnet proofs (`mixnet_proofs`)**:
  - columns: `id SERIAL PRIMARY KEY`, `layer INT`, `input_count INT`, `output_count INT`, `proof_hash TEXT`
  - The code stores `proof` -> `proof_hash`, and the mixnet now produces commitment hashes and includes `input_commit`/`output_commit` in the proof dict (but repo only persists `proof` to `proof_hash` column).
- **Logs (`logs`)**:
  - columns: `id SERIAL`, `message TEXT`, `log_type TEXT`, `created_at TIMESTAMP DEFAULT NOW()`.

### End-to-end flows (technical, step-by-step)

See the repository files for exact call sites; in short:

1. **Registration** (UI: Registration page)

   - `voter_repo.add_voter(voter_id, name)` inserts the voter.
   - `VotingAuthority.register_voter(voter_id)` updates authority's in-memory set.

2. **Request Token (Blind signature issuance)**

   - VoterClient generates a token, computes `token_hash`, blinds the hash, calls `VotingAuthority.issue_blind_signature(blinded_hash, voter_id)`, unblinds the signature, and stores `token_hash` and signature with `TokenRepository.add_token()`.

3. **Cast Vote**

   - Token and signature are read from DB, signature verified with `SecureRSA.verify_hash()`, a `ballot_id` is generated and inserted via `BallotRepository.add_ballot()`. `VoterRepository.mark_voted()` marks voter as voted.

4. **Mix Network**

   - `BallotRepository.get_all_ballots()` -> `VerifiableMixNet.mix(ballots)`, produce shuffled ballots and per-layer proofs. `MixNetRepository.save_proof()` inserts proofs into `mixnet_proofs`.

5. **Tally**
   - `BallotRepository.get_all_ballots()` then server computes counts per `candidate` and displays results.

### Important observations, security gaps, and recommendations

(summarized; see code comments and issues in repo for details):

- Ballots stored in plaintext (privacy not guaranteed). Use encryption and verifiable shuffle for privacy.
- Token reuse prevention is incomplete (see `used_token_hashes`). Add DB-backed atomic mark-as-used during ballot insert.
- RSA keys are generated in-memory; persist keys to survive restarts.
- Use vetted crypto libs for production.
- Ensure `DATABASE_URL` is correct for your runtime (use `db` hostname in Docker Compose).

If you'd like, I can implement one of the recommended fixes (prevent double-voting atomically, persist RSA keys, or extend mixnet proof persistence). Tell me which and I'll implement it.
