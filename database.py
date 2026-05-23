"""
database.py — Supabase (PostgreSQL) persistence layer for Nexus Excel AI.
Manages users table: email, plan_type, payment status, trial dates, expiry_date, and passwords.
"""

import streamlit as st
import hashlib
import secrets
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Optional

PLAN_LABELS = {
    "none":         "No Plan",
    "trial":        "2-Day Trial",
    "free_trial":   "7-Day Free Trial",
    "basic":        "Basic",
    "premium":      "Premium",
    "pro":          "Pro",
}

# ── Password Hashing Engine (Standard PBKDF2-HMAC-SHA256) ──────
def hash_password(password: str) -> str:
    """Securely hash a password using PBKDF2 HMAC SHA-256 with a salt."""
    salt = secrets.token_hex(16)
    # Using 100,000 iterations for highly secure password derivation
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{key.hex()}"

def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify a provided password against a stored PBKDF2 hash."""
    if not stored_hash or ":" not in stored_hash:
        return False
    try:
        salt, stored_key_hex = stored_hash.split(":")
        key = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt.encode(), 100000)
        return key.hex() == stored_key_hex
    except Exception:
        return False

# ── Connection Setup ──────────────────────────────────────────
@st.cache_resource
def init_connection() -> Optional[Client]:
    """Initializes the Supabase client once and caches it for performance."""
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if not url or not key:
            print("Supabase Warning: Connection credentials missing in st.secrets.")
            return None
        return create_client(url, key)
    except Exception as e:
        print(f"Supabase Client Instantiation Error: {e}")
        return None

try:
    supabase = init_connection()
except Exception as e:
    supabase = None
    print(f"Supabase Connection Error: {e}")

# ── Helpers ───────────────────────────────────────────────────
def _format_user(user: dict) -> dict:
    """Ensures the Supabase dictionary perfectly matches a standardized format with strict types."""
    if user:
        # Guarantee has_payment_on_file is a standard boolean
        val = user.get("has_payment_on_file", 0)
        if isinstance(val, bool):
            user["has_payment_on_file"] = val
        else:
            user["has_payment_on_file"] = bool(int(val) if str(val).isdigit() else val)
    return user

# ── Auth & CRUD ───────────────────────────────────────────────
def get_user(email: str) -> Optional[dict]:
    """Return user dict or None if not found."""
    if not supabase: 
        return None
    try:
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data and len(response.data) > 0:
            return _format_user(response.data[0])
        return None
    except Exception as e:
        print(f"Database error in get_user: {e}")
        return None

def verify_or_create_user(email: str, password: str):
    """
    Checks if email exists. If so, validates password (with auto hashing-upgrade support).
    If not, creates a new user with a hashed password.
    Returns user dict on success, False on incorrect password.
    """
    if not supabase: 
        return False
    
    user = get_user(email)
    
    if user:
        stored_pw = user.get("password")
        if stored_pw is None:
            # Handle legacy user with null password (assigning a password on first login)
            try:
                hashed_pw = hash_password(password)
                supabase.table("users").update({"password": hashed_pw}).eq("email", email).execute()
                user["password"] = hashed_pw
                return user
            except Exception as e:
                print(f"Error assigning password: {e}")
                return False
                
        # Validate password (checking if it's already a secure hash or if we need to migrate it)
        if ":" in stored_pw:
            if verify_password(stored_pw, password):
                return user
            return False
        else:
            # Plaintext fallback migration
            if stored_pw == password:
                try:
                    hashed_pw = hash_password(password)
                    supabase.table("users").update({"password": hashed_pw}).eq("email", email).execute()
                    user["password"] = hashed_pw
                    return user
                except Exception as e:
                    print(f"Error migrating password hash: {e}")
                    return user  # Return user anyway, since plaintext matched
            return False
    else:
        # Create a new user with a hashed password
        try:
            hashed_pw = hash_password(password)
            new_user = {
                "email": email,
                "password": hashed_pw,
                "plan_type": "none",
                "has_payment_on_file": False
            }
            res = supabase.table("users").insert(new_user).execute()
            return _format_user(res.data[0]) if res.data else False
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

def admin_create_user(email: str, password: str, plan_type: str, duration_days: int) -> bool:
    """Admin function: Inserts or updates a user with hashed password and specific expiration."""
    if not supabase: 
        return False
    try:
        if plan_type.lower() == "trial":
            duration_days = 2
            
        expiry_date = (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d %H:%M:%S")
        hashed_pw = hash_password(password)
        
        user = get_user(email)
        payload = {
            "password": hashed_pw,
            "plan_type": plan_type,
            "has_payment_on_file": True,
            "expiry_date": expiry_date,
            "trial_end_date": None 
        }
        
        if user:
            supabase.table("users").update(payload).eq("email", email).execute()
        else:
            payload["email"] = email
            supabase.table("users").insert(payload).execute()
            
        return True
    except Exception as e:
        print(f"Admin create user error: {e}")
        return False

def activate_plan(email: str, plan_type: str) -> Optional[dict]:
    """
    Set plan + mark payment received.
    Automatically assigns expiry_date for universal compliance.
    """
    if not supabase: 
        return None
    try:
        now = datetime.now()
        if plan_type == "free_trial":
            trial_start = now.strftime("%Y-%m-%d %H:%M:%S")
            trial_end   = (now + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            
            supabase.table("users").update({
                "plan_type": plan_type,
                "has_payment_on_file": True,
                "trial_start_date": trial_start,
                "trial_end_date": trial_end,
                "expiry_date": trial_end
            }).eq("email", email).execute()
        elif plan_type == "trial":
            trial_start = now.strftime("%Y-%m-%d %H:%M:%S")
            trial_end   = (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
            
            supabase.table("users").update({
                "plan_type": plan_type,
                "has_payment_on_file": True,
                "trial_start_date": trial_start,
                "trial_end_date": trial_end,
                "expiry_date": trial_end
            }).eq("email", email).execute()
        else:
            supabase.table("users").update({
                "plan_type": plan_type,
                "has_payment_on_file": True,
                "expiry_date": None  # Indefinite standard SaaS plan unless manually revoked
            }).eq("email", email).execute()
            
        return get_user(email)
    except Exception as e:
        print(f"Error in activate_plan: {e}")
        return None

def has_used_trial(email: str) -> bool:
    """Return True if this email has EVER activated a free trial."""
    user = get_user(email)
    if not user: 
        return False
    return user.get("trial_start_date") is not None

def is_account_expired(user: dict) -> bool:
    """Universal Check: Returns True if the current date is past the user's expiry_date."""
    if not user or not user.get("expiry_date"):
        return False  # Indefinite access if no expiry is set
    try:
        # Slicing [:19] protects against minor timezone/Supabase formatting differences
        end = datetime.strptime(str(user["expiry_date"])[:19], "%Y-%m-%d %H:%M:%S")
        return datetime.now() > end
    except Exception:
        return False

def days_remaining(user: dict) -> int:
    """Return whole days left in access (0 if expired)."""
    if not user.get("expiry_date"):
        return 0
    try:
        end  = datetime.strptime(str(user["expiry_date"])[:19], "%Y-%m-%d %H:%M:%S")
        diff = end - datetime.now()
        return max(0, diff.days)
    except Exception:
        return 0

# ── Admin Analytics & Control ──────────────────────────────────
def get_admin_stats() -> dict:
    """Returns aggregated data for the admin dashboard from Supabase."""
    if not supabase: 
        return {"total_users": 0, "plans": {}}
    try:
        count_res = supabase.table("users").select("id", count="exact").execute()
        total = count_res.count if count_res.count is not None else 0
        
        plan_res = supabase.table("users").select("plan_type").execute()
        plans = {}
        for row in plan_res.data:
            pt = row.get("plan_type", "none")
            plans[pt] = plans.get(pt, 0) + 1
            
        return {"total_users": total, "plans": plans}
    except Exception as e:
        print(f"Error in get_admin_stats: {e}")
        return {"total_users": 0, "plans": {}}

def block_user_trial(email: str) -> bool:
    """Manually forces a user's account/trial to expire."""
    if not supabase: 
        return False
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        supabase.table("users").update({
            "expiry_date": yesterday, 
            "trial_end_date": yesterday
        }).eq("email", email).execute()
        return True
    except Exception as e:
        print(f"Error in block_user_trial: {e}")
        return False
