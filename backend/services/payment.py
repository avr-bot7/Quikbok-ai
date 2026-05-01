import razorpay
import os
import hmac
import hashlib

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')

BASIC_PLAN = {'name': 'BASIC', 'amount': 49900, 'period': 'monthly'}
PRO_PLAN = {'name': 'PRO', 'amount': 99900, 'period': 'monthly'}
PREMIUM_PLAN = {'name': 'PREMIUM', 'amount': 199900, 'period': 'monthly'}

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_subscription_plan(name, amount, period):
    try:
        plan = client.plan.create({
            'period': period,
            'interval': 1,
            'item': {
                'name': name,
                'amount': amount,
                'currency': 'INR',
            }
        })
        return plan
    except Exception as e:
        print(f"Error creating plan: {e}")
        return None

def create_subscription(owner_id, plan_id):
    try:
        sub = client.subscription.create({
            'plan_id': plan_id,
            'customer_notify': 1,
            'notes': {'owner_id': owner_id}
        })
        return sub
    except Exception as e:
        print(f"Error creating subscription: {e}")
        return None

def verify_payment_signature(payload, signature):
    try:
        import hmac
        import hashlib
        
        # Convert payload to bytes if it's a string
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        # Convert signature to bytes if it's a string
        if isinstance(signature, str):
            signature = signature.encode('utf-8')
        
        # Generate expected signature
        expected_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures securely
        return hmac.compare_digest(expected_signature, signature.decode('utf-8') if isinstance(signature, bytes) else signature)
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False

def get_subscription_status(subscription_id):
    try:
        sub = client.subscription.fetch(subscription_id)
        return sub.get('status')
    except Exception as e:
        print(f"Error fetching subscription status: {e}")
        return None
