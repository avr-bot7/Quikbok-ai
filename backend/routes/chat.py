from flask import Blueprint, request, jsonify, render_template, make_response, current_app
from flask_cors import cross_origin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.services.ai_service import BookingAgent
from backend.models.database import get_owner_by_id, create_booking, normalize_owner_id, owner_exists
import traceback
import re
import os

chat_bp = Blueprint('chat', __name__)
agent = BookingAgent()

# Initialize limiter for chat blueprint
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30 per minute"]
)

def format_booking_response(business_type: str, booking_details: dict) -> str:
    """Format booking details as clean plain-text structured output."""
    if not booking_details:
        return None
    
    business_type = str(business_type or "").strip().lower().replace("-", "_").replace(" ", "_")
    name = booking_details.get('name', '')
    date = booking_details.get('date', '')
    service = booking_details.get('service', '')
    phone = booking_details.get('phone', '')
    
    lines = []
    
    if business_type in {"hotel", "resort", "stay", "lodging"}:
        # Parse hotel details: date is "check_in to check_out", service is "Room booking: X | Guests: Y"
        dates = date.split(" to ") if " to " in date else [date, date]
        check_in = dates[0].strip() if len(dates) > 0 else date
        check_out = dates[1].strip() if len(dates) > 1 else date
        
        # Extract room type and guests from service
        room_type = ""
        guests = ""
        if "Room booking:" in service:
            parts = service.split("|")
            if len(parts) > 0:
                room_type = parts[0].replace("Room booking:", "").strip()
            if len(parts) > 1:
                guests_part = parts[1].strip()
                guests = guests_part.replace("Guests:", "").strip()
        
        lines.append(f"Name: {name}")
        lines.append(f"Check-in: {check_in}")
        lines.append(f"Check-out: {check_out}")
        if room_type:
            lines.append(f"Room: {room_type}")
        if guests:
            lines.append(f"Guests: {guests}")
        lines.append(f"Phone: {phone}")
        
    elif business_type in {"restaurant", "cafe", "dining", "food"}:
        # Parse restaurant details: date is "date time", service is "Table reservation for X people"
        people = ""
        if "Table reservation for" in service:
            match = re.search(r"Table reservation for (\d+)", service)
            if match:
                people = match.group(1)
        
        lines.append(f"Name: {name}")
        lines.append(f"Date & Time: {date}")
        if people:
            lines.append(f"People: {people}")
        lines.append(f"Phone: {phone}")
        
    elif business_type in {"tour_guide", "tour_operator", "tourguide", "touroperator", "tour", "travel"}:
        # Parse tour details: date is just date, service is "Tour booking: X | People: Y"
        tour_type = ""
        people = ""
        if "Tour booking:" in service:
            parts = service.split("|")
            if len(parts) > 0:
                tour_type = parts[0].replace("Tour booking:", "").strip()
            if len(parts) > 1:
                people_part = parts[1].strip()
                people = people_part.replace("People:", "").strip()
        
        lines.append(f"Name: {name}")
        if tour_type:
            lines.append(f"Tour: {tour_type}")
        lines.append(f"Date: {date}")
        if people:
            lines.append(f"People: {people}")
        lines.append(f"Phone: {phone}")
        
    else:
        # Other/generic format
        lines.append(f"Name: {name}")
        lines.append(f"Date: {date}")
        if service:
            lines.append(f"Service: {service}")
        lines.append(f"Phone: {phone}")
    
    # Add the closing message
    lines.append("")
    lines.append("Booking request received.")
    
    return "\n".join(lines)

def save_booking_if_complete(owner_id, ai_reply, can_save: bool):
    """Check if AI reply contains a BOOKING_COMPLETE marker. If so, save to DB."""
    details = agent.detect_booking_complete(ai_reply)
    if details:
        if not can_save:
            print(f"BOOKING_COMPLETE received but saving is disabled (owner_id={owner_id!r})")
            return None
        oid = normalize_owner_id(owner_id)
        if not oid:
            print(f"BOOKING_COMPLETE but no owner_id — not saving: {details}")
            return None
        try:
            create_booking(
                oid,
                details.get('name'),
                details.get('service'),
                details.get('date'),
                details.get('phone')
            )
            print(f"BOOKING SAVED: {details}")
            return details
        except Exception as e:
            print(f"Error saving booking: {e}")
    return None

@chat_bp.route('/chat', methods=['POST'])
@cross_origin()
@limiter.limit("30 per minute")
def chat():
    print(f"\n=== CHAT ROUTE ACCESS ===")
    print(f"Request data: {request.get_json()}")
    
    try:
        data = request.get_json() or {}
        owner_id = normalize_owner_id(data.get('owner_id'))
        message = data.get('message')
        conversation_history = data.get('conversation_history', [])
        if not isinstance(conversation_history, list):
            print("conversation_history payload is not a list; defaulting to empty list")
            conversation_history = []
        
        print(f"📝 Chat Request:")
        print(f"  Owner ID: {owner_id}")
        print(f"  Message: {message}")
        print(f"  History length: {len(conversation_history)}")
        for idx, item in enumerate(conversation_history, start=1):
            if isinstance(item, dict):
                role = item.get("role")
                content = item.get("content")
            else:
                role = "unknown"
                content = str(item)
            print(f"  History[{idx:02d}] role={role} content={content}")

        # Fetch owner details from DB for secure prompt construction
        business_name = 'Hotel Demo Rishikesh'
        business_type = 'hotel'
        can_save = False
        if owner_id and owner_id != 'demo':
            owner = get_owner_by_id(owner_id)
            if owner:
                business_name = owner.get('business_name', business_name)
                business_type = owner.get('business_type', business_type)
                can_save = True
        # Only allow saving if owner_id exists in DB
        if can_save and not owner_exists(owner_id):
            can_save = False

        # Check if OpenRouter key is available
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_key or openrouter_key.strip() == '':
            # Return placeholder response when OpenRouter key is missing
            placeholder_reply = "Hi! I am the Quikbok booking assistant. I can help you book a service. What would you like to book?"
            print(f"[ERROR] OPENROUTER_API_KEY not set!")
            return jsonify({"reply": placeholder_reply})
        
        # Detect if this is demo mode
        is_demo = (owner_id is None or owner_id == 'demo')
        
        try:
            ai_reply, updated_history = agent.get_response(conversation_history, message, business_name, business_type, is_demo=is_demo)
            try:
                print(f"AI reply received: {ai_reply}")
            except Exception:
                print(f"AI reply received (escaped): {ai_reply.encode('ascii', errors='backslashreplace').decode('ascii')}")
        except Exception as ai_error:
            # Handle all Gemini errors (quota, auth, rate limit, etc.) with placeholder response
            print(f"Gemini API Error: {type(ai_error).__name__}: {ai_error}")
            print(traceback.format_exc())
            placeholder_reply = "Hi! I am the Quikbok booking assistant. I can help you book a service. What would you like to book?"
            print(f"Returning placeholder: {placeholder_reply}")
            conversation_history.append({"role": "assistant", "content": placeholder_reply})
            ai_reply = placeholder_reply
            updated_history = conversation_history
        
        # Save booking only when owner is real+known and marker is present
        booking_details = save_booking_if_complete(owner_id, ai_reply, can_save)
        
        # Format reply: if booking complete, use clean formatted output; else remove marker line
        if booking_details:
            # Reformat as clean plain-text structured output
            clean_reply = format_booking_response(business_type, booking_details)
        else:
            # Remove marker line from what the user sees
            clean_reply = re.sub(r'\n?BOOKING_COMPLETE\|[^\n]+', '', ai_reply).strip()
        
        response = {"reply": clean_reply, "conversation_history": updated_history}
        if booking_details:
            response["booking_complete"] = True
            response["booking_details"] = booking_details
        return jsonify(response)
    except Exception as e:
        print(f"CHAT ERROR: {traceback.format_exc()}")
        # Return placeholder response for any error
        placeholder_reply = "Hi! I am the Quikbok booking assistant. I can help you book a service. What would you like to book?"
        return jsonify({"reply": placeholder_reply})

@chat_bp.route('/widget/<owner_id>')
@cross_origin()
def widget(owner_id):
    try:
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        js = f"""
        <script>
        (function() {{
            var chatWidget = document.createElement('iframe');
            chatWidget.src = '{base_url}/book/{owner_id}';
            chatWidget.style.width = '350px';
            chatWidget.style.height = '500px';
            chatWidget.style.border = 'none';
            document.body.appendChild(chatWidget);
        }})();
        </script>
        """
        resp = make_response(js)
        resp.headers['Content-Type'] = 'application/javascript'
        return resp
    except Exception as e:
        return f"// Error: {e}", 500

@chat_bp.route('/book/<owner_id>')
@cross_origin()
def book(owner_id):
    try:
        # Get owner details to show business name
        business_name = 'Quikbok'  # Default
        if owner_id and owner_id != 'demo':
            from backend.models.database import get_owner_by_id
            owner = get_owner_by_id(owner_id)
            if owner:
                business_name = owner.get('business_name', 'Quikbok')
        
        return render_template('book.html', owner_id=owner_id, business_name=business_name)
    except Exception as e:
        return f"Error: {e}", 500
