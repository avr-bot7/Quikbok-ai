# Quikbok - AI Booking Agent

Quikbok is an AI-powered booking platform that enables businesses to automate customer bookings through WhatsApp and web interfaces.

## Features

- 🤖 **AI-Powered Chat**: Intelligent conversation-based booking system
- 💬 **WhatsApp Integration**: Automated booking via WhatsApp
- 📊 **Dashboard**: Complete booking management interface
- 💳 **Payment Processing**: Integrated payment gateway (Razorpay)
- 📱 **Mobile Responsive**: Works on all devices
- 🔔 **Real-time Notifications**: Instant booking alerts

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Payments**: Razorpay
- **Messaging**: Twilio WhatsApp
- **AI**: OpenAI GPT

## Installation

1. Clone the repository
```bash
git clone <repository-url>
cd quikbok
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. Run the application
```bash
python app.py
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key

# Payments
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# WhatsApp
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Flask
SECRET_KEY=your_secret_key
BASE_URL=http://localhost:5000
```

## Database Schema

### Owners Table
- `id` (UUID, Primary Key)
- `email` (Text, Unique)
- `name` (Text)
- `business_name` (Text)
- `business_type` (Text)
- `plan` (Text)
- `is_active` (Boolean)
- `password_hash` (Text)
- `ai_instructions` (Text)
- `whatsapp_number` (Text)
- `created_at` (Timestamp)

### Bookings Table
- `id` (UUID, Primary Key)
- `owner_id` (UUID, Foreign Key)
- `customer_name` (Text)
- `customer_phone` (Text)
- `service` (Text)
- `date` (Text)
- `status` (Text)
- `created_at` (Timestamp)

### Demo Requests Table
The **demo_requests table** stores demo booking requests:
- `id` (UUID, Primary Key)
- `name` (Text) - Contact person name
- `business_name` (Text) - Business name
- `whatsapp_number` (Text) - Contact WhatsApp number
- `business_type` (Text) - Type of business
- `preferred_time` (Text) - Preferred call time
- `created_at` (Timestamp) - Request submission time

## Setup Instructions

### 1. Database Setup

Create the following tables in your Supabase database:

```sql
-- Owners table
CREATE TABLE Owners (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    business_name TEXT,
    business_type TEXT,
    plan TEXT DEFAULT 'free',
    is_active BOOLEAN DEFAULT false,
    password_hash TEXT NOT NULL,
    ai_instructions TEXT,
    whatsapp_number TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bookings table
CREATE TABLE bookings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    owner_id UUID REFERENCES Owners(id),
    customer_name TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    service TEXT NOT NULL,
    date TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Demo requests table
CREATE TABLE demo_requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    business_name TEXT NOT NULL,
    whatsapp_number TEXT NOT NULL,
    business_type TEXT NOT NULL,
    preferred_time TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. WhatsApp Integration

1. Create a Twilio account
2. Activate WhatsApp sandbox
3. Add your Twilio credentials to `.env`
4. Configure webhook URL in Twilio: `https://yourdomain.com/webhook/twilio`

### 3. Payment Integration

1. Create a Razorpay account
2. Add your Razorpay keys to `.env`
3. Configure webhook URL in Razorpay: `https://yourdomain.com/webhook/razorpay`

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /signup` - User registration
- `POST /logout` - User logout

### Dashboard
- `GET /dashboard` - Main dashboard
- `GET /dashboard/settings` - Settings page
- `POST /dashboard/settings` - Update settings
- `POST /dashboard/booking/update-status` - Update booking status

### Chat & Booking
- `POST /chat` - AI chat endpoint
- `GET /widget/<owner_id>` - Chat widget
- `GET /book/<owner_id>` - Standalone booking page
- `POST /book/complete` - Complete booking

### Webhooks
- `POST /webhook/twilio` - Twilio WhatsApp webhook
- `POST /webhook/razorpay` - Razorpay payment webhook

### Demo
- `GET /demo` - Demo request form
- `POST /demo` - Submit demo request

### Legal
- `GET /privacy` - Privacy policy
- `GET /terms` - Terms of service

## Usage

### For Business Owners

1. **Sign up** for an account
2. **Configure** your business details and AI instructions
3. **Set up** WhatsApp integration (optional)
4. **Share** your booking link with customers
5. **Manage** bookings through the dashboard

### For Customers

1. **Visit** the business's booking link
2. **Chat** with the AI assistant
3. **Provide** booking details
4. **Confirm** and pay (if required)
5. **Receive** confirmation via WhatsApp

## Development

### Running Tests
```bash
python test_booking.py
python test_twilio_webhook.py
```

### Adding New Features
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

## Security

- CSRF protection enabled
- Password hashing with bcrypt
- Input validation and sanitization
- Secure session management
- HTTPS enforcement in production

## Legal & Compliance

- **Privacy Policy**: Available at `/privacy`
- **Terms of Service**: Available at `/terms`
- **Indian IT Act Compliance**: Data protection measures implemented
- **GDPR Considerations**: User data rights and deletion procedures


## License

© 2026 Quikbok Inc. All rights reserved.
