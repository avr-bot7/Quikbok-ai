#!/usr/bin/env python3
"""Test script to verify OpenRouter API key works"""

import os
import json
import sys
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv(override=True)

def test_openrouter_api():
    """Test OpenRouter API with a simple request"""
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key or api_key.strip() == "":
        print("[ERROR] OPENROUTER_API_KEY is missing in .env")
        return False
    
    print(f"[INFO] Testing OpenRouter API...")
    print(f"[INFO] API Key (first 20 chars): {api_key[:20]}...")
    print(f"[INFO] API Key (last 10 chars): ...{api_key[-10:]}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "QuikBok Test",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": "What is 2+2? Reply with just the number."
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }
    
    try:
        print("\n[REQUEST] Making API call to OpenRouter...")
        print(f"[REQUEST] Endpoint: https://openrouter.ai/api/v1/chat/completions")
        print(f"[REQUEST] Model: {data['model']}")
        print(f"[REQUEST] Message: {data['messages'][0]['content']}")
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"\n[RESPONSE] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] API call successful!")
            print(f"[RESPONSE] Model used: {result.get('model')}")
            
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "")
                print(f"[RESPONSE] Content: {content}")
                print(f"\n✓ OpenRouter API is working correctly!")
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
        print("[ERROR] Request timed out - OpenRouter may be unreachable")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_openrouter_api()
    sys.exit(0 if success else 1)
