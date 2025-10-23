# utils/otp_service.py
import smtplib
import random
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def generate_otp():
    """Generate a 6-digit OTP"""
    return random.randint(100000, 999999)


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
