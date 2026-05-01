from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from models.database import (
    get_bookings_by_owner,
    update_booking_status,
    get_owner_by_email,
    update_owner_settings,
    normalize_owner_id,
    count_bookings_total,
    count_bookings_pending,
    count_bookings_confirmed_today,
)
from routes.auth import login_required
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    owner_id = normalize_owner_id(session.get('owner_id'))
    print(f"\n=== DASHBOARD LOAD ===")
    print(f"  Session owner_id (normalized): {owner_id!r}")
    print(f"  Session email: {session.get('email')}")
    bookings = get_bookings_by_owner(owner_id) or []
    print(f"  Session owner_id: {session.get('owner_id')!r}")
    for b in bookings:
        print(f"    Booking owner_id: {b.get('owner_id')!r}")
    today = date.today().isoformat()
    total = count_bookings_total(owner_id)
    pending = count_bookings_pending(owner_id)
    confirmed_today = count_bookings_confirmed_today(owner_id, today)
    recent = sorted(bookings, key=lambda b: b.get('date', ''), reverse=True)[:10]
    print(f"  Stats: total={total}, pending={pending}, confirmed_today={confirmed_today}")
    return render_template('dashboard.html', total=total, pending=pending, confirmed_today=confirmed_today, recent=recent)

@dashboard_bp.route('/dashboard/booking/<uuid:id>/confirm', methods=['POST'])
@login_required
def confirm_booking(id):
    result = update_booking_status(id, 'confirmed')
    if result and result.data:
        flash('Booking confirmed.', 'success')
    else:
        flash('Failed to confirm booking.', 'error')
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/dashboard/booking/<uuid:id>/reject', methods=['POST'])
@login_required
def reject_booking(id):
    result = update_booking_status(id, 'rejected')
    if result and result.data:
        flash('Booking rejected.', 'warning')
    else:
        flash('Failed to reject booking.', 'error')
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/dashboard/settings', methods=['GET', 'POST'])
@login_required
def settings():
    owner_id = normalize_owner_id(session.get('owner_id'))
    owner = get_owner_by_email(session.get('email'))
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    embed_code = f'<script src="{base_url}/widget/{owner_id}"></script>'
    booking_link = f'{base_url}/book/{owner_id}'
    
    if request.method == 'POST':
        business_name = request.form.get('business_name')
        ai_instructions = request.form.get('ai_instructions')
        whatsapp_number = request.form.get('whatsapp_number')
        whatsapp_provider = request.form.get('whatsapp_provider', 'twilio')
        
        if business_name:
            update_owner_settings(owner_id, business_name, ai_instructions, whatsapp_number, whatsapp_provider)
            flash('Settings updated successfully.', 'success')
            # Refresh owner object to show new settings
            owner = get_owner_by_email(session.get('email'))
            
    return render_template('settings.html', owner=owner, embed_code=embed_code, booking_link=booking_link)

@dashboard_bp.route('/booking/update-status', methods=['POST'])
@login_required
def update_booking_status_ajax():
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        new_status = data.get('status')
        
        if not booking_id or not new_status:
            return jsonify({'success': False, 'message': 'Missing booking_id or status'}), 400
        
        # Validate status
        if new_status not in ['confirmed', 'rejected', 'pending']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        # Update booking in database
        result = update_booking_status(booking_id, new_status)
        
        if result and result.data:
            return jsonify({'success': True, 'message': f'Booking {new_status} successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update booking'}), 500
            
    except Exception as e:
        print(f"Error updating booking status: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@dashboard_bp.route('/dashboard/billing')
@login_required
def billing():
    # Load billing and plan info from Supabase
    owner_id = normalize_owner_id(session.get('owner_id'))
    owner = get_owner_by_email(session.get('email'))
    
    if owner:
        plan = owner.get('plan', 'basic')
        is_active = owner.get('is_active', True)
        status = 'active' if is_active else 'cancelled'
    else:
        plan = 'basic'
        status = 'active'
    
    # Calculate next billing date (30 days from now for demo)
    from datetime import datetime, timedelta
    next_billing_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return render_template('billing.html', plan=plan, status=status, next_billing_date=next_billing_date)
