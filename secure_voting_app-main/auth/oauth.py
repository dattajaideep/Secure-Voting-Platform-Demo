# auth/oauth.py
import os
from dotenv import load_dotenv
from streamlit_oauth import OAuth2Component

# Load environment variables (Google credentials)
load_dotenv()
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")

# OAuth URLs
OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
OAUTH_REDIRECT_URI = "http://localhost:8501"

# Shared OAuth2Component instance
oauth2 = OAuth2Component(
    client_id=OAUTH_CLIENT_ID,
    client_secret=OAUTH_CLIENT_SECRET,
    authorize_endpoint=OAUTH_AUTHORIZE_URL,
    token_endpoint=OAUTH_TOKEN_URL
)
