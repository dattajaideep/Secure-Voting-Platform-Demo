# auth/oauth.py
import os
from dotenv import load_dotenv
from streamlit_oauth import OAuth2Component

# Load environment variables (Google credentials)
load_dotenv()

OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8501/auth/callback")

# OAuth URLs
OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Validate OAuth credentials
if not OAUTH_CLIENT_ID or not OAUTH_CLIENT_SECRET:
    raise ValueError("OAuth credentials (OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET) must be set in .env")

# Shared OAuth2Component instance (redirect_uri is handled in Streamlit config)
oauth2 = OAuth2Component(
    client_id=OAUTH_CLIENT_ID,
    client_secret=OAUTH_CLIENT_SECRET,
    authorize_endpoint=OAUTH_AUTHORIZE_URL,
    token_endpoint=OAUTH_TOKEN_URL
)

def get_oauth_config():
    """Return OAuth configuration"""
    return {
        'client_id': OAUTH_CLIENT_ID,
        'client_secret': OAUTH_CLIENT_SECRET,
        'redirect_uri': OAUTH_REDIRECT_URI,
        'scopes': ['openid', 'email', 'profile'],
        'auth_uri': OAUTH_AUTHORIZE_URL,
        'token_uri': OAUTH_TOKEN_URL
    }

def validate_oauth_config():
    """Validate OAuth config is complete"""
    try:
        get_oauth_config()
        return True
    except ValueError:
        return False