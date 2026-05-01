import os
import socket
import sqlite3
import uuid as _uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from supabase import create_client, Client


# Ensure .env is loaded even when this module is imported directly (tests, scripts)
load_dotenv(override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def _is_valid_supabase_url(url: Optional[str]) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and bool(parsed.netloc) and parsed.netloc.endswith(".supabase.co")
    except Exception:
        return False


def _can_resolve_host(hostname: Optional[str]) -> bool:
    if not hostname:
        return False
    try:
        socket.getaddrinfo(hostname, 443)
        return True
    except Exception:
        return False


_BACKEND: str = "supabase"  # or 'sqlite'
_SUPABASE: Optional[Client] = None


def _sqlite_db_path() -> Path:
    # backend/models/database.py -> repo root is 2 levels up
    root = Path(__file__).resolve().parents[2]
    return root / "quikbok.db"


_SQLITE_CONN: Optional[sqlite3.Connection] = None


class _SQLiteResponse:
    def __init__(self, data=None, count: Optional[int] = None):
        self.data = data or []
        self.count = count


class _SQLiteTableAdapter:
    def __init__(self, conn: sqlite3.Connection, table: str):
        self._conn = conn
        self._table = table
        self._updates: Optional[dict[str, Any]] = None
        self._where: Optional[tuple[str, Any]] = None

    def update(self, data: dict[str, Any]):
        self._updates = data
        return self

    def eq(self, column: str, value: Any):
        self._where = (column, value)
        return self

    def execute(self):
        if not self._updates:
            return _SQLiteResponse([])
        if not self._where:
            raise ValueError("SQLite adapter requires a WHERE clause")
        set_clause = ", ".join([f"{k} = ?" for k in self._updates.keys()])
        values = list(self._updates.values())
        where_col, where_val = self._where
        values.append(where_val)
        self._conn.execute(f"UPDATE {self._table} SET {set_clause} WHERE {where_col} = ?", values)
        self._conn.commit()
        return _SQLiteResponse([])


class _SQLiteDBAdapter:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def table(self, name: str) -> _SQLiteTableAdapter:
        return _SQLiteTableAdapter(self._conn, name)


def _sqlite_connect() -> sqlite3.Connection:
    global _SQLITE_CONN
    if _SQLITE_CONN is None:
        conn = sqlite3.connect(str(_sqlite_db_path()), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _SQLITE_CONN = conn
        _sqlite_init_schema(conn)
    return _SQLITE_CONN


def _sqlite_init_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Owners (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            business_name TEXT,
            business_type TEXT,
            plan TEXT DEFAULT 'basic',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            ai_instructions TEXT,
            whatsapp_number TEXT,
            whatsapp_provider TEXT DEFAULT 'twilio',
            meta_phone_number_id TEXT,
            meta_access_token TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            customer_name TEXT,
            service TEXT,
            date TEXT,
            phone TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_requests (
            id TEXT PRIMARY KEY,
            name TEXT,
            business_name TEXT,
            whatsapp_number TEXT,
            business_type TEXT,
            preferred_time TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def _supabase_connect() -> Optional[Client]:
    global _SUPABASE
    if _SUPABASE is not None:
        return _SUPABASE

    if not _is_valid_supabase_url(SUPABASE_URL) or not SUPABASE_KEY:
        return None

    hostname = urlparse(SUPABASE_URL).hostname
    if not _can_resolve_host(hostname):
        return None

    try:
        _SUPABASE = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _SUPABASE
    except Exception:
        return None


def _ensure_backend() -> None:
    """Choose Supabase when it appears reachable, otherwise fall back to SQLite."""
    global _BACKEND
    if _BACKEND == "sqlite":
        _sqlite_connect()
        return

    client = _supabase_connect()
    if client is None:
        _BACKEND = "sqlite"
        _sqlite_connect()


def _using_supabase() -> bool:
    _ensure_backend()
    return _BACKEND == "supabase" and _SUPABASE is not None


def _fallback_to_sqlite(reason: Exception) -> None:
    global _BACKEND
    # Any connect/DNS failure should switch demo to local sqlite.
    _BACKEND = "sqlite"
    _sqlite_connect()


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
    _ensure_backend()
    return _SUPABASE if _using_supabase() else _SQLiteDBAdapter(_sqlite_connect())

def create_owner(email, password_hash, name, business_name, business_type):
    _ensure_backend()
    if _using_supabase():
        try:
            data = {
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "business_name": business_name,
                "business_type": business_type,
                "plan": "basic",
                "is_active": True,
            }
            response = _SUPABASE.table("Owners").insert(data).execute()
            return response
        except Exception as e:
            print(f"CREATE_OWNER ERROR (supabase): {type(e).__name__}: {str(e)}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        owner_id = str(_uuid.uuid4())
        conn.execute(
            """
            INSERT INTO Owners (id, email, password_hash, name, business_name, business_type, plan, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_id,
                email,
                password_hash,
                name,
                business_name,
                business_type,
                "basic",
                1,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()

        class _Resp:
            def __init__(self, data):
                self.data = data

        return _Resp([{"id": owner_id, "email": email}])
    except Exception as e:
        print(f"CREATE_OWNER ERROR (sqlite): {type(e).__name__}: {str(e)}")
        return None

def get_owner_by_whatsapp_number(whatsapp_number):
    _ensure_backend()
    if _using_supabase():
        try:
            response = _SUPABASE.table("Owners").select("*").eq("whatsapp_number", whatsapp_number).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"GET_OWNER_BY_WHATSAPP ERROR (supabase): {type(e).__name__}: {str(e)}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        row = conn.execute("SELECT * FROM Owners WHERE whatsapp_number = ? LIMIT 1", (whatsapp_number,)).fetchone()
        return dict(row) if row else None
    except Exception as e:
        print(f"GET_OWNER_BY_WHATSAPP ERROR (sqlite): {type(e).__name__}: {str(e)}")
        return None

def get_owner_by_meta_phone_number_id(phone_number_id):
    try:
        if not phone_number_id:
            return None

        if _using_supabase():
            for column_name in ("meta_phone_number_id", "phone_number_id"):
                try:
                    response = (
                        _SUPABASE.table("Owners")
                        .select("*")
                        .eq(column_name, str(phone_number_id))
                        .limit(1)
                        .execute()
                    )
                    if response.data:
                        return response.data[0]
                except Exception as e:
                    print(f"GET_OWNER_BY_META_PHONE_NUMBER_ID ERROR (supabase): {e}")
                    _fallback_to_sqlite(e)
                    break

        # SQLite fallback
        try:
            conn = _sqlite_connect()
            row = conn.execute(
                "SELECT * FROM Owners WHERE meta_phone_number_id = ? LIMIT 1", (str(phone_number_id),)
            ).fetchone()
            return dict(row) if row else None
        except Exception:
            return None

        return None
    except Exception as e:
        print(f"GET_OWNER_BY_META_PHONE_NUMBER_ID ERROR: {type(e).__name__}: {str(e)}")
        return None

def get_owner_by_email(email):
    _ensure_backend()
    if _using_supabase():
        try:
            response = _SUPABASE.table("Owners").select("*").eq("email", email).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching owner (supabase): {e}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        row = conn.execute("SELECT * FROM Owners WHERE email = ? LIMIT 1", (email,)).fetchone()
        return dict(row) if row else None
    except Exception as e:
        print(f"Error fetching owner (sqlite): {e}")
        return None

def get_owner_by_id(owner_id):
    oid = normalize_owner_id(owner_id)
    if not oid:
        return None

    _ensure_backend()
    if _using_supabase():
        try:
            response = _SUPABASE.table("Owners").select("*").eq("id", oid).single().execute()
            return response.data
        except Exception as e:
            print(f"Error fetching owner by id (supabase): {e}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        row = conn.execute("SELECT * FROM Owners WHERE id = ? LIMIT 1", (oid,)).fetchone()
        return dict(row) if row else None
    except Exception as e:
        print(f"Error fetching owner by id (sqlite): {e}")
        return None


def owner_exists(owner_id) -> bool:
    try:
        return get_owner_by_id(owner_id) is not None
    except Exception:
        return False

def get_first_owner():
    _ensure_backend()
    if _using_supabase():
        try:
            response = _SUPABASE.table("Owners").select("*").limit(1).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error fetching first owner (supabase): {e}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        row = conn.execute("SELECT * FROM Owners LIMIT 1").fetchone()
        return dict(row) if row else None
    except Exception as e:
        print(f"Error fetching first owner (sqlite): {e}")
        return None

def create_booking(owner_id, customer_name, service, date, phone):
    oid = normalize_owner_id(owner_id)
    if not oid:
        print("CREATE_BOOKING: skipped — invalid owner_id")
        return None

    _ensure_backend()
    if _using_supabase():
        try:
            data = {
                "owner_id": oid,
                "customer_name": customer_name,
                "service": service,
                "date": date,
                "phone": phone,
                "status": "pending",
            }
            print(f"\n=== CREATE BOOKING ===")
            print(f"  owner_id: {oid}")
            print(f"  customer_name: {customer_name}")
            print(f"  service: {service}")
            print(f"  date: {date}")
            print(f"  phone: {phone}")
            response = _SUPABASE.table("bookings").insert(data).execute()
            print(f"  RESULT: {response.data}")
            return response
        except Exception as e:
            print(f"Error creating booking (supabase): {e}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        booking_id = str(_uuid.uuid4())
        conn.execute(
            """
            INSERT INTO bookings (id, owner_id, customer_name, service, date, phone, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking_id,
                oid,
                customer_name,
                service,
                date,
                phone,
                "pending",
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()

        class _Resp:
            def __init__(self, data):
                self.data = data

        return _Resp([{"id": booking_id, "owner_id": oid}])
    except Exception as e:
        print(f"Error creating booking (sqlite): {e}")
        return None

def get_bookings_by_owner(owner_id):
    oid = normalize_owner_id(owner_id)
    if not oid:
        print("GET_BOOKINGS_BY_OWNER: empty owner_id after normalize")
        return []

    _ensure_backend()
    if _using_supabase():
        try:
            print(f"\n=== GET BOOKINGS BY OWNER ===")
            print(f"  Querying owner_id: {oid!r} (type: {type(oid).__name__})")
            response = _SUPABASE.table("bookings").select("*").eq("owner_id", oid).execute()
            print(f"  Found {len(response.data) if response.data else 0} bookings")
            if response.data:
                for b in response.data:
                    print(
                        f"    - {b.get('customer_name')} | {b.get('service')} | {b.get('date')} | {b.get('status')}"
                    )
            return response.data
        except Exception as e:
            print(f"Error fetching bookings (supabase): {e}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        rows = conn.execute(
            "SELECT * FROM bookings WHERE owner_id = ? ORDER BY created_at DESC", (oid,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error fetching bookings (sqlite): {e}")
        return []

def count_bookings_total(owner_id):
    """Count all bookings for this owner (Supabase)."""
    try:
        oid = normalize_owner_id(owner_id)
        if not oid:
            return 0
        _ensure_backend()
        if _using_supabase():
            response = (
                _SUPABASE.table("bookings")
                .select("id", count="exact")
                .eq("owner_id", oid)
                .execute()
            )
            return response.count if response.count is not None else 0

        conn = _sqlite_connect()
        row = conn.execute("SELECT COUNT(*) AS c FROM bookings WHERE owner_id = ?", (oid,)).fetchone()
        return int(row["c"]) if row else 0
    except Exception as e:
        print(f"count_bookings_total error: {e}")
        return 0


def count_bookings_pending(owner_id):
    """Count bookings with status pending for this owner."""
    try:
        oid = normalize_owner_id(owner_id)
        if not oid:
            return 0
        _ensure_backend()
        if _using_supabase():
            response = (
                _SUPABASE.table("bookings")
                .select("id", count="exact")
                .eq("owner_id", oid)
                .eq("status", "pending")
                .execute()
            )
            return response.count if response.count is not None else 0

        conn = _sqlite_connect()
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM bookings WHERE owner_id = ? AND status = ?", (oid, "pending")
        ).fetchone()
        return int(row["c"]) if row else 0
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
        _ensure_backend()
        if _using_supabase():
            response = (
                _SUPABASE.table("bookings")
                .select("id", count="exact")
                .eq("owner_id", oid)
                .eq("status", "confirmed")
                .gte("date", start)
                .lt("date", end)
                .execute()
            )
            return response.count if response.count is not None else 0

        conn = _sqlite_connect()
        # SQLite stores 'date' as text; for demo treat string prefix YYYY-MM-DD
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM bookings
            WHERE owner_id = ? AND status = ? AND substr(date, 1, 10) = ?
            """,
            (oid, "confirmed", today_iso),
        ).fetchone()
        return int(row["c"]) if row else 0
    except Exception as e:
        print(f"count_bookings_confirmed_today error: {e}")
        return 0


def update_booking_status(booking_id, status):
    _ensure_backend()
    if _using_supabase():
        try:
            response = _SUPABASE.table("bookings").update({"status": status}).eq("id", str(booking_id)).execute()
            return response
        except Exception as e:
            print(f"Error updating booking status (supabase): {e}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, str(booking_id)))
        conn.commit()

        class _Resp:
            def __init__(self, data):
                self.data = data

        return _Resp([{"id": str(booking_id), "status": status}])
    except Exception as e:
        print(f"Error updating booking status (sqlite): {e}")
        return None

def update_owner_settings(
    owner_id,
    business_name,
    ai_instructions,
    whatsapp_number=None,
    whatsapp_provider=None,
    meta_phone_number_id=None,
    meta_access_token=None,
):
    oid = normalize_owner_id(owner_id)
    if not oid:
        return None

    _ensure_backend()
    if _using_supabase():
        try:
            data = {"business_name": business_name, "ai_instructions": ai_instructions}
            if whatsapp_number:
                data["whatsapp_number"] = whatsapp_number
            if whatsapp_provider:
                data["whatsapp_provider"] = whatsapp_provider
            if meta_phone_number_id is not None:
                data["meta_phone_number_id"] = meta_phone_number_id.strip()
            if meta_access_token is not None:
                data["meta_access_token"] = meta_access_token.strip()
            response = _SUPABASE.table("Owners").update(data).eq("id", oid).execute()
            return response
        except Exception as e:
            print(f"Error updating owner settings (supabase): {e}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        updates: list[str] = []
        values: list[Any] = []
        if business_name is not None:
            updates.append("business_name = ?")
            values.append(business_name)
        if ai_instructions is not None:
            updates.append("ai_instructions = ?")
            values.append(ai_instructions)
        if whatsapp_number is not None:
            updates.append("whatsapp_number = ?")
            values.append(whatsapp_number)
        if whatsapp_provider is not None:
            updates.append("whatsapp_provider = ?")
            values.append(whatsapp_provider)
        if meta_phone_number_id is not None:
            updates.append("meta_phone_number_id = ?")
            values.append(meta_phone_number_id.strip())
        if meta_access_token is not None:
            updates.append("meta_access_token = ?")
            values.append(meta_access_token.strip())
        if not updates:
            return None
        values.append(oid)
        conn.execute(f"UPDATE Owners SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

        class _Resp:
            def __init__(self, data):
                self.data = data

        return _Resp([{"id": oid}])
    except Exception as e:
        print(f"Error updating owner settings (sqlite): {e}")
        return None


def update_owner_plan(owner_id, plan_name):
    oid = normalize_owner_id(owner_id)
    if not oid:
        return None

    _ensure_backend()
    if _using_supabase():
        try:
            return (
                _SUPABASE.table("Owners")
                .update({"plan": plan_name, "is_active": True})
                .eq("id", oid)
                .execute()
            )
        except Exception as e:
            print(f"Error updating owner plan (supabase): {e}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        conn.execute("UPDATE Owners SET plan = ?, is_active = 1 WHERE id = ?", (plan_name, oid))
        conn.commit()

        class _Resp:
            def __init__(self, data):
                self.data = data

        return _Resp([{"id": oid, "plan": plan_name}])
    except Exception as e:
        print(f"Error updating owner plan (sqlite): {e}")
        return None

def create_demo_request(name, business_name, whatsapp_number, business_type, preferred_time):
    _ensure_backend()
    if _using_supabase():
        try:
            data = {
                "name": name,
                "business_name": business_name,
                "whatsapp_number": whatsapp_number,
                "business_type": business_type,
                "preferred_time": preferred_time,
            }
            response = _SUPABASE.table("demo_requests").insert(data).execute()
            return response
        except Exception as e:
            print(f"Error creating demo request (supabase): {e}")
            _fallback_to_sqlite(e)

    try:
        conn = _sqlite_connect()
        rid = str(_uuid.uuid4())
        conn.execute(
            """
            INSERT INTO demo_requests (id, name, business_name, whatsapp_number, business_type, preferred_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rid,
                name,
                business_name,
                whatsapp_number,
                business_type,
                preferred_time,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()

        class _Resp:
            def __init__(self, data):
                self.data = data

        return _Resp([{"id": rid}])
    except Exception as e:
        print(f"Error creating demo request (sqlite): {e}")
        return None
