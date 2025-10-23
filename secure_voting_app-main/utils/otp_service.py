# utils/otp_service.py
import smtplib
import random
import os
import pyotp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
OTP_ISSUER = os.getenv("OTP_ISSUER", "SecureVotingPlatform")
OTP_WINDOW = int(os.getenv("OTP_WINDOW", "1"))


def generate_otp():
    """Generate a 6-digit OTP"""
    return random.randint(100000, 999999)

def create_totp_secret(user_email: str) -> dict:
    """Create TOTP secret for user 2FA"""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user_email,
        issuer_name=OTP_ISSUER
    )
    return {
        'secret': secret,
        'provisioning_uri': provisioning_uri
    }

def verify_totp(secret: str, token: str) -> bool:
    """Verify TOTP token"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=OTP_WINDOW)

def get_current_totp(secret: str) -> str:
    """Get current TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.now()

def send_otp_email(recipient_email, otp):
    """Send OTP via Gmail SMTP"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = 'Secure Voting System - Your OTP Code'
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Secure Voting System</h2>
            <p>Your One-Time Password (OTP) is:</p>
            <h1 style="color: #4CAF50; font-size: 32px;">{otp}</h1>
            <p>This OTP is valid for 5 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
    
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return False
