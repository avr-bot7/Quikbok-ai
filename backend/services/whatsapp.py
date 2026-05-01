import os
import logging
import requests
import json
import hashlib
import hmac
from twilio.rest import Client
from flask import request
from twilio.request_validator import RequestValidator

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM')

# Meta WhatsApp Cloud API credentials
META_PHONE_NUMBER_ID = os.getenv('META_PHONE_NUMBER_ID')
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
META_WEBHOOK_VERIFY_TOKEN = os.getenv('META_WEBHOOK_VERIFY_TOKEN', 'quikbok_verify_token')

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

logging.basicConfig(level=logging.INFO)

def send_message(to_number, message):
    try:
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_FROM,
            to=to_number
        )
        logging.info(f"Sent WhatsApp message to {to_number}")
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")

def send_booking_alert(owner_phone, booking_details):
    try:
        msg = (
            f"New Booking Alert!\n"
            f"Customer: {booking_details.get('name')}\n"
            f"Service: {booking_details.get('service')}\n"
            f"Date: {booking_details.get('date')}\n"
            f"Phone: {booking_details.get('phone')}\n"
            f"Login to dashboard to confirm."
        )
        send_message(owner_phone, msg)
        logging.info(f"Sent booking alert to {owner_phone}")
    except Exception as e:
        logging.error(f"Error sending booking alert: {e}")

def verify_twilio_signature(request):
    try:
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        signature = request.headers.get('X-Twilio-Signature', '')
        url = request.url
        params = request.form.to_dict()
        return validator.validate(url, params, signature)
    except Exception as e:
        logging.error(f"Error verifying Twilio signature: {e}")
        return False


class WhatsAppCloud:
    """Meta WhatsApp Cloud API implementation"""
    
    def __init__(self, phone_number_id=None, access_token=None):
        self.phone_number_id = phone_number_id or META_PHONE_NUMBER_ID
        self.access_token = access_token or META_ACCESS_TOKEN
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def send_message(self, to_number, message):
        """Send message via Meta WhatsApp Cloud API"""
        try:
            # Remove 'whatsapp:' prefix if present
            clean_number = to_number.replace('whatsapp:', '')
            
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logging.info(f"Sent WhatsApp Cloud message to {to_number}")
                return True
            else:
                logging.error(f"Failed to send WhatsApp Cloud message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending WhatsApp Cloud message: {e}")
            return False
    
    def verify_webhook(self, request):
        """Verify Meta webhook"""
        try:
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            
            if mode == 'subscribe' and token == META_WEBHOOK_VERIFY_TOKEN:
                logging.info("Webhook verified successfully")
                return challenge
            else:
                logging.warning("Webhook verification failed")
                return None
                
        except Exception as e:
            logging.error(f"Error verifying webhook: {e}")
            return None
    
    def parse_incoming_message(self, request_data):
        """Parse incoming message from Meta webhook"""
        try:
            data = request_data
            
            # Check if this is a message
            if 'entry' in data and data['entry']:
                for entry in data['entry']:
                    if 'changes' in entry:
                        for change in entry['changes']:
                            value = change.get('value', {})
                            metadata = value.get('metadata', {})
                            if 'messages' in value:
                                messages = value['messages']
                                for message in messages:
                                    if message['type'] == 'text':
                                        return {
                                            'From': f"whatsapp:{message['from']}",
                                            'Body': message['text']['body'],
                                            'MessageSid': message.get('id', ''),
                                            'phone_number_id': metadata.get('phone_number_id', ''),
                                            'display_phone_number': metadata.get('display_phone_number', ''),
                                            'provider': 'meta'
                                        }
            return None
            
        except Exception as e:
            logging.error(f"Error parsing incoming message: {e}")
            return None


def send_message_via_provider(owner, to_number, message):
    """Send message using the owner's preferred WhatsApp provider"""
    try:
        provider = owner.get('whatsapp_provider', 'twilio')
        
        if provider == 'meta':
            # Use Meta WhatsApp Cloud API
            cloud_client = WhatsAppCloud(
                phone_number_id=owner.get('meta_phone_number_id'),
                access_token=owner.get('meta_access_token'),
            )
            return cloud_client.send_message(to_number, message)
        else:
            # Use Twilio (default)
            twilio_client.messages.create(
                body=message,
                from_=TWILIO_WHATSAPP_FROM,
                to=to_number
            )
            logging.info(f"Sent WhatsApp message to {to_number} via Twilio")
            return True
            
    except Exception as e:
        logging.error(f"Error sending message via {provider}: {e}")
        return False


def send_booking_alert_via_provider(owner, booking_details):
    """Send booking alert using the owner's preferred WhatsApp provider"""
    try:
        msg = (
            f"New Booking Alert!\n"
            f"Customer: {booking_details.get('name')}\n"
            f"Service: {booking_details.get('service')}\n"
            f"Date: {booking_details.get('date')}\n"
            f"Phone: {booking_details.get('phone')}\n"
            f"Login to dashboard to confirm."
        )
        
        owner_phone = owner.get('whatsapp_number')
        if owner_phone:
            return send_message_via_provider(owner, owner_phone, msg)
        else:
            logging.warning(f"No WhatsApp number for owner {owner.get('id')}")
            return False
            
    except Exception as e:
        logging.error(f"Error sending booking alert: {e}")
        return False
