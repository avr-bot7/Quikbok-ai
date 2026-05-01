# Quikbok Project Structure

This document explains how the Quikbok project is organized in simple terms for beginners.

## 📁 Folder Structure

```
quikbok/
├── frontend/          ← Everything users see and interact with
│   ├── templates/     ← HTML files (web pages)
│   └── static/        ← CSS, JavaScript, and images
│       ├── css/       ← Style files for making pages look good
│       ├── js/        ← JavaScript files for interactive features
│       └── images/    ← Pictures and graphics
├── backend/           ← All Python server code (the "brain")
│   ├── routes/        ← URL handlers (what happens when you visit a page)
│   ├── models/        ← Database functions (saving and getting data)
│   └── services/      ← External API connections (AI, WhatsApp, Payments)
├── config/            ← Configuration files
│   ├── config.py      ← App settings and environment variables
│   └── .env           ← Secret keys and passwords
├── docs/              ← Documentation (like this file)
│   ├── README.md      ← Main project documentation
│   ├── API.md         ← API documentation
│   └── STRUCTURE.md   ← This file - project structure explanation
├── tests/             ← Testing files
│   └── verify_suite.py ← Tests to make sure everything works
└── app.py             ← Main entry point (starts the application)
```

## 🎯 What Each Folder Does

### **frontend/** - The User Interface
This is everything the user sees in their web browser.

- **templates/**: HTML files that create the web pages
  - `index.html` - Main landing page
  - `dashboard.html` - User dashboard
  - `login.html`, `signup.html` - Authentication pages
  - `settings.html` - User settings page

- **static/**: Files that make the pages look good and work
  - **css/**: Style sheets for colors, fonts, layout
  - **js/**: JavaScript for interactive features like the chat widget
  - **images/**: Logos, icons, and other graphics

### **backend/** - The Server Logic
This is the "brain" of the application that runs on the server.

- **routes/**: Handle what happens when users visit different URLs
  - `auth.py` - Login, signup, logout
  - `chat.py` - Chat API for the AI assistant
  - `dashboard.py` - Dashboard page logic
  - `payment.py` - Payment processing
  - `webhook.py` - External service notifications

- **models/**: Database operations
  - `database.py` - Functions to save and get data from Supabase
  - Handles users, bookings, and other data

- **services/**: Connections to external services
  - `ai_service.py` - Google Gemini AI integration
  - `payment.py` - Razorpay payment processing
  - `whatsapp.py` - WhatsApp messaging (Twilio and Meta)

### **config/** - Settings and Secrets
- **config.py**: Application settings and configuration
- **.env**: Secret keys, API keys, database passwords (never share this file!)

### **docs/** - Documentation
- **README.md**: Main project documentation
- **API.md**: Technical API documentation
- **STRUCTURE.md**: This file explaining the project structure

### **tests/** - Quality Assurance
- **verify_suite.py**: Tests to make sure everything works correctly
- **test_*.py**: Various test files for different features

### **app.py** - The Starting Point
This is the main file that starts the entire application. It:
- Sets up the Flask web server
- Connects all the different parts
- Registers all the routes (URL handlers)

## 🔗 How It All Works Together

1. **User visits a website** → **frontend/templates** shows the HTML page
2. **User clicks something** → **frontend/static/js** handles the interaction
3. **JavaScript sends request** → **backend/routes** receives and processes it
4. **Route needs data** → **backend/models** gets/saves from database
5. **Route needs AI help** → **backend/services** talks to external APIs
6. **Response goes back** → **frontend/templates** updates the page

## 🛠️ Development Workflow

When you want to add a new feature:

1. **Frontend**: Add HTML to `frontend/templates/` and CSS/JS to `frontend/static/`
2. **Backend**: Add route logic to `backend/routes/`
3. **Database**: Add data functions to `backend/models/`
4. **External APIs**: Add service code to `backend/services/`
5. **Configuration**: Update `config/config.py` if needed
6. **Testing**: Add tests to `tests/`

## 📝 Import Paths

Because of the new structure, Python imports look like this:

```python
# Old way (before reorganization)
from models.database import get_user
from services.ai_service import BookingAgent
from routes.auth import login_required

# New way (after reorganization)
from backend.models.database import get_user
from backend.services.ai_service import BookingAgent
from backend.routes.auth import login_required
```

## 🚀 Running the Application

1. Make sure you're in the `quikbok/` folder
2. Run: `python app.py`
3. Open your browser to: `http://localhost:5000`

The app will automatically find templates in `frontend/templates/` and static files in `frontend/static/`.

## 💡 Tips for Beginners

- **Start with frontend**: Look at `frontend/templates/` to understand the user interface
- **Then backend**: Check `backend/routes/` to see how pages work
- **Database**: Look at `backend/models/database.py` for data operations
- **Configuration**: Check `config/config.py` for settings
- **Testing**: Run files in `tests/` to verify everything works

This structure makes it easy to find what you're looking for and keeps related code together!
