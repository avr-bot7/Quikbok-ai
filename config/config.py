import os
from dotenv import load_dotenv

load_dotenv(override=True)

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = {
        'GEMINI_API_KEY': 'Google Gemini API key for AI chat functionality',
        'SUPABASE_URL': 'Supabase database URL',
        'SUPABASE_KEY': 'Supabase database key',
        'SECRET_KEY': 'Flask secret key for session security',
        'TWILIO_ACCOUNT_SID': 'Twilio account SID for WhatsApp',
        'TWILIO_AUTH_TOKEN': 'Twilio auth token for WhatsApp',
        'TWILIO_WHATSAPP_FROM': 'Twilio WhatsApp number',
        'META_PHONE_NUMBER_ID': 'Meta WhatsApp Cloud Phone Number ID',
        'META_ACCESS_TOKEN': 'Meta WhatsApp Cloud Access Token'
    }
    
    missing_vars = []
    for var_name, description in required_vars.items():
        if not os.getenv(var_name):
            missing_vars.append(f"  - {var_name}: {description}")
    
    if missing_vars:
        print("\n" + "="*60)
        print("⚠️  WARNING: Missing Environment Variables")
        print("="*60)
        print("The following environment variables are not set:")
        print("\n".join(missing_vars))
        print("\nPlease set these variables in your .env file.")
        print("Some features may not work correctly without them.")
        print("="*60)
        print()
    else:
        print("✅ All required environment variables are set.")

class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM')
    META_PHONE_NUMBER_ID = os.getenv('META_PHONE_NUMBER_ID')
    META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
    META_WEBHOOK_VERIFY_TOKEN = os.getenv('META_WEBHOOK_VERIFY_TOKEN', 'quikbok_verify_token')
    SECRET_KEY = os.getenv('SECRET_KEY')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
