# Quikbok — AI Booking Agent

> 24/7 AI-powered booking assistant for small hotels, restaurants, and tour operators in Uttarakhand, India.

[![Live Demo](https://img.shields.io/badge/Live-Demo-6366F1?style=for-the-badge)](https://quikbok-ai.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3-000000?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com)

---

## What is Quikbok?

Small businesses in Rishikesh, Haridwar, and Dehradun miss booking requests every night because they can't reply to WhatsApp messages 24/7. Quikbok solves this with an AI agent that:

- Replies instantly to customers in **Hindi and English (Hinglish)**
- Collects name, date, service, and phone number through natural conversation
- Saves bookings to a dashboard automatically
- Sends the owner a **WhatsApp notification** for every new booking

---

## Features

- 🤖 **AI Chat Widget** — embed on any website with 1 line of code
- 🔗 **Booking Link** — shareable link for businesses without a website
- 📱 **WhatsApp Bot** — AI replies directly on the business WhatsApp number
- 📊 **Owner Dashboard** — view, confirm, and reject bookings
- 💳 **Razorpay Billing** — subscription-based payments with UPI support
- 🔒 **Secure** — password hashing, CSRF protection, rate limiting

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10 + Flask |
| AI | OpenRouter API (Google Gemini) |
| Database | Supabase (PostgreSQL) |
| Messaging | Twilio WhatsApp API |
| Payments | Razorpay |
| Frontend | HTML + Tailwind CSS + JavaScript |
| Deployment | Render |

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/avr-bot7/Quikbok-ai.git
cd Quikbok-ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Fill in your API keys in .env

# Run the app
python app.py
```

Open `http://localhost:5000` in your browser.

---

## Environment Variables

```env
OPENROUTER_API_KEY=your_openrouter_key
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=your_supabase_anon_key
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=your_secret
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
SECRET_KEY=your_flask_secret
BASE_URL=http://localhost:5000
```

See `.env.example` for the full list.

---

## Project Structure

```
quikbok/
├── app.py                  # Entry point
├── backend/
│   ├── routes/             # URL handlers (auth, chat, dashboard, payments)
│   ├── models/             # Database operations (Supabase + SQLite fallback)
│   └── services/           # External APIs (AI, WhatsApp, Payments)
├── frontend/
│   ├── templates/          # HTML pages (12 pages total)
│   └── static/             # CSS, JavaScript, chat widget
└── config/                 # App configuration
```

---

## Pages

| Page | Description |
|---|---|
| `/` | Landing page with live chat demo |
| `/signup` `/login` | Owner authentication |
| `/dashboard` | Bookings overview and management |
| `/dashboard/settings` | WhatsApp setup and embed code |
| `/book/<owner_id>` | Shareable booking link |
| `/demo` | Book a demo call |
| `/pricing` | Plans and billing |

---

## Database Schema

**Owners** — business accounts (id, email, password_hash, business_name, business_type, plan, whatsapp_number)

**Bookings** — booking records (id, owner_id → FK, customer_name, service, date, phone, status)

**Demo Requests** — lead capture (id, name, business_name, whatsapp_number, preferred_time)

---

## Built By

**Atharv Rajput** — B.Tech CSE, Gurukul Kangri University, Haridwar
- Backend development, AI integration, database design, deployment

**Teammate** — Research, testing, documentation, presentation

---

## License

© 2026 Quikbok. Built as a B.Tech college project.
