from flask import Blueprint, request, redirect, url_for, flash, session, jsonify, render_template
from backend.services.payment import create_subscription_plan, create_subscription, BASIC_PLAN, PRO_PLAN, PREMIUM_PLAN
from backend.models.database import get_owner_by_email, update_owner_settings
from backend.routes.auth import login_required
import os

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/payment/create-subscription', methods=['GET', 'POST'])
def create_payment_subscription():
    print(f"\n=== PAYMENT ROUTE ACCESS ===")
    print(f"Method: {request.method}")
    print(f"Session: {dict(session)}")
    
    if request.method == 'GET':
        plan_name = request.args.get('plan', 'basic')
        return render_template('payment.html', plan_name=plan_name)
    
    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        plan_name = payload.get('plan') or request.form.get('plan') or 'basic'
        print(f"Plan requested: {plan_name}")
        
        # Check Razorpay credentials (optional) and get plan details
        razorpay_key_id = os.getenv('RAZORPAY_KEY_ID', 'fake_key_for_college_project')
        razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET', 'fake_secret_for_college_project')
        print(f"Razorpay Key ID used: {bool(os.getenv('RAZORPAY_KEY_ID'))}")
        print(f"Razorpay Key Secret used: {bool(os.getenv('RAZORPAY_KEY_SECRET'))}")

        # Get plan details
        if plan_name == 'basic':
            plan_details = BASIC_PLAN
        elif plan_name == 'pro':
            plan_details = PRO_PLAN
        elif plan_name == 'premium':
            plan_details = PREMIUM_PLAN
        else:
            plan_details = BASIC_PLAN
        
        # --- ADD THIS MOCK RESPONSE FOR YOUR COLLEGE DEMO ---
        # Instead of actually calling Razorpay, just return a fake order
        return jsonify({
            'success': True,
            'order_id': 'order_fake_12345',
            'amount': plan_details['amount'],
            'currency': 'INR',
            'key_id': razorpay_key_id,
            'plan_name': plan_name
        })
        # --------------------------------------------------

        # (The real Razorpay integration is intentionally skipped for the demo.)

@payment_bp.route('/payment/success', methods=['POST'])
def payment_success():
    try:
        # Verify Razorpay signature
        import razorpay
        client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')))
        
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        client.utility.verify_payment_signature(params_dict)
        
        # Get plan name from order notes
        order = client.order.fetch(order_id)
        plan_name = order['notes']['plan_name']
        owner_id = order['notes']['owner_id']
        
        # Update owner plan
        if owner_id != 'demo':
            from backend.models.database import update_owner_plan
            update_owner_plan(owner_id, plan_name)
            
            # Update session
            session['plan'] = plan_name
        
        flash(f'Successfully upgraded to {plan_name.upper()} plan!', 'success')
        return redirect(url_for('dashboard.billing'))
        
    except Exception as e:
        print(f"Payment verification error: {e}")
        flash('Payment verification failed. Please contact support.', 'danger')
        return redirect(url_for('dashboard.billing'))

@payment_bp.route('/payment/failure')
def payment_failure():
    flash('Payment failed. Please try again.', 'danger')
    return redirect(url_for('dashboard.billing'))
