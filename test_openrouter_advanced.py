#!/usr/bin/env python3
"""Advanced test script for OpenRouter with booking assistant scenarios"""

import os
import json
import sys
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv(override=True)

def test_booking_assistant_prompt():
    """Test OpenRouter with a booking assistant prompt (like QuikBok uses)"""
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key or api_key.strip() == "":
        print("[ERROR] OPENROUTER_API_KEY is missing in .env")
        return False
    
    print("[INFO] Testing OpenRouter with booking assistant prompt...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "QuikBok Booking Test",
        "Content-Type": "application/json",
    }
    
    system_prompt = """You are a friendly AI booking assistant for a hotel.
You only handle room or stay bookings.
Collect and confirm: full name, check-in date, check-out date, room type, number of guests, and phone number.
Reply in Hinglish and stay conversational.
When all details are confirmed, end your message with exactly this marker on a new line:
HOTEL_BOOKING_COMPLETE|name|check_in|check_out|room_type|guests|phone"""
    
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": "Namaste! Main ek deluxe room book karna chahta hoon. Mera naam Raj Kumar hai. 2026-05-10 se 2026-05-15 tak. 3 log hain. Mera phone: +919876543210"
            }
        ],
        "temperature": 0.2,
        "max_tokens": 512,
    }
    
    try:
        print("\n[REQUEST] Making booking assistant API call...")
        print(f"[REQUEST] System prompt: Hotel booking assistant")
        print(f"[REQUEST] User message (Hinglish): Booking for 3 people, deluxe room")
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"\n[RESPONSE] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] Booking assistant API call successful!")
            print(f"[RESPONSE] Model used: {result.get('model')}")
            
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "")
                print(f"\n[RESPONSE] Assistant reply:")
                print(f"---")
                print(content)
                print(f"---")
                
                # Check if booking marker was detected
                if "HOTEL_BOOKING_COMPLETE|" in content:
                    print(f"\n✓ Booking marker detected! Extraction successful!")
                else:
                    print(f"\n⚠ No booking marker in response (response may be partial or AI decided not to confirm)")
                
                print(f"\n✓ OpenRouter is suitable for QuikBok booking assistant!")
                return True
            else:
                print(f"[ERROR] Unexpected response format: {result}")
                return False
        else:
            print(f"[ERROR] API request failed!")
            print(f"[ERROR] Status: {response.status_code}")
            print(f"[ERROR] Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_models():
    """Test availability of different models on OpenRouter"""
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[ERROR] OPENROUTER_API_KEY is missing")
        return False
    
    print("\n\n[INFO] Testing model availability...")
    
    models_to_test = [
        "openai/gpt-4o-mini",
        "google/gemini-2.0-flash-lite",
        "anthropic/claude-3.5-sonnet",
        "meta-llama/llama-3.1-8b-instruct",
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "QuikBok Model Test",
        "Content-Type": "application/json",
    }
    
    for model in models_to_test:
        try:
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Say OK"
                    }
                ],
                "max_tokens": 10,
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  ✓ {model}")
            else:
                error_msg = response.json().get("error", {}).get("message", f"Status {response.status_code}")
                print(f"  ✗ {model} - {error_msg}")
        except Exception as e:
            print(f"  ✗ {model} - Error: {str(e)[:50]}")

if __name__ == "__main__":
    print("=" * 70)
    print("QuikBok OpenRouter API Key Test Suite")
    print("=" * 70)
    
    test1_success = test_booking_assistant_prompt()
    test_multiple_models()
    
    print("\n" + "=" * 70)
    if test1_success:
        print("All tests completed successfully! ✓")
        print("The OpenRouter API key is ready for QuikBok integration.")
    else:
        print("Some tests failed. Please check the errors above.")
    print("=" * 70)
    
    sys.exit(0 if test1_success else 1)
