# ============================================================================
# Standard Library Imports
# ============================================================================
import os
import sys
import secrets
from datetime import timedelta
from traceback import format_exc

# ============================================================================
# Third-Party Imports
# ============================================================================
from flask import Flask, render_template, session, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

# ============================================================================
# Local Imports
# ============================================================================
from config.config import Config
from backend.routes.auth import auth_bp
from backend.routes.chat import chat_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.webhook import webhook_bp
from backend.routes.payment import payment_bp
from backend.routes.whatsapp_cloud import whatsapp_cloud_bp
from backend.models.database import get_first_owner, create_demo_request
from backend.services.ai_service import BookingAgent

# ============================================================================
# Avoid Windows console UnicodeEncodeError when printing Gemini output (Hindi/emoji).
# ============================================================================
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

# ============================================================================
# Flask App Initialization
# ============================================================================
app = Flask(__name__, 
           template_folder='frontend/templates',
           static_folder='frontend/static')
app.config.from_object(Config)
CORS(app, resources={r"/chat*": {"origins": "*"}})

# ============================================================================
# Secret Key Fallback Setup
# ============================================================================
# Ensure `SECRET_KEY` is available for sessions/CSRF. If it's missing, generate
# a temporary key for demo purposes and warn (do NOT use this in production).
secret = getattr(Config, 'SECRET_KEY', None) or os.getenv('SECRET_KEY')
if not secret:
    temp_secret = secrets.token_urlsafe(32)
    print('Warning: SECRET_KEY not set. Using temporary secret for sessions/CSRF (demo only).')
    app.secret_key = temp_secret
else:
    app.secret_key = secret

# ============================================================================
# CSRF Protection Initialization
# ============================================================================
csrf = CSRFProtect(app)

# ============================================================================
# Configure Session Timeout
# ============================================================================
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# ============================================================================
# Initialize Rate Limiter
# ============================================================================
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# ============================================================================
# Register Blueprints
# ============================================================================
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(webhook_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(whatsapp_cloud_bp)

# ============================================================================
# CSRF Exemptions (after blueprint registration)
# ============================================================================
# Exempt chat blueprint from CSRF protection (API endpoint)
csrf.exempt(chat_bp)

# Exempt webhook blueprint from CSRF protection (API endpoint)
csrf.exempt(webhook_bp)

# Exempt payment blueprint from CSRF protection (API endpoint; called via fetch/JSON)
csrf.exempt(payment_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/demo', methods=['GET', 'POST'])
def demo():
    print(f"\n=== DEMO ROUTE ACCESS ===")
    print(f"Method: {request.method}")
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            business_name = request.form.get('business_name')
            whatsapp_number = request.form.get('whatsapp_number')
            business_type = request.form.get('business_type')
            preferred_time = request.form.get('preferred_time')
            
            print(f"📝 Demo Request Data:")
            print(f"  Name: {name}")
            print(f"  Business: {business_name}")
            print(f"  WhatsApp: {whatsapp_number}")
            print(f"  Type: {business_type}")
            print(f"  Time: {preferred_time}")
            
            # Save to Supabase
            create_demo_request(name, business_name, whatsapp_number, business_type, preferred_time)
            
            print("✅ Demo request saved successfully")
            return render_template('demo_thankyou.html')
        except Exception as e:
            print(f"❌ Error saving demo request: {type(e).__name__}: {str(e)}")
            print(f"Full traceback: {format_exc()}")
            return render_template('demo.html', error="Failed to submit request. Please try again.")
    
    return render_template('demo.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.tailwindcss.com; connect-src 'self';"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
