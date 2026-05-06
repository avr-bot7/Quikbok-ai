import os
import re
import traceback
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class BookingAgent:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print(f"[CRITICAL] OPENROUTER_API_KEY not set in environment!")
        else:
            print(f"[DEBUG] OPENROUTER_API_KEY loaded: {api_key[:10]}...")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = "openai/gpt-4o-mini"  # Free model available on OpenRouter

    def get_response(self, conversation_history, user_message, business_name, business_type, is_demo=False):
        conversation_history.append({"role": "user", "content": user_message})
        
        if is_demo:
            system_prompt = """You are Quikbok AI, a booking assistant for businesses in Uttarakhand India. 
When a user asks about your service, explain: 'Hi! I am Quikbok AI booking assistant. Quikbok helps hotels, restaurants and tour operators in Uttarakhand get their own AI booking agent. Want to see a demo or sign up? Visit our pricing page or click Get Started above.'
Be warm and helpful in Hinglish."""
        else:
            system_prompt = f"""You are a friendly AI booking assistant for {business_name}, a {business_type} in Uttarakhand India. 
Help customers book appointments by collecting: full name, date, service, phone number.
Reply in Hinglish (mix of Hindi and English). Be warm and conversational.
Once you have all 4 details, end your message with exactly:
BOOKING_COMPLETE|name|date|service|phone"""

        messages = [{"role": "system", "content": system_prompt}] + conversation_history

        try:
            print(f"[OpenRouter] Calling API with model={self.model}, messages={len(messages)}, is_demo={is_demo}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            reply = response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": reply})
            print(f"[OpenRouter] Response received: {reply[:100]}...")
            return reply, conversation_history
        except Exception as e:
            print(f"[OpenRouter ERROR] {type(e).__name__}: {e}")
            print(traceback.format_exc())
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
