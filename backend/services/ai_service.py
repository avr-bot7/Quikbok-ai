import os
import re
import traceback
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


_OUT_OF_SCOPE_INSTRUCTION = (
    "IMPORTANT — out-of-scope requests:\n"
    "If a user asks you to do ANYTHING outside of booking — such as writing code, accessing software "
    "(Unity 3D, Blender, VS Code, etc.), creating 3D scenes, fixing games, debugging programs, "
    "generating images, browsing the internet, or any other task unrelated to booking — politely "
    "explain that you are only a booking assistant and cannot help with that. "
    "Do NOT pretend to have those capabilities or claim to be waiting for permission. "
    "Redirect them warmly to what you can do (making a booking)."
)


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
            system_prompt = (
                f"You are Quikbok AI, a booking assistant for businesses in Uttarakhand India.\n"
                f"Your ONLY purpose is to help customers make bookings for hotels, restaurants, and tour operators.\n"
                f"When a user asks about your service, explain: 'Hi! I am Quikbok AI booking assistant. "
                f"Quikbok helps hotels, restaurants and tour operators in Uttarakhand get their own AI booking agent. "
                f"Want to see a demo or sign up? Visit our pricing page or click Get Started above.'\n"
                f"Be warm and helpful in Hinglish.\n\n"
                f"{_OUT_OF_SCOPE_INSTRUCTION}"
            )
        else:
            system_prompt = (
                f"You are a friendly AI booking assistant for {business_name}, a {business_type} in Uttarakhand India.\n"
                f"Your ONLY purpose is to help customers book services by collecting: full name, date, service, phone number.\n"
                f"Reply in Hinglish (mix of Hindi and English). Be warm and conversational.\n"
                f"Once you have all 4 details, end your message with exactly:\n"
                f"BOOKING_COMPLETE|name|date|service|phone\n\n"
                f"{_OUT_OF_SCOPE_INSTRUCTION}"
            )

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
