# Secure Voting Platform

A cryptographically secure, role-based access controlled voting system built with Streamlit, SQLite, and advanced cryptographic primitives.

## Overview

This secure voting platform implements end-to-end verifiable voting using advanced cryptographic techniques including:
- **RSA Blind Signatures** for voter anonymity
- **Verifiable Mix Networks** for vote shuffling
- **One-Time Token System** for vote authorization
- **Role-Based Access Control (RBAC)** for database operations
- **Google OAuth 2.0** for user authentication

## Key Features

### Security Features
- 🔐 **Blind Signature Scheme**: Ensures voter anonymity while preventing double voting
- 🔀 **Verifiable Mix Network**: Shuffles votes in a cryptographically verifiable manner
- 🔑 **RSA Encryption**: Secure token generation and ballot encryption
- 🛡️ **RBAC Database Access**: Fine-grained permission control per user role
- 🚨 **Comprehensive Audit Logging**: All operations tracked for compliance

### User Features
- 👤 **Google OAuth Integration**: Seamless user authentication
- 📊 **Real-time Results Dashboard**: View vote tallies with verification
- 🗳️ **Simple Voting Interface**: User-friendly ballot casting
- 📋 **Admin Dashboard**: System management and monitoring
- 📖 **Audit Logs**: Complete transaction history

## Project Structure

```
secure_voting_app-main/
├── auth/                          # OAuth & authentication
│   └── oauth.py                   # Google OAuth2 implementation
├── crypto/                        # Cryptographic modules
│   ├── rsa.py                     # RSA key generation & operations
│   ├── hashing.py                 # Secure hashing utilities
│   ├── rng.py                     # Random number generation
│   └── __init__.py
├── db/                            # Database & access control
│   ├── access_control.py          # RBAC enforcement layer
│   ├── connection.py              # SQLite connection management
│   ├── init_db.py                 # Database initialization
│   └── repositories/              # Data access objects
│       ├── voter_repository.py    # Voter record management
│       ├── ballot_repository.py   # Ballot storage
│       ├── token_repository.py    # Token management
│       ├── log_repository.py      # Audit logging
│       └── mixnet_repository.py   # Mix network data
├── pages/                         # Streamlit page routes
│   ├── 00_admin_login.py          # Admin authentication
│   ├── 01_registration.py         # Voter registration
│   ├── 02_request_token.py        # Blind signature request
│   ├── 03_cast_vote.py            # Ballot casting
│   ├── 04_mixnet.py               # Mix network verification
│   ├── 05_tally.py                # Result tallying
│   └── 06_logs.py                 # Audit log viewer
├── services/                      # Core business logic
│   ├── voting_authority.py        # Blind signature issuer
│   ├── voter_client.py            # Voter side cryptography
│   ├── mixnet.py                  # Verifiable mix network
│   └── secure_rsa.py              # RSA operations
├── utils/                         # Utility functions
│   ├── roles.py                   # RBAC role definitions
│   ├── logger.py                  # Event logging
│   ├── crypto.py                  # Crypto utilities
│   └── otp_service.py             # OTP generation
├── tests/                         # Test suite
│   ├── test_access_control_rbac.py
│   ├── test_integration_workflows.py
│   └── test_repositories_rbac.py
├── streamlit_app.py               # Main application entry point
├── requirements.txt               # Python dependencies
├── .env                           # Environment configuration
└── voting_keys.json              # Stored RSA key pairs
```

## Installation

### Prerequisites
- Python 3.8+
- pip
- SQLite3

### Setup

1. **Clone the repository**
```bash
cd secure_voting_app-main
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the root directory:
```env
# Google OAuth
OAUTH_CLIENT_ID=your_google_client_id
OAUTH_CLIENT_SECRET=your_google_client_secret

# Admin credentials
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure_password_here

# Database
DATABASE_PATH=voting_system.db

# Authentication Security
MAX_LOGIN_ATTEMPTS=3       # Maximum failed login attempts before lockout
LOGIN_LOCKOUT_MINUTES=30   # Duration of account lockout in minutes
```

5. **Run the application**
```bash
streamlit run streamlit_app.py
```

The application will be available at `http://localhost:8501`

## Architecture

### Voting Flow

1. **Registration Phase**
   - Voter registers via OAuth
   - Stored in voters table with `has_voted=False`

2. **Token Request Phase**
   - Voter generates blind signature request
   - Voting Authority issues blind signature without seeing voter identity
   - One-time token created for vote submission

3. **Casting Phase**
   - Voter selects candidate
   - Vote encrypted with ballot authority's public key
   - Token submitted alongside encrypted vote

4. **Mixing Phase**
   - Verifiable Mix Network shuffles ballots
   - Output linked to neither voter nor original ballot
   - Tally conducted on mixed results

### Role-Based Access Control (RBAC)

**Voter Role** (`voter_read`)
- SELECT on voters, ballots, tally_results, logs
- Restricted to their own records only

**Admin Role** (`admin_full`)
- Full access to all tables
- Can manage voters, generate reports, view audit logs

**Database-Level Enforcement**
- Access control checked at query execution
- Prevents unauthorized data access
- Logs all denied access attempts

## API & Core Services

### VotingAuthority
Manages the blind signature scheme and vote validation.

```python
from services.voting_authority import VotingAuthority

voting_authority = VotingAuthority(db_connection)
blind_sig = voting_authority.issue_blind_signature(blinded_hash, voter_id)
ballot_id = voting_authority.verify_token_and_cast_ballot(token_hash, signature, candidate)
```

### VoterClient
Handles voter-side cryptographic operations.

```python
from services.voter_client import VoterClient

client = VoterClient(public_key)
blinded_hash = client.blind_hash(message)
unblinded_sig = client.unblind_signature(blind_signature)
```

### VerifiableMixNet
Implements cryptographically verifiable vote mixing.

```python
from services.mixnet import VerifiableMixNet

mixnet = VerifiableMixNet(public_key)
mixed_votes, proof = mixnet.shuffle_and_prove(ballots)
```

## Database Schema

### voters
```
voter_id (PRIMARY KEY)
name TEXT
email TEXT UNIQUE
has_token BOOLEAN
has_voted BOOLEAN
registered_at TIMESTAMP
```

### tokens
```
token_id (PRIMARY KEY)
voter_id FOREIGN KEY
token_hash TEXT UNIQUE
created_at TIMESTAMP
used BOOLEAN
```

### ballots
```
ballot_id (PRIMARY KEY)
voter_id FOREIGN KEY
candidate TEXT
encrypted_vote TEXT
created_at TIMESTAMP
```

### tally_results
```
candidate TEXT PRIMARY KEY
vote_count INTEGER
percentage REAL
```

### logs
```
log_id (PRIMARY KEY)
user_email TEXT
action TEXT
timestamp TIMESTAMP
status TEXT (success/failed)
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Test coverage includes:
- RBAC enforcement and permission validation
- Repository operations with access control
- End-to-end voting workflows
- Cryptographic operations (RSA, blind signatures)
- Database access control policies

## Security Considerations

### Current Implementation
- ✅ Blind signatures for voter anonymity
- ✅ Role-based database access control
- ✅ OAuth 2.0 for authentication
- ✅ Comprehensive audit logging
- ✅ Vote encryption

### Production Recommendations
- 🔧 Use 2048+ bit RSA keys (currently 1024 for demo)
- 🔧 Implement HTTPS/TLS for all communications
- 🔧 Use proper certificate verification for OAuth
- 🔧 Add rate limiting and DDoS protection
- 🔧 Implement voter authentication with 2FA
- 🔧 Use enterprise-grade database (PostgreSQL) with full audit trails
- 🔧 Add hardware security modules (HSM) for key storage
- 🔧 Regular security audits and penetration testing

## Admin Panel Features

Access admin dashboard at `/pages/00_admin_login.py`:
- 📊 View voting statistics
- 👥 Manage registered voters
- 🗳️ Monitor ballot submissions
- 📋 Review audit logs
- 🔧 System configuration

## Pages Overview

| Page | Route | Purpose |
|------|-------|---------|
| Admin Login | 00_admin_login.py | Admin authentication |
| Registration | 01_registration.py | New voter registration |
| Request Token | 02_request_token.py | Blind signature request |
| Cast Vote | 03_cast_vote.py | Vote submission |
| Mix Network | 04_mixnet.py | Vote shuffling verification |
| Tally Results | 05_tally.py | View election results |
| Audit Logs | 06_logs.py | Review system logs |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Created as a demonstration of secure voting systems with cryptographic verification and role-based access control.

## Support

For issues, questions, or suggestions, please open an issue on GitHub or contact the project maintainers.

---

**Last Updated**: October 23, 2025
