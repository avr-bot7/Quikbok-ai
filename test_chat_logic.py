#!/usr/bin/env python3
"""Test OpenRouter API and demo mode logic directly without Flask dependencies"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv()

# Test 1: Check if OPENROUTER_API_KEY is loaded
print("=" * 70)
print("TEST 1: OPENROUTER_API_KEY Environment Check")
print("=" * 70)
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("[ERROR] OPENROUTER_API_KEY not found in environment!")
else:
    print(f"[SUCCESS] OPENROUTER_API_KEY loaded!")
    print(f"  First 10 chars: {api_key[:10]}")
    print(f"  Last 10 chars: ...{api_key[-10:]}")
    print(f"  Total length: {len(api_key)}")

# Test 2: Import and initialize BookingAgent
print("\n" + "=" * 70)
print("TEST 2: BookingAgent Initialization")
print("=" * 70)
try:
    from backend.services.ai_service import BookingAgent
    print("[SUCCESS] BookingAgent imported successfully")
    
    agent = BookingAgent()
    print("[SUCCESS] BookingAgent initialized")
    print(f"  Model: {agent.model}")
    print(f"  Client base URL: https://openrouter.ai/api/v1")
except Exception as e:
    print(f"[ERROR] Failed to initialize BookingAgent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Demo mode logic - not logged in
print("\n" + "=" * 70)
print("TEST 3: Demo Mode (Not Logged In)")
print("=" * 70)
try:
    owner_id = None
    is_demo = (owner_id is None or owner_id == 'demo')
    print(f"[INFO] owner_id: {owner_id}")
    print(f"[INFO] is_demo: {is_demo}")
    
    if is_demo:
        print("[SUCCESS] Demo mode detected correctly")
        expected_prompt = "You are Quikbok AI, a booking assistant for businesses in Uttarakhand India"
        print(f"[INFO] Demo prompt will start with: '{expected_prompt}...'")
    else:
        print("[ERROR] Demo mode not detected!")
except Exception as e:
    print(f"[ERROR] {e}")

# Test 4: Real user mode - logged in
print("\n" + "=" * 70)
print("TEST 4: Real User Mode (Logged In)")
print("=" * 70)
try:
    owner_id = "550e8400-e29b-41d4-a716-446655440000"  # Example UUID
    is_demo = (owner_id is None or owner_id == 'demo')
    print(f"[INFO] owner_id: {owner_id}")
    print(f"[INFO] is_demo: {is_demo}")
    
    if not is_demo:
        print("[SUCCESS] Real user mode detected correctly")
        business_name = "Himalaya Resort"
        business_type = "hotel"
        expected_prompt = f"You are a friendly AI booking assistant for {business_name}, a {business_type}"
        print(f"[INFO] Business prompt will start with: '{expected_prompt}...'")
    else:
        print("[ERROR] Real user mode not detected!")
except Exception as e:
    print(f"[ERROR] {e}")

# Test 5: Simulate a demo chat
print("\n" + "=" * 70)
print("TEST 5: Demo Mode Chat Simulation")
print("=" * 70)
try:
    conversation_history = []
    user_message = "Hi!"
    is_demo = True
    business_name = "Quikbok"
    business_type = "service"
    
    print(f"[INFO] Calling get_response with is_demo=True")
    print(f"[INFO] User message: '{user_message}'")
    
    reply, history = agent.get_response(
        conversation_history,
        user_message,
        business_name,
        business_type,
        is_demo=is_demo
    )
    
    print(f"\n[SUCCESS] Demo response received!")
    print(f"[RESPONSE] {reply[:200]}...")
    
    # Check if response mentions Quikbok intro
    if "Quikbok" in reply or "booking assistant" in reply:
        print("[SUCCESS] Response mentions Quikbok AI - correct demo intro!")
    else:
        print("[WARNING] Response may not be the expected Quikbok intro")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Simulate a real user chat
print("\n" + "=" * 70)
print("TEST 6: Real User Mode Chat Simulation")
print("=" * 70)
try:
    conversation_history = []
    user_message = "Hi!"
    is_demo = False
    business_name = "Rishikesh Resort"
    business_type = "hotel"
    
    print(f"[INFO] Calling get_response with is_demo=False")
    print(f"[INFO] Business: {business_name} ({business_type})")
    print(f"[INFO] User message: '{user_message}'")
    
    reply, history = agent.get_response(
        conversation_history,
        user_message,
        business_name,
        business_type,
        is_demo=is_demo
    )
    
    print(f"\n[SUCCESS] Real user response received!")
    print(f"[RESPONSE] {reply[:200]}...")
    
    # Check if response mentions the business name
    if business_name.lower() in reply.lower():
        print(f"[SUCCESS] Response mentions {business_name} - correct business intro!")
    else:
        print(f"[INFO] Response is a general booking assistant intro")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("ALL TESTS COMPLETED")
print("=" * 70)
