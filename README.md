# Secure Voting Platform Demo

A secure, privacy-preserving voting platform built with Streamlit, implementing cryptographic protocols for secure vote transmission and tallying.

## Project Structure

```
├── app/                     # Main application
│   ├── streamlit_app.py    # Entry point
│   ├── auth/               # Authentication modules
│   ├── crypto/             # Cryptographic operations
│   ├── db/                 # Database layer
│   ├── pages/              # Streamlit pages
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions
│   └── tests/              # Test suite
├── config/                 # Configuration files
├── docs/                   # Documentation
└── requirements.txt        # Python dependencies
```

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app/streamlit_app.py
```

### Running Tests
```bash
pytest app/tests/
```

## Key Features

- **Secure Vote Transmission**: RSA encryption for vote confidentiality
- **Mix Network**: Anonymous vote shuffling
- **Role-Based Access Control**: Admin and voter roles
- **Data Masking**: Privacy protection for voter data
- **Session Management**: Secure session handling with timeouts
- **One Vote Per Voter**: Ensures voting integrity
- **Audit Logs**: Comprehensive logging for compliance

## Architecture

### Authentication & Authorization
- OAuth2 integration for user authentication
- Role-based access control (RBAC)
- Session management with timeout

### Cryptography
- RSA encryption for ballot transmission
- Secure random number generation
- Data hashing and validation

### Database
- SQLite with parameterized queries
- Voter repository
- Ballot repository
- Log repository
- Token repository

### Services
- Voting Authority: Manages voting process
- Voter Client: Handles voter interactions
- Mix Network: Anonymous vote shuffling
- Vote Transmission: Secure vote delivery

## Documentation

See the `docs/` folder for detailed documentation on:
- Architecture and design
- API reference
- Implementation details
- Security considerations

## Development

### Project Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running with Streamlit
```bash
streamlit run app/streamlit_app.py
```

### Running Tests
```bash
pytest app/tests/ -v
pytest app/tests/ --cov=app
```

## Contributing

Please ensure all tests pass before submitting changes:
```bash
pytest app/tests/
flake8 app/
```

## License

See LICENSE file for details.
