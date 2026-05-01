from flask import Blueprint, request, jsonify, render_template, make_response, current_app
from flask_cors import cross_origin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import traceback
import re

chat_bp = Blueprint('chat', __name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30 per minute"]
)

def get_agent():
    try:
        from services.ai_service import BookingAgent
        return BookingAgent()
    except:
        try:
            from backend.services.ai_service import BookingAgent
            return BookingAgent()
        except Exception as e:
            print(f"Could not load BookingAgent: {e}")
            return None

def get_db_functions():
    try:
        from models.database import get_owner_by_id, create_booking, normalize_owner_id
        return get_owner_by_id, create_booking, normalize_owner_id
    except:
        try:
            from backend.models.database import get_owner_by_id, create_booking, normalize_owner_id
            return get_owner_by_id, create_booking, normalize_owner_id
        except Exception as e:
            print(f"Could not load DB functions: {e}")
            return None, None, None

@chat_bp.route('/chat', methods=['POST'])
@cross_origin()
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"reply": "Invalid request.", "conversation_history": []})

        owner_id = data.get('owner_id', 'demo')
        message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])

        print(f"CHAT: owner={owner_id} msg={message} history_len={len(conversation_history)}")

        get_owner_by_id, create_booking, normalize_owner_id = get_db_functions()

        business_name = 'Hotel Demo Rishikesh'
        business_type = 'hotel'

        if owner_id and owner_id != 'demo' and get_owner_by_id and normalize_owner_id:
            oid = normalize_owner_id(owner_id)
            if oid:
                owner = get_owner_by_id(oid)
                if owner:
                    business_name = owner.get('business_name', business_name)
                    business_type = owner.get('business_type', business_type)

        agent = get_agent()

        if not agent:
            conversation_history.append({"role": "user", "content": message})
            reply = "Sorry, AI service unavailable right now."
            conversation_history.append({"role": "assistant", "content": reply})
            return jsonify({"reply": reply, "conversation_history": conversation_history})

        try:
            from config import Config
            gemini_key = getattr(Config, 'GEMINI_API_KEY', '')
            if not gemini_key or gemini_key.strip() == '':
                conversation_history.append({"role": "user", "content": message})
                reply = "AI key not configured. Please contact support."
                conversation_history.append({"role": "assistant", "content": reply})
                return jsonify({"reply": reply, "conversation_history": conversation_history})
        except:
            pass

        try:
            ai_reply, updated_history = agent.get_response(
                conversation_history, message, business_name, business_type
            )
            print(f"AI REPLY: {ai_reply[:100]}")
        except Exception as ai_error:
            print(f"GEMINI ERROR: {ai_error}")
            conversation_history.append({"role": "user", "content": message})
            reply = "I had trouble processing that. Please try again."
            conversation_history.append({"role": "assistant", "content": reply})
            return jsonify({"reply": reply, "conversation_history": conversation_history})

        booking_details = None
        if create_booking and normalize_owner_id:
            details = agent.detect_booking_complete(ai_reply)
            if details:
                if owner_id != 'demo':
                    try:
                        oid = normalize_owner_id(owner_id)
                        if oid:
                            create_booking(
                                oid,
                                details.get('name'),
                                details.get('service'),
                                details.get('date'),
                                details.get('phone')
                            )
                            print(f"BOOKING SAVED: {details}")
                    except Exception as e:
                        print(f"Booking save error: {e}")
                booking_details = details

        clean_reply = re.sub(r'\n?BOOKING_COMPLETE\|[^\n]+', '', ai_reply).strip()

        response = {
            "reply": clean_reply,
            "conversation_history": updated_history
        }
        if booking_details:
            response["booking_complete"] = True
            response["booking_details"] = booking_details

        return jsonify(response)

    except Exception as e:
        print(f"CHAT FATAL ERROR: {traceback.format_exc()}")
        conversation_history = data.get('conversation_history', []) if 'data' in dir() else []
        conversation_history.append({"role": "user", "content": data.get('message', '') if 'data' in dir() else ''})
        reply = "Something went wrong. Please try again."
        conversation_history.append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply, "conversation_history": conversation_history})

@chat_bp.route('/widget/<owner_id>')
@cross_origin()
def widget(owner_id):
    try:
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        js = f"""(function(){{
var s=document.createElement('script');
s.src='{base_url}/static/js/chat.js';
s.setAttribute('data-owner-id','{owner_id}');
document.head.appendChild(s);
}})();"""
        resp = make_response(js)
        resp.headers['Content-Type'] = 'application/javascript'
        return resp
    except Exception as e:
        return f"// Error: {e}", 500

@chat_bp.route('/book/<owner_id>')
@cross_origin()
def book(owner_id):
    try:
        business_name = 'Quikbok'
        get_owner_by_id, _, normalize_owner_id = get_db_functions()
        if owner_id and owner_id != 'demo' and get_owner_by_id and normalize_owner_id:
            oid = normalize_owner_id(owner_id)
            if oid:
                owner = get_owner_by_id(oid)
                if owner:
                    business_name = owner.get('business_name', 'Quikbok')
        return render_template('book.html', owner_id=owner_id, business_name=business_name)
    except Exception as e:
        return f"Error: {e}", 500