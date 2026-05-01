from flask import Blueprint, request, jsonify, Response
import json
import logging
from backend.services.whatsapp import WhatsAppCloud, send_message_via_provider
from backend.models.database import (
    get_owner_by_meta_phone_number_id,
    create_booking,
    normalize_owner_id,
)
from backend.services.ai_service import BookingAgent
from config.config import Config

whatsapp_cloud_bp = Blueprint('whatsapp_cloud', __name__)

@whatsapp_cloud_bp.route('/webhook/whatsapp-cloud', methods=['GET', 'POST'])
def whatsapp_cloud_webhook():
    """Handle Meta WhatsApp Cloud API webhook"""
    
    if request.method == 'GET':
        # Webhook verification
        cloud_client = WhatsAppCloud()
        challenge = cloud_client.verify_webhook(request)
        
        if challenge:
            return Response(challenge, status=200, mimetype='text/plain')
        else:
            return Response('Verification failed', status=403)
    
    elif request.method == 'POST':
        # Handle incoming messages
        try:
            # Get JSON data from request
            if request.is_json:
                data = request.get_json()
            else:
                # Try to get raw data and parse as JSON
                raw_data = request.get_data(as_text=True)
                data = json.loads(raw_data) if raw_data else {}
            
            logging.info(f"Received WhatsApp Cloud webhook: {data}")
            
            # Parse incoming message
            cloud_client = WhatsAppCloud()
            message_data = cloud_client.parse_incoming_message(data)
            
            if message_data:
                # Extract message details
                from_number = message_data.get('From', '')
                message_body = message_data.get('Body', '')
                phone_number_id = message_data.get('phone_number_id', '')
                
                logging.info(f"Message from {from_number}: {message_body}")

                owner = get_owner_by_meta_phone_number_id(phone_number_id)
                if owner:
                    logging.info(
                        f"Found Meta owner for phone_number_id={phone_number_id}: {owner.get('business_name')}"
                    )
                else:
                    logging.warning(
                        f"No Meta owner found for phone_number_id={phone_number_id} from {from_number}"
                    )
                
                if owner:
                    try:
                        agent = BookingAgent()
                        business_name = owner.get('business_name', 'Quikbok')
                        business_type = owner.get('business_type', 'business')

                        if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY.strip() == '':
                            ai_reply = "Hi! I am the Quikbok booking assistant. I can help you book a service. What would you like to book?"
                        else:
                            ai_reply, _ = agent.get_response([], message_body, business_name, business_type)

                        booking_details = agent.detect_booking_complete(ai_reply)
                        if booking_details:
                            try:
                                create_booking(
                                    normalize_owner_id(owner.get('id')),
                                    booking_details['name'],
                                    booking_details['service'],
                                    booking_details['date'],
                                    booking_details['phone']
                                )
                                logging.info(f"Saved Meta booking: {booking_details}")
                            except Exception as booking_error:
                                logging.error(f"Error saving Meta booking: {booking_error}")

                        import re
                        response = re.sub(r'\n?BOOKING_COMPLETE\|[^\n]+', '', ai_reply).strip()
                        
                        # Send response via owner's configured provider/credentials
                        if response:
                            send_message_via_provider(owner, from_number, response)
                            logging.info(f"Sent response via WhatsApp Cloud: {response}")
                        
                    except Exception as e:
                        logging.error(f"Error processing message: {e}")
            
            return Response('OK', status=200)
            
        except Exception as e:
            logging.error(f"Error processing WhatsApp Cloud webhook: {e}")
            return Response('Error', status=500)
    
    else:
        return Response('Method not allowed', status=405)
