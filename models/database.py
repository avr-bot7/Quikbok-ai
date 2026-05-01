import os
import uuid as _uuid
from supabase import create_client, Client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def normalize_owner_id(owner_id):
    """Ensure owner_id is a canonical UUID string for Supabase filters and inserts."""
    if owner_id is None:
        return None
    if isinstance(owner_id, _uuid.UUID):
        return str(owner_id)
    s = str(owner_id).strip()
    if not s or s.lower() == "none":
        return None
    return s

def get_db():
    return supabase

def create_owner(email, password_hash, name, business_name, business_type):
    try:
        data = {
            "email": email,
            "password_hash": password_hash,
            "name": name,
            "business_name": business_name,
            "business_type": business_type,
            "plan": "basic",
            "is_active": True
        }
        response = supabase.table("Owners").insert(data).execute()
        return response
    except Exception as e:
        print(f"CREATE_OWNER ERROR: {type(e).__name__}: {str(e)}")
        return None

def get_owner_by_whatsapp_number(whatsapp_number):
    try:
        response = supabase.table("Owners").select("*").eq("whatsapp_number", whatsapp_number).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"GET_OWNER_BY_WHATSAPP ERROR: {type(e).__name__}: {str(e)}")
        return None

def get_owner_by_email(email):
    try:
        response = supabase.table("Owners").select("*").eq("email", email).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching owner: {e}")
        return None

def get_owner_by_id(owner_id):
    try:
        oid = normalize_owner_id(owner_id)
        if not oid:
            return None
        response = supabase.table("Owners").select("*").eq("id", oid).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching owner by id: {e}")
        return None

def get_first_owner():
    try:
        response = supabase.table("Owners").select("*").limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error fetching first owner: {e}")
        return None

def create_booking(owner_id, customer_name, service, date, phone):
    try:
        oid = normalize_owner_id(owner_id)
        if not oid:
            print("CREATE_BOOKING: skipped — invalid owner_id")
            return None
        data = {
            "owner_id": oid,
            "customer_name": customer_name,
            "service": service,
            "date": date,
            "phone": phone,
            "status": "pending"
        }
        print(f"\n=== CREATE BOOKING ===")
        print(f"  owner_id: {oid}")
        print(f"  customer_name: {customer_name}")
        print(f"  service: {service}")
        print(f"  date: {date}")
        print(f"  phone: {phone}")
        response = supabase.table("bookings").insert(data).execute()
        print(f"  RESULT: {response.data}")
        return response
    except Exception as e:
        print(f"Error creating booking: {e}")
        return None

def get_bookings_by_owner(owner_id):
    try:
        oid = normalize_owner_id(owner_id)
        if not oid:
            print("GET_BOOKINGS_BY_OWNER: empty owner_id after normalize")
            return []
        print(f"\n=== GET BOOKINGS BY OWNER ===")
        print(f"  Querying owner_id: {oid!r} (type: {type(oid).__name__})")
        response = supabase.table("bookings").select("*").eq("owner_id", oid).execute()
        print(f"  Found {len(response.data) if response.data else 0} bookings")
        if response.data:
            for b in response.data:
                print(f"    - {b.get('customer_name')} | {b.get('service')} | {b.get('date')} | {b.get('status')}")
        return response.data
    except Exception as e:
        print(f"Error fetching bookings: {e}")
        return None

def count_bookings_total(owner_id):
    """Count all bookings for this owner (Supabase)."""
    try:
        oid = normalize_owner_id(owner_id)
        if not oid:
            return 0
        response = (
            supabase.table("bookings")
            .select("id", count="exact")
            .eq("owner_id", oid)
            .execute()
        )
        return response.count if response.count is not None else 0
    except Exception as e:
        print(f"count_bookings_total error: {e}")
        return 0


def count_bookings_pending(owner_id):
    """Count bookings with status pending for this owner."""
    try:
        oid = normalize_owner_id(owner_id)
        if not oid:
            return 0
        response = (
            supabase.table("bookings")
            .select("id", count="exact")
            .eq("owner_id", oid)
            .eq("status", "pending")
            .execute()
        )
        return response.count if response.count is not None else 0
    except Exception as e:
        print(f"count_bookings_pending error: {e}")
        return 0


def count_bookings_confirmed_today(owner_id, today_iso):
    """Count confirmed bookings whose calendar date is today.

    The `date` column may be stored as timestamptz; exact .eq('date', 'YYYY-MM-DD')
    does not match 'YYYY-MM-DDTHH:MM:SS+00:00', so we use a half-open UTC day range.
    """
    try:
        from datetime import datetime, timedelta

        oid = normalize_owner_id(owner_id)
        if not oid or not today_iso:
            return 0
        d = datetime.strptime(today_iso, "%Y-%m-%d").date()
        next_day = (d + timedelta(days=1)).isoformat()
        start = f"{today_iso}T00:00:00+00:00"
        end = f"{next_day}T00:00:00+00:00"
        response = (
            supabase.table("bookings")
            .select("id", count="exact")
            .eq("owner_id", oid)
            .eq("status", "confirmed")
            .gte("date", start)
            .lt("date", end)
            .execute()
        )
        return response.count if response.count is not None else 0
    except Exception as e:
        print(f"count_bookings_confirmed_today error: {e}")
        return 0


def update_booking_status(booking_id, status):
    try:
        response = supabase.table("bookings").update({"status": status}).eq("id", booking_id).execute()
        return response
    except Exception as e:
        print(f"Error updating booking status: {e}")
        return None

def update_owner_settings(owner_id, business_name, ai_instructions, whatsapp_number=None, whatsapp_provider=None):
    try:
        oid = normalize_owner_id(owner_id)
        if not oid:
            return None
        data = {
            "business_name": business_name,
            "ai_instructions": ai_instructions
        }
        if whatsapp_number:
            data["whatsapp_number"] = whatsapp_number
        if whatsapp_provider:
            data["whatsapp_provider"] = whatsapp_provider
        response = supabase.table("Owners").update(data).eq("id", oid).execute()
        return response
    except Exception as e:
        print(f"Error updating owner settings: {e}")
        return None

def create_demo_request(name, business_name, whatsapp_number, business_type, preferred_time):
    try:
        data = {
            "name": name,
            "business_name": business_name,
            "whatsapp_number": whatsapp_number,
            "business_type": business_type,
            "preferred_time": preferred_time
        }
        response = supabase.table("demo_requests").insert(data).execute()
        return response
    except Exception as e:
        print(f"Error creating demo request: {e}")
        return None
