from flask import Blueprint, request, jsonify, abort
from backend.services.payment import verify_payment_signature
from backend.services.whatsapp import send_message_via_provider, send_booking_alert_via_provider, verify_twilio_signature
from backend.services.ai_service import BookingAgent
from backend.models.database import get_db, get_owner_by_whatsapp_number
import os

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook/razorpay', methods=['POST'])
def razorpay_webhook():
    try:
        payload = request.get_data()
        signature = request.headers.get('X-Razorpay-Signature')
        if not verify_payment_signature(payload, signature):
            abort(400, 'Invalid signature')
        event = request.json
        db = get_db()
        if event['event'] == 'payment.captured':
            owner_id = event['payload']['payment']['entity']['notes']['owner_id']
            db.table('Owners').update({'is_active': True}).eq('id', owner_id).execute()
        elif event['event'] == 'subscription.cancelled':
            owner_id = event['payload']['subscription']['entity']['notes']['owner_id']
            db.table('Owners').update({'is_active': False}).eq('id', owner_id).execute()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@webhook_bp.route('/webhook/twilio', methods=['POST'])
def twilio_webhook():
    try:
        # Verify Twilio signature (optional for sandbox testing)
        # if not verify_twilio_signature(request):
        #     abort(400, 'Invalid Twilio signature')
        
        # Extract message details
        from_number = request.form.get('From')  # Customer's WhatsApp number
        to_number = request.form.get('To')      # Twilio WhatsApp number (owner's sandbox number)
        body = request.form.get('Body')         # Customer's message
        
        print(f"📱 WhatsApp Message: From {from_number} To {to_number}: {body}")
        
        # Find the matching owner by their WhatsApp number (for Twilio provider)
        owner = get_owner_by_whatsapp_number(to_number)
        
        if not owner:
            print(f"❌ No owner found with WhatsApp number: {to_number}")
            # Send default response
            send_message_via_provider({'whatsapp_provider': 'twilio'}, from_number, "Hi! This number is not configured for Quikbok booking. Please contact the business owner.")
            return '', 200  # Return 200 to Twilio to avoid retry
        
        print(f"✅ Found owner: {owner['business_name']} ({owner['email']})")
        
        # Use same chat logic as routes/chat.py
        from config.config import Config
        if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY.strip() == '':
            # Use placeholder response when Gemini key is missing
            ai_reply = "Hi! I am the Quikbok booking assistant. I can help you book a service. What would you like to book?"
        else:
            # Use real Gemini when available
            try:
                agent = BookingAgent()
                ai_reply = agent.get_response([], body, owner['business_name'], owner['business_type'])
                
                # Check for booking completion
                booking_details = agent.detect_booking_complete(ai_reply)
                if booking_details:
                    # Save booking to database
                    from backend.models.database import create_booking
                    try:
                        create_booking(
                            owner['id'],
                            booking_details['name'],
                            booking_details['service'],
                                booking_details['date'],
                                booking_details['phone']
                        )
                        print(f"📅 Booking saved: {booking_details}")
                        
                        # Send notification to owner using their preferred provider
                        send_booking_alert_via_provider(owner, booking_details)
                    except Exception as booking_error:
                        print(f"❌ Error saving booking: {booking_error}")
                
                # Clean reply: remove the BOOKING_COMPLETE marker from what the customer sees
                import re
                ai_reply = re.sub(r'\n?BOOKING_COMPLETE\|[^\n]+', '', ai_reply).strip()
                
            except Exception as ai_error:
                print(f"❌ Gemini API Error: {ai_error}")
                # Fallback to placeholder response
                ai_reply = "Hi! I am the Quikbok booking assistant. I can help you book a service. What would you like to book?"
        
        # Send AI reply back to customer using owner's preferred provider
        send_message_via_provider(owner, from_number, ai_reply)
        print(f"📤 Sent reply to {from_number}: {ai_reply}")
        
        # Return TwiML response (required by Twilio)
        from flask import Response
        twiml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{ai_reply}</Message>
</Response>'''
        
        return Response(twiml_response, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Twilio webhook error: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
