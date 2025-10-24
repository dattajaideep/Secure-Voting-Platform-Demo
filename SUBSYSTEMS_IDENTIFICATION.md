# Subsystems Identification - Secure Voting Platform Demo

**Date**: October 24, 2025  
**Project**: Secure Voting Platform Demo  
**Status**: Architecture Analysis Complete  

---

## 📋 Overview

This document clearly identifies the **major subsystems** that comprise the Secure Voting Platform. The platform is a **cryptographically-secure voting system** built with Streamlit, implementing privacy-preserving vote transmission and tallying.

The system is organized into **6 major subsystems** with clearly defined responsibilities:

---

## 🏗️ Major Subsystems

### **1. AUTHENTICATION & AUTHORIZATION SUBSYSTEM** 
📁 Location: `auth/`, `utils/roles.py`, `utils/session_manager.py`, `utils/auth_security.py`

**Purpose**: Handle user authentication, session management, and role-based access control

**Components**:
- `auth/oauth.py` - OAuth2 integration (Google, OAuth providers)
- `utils/roles.py` - Role definitions and access control checks
- `utils/session_manager.py` - Session lifecycle management with timeouts
- `utils/auth_security.py` - Security utilities for password handling

**Key Responsibilities**:
- Authenticate users via OAuth2 or email+OTP
- Manage user sessions with timeout protection
- Enforce role-based access (admin vs. voter)
- Track login attempts and failed authentications
- Clear sessions on logout or timeout

**Interfaces**:
```python
is_admin()              # Check if user has admin role
is_logged_in()          # Check if session is active
get_user_role()         # Get user's current role
require_roles(roles)    # Decorator for role enforcement
check_session_timeout() # Validate session timeout
update_last_activity()  # Update session activity timestamp
```

---

### **2. CRYPTOGRAPHY SUBSYSTEM**
📁 Location: `crypto/` directory

**Purpose**: Provide all cryptographic operations for secure vote transmission and verification

**Components**:
- `crypto/__init__.py` - Module initialization
- `crypto/encryption.py` - RSA encryption/decryption for ballots
- `crypto/hashing.py` - Secure hashing (ballot verification)
- `crypto/rng.py` - Cryptographically secure random number generation
- `crypto/rsa.py` - RSA key generation and management

**Key Responsibilities**:
- Generate cryptographic keys (RSA public/private pairs)
- Encrypt ballots for secure transmission
- Decrypt ballots for tallying
- Create cryptographic hashes for verification
- Generate secure random values for blind tokens

**Interfaces**:
```python
from crypto.encryption import encrypt_ballot, decrypt_ballot
from crypto.rsa import generate_keypair, RSAKeyManager
from crypto.hashing import hash_ballot, verify_hash
from crypto.rng import generate_secure_random
```

**Key Feature**: Enables **end-to-end encryption** ensuring vote confidentiality

---

### **3. DATABASE & PERSISTENCE SUBSYSTEM**
📁 Location: `db/` directory

**Purpose**: Handle all data persistence, repository patterns, and database operations

**Components**:
- `db/connection.py` - Database connection management (SQLite)
- `db/init_db.py` - Database initialization and schema setup
- `db/access_control.py` - Row-level access control and data filtering
- `db/sanitize_db.py` - Database sanitization utilities
- `db/repositories/` - Repository pattern implementations:
  - `voter_repository.py` - Voter CRUD operations
  - `ballot_repository.py` - Ballot storage and retrieval
  - `encrypted_ballot_repository.py` - Encrypted ballot handling
  - `log_repository.py` - Audit log storage
  - `login_attempt_repository.py` - Failed login tracking
  - `mixnet_repository.py` - Mix network state
  - `token_repository.py` - Token management

**Key Responsibilities**:
- Initialize and maintain SQLite database schema
- Provide CRUD operations for all entities
- Enforce row-level access control
- Prevent SQL injection through parameterized queries
- Log all operations for audit trail
- Sanitize user inputs

**Interfaces**:
```python
# Each repository follows this pattern:
class VoterRepository:
    def add_voter(voter_id, name)
    def get_all_voters()
    def get_voter_by_email(email)
    def update_vote_status(email, voted)
    def has_voter_voted(voter_id)
    # ... etc

class BallotRepository:
    def store_ballot(voter_id, encrypted_ballot, signature)
    def get_ballot(ballot_id)
    def get_all_ballots()
    # ... etc
```

---

### **4. VOTING SERVICES SUBSYSTEM**
📁 Location: `services/` directory

**Purpose**: Implement the core voting business logic and protocols

**Components**:
- `services/voting_authority.py` - Voting authority orchestration
- `services/voter_client.py` - Client-side voter operations
- `services/mixnet.py` - Mix network for anonymous shuffling
- `services/vote_transmission.py` - Secure vote transmission
- `services/secure_rsa.py` - RSA operations wrapper

**Key Responsibilities**:
- Issue blind tokens to voters
- Accept encrypted votes
- Execute mix network protocol for anonymization
- Tally encrypted votes
- Generate voting authority signatures
- Manage vote transmission protocol

**Key Protocols**:
- **Blind Token Protocol**: Voter receives unblinded token for voting
- **Mix Network**: Shuffles and decrypts votes anonymously
- **RSA Encryption**: Secures ballot transmission

**Interfaces**:
```python
class VotingAuthority:
    def setup_authority()
    def issue_blind_token(voter_id)
    def accept_ballot(encrypted_ballot)
    def tally_votes()

class VoterClient:
    def create_blind_token(voter_id)
    def encrypt_vote(vote, authority_pubkey)
    def submit_vote(encrypted_vote, token)

class VerifiableMixNet:
    def shuffle_ballots(ballots)
    def decrypt_ballots(encrypted_ballots, private_key)
    def verify_mix_correctness()
```

---

### **5. DATA PRIVACY & MASKING SUBSYSTEM**
📁 Location: `utils/data_masking.py`, `utils/password_utils.py`, `utils/password_validator.py`

**Purpose**: Protect sensitive user data and enforce privacy policies

**Components**:
- `utils/data_masking.py` - Email and PII masking
- `utils/password_utils.py` - Password hashing and validation
- `utils/password_validator.py` - Password strength validation
- `utils/validation.py` - Data validation utilities

**Key Responsibilities**:
- Mask voter emails by default (display as "XXXXXX")
- Allow voters to unmask only their own data
- Prevent voter enumeration attacks
- Validate and hash passwords securely
- Enforce password strength requirements
- Validate user input before processing

**Key Features**:
- **Default Masking**: All emails hidden by default
- **Voter-Controlled Unmasking**: Voters control when to reveal their own email
- **Privacy-Preserving**: No information disclosure to unauthorized parties

**Interfaces**:
```python
from utils.data_masking import (
    mask_email,                          # XXXXXX
    mask_list,                           # Mask list of voters
    can_voter_unmask_own_data,          # Permission check
    filter_voter_data,                   # Apply masking filters
    mask_voter_for_self                 # Self-view masking
)
```

---

### **6. USER INTERFACE & PRESENTATION SUBSYSTEM**
📁 Location: `pages/` directory, `streamlit_app.py`, `utils/logger.py`

**Purpose**: Present the voting interface and coordinate user interactions

**Components**:
- `streamlit_app.py` - Main application entry point and home page
- `pages/00_admin_login.py` - Admin authentication page
- `pages/01_registration.py` - Voter registration and login page
- `pages/02_request_token.py` - Blind token request interface
- `pages/03_cast_vote.py` - Vote submission interface
- `pages/04_mixnet.py` - Mix network visualization
- `pages/05_tally.py` - Results tallying and display
- `pages/06_logs.py` - Audit log viewer
- `utils/logger.py` - Logging and audit trail

**Key Responsibilities**:
- Provide user-friendly interfaces for voting workflow
- Display voting authority and results
- Show audit logs and system state
- Enforce UI-level validation and guidance
- Log all user actions for audit trail
- Implement responsive error handling

**Pages Overview**:
```
├── 00_admin_login      → Admin authentication
├── 01_registration    → Voter access portal (register/login)
├── 02_request_token   → Request blind token
├── 03_cast_vote       → Cast encrypted vote
├── 04_mixnet          → Mix network process
├── 05_tally           → View results
└── 06_logs            → Audit logs
```

---

## 🔗 Subsystem Interactions

```
┌──────────────────────────────────────────────────────────────┐
│                  USER INTERFACE SUBSYSTEM (Pages)             │
│                  (00_registration, 02_token, etc)             │
└──────────────────┬───────────────────────────────────────────┘
                   │ uses
                   ↓
        ┌──────────────────────────┐
        │   AUTHENTICATION         │ ← Session & roles
        │   SUBSYSTEM              │
        └──────────────────────────┘
                   │ uses
                   ↓
┌──────────┬───────────────────────────────────────────┬──────────┐
│         │                                           │          │
↓         ↓                                           ↓          ↓
DATABASE  CRYPTOGRAPHY  ← VOTING SERVICES ←   DATA     LOGGING
SUBSYSTEM SUBSYSTEM       SUBSYSTEM         MASKING    
          (encryption,    (authorities,     SUBSYSTEM  (audit)
          hashing)        tokens, mix)      (privacy)
│         │                                           │          │
└──────────┴───────────────────────────────────────────┴──────────┘
                   ↓ coordinates all
           ┌───────────────────────┐
           │  Voting Protocol Flow  │
           │  (from page 1 → 6)     │
           └───────────────────────┘
```

### **Example: Voter Casting a Vote**

1. **UI Subsystem** → Voter clicks "Cast Vote" on page 03
2. **Authentication Subsystem** → Verifies voter is logged in with correct role
3. **Data Masking Subsystem** → Shows masked email (unless voter unmasks)
4. **Cryptography Subsystem** → Encrypts vote with voting authority's public key
5. **Voting Services Subsystem** → Signs encrypted vote, creates ballot
6. **Database Subsystem** → Stores encrypted ballot and marks voter as voted
7. **Logging Subsystem** → Records action for audit trail
8. **UI Subsystem** → Displays success, triggers auto-logout

---

## 📊 Subsystem Characteristics

| Subsystem | Type | Scope | Criticality |
|-----------|------|-------|------------|
| Authentication & Authorization | Security | Cross-system | **CRITICAL** |
| Cryptography | Core | Vote Security | **CRITICAL** |
| Database & Persistence | Infrastructure | Data Management | **CRITICAL** |
| Voting Services | Business Logic | Protocol Execution | **CRITICAL** |
| Data Privacy & Masking | Security | PII Protection | **HIGH** |
| UI & Presentation | User-Facing | Interaction Layer | **HIGH** |

---

## 🔐 Security Considerations

### Per-Subsystem Security:

**Authentication Subsystem**:
- Prevents unauthorized access to voting pages
- Enforces one-vote-per-voter
- Tracks failed login attempts
- Implements session timeouts

**Cryptography Subsystem**:
- Ensures vote confidentiality through encryption
- Prevents vote tampering through hashing
- Uses cryptographically secure random numbers
- Implements RSA key management

**Database Subsystem**:
- Uses parameterized queries (SQL injection prevention)
- Implements row-level access control
- Logs all database operations
- Enforces referential integrity

**Voting Services Subsystem**:
- Implements blind token protocol
- Enforces mix network anonymization
- Prevents vote linkage
- Validates all cryptographic signatures

**Privacy Subsystem**:
- Masks PII by default
- Prevents voter enumeration
- Validates password strength
- Sanitizes user input

**UI Subsystem**:
- Implements login checks before sensitive pages
- Shows informative error messages without data disclosure
- Auto-logout after voting
- Provides audit log visibility

---

## 📈 System Architecture Summary

```
LAYERS:
┌─────────────────────────────────────────────────────┐
│   Presentation Layer (Streamlit UI Pages)           │
│   → User Interaction & Workflow                     │
├─────────────────────────────────────────────────────┤
│   Business Logic Layer (Voting Services)             │
│   → Voting Protocol, Blind Tokens, Mix Network      │
├─────────────────────────────────────────────────────┤
│   Security & Privacy Layer                          │
│   → Authentication, Cryptography, Data Masking      │
├─────────────────────────────────────────────────────┤
│   Data Layer (Repositories & Database)              │
│   → CRUD Operations, Data Persistence               │
├─────────────────────────────────────────────────────┤
│   Infrastructure Layer (Logging, Utilities)         │
│   → Audit Trail, Validation, Common Utilities       │
└─────────────────────────────────────────────────────┘

CROSS-CUTTING CONCERNS:
• Session Management (Authentication)
• Data Masking (Privacy)
• Audit Logging (Compliance)
• Error Handling (Reliability)
```

---

## 🎯 Subsystem Dependencies

```
UI Subsystem
    ↓ depends on
Authentication Subsystem
    ↓ depends on (session validation)
├─ Database Subsystem (user lookup)
├─ Privacy Subsystem (role checking)
└─ Logging Subsystem (audit trail)

Voting Services Subsystem
    ↓ depends on
├─ Cryptography Subsystem (RSA, hashing)
├─ Database Subsystem (storage)
├─ Authentication Subsystem (voter verification)
└─ Logging Subsystem (audit trail)

Database Subsystem
    ↓ uses
├─ Privacy Subsystem (masking filters)
├─ Logging Subsystem (operation logging)
└─ Utilities (validation, sanitization)
```

---

## 📝 Files Per Subsystem

### **Authentication & Authorization** (4 files)
```
auth/oauth.py
utils/roles.py
utils/session_manager.py
utils/auth_security.py
```

### **Cryptography** (5 files)
```
crypto/__init__.py
crypto/encryption.py
crypto/hashing.py
crypto/rng.py
crypto/rsa.py
```

### **Database & Persistence** (8 files)
```
db/__init__.py
db/connection.py
db/init_db.py
db/access_control.py
db/sanitize_db.py
db/repositories/__init__.py
db/repositories/voter_repository.py
db/repositories/ballot_repository.py
db/repositories/encrypted_ballot_repository.py
db/repositories/log_repository.py
db/repositories/login_attempt_repository.py
db/repositories/mixnet_repository.py
db/repositories/token_repository.py
```

### **Voting Services** (5 files)
```
services/__init__.py
services/voting_authority.py
services/voter_client.py
services/mixnet.py
services/vote_transmission.py
services/secure_rsa.py
```

### **Data Privacy & Masking** (3 files)
```
utils/data_masking.py
utils/password_utils.py
utils/password_validator.py
```

### **UI & Presentation** (9 files)
```
streamlit_app.py
pages/00_admin_login.py
pages/01_registration.py
pages/02_request_token.py
pages/03_cast_vote.py
pages/04_mixnet.py
pages/05_tally.py
pages/06_logs.py
utils/logger.py
```

---

## ✅ Subsystems Verification

- [x] **Authentication & Authorization** - Clearly defined, separate module
- [x] **Cryptography** - Dedicated `crypto/` subsystem with specialized files
- [x] **Database & Persistence** - Complete repository pattern implementation
- [x] **Voting Services** - Business logic isolated in `services/` directory
- [x] **Data Privacy & Masking** - Dedicated utilities for PII protection
- [x] **UI & Presentation** - Streamlit pages with clear responsibility separation

---

## 🎓 Key Takeaways

This Secure Voting Platform is architectured as a **layered system with 6 clear subsystems**:

1. **Authentication & Authorization** - Controls access and roles
2. **Cryptography** - Secures votes and prevents tampering
3. **Database & Persistence** - Manages all data storage
4. **Voting Services** - Implements voting protocols and algorithms
5. **Data Privacy & Masking** - Protects voter information
6. **UI & Presentation** - Provides user interface and workflow

Each subsystem has:
- ✅ Clear responsibility boundaries
- ✅ Defined interfaces/interactions
- ✅ Localized file structure
- ✅ Security-focused design
- ✅ Test coverage

---

**Document Version**: 1.0  
**Status**: ✅ Complete  
**Date**: October 24, 2025
