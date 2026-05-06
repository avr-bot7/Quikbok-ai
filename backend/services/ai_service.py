import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class BookingAgent:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.model = "google/gemini-2.0-flash-exp:free"

    def get_response(self, conversation_history, user_message, business_name, business_type):
        conversation_history.append({"role": "user", "content": user_message})
        
        system_prompt = f"""You are a friendly AI booking assistant for {business_name}, a {business_type} in Uttarakhand India. 
Help customers book appointments by collecting: full name, date, service, phone number.
Reply in Hinglish (mix of Hindi and English). Be warm and conversational.
Once you have all 4 details, end your message with exactly:
BOOKING_COMPLETE|name|date|service|phone"""

        messages = [{"role": "system", "content": system_prompt}] + conversation_history

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            reply = response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": reply})
            return reply, conversation_history
        except Exception as e:
            print(f"OpenRouter Error: {e}")
            reply = "Sorry, I could not process that. Please try again."
            conversation_history.append({"role": "assistant", "content": reply})
            return reply, conversation_history

    def detect_booking_complete(self, message):
        if "BOOKING_COMPLETE" not in message:
            return None
        try:
            marker = re.search(r'BOOKING_COMPLETE\|([^|]+)\|([^|]+)\|([^|]+)\|([^\n|]+)', message)
            if marker:
                return {
                    "name": marker.group(1).strip(),
                    "date": marker.group(2).strip(),
                    "service": marker.group(3).strip(),
                    "phone": marker.group(4).strip()
                }
        except Exception as e:
            print(f"Booking detection error: {e}")
        return None
