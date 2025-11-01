# ✅ Voting Platform Security Requirements & Secure Voting Platform Demo

<!-- Badges: CI | Tests | License | Python | Streamlit -->
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/dattajaideep/Secure-Voting-Platform-Demo/actions)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/streamlit.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-blue.svg)](https://pytest.org)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/streamlit-ready-orange.svg)](https://streamlit.io)


This repository contains a secure, privacy-preserving voting platform demo built with Streamlit. It implements cryptographic workflows (blind tokens, RSA encryption, mixnet shuffling) to demonstrate end-to-end confidentiality, anonymous tallying, and auditability.

This README combines two perspectives:
- A security requirements & evidence summary used for review and assessments.
- Developer-facing quick start, project layout, and troubleshooting guidance for contributors and reviewers.

---

Table of contents
- Project snapshot
- Quick start (2 minutes)
- System architecture & modules
- Security requirements (detailed status & notes)
- Development-specific security controls
- Project layout & important files
- Common tasks
- Troubleshooting
- Contributing
- License
- Where to go next

---

Project snapshot / Demo

![StreamLit Module](/images/VoteCast.gif)
![StreamLit Module](/images/AdminFunction.gif)
![StreamLit Module](/images/MixNet_Demo.gif)
![StreamLit Module](/images/Platform_View_Demo.gif)

System architecture overview

![System Architecture Overview](/images/System%20Arch%20Overview.png)

The system sequence diagram

![System Architecture Overview](/images/Big%20Complete%20Seq%20Diagram.png)

Repository modules overview

![Repository Modules](/images/repo%20modules.png)

The system is composed of several key modules working together:

Core Modules
1. **Authentication Module**
   ![Auth Module](/images/Auth%20Module.png)

2. **Cryptographic Module**
   ![Crypto Module](/images/Crypto%20Module.png)

3. **Database Module**
   ![DB Module](/images/DB%20Module.png)

4. **Utils Module**
   ![Utils Module](/images/Utils%20Module.png)

5. **Streamlit Interface**
   ![StreamLit Module](/images/StreamLit%20Module.png)

6. **Mixnet Module**
   ![StreamLit Module](/images/Mixnet%20Flow.png)

7. **Voting Module**
   ![Voting Module](/images/cast%20vote%20module.png)

8. **OTP Module**
   ![OTP Module](/images/OTP%20FLOW.png)
   
Database structure

![ER Diagram](/images/ER%20diagram.png)

---

Quick start (2 minutes)

1. Create and activate a Python virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit app (default file in repository root):

```bash
streamlit run streamlit_app.py
```

If the app is located in `secure_voting_app-main/` (some packaged examples), run:

```bash
streamlit run secure_voting_app-main/streamlit_app.py
```

Open the URL printed by Streamlit (usually http://localhost:8501).

---

Security requirements (voting-specific) — status, evidence & notes

This document summarizes the security requirements implemented in the Voting Platform, along with status, evidence, and notes for partially implemented or recommended improvements.

| Requirement | Status | Evidence / Notes |
|-------------|--------|----------------|
| **Blind token / Token binding**: Voting tokens must be blinded, one-time use; only token hashes stored server-side | ✅ Implemented | `02_request_token.py` uses `client.create_blind_token()`; `db/repositories/token_repository.py` stores token hashes; flow supports blinding and hashing |
| **MixNet verification/proofs**: Proofs saved and verifiable (privacy + verifiability) | ✅ Implemented | `services/mixnet.py` (VerifiableMixNet), `04_mixnet.py` saves proofs, repository supports verification |
| **Registered voter access**: Only registered voters can access voter-only functions | ✅ Implemented | Checks in `02_request_token.py`, `03_cast_vote.py` for `st.session_state['user_email']` and role == 'user'; consider adding server-side API checks |
| **Session timeout**: 5 minutes of inactivity invalidates session state | ✅ Implemented | `session_manager.py` used in `00_admin_login.py`, `03_cast_vote.py`; tested in `secure_voting_app/tests/session_tests/*` |
| **Login lockout**: 30-minute lockout after 3 failed attempts (configurable) | ✅ Implemented | `login_attempt_repository.py`, `auth_security.py`; env-configurable (`MAX_LOGIN_ATTEMPTS=3, LOGIN_LOCKOUT_MINUTES=30`) |
| **Input validation & sanitization** | ✅ Implemented | `validation.py` used across endpoints; recommend a sweep to ensure server-side validation everywhere |
| **Password hashing & salting** | ⚠ Partially implemented | `hashing.py`, `password_utils.py`; fallback to insecure `default_secret_key` if env missing. **Future development:** Remove insecure defaults, fail fast if secrets missing |
| **One vote per user**: Prevent double voting | ✅ Implemented | `ballot_repository.py` logic and `test_one_vote_per_voter.py` |
| **RBAC**: Enforce least privilege per role | ✅ Implemented | `roles.py`, page-level checks using `st.session_state['role']` |
| **Voter data privacy**: Masked or minimized data for unauthorized roles | ✅ Implemented | `data_masking.py`, `test_data_masking.py` |
| **End-to-end encryption of votes** | ✅ Implemented | `encryption.py`, `rsa.py`, `services/secure_rsa.py`; tested in `test_end_to_end_encryption.py` |
| **Database role restriction** | ⚠ Partially implemented | Access control helpers exist (`access_control.py`) but DB-level minimal-permission enforcement depends on setup. **Future development:** Use minimal DB user permissions and provide migration/docs |
| **CI/CD ephemeral secrets decoding** | ✅ Implemented | `cd.yml` decodes base64 secrets with cleanup; verify strict file permissions |
| **Code documentation & review** | ⚠ Organizational | Policy referenced in docs; not enforced by code. **Future development:** CI could enforce commit signatures |
| **Security unit & integration tests** | ✅ Implemented | `secure_voting_app/tests/*`; CI workflow `cd.yml` runs tests |
| **Strong cryptographic randomness** | ✅ Implemented | `rng.py` uses `secrets`; `encryption.py` and `rsa.py` use `secrets` |
| **No hardcoded secrets** | ⚠ Partially implemented | CI uses `$ secrets.*`; but `.env` contains real-looking secrets. **Future development:** Remove `.env` secrets, rotate keys, use secret manager only |
| **Secure key & secret management** | ⚠ Partially implemented | Env-based keys exist; defaults are insecure. **Future development:** Remove defaults, fail if missing, support key rotation |
| **Replay attack protection** | ⚠ Partially implemented | `encryption.py` uses `transmission_id`; server-side deduplication not obvious. **Future development:** Enforce DB constraint or server-side uniqueness checks |
| **Tamper-evident, append-only audit logs** | ⚠ Partially implemented | Logs exist (`log_repository.py`, `06_logs.py`) but no DB-level enforcement. **Future development:** Use write-only tables, cryptographic chaining, or restricted permissions |
| **Non-repudiation of critical admin actions** | ⚠ Partially implemented | Logs actions with timestamp (`add_log()`), but no cryptographic signing. **Future development:** Sign critical actions or enforce audit log integrity |

Notes: This section is intended for auditors and reviewers. The Status column reflects current implementation in the codebase; Evidence points to files and tests that demonstrate the feature. Items flagged with ⚠ denote partial implementations and suggested future remediation.

---

Development-specific security controls

- Database & Access Restrictions
  - Enforce access control logic when users attempt to access resources.
  - Use minimal DB roles for production.

- Secure Coding Practices
  - Input validation and sanitization across endpoints.
  - No hardcoded secrets; use environment variables and secret managers.

- Code Review & Version Control
  - Documented code and code reviews for all commits.
  - Sign commits and validate origins.

- Testing
  - Security unit and integration tests implemented.
  - Tests run as part of CI/CD workflow.

---

Project layout (important files)

- `streamlit_app.py` — main Streamlit entry point (launches pages under `pages/`).
- `pages/` — Streamlit page modules that implement the voting flow (registration → request token → cast vote → mixnet → tally → audit logs).
- `crypto/` — cryptographic helpers (RSA, hashing, RNG, encryption wrappers).
- `services/` — core voting and mixnet logic used by the app.
- `db/` — lightweight SQLite persistence and repository classes.
- `auth/` and `utils/` — authentication, session management, RBAC, and data-masking utilities.
- `tests/` and `secure_voting_app-main/tests/` — automated tests and integration checks.

For a full architecture overview see `SUBSYSTEMS_IDENTIFICATION.md` in the repository root.

---

Common tasks

- Run the test suite (fast unit + integration tests):

```bash
pytest -q
```

- Run a specific test file:

```bash
pytest tests/test_example.py -q
```

- Lint with flake8 (if installed):

```bash
flake8 .
```

---

Developer notes / assumptions

- Entry point: This README assumes `streamlit_app.py` at the repository root is the app entry. Some distributions of the demo place the code in `secure_voting_app-main/`; in that case run Streamlit against the file inside that folder.
- Database: The app uses SQLite files created at runtime (check `db/connection.py` and `db/init_db.py`). No external DB server required for local development.
- Keys & secrets: For a local demo, RSA keys may be generated on demand. For production you must supply persistent key material and avoid storing private keys in plaintext.

---

Troubleshooting

- "Streamlit can't find streamlit_app.py": check whether the entrypoint lives under `secure_voting_app-main/` and run Streamlit against that path.
- Missing Python packages: double-check `pip install -r requirements.txt` and your active virtual environment.
- Tests failing with DB errors: remove any stale local SQLite files (look for `.db` files in the repo root or `db/` folder) and re-init the DB if present (`db/init_db.py`).

If you're stuck, open an issue with the test output and environment details (OS, Python version).

---

Contributing

Contributions are welcome. Short checklist for contributors:

1. Fork the repository and create a feature branch.
2. Run and add tests for new behavior (pytest).
3. Run linters and keep changes focused.
4. Create a concise PR with rationale and test evidence.

Suggested commands:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
flake8 .
```

If you'd like, I can also:

- Add a small CONTRIBUTING.md with the exact test commands and GitHub workflow tips.
- Create a short quick-start script to automate venv creation + dependency install + launching Streamlit.

---

## License

This project is published under the MIT License. See the `LICENSE` file at the repository root for the full text and conditions.

- SPDX: MIT
- Copyright: see `LICENSE`

Maintainers should ensure license notices are preserved in derivative works and packaged distributions.

---

## Commit history (short)

Below is a short, recent commit history extracted from the repository to help reviewers quickly see recent activity. To view the full history locally, run:

```bash
git log --oneline --decorate --graph --all
```

Recent commits (last 5):

- 54c3fe0 2025-10-25 Refactor code structure for improved readability and maintainability
- 294a406 2025-10-24 Add database initialization in repository constructor with logging for failures
- 60b8945 2025-10-24 Refactor requirements.txt to remove duplicates and organize dependencies
- b760e0e 2025-10-24 Implement comprehensive audit logging system with access control
- e8208f8 2025-10-24 one vote per user, password validation, access control manage

If you'd like, I can expand this section to include a generated CHANGELOG.md based on tags or commit messages.

---

## Changelog (high level)

This repository does not currently contain a formal CHANGELOG file. Suggested policy for next steps:

- Use semantic commits or keep a `CHANGELOG.md` updated for release notes.
- Tag releases with annotated git tags and draft release notes on GitHub.
- Optionally adopt an automated changelog generator (e.g., `git-cliff`, `auto-changelog`) for consistency.

---

Where to go next

- `SUBSYSTEMS_IDENTIFICATION.md` — high-level architecture and components.
- `docs/` — implementation notes and design rationale.

This repository is a demo and educational artifact — do not use it as-is for real elections without a formal security review.

Completion: Updated README with clearer quick-start, developer notes, troubleshooting guidance, badges, license summary, and commit history snippet.