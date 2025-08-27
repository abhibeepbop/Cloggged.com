from fastapi import FastAPI, HTTPException, status, Depends, Request, Security
from fastapi import Body
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status, Request
from firebase_admin import firestore
from datetime import datetime
from google_auth_oauthlib.flow import Flow
import os
import json
from urllib.parse import urlencode
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from apscheduler.schedulers.background import BackgroundScheduler
import threading
from firebase_admin import firestore
from firebase_manager import FirebaseManager
from email_classifier import EmailClassifier
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware
from stripe_handler import StripeHandler
import stripe
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore as gcf

app = FastAPI()

# Frontend base URL and CORS origins
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ADDITIONAL_FRONTEND_ORIGIN = os.getenv("ADDITIONAL_FRONTEND_ORIGIN", "")
_origins = [FRONTEND_URL]
if ADDITIONAL_FRONTEND_ORIGIN and ADDITIONAL_FRONTEND_ORIGIN not in _origins:
    _origins.append(ADDITIONAL_FRONTEND_ORIGIN)
if "http://localhost:3000" not in _origins:
    _origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase Admin from environment (Render/production)
try:
    firebase_admin.get_app()
except ValueError:
    from config import (
        FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY_ID, FIREBASE_PRIVATE_KEY,
        FIREBASE_CLIENT_EMAIL, FIREBASE_CLIENT_ID
    )
    sa_info = {
        "type": "service_account",
        "project_id": FIREBASE_PROJECT_ID,
        "private_key_id": FIREBASE_PRIVATE_KEY_ID,
        "private_key": (FIREBASE_PRIVATE_KEY or "").replace('\\n', '\n'),
        "client_email": FIREBASE_CLIENT_EMAIL,
        "client_id": FIREBASE_CLIENT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{FIREBASE_CLIENT_EMAIL}",
    }
    cred = credentials.Certificate(sa_info)
    firebase_admin.initialize_app(cred)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/oauth-callback")

GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "project_id": os.getenv("FIREBASE_PROJECT_ID", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI],
        "javascript_origins": []
    }
}

bearer_scheme = HTTPBearer()

def verify_firebase_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    id_token = auth_header.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        # Ensure user profile exists in Firestore
        db = firestore.client()
        user_ref = db.collection("identifier").document(decoded_token["uid"])
        user_doc = user_ref.get()
        if not user_doc.exists:
            # Create user profile
            user_ref.set({
                "uid": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "created_at": datetime.utcnow(),
                "settings": {},
                "gmail_tokens": None
            })
        return decoded_token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token")


# Unified access check used across auth flows
def user_can_access_dashboard(user_data: dict) -> bool:
    """Return True if the user should see the dashboard (active sub or active trial)."""
    try:
        now_ts = int(datetime.utcnow().timestamp())
    except Exception:
        now_ts = 0

    def to_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value == 1
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y"}
        return False

    # Relaxed rule: subscribed flag OR free trial is enough (coerce string/number values)
    has_active_subscription = to_bool(user_data.get("subscribed")) or (
        user_data.get("subscription_status") == "active" and to_bool(user_data.get("payment_completed"))
    )

    trial_end = user_data.get("trial_end")
    in_free_trial = to_bool(user_data.get("free_trial")) or (
        isinstance(trial_end, (int, float)) and trial_end > now_ts
    )

    return bool(has_active_subscription or in_free_trial)

# --- Session (JWT) helpers ---
import jwt

JWT_SECRET = os.getenv("APP_JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"
SESSION_COOKIE_NAME = "session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days

def create_session_jwt(user_id: str) -> str:
    now = int(datetime.utcnow().timestamp())
    payload = {"sub": user_id, "iat": now, "exp": now + SESSION_TTL_SECONDS, "typ": "session"}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_session_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

def set_session_cookie(response: JSONResponse, token: str):
    # Use secure cookies in production (cross-site Vercel ↔ Render)
    secure_flag = os.getenv("COOKIE_SECURE", "true").strip().lower() == "true"
    same_site = "none" if secure_flag else "lax"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=secure_flag,
        samesite=same_site,
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )

def clear_session_cookie(response: JSONResponse):
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")

def get_session_user_id_or_401(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Missing session cookie")
    try:
        payload = decode_session_jwt(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid session payload")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session token")

# --- Helpers: JSON-safe serialization for Firestore data ---
def _json_safe(value):
    try:
        # Firestore timestamp objects (DatetimeWithNanoseconds) and datetime
        if hasattr(value, "__class__") and value.__class__.__name__.endswith("DatetimeWithNanoseconds"):
            return int(value.timestamp())
        from datetime import datetime as _dt
        if isinstance(value, _dt):
            return int(value.timestamp())
    except Exception:
        pass
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value

def _sanitize_user_for_client(user: dict) -> dict:
    """Remove sensitive fields before sending user data to the frontend."""
    if not isinstance(user, dict):
        return {}
    redacted = dict(user)
    # Never expose OAuth tokens or secrets to the browser
    redacted.pop("gmail_tokens", None)
    return redacted

# --- Billing/access helpers ---
def _compute_can_access(user: dict) -> bool:
    try:
        now_ts = int(datetime.utcnow().timestamp())
    except Exception:
        now_ts = 0
    subscribed = bool(user.get("subscribed") is True)
    trial_end = user.get("trial_end")
    in_trial = isinstance(trial_end, (int, float)) and trial_end > now_ts
    return bool(subscribed or in_trial)

# --- Session (JWT) helpers ---
 


def _normalize_category(raw_category: str) -> str:
    if not raw_category:
        return "Other"
    c = str(raw_category).strip().lower()
    if c == 'spam':
        return 'Spam'
    if c in ['not_spam', 'notspam', 'ham', 'nonspam', 'not spam']:
        return 'Other'
    if c in ['work', 'professional', 'business']:
        return 'Work'
    if c in ['finance', 'financial', 'banking']:
        return 'Finance'
    if c in ['security', 'secure', 'account']:
        return 'Security'
    if c in ['otps', 'otp', 'verification', 'code']:
        return 'OTPs'
    if c in ['family', 'personal', 'friends']:
        return 'Family'
    if c in ['urgent', 'important', 'priority']:
        return 'Urgent'
    return 'Other'


def _update_user_stats_on_classification(user_id: str, classification: str, ts_seconds: int) -> None:
    try:
        db = firestore.client()
        stats_ref = db.collection('identifier').document(user_id).collection('meta').document('stats')
        from datetime import datetime as _dt
        date_key = _dt.utcfromtimestamp(ts_seconds).strftime('%Y-%m-%d')
        category = _normalize_category(classification)
        updates = {
            'total_processed': gcf.Increment(1),
            f'category_counts.{category}': gcf.Increment(1),
            f'daily.{date_key}.processed': gcf.Increment(1),
            'updated_at': ts_seconds,
        }
        if category == 'Spam':
            updates[f'daily.{date_key}.spam'] = gcf.Increment(1)
        stats_ref.set(updates, merge=True)
    except Exception as _:
        # Non-fatal; classification persists even if stats update fails
        pass


def _get_env_int(name: str, default_value: int) -> int:
    try:
        return int(os.getenv(name, str(default_value)))
    except Exception:
        return default_value


def _get_monthly_processed_count(user_id: str) -> int:
    """Sum processed counts for the current calendar month from the aggregated stats doc."""
    try:
        db = firestore.client()
        stats_ref = db.collection('identifier').document(user_id).collection('meta').document('stats')
        snap = stats_ref.get()
        if not snap.exists:
            return 0
        stats = snap.to_dict() or {}
        daily = stats.get('daily') or {}
        from datetime import datetime as _dt
        now = _dt.utcnow()
        month_prefix = now.strftime('%Y-%m-')  # e.g., 2025-08-
        total = 0
        for day_key, entry in daily.items():
            try:
                if str(day_key).startswith(month_prefix):
                    total += int((entry or {}).get('processed') or 0)
            except Exception:
                continue
        return total
    except Exception:
        return 0


@app.post("/rebuild-stats")
def rebuild_stats(request: Request, days: int = 30):
    """Rebuild aggregated stats for the current user from existing email_classifications.
    Time-windowed (default 30 days) to control reads. Uses same normalization as classifier.
    """
    user_id = get_session_user_id_or_401(request)
    try:
        from datetime import datetime, timedelta
        db = firestore.client()
        coll = db.collection('identifier').document(user_id).collection('email_classifications')

        now_dt = datetime.utcnow().replace(tzinfo=None)
        start_dt = now_dt - timedelta(days=max(int(days), 1))

        # Fetch windowed docs; support both int seconds and Firestore Timestamp
        docs = []
        try:
            q = coll.where('timestamp', '>=', int(start_dt.timestamp()))
            docs = list(q.stream())
        except Exception:
            try:
                q = coll.where('timestamp', '>=', start_dt)
                docs = list(q.stream())
            except Exception:
                docs = list(coll.stream())

        total = 0
        spam_total = 0
        category_counts: dict[str, int] = {}
        daily: dict[str, dict] = {}

        for d in docs:
            data = d.to_dict() or {}
            ts = data.get('timestamp')
            if ts is None:
                continue
            if isinstance(ts, (int, float)):
                # seconds vs ms
                ts_sec = int(ts / 1000) if ts > 1000000000000 else int(ts)
            else:
                try:
                    ts_sec = int(ts.timestamp())
                except Exception:
                    continue

            from datetime import datetime as _dt
            date_key = _dt.utcfromtimestamp(ts_sec).strftime('%Y-%m-%d')

            raw_cat = str(data.get('classification') or '').strip()
            cat = _normalize_category(raw_cat)

            total += 1
            category_counts[cat] = category_counts.get(cat, 0) + 1

            entry = daily.get(date_key) or { 'processed': 0, 'spam': 0 }
            entry['processed'] = int(entry['processed']) + 1
            if cat == 'Spam' or raw_cat.lower() in {'spam', 'not_spam', 'notspam'}:
                entry['spam'] = int(entry['spam']) + 1
                spam_total += 1
            daily[date_key] = entry

        stats_ref = db.collection('identifier').document(user_id).collection('meta').document('stats')
        update_doc = {
            'total_processed': int(total),
            'category_counts': {k: int(v) for k, v in category_counts.items()},
            'daily': daily,
            'updated_at': int(datetime.utcnow().timestamp()),
        }
        stats_ref.set(update_doc, merge=True)
        return { 'success': True, 'recounted': int(total), 'categories': update_doc.get('category_counts', {}) }
    except Exception as e:
        return { 'success': False, 'error': str(e) }

@app.get("/")
def read_root(code: str = None, state: str = None):
    """Handle OAuth callback at root path since redirect_uri is http://localhost"""
    if code and state:
        return gmail_oauth2callback(code, state)
    return {"status": "ok", "message": "Mail Agent API is running"}


 

@app.get("/firestore-test")
def firestore_test():
    try:
        db = firestore.client()
        # Write a test document
        doc_ref = db.collection("test_collection").document("test_doc")
        doc_ref.set({"message": "Hello from FastAPI!"})
        # Read it back
        doc = doc_ref.get()
        return {"success": True, "data": doc.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}



@app.get("/check-user/{email}")
def check_user(email: str):
    """Check if a user exists in Firebase and their subscription status"""
    try:
        db = firestore.client()
        users_ref = db.collection("identifier")
        query = users_ref.where("email", "==", email).limit(1)
        docs = query.get()
        
        if docs:
            user_doc = docs[0]
            user_data = user_doc.to_dict()
            return {
                "exists": True,
                "user_id": user_doc.id,
                "subscription_status": user_data.get("subscription_status"),
                "payment_completed": user_data.get("payment_completed"),
                "email": user_data.get("email"),
                "full_data": user_data
            }
        else:
            return {"exists": False, "message": f"No user found with email {email}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/protected")
def protected_route(
    user=Depends(verify_firebase_token),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    return {"message": f"Hello, {user['uid']}!"}

@app.get("/auth/google")
def google_auth():
    """Initial Google OAuth for sign-in (no Firebase token required)"""
    print("Starting Google OAuth for sign-in...")
    # Start OAuth flow for Gmail
    flow = Flow.from_client_config(GOOGLE_CLIENT_CONFIG, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
    # Use a temporary state for sign-in
    # Do not force prompt=consent here to avoid repeated consent screens for returning users
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state="signin"  # Use "signin" to distinguish from Gmail connection
    )
    print("AUTH_URL:", auth_url)
    # Redirect directly to Google OAuth
    return RedirectResponse(url=auth_url)

@app.get("/gmail/connect")
def gmail_connect(user=Depends(verify_firebase_token)):
    print("GOOGLE_REDIRECT_URI:", GOOGLE_REDIRECT_URI)
    print("GOOGLE_SCOPES:", GOOGLE_SCOPES)
    # Start OAuth flow for Gmail
    flow = Flow.from_client_config(GOOGLE_CLIENT_CONFIG, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
    # Use user's UID as state to identify them in callback
    # If the user already has a refresh token saved, skip OAuth and go straight to payment
    try:
        db = firestore.client()
        user_doc = db.collection("identifier").document(user["uid"]).get()
        if user_doc.exists:
            user_data = user_doc.to_dict() or {}
            if user_data.get("gmail_tokens", {}).get("refresh_token"):
                return RedirectResponse(url=f"{FRONTEND_URL}/payment")
    except Exception:
        pass

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=user["uid"]
    )
    print("AUTH_URL:", auth_url)
    print("AUTH_URL length:", len(auth_url))
    # Check if redirect_uri parameter is in the URL
    if "redirect_uri=" in auth_url:
        print("Redirect URI parameter found in URL")
    else:
        print("WARNING: Redirect URI parameter NOT found in URL")
    # Redirect directly to Google OAuth
    return RedirectResponse(url=auth_url)

@app.get("/gmail/oauth2callback")
def gmail_oauth2callback(code: str, state: str):
    try:
        print("=== OAUTH CALLBACK STARTED ===")
        print("OAuth callback received - code:", code[:20] + "..." if code else "None")
        print("OAuth callback received - state:", state)
        print("GOOGLE_REDIRECT_URI:", GOOGLE_REDIRECT_URI)
        
        # state is either "signin" or the user's UID
        flow = Flow.from_client_config(GOOGLE_CLIENT_CONFIG, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
        print("Flow created successfully")
        
        flow.fetch_token(code=code)
        print("Token fetched successfully")
        
        credentials = flow.credentials
        tokens = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None
        }
        print("Tokens prepared successfully")
        
        if state == "signin":
            # This is initial sign-in, check if user already has subscription
            print("=== INITIAL SIGN-IN FLOW ===")
            
            # Get user info from Google
            from googleapiclient.discovery import build
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            user_email = user_info.get('email')
            user_name = user_info.get('name', 'User')
            
            print(f"User signed in: {user_email}")
            print(f"User name: {user_name}")
            
            # Check if user exists in Firebase with subscription
            db = firestore.client()
            users_ref = db.collection("identifier")
            query = users_ref.where("email", "==", user_email).limit(1)
            docs = query.get()
            
            print(f"Checking Firebase for user: {user_email}")
            print(f"Found {len(list(docs))} documents")
            
            if docs:
                user_doc = docs[0]
                user_data = user_doc.to_dict()
                
                print(f"User data found: {user_data}")
                print(f"Free trial: {user_data.get('free_trial')}")
                print(f"Subscribed: {user_data.get('subscribed')}")
                
                # Persist Gmail tokens on initial sign-in as well (automate connection)
                try:
                    existing_tokens = (user_data or {}).get("gmail_tokens") or {}
                    if not tokens.get("refresh_token"):
                        tokens["refresh_token"] = existing_tokens.get("refresh_token")
                    user_doc.reference.update({
                        "gmail_tokens": tokens,
                        "authflow": True,
                        "consent": True
                    })
                    print("Stored gmail_tokens on initial sign-in and set authflow=True")
                except Exception as e:
                    print(f"Error storing gmail_tokens on sign-in: {e}")
                print(f"Set authflow to True for user {user_email}")
                
                # Unified access check
                if user_can_access_dashboard(user_data):
                    print("Access granted by unified rule, redirecting to dashboard")
                    try:
                        # Create session and set cookie
                        session_token = create_session_jwt(user_doc.id)
                        resp = RedirectResponse(url=f"{FRONTEND_URL}/dashboard")
                        set_session_cookie(resp, session_token)
                        return resp
                    except Exception as e:
                        print(f"Error creating session token: {e}")
                        resp = RedirectResponse(url=f"{FRONTEND_URL}/dashboard")
                        return resp
                else:
                    print("Access denied by unified rule, redirecting to pricing (keep session)")
                    try:
                        session_token = create_session_jwt(user_doc.id)
                        resp = RedirectResponse(url=f"{FRONTEND_URL}/pricing")
                        set_session_cookie(resp, session_token)
                        return resp
                    except Exception:
                        return RedirectResponse(url=f"{FRONTEND_URL}/pricing")
            else:
                print(f"New user {user_email}, creating user record and redirecting appropriately")
                # Create new user record with authflow set to True
                new_user_data = {
                    "email": user_email,
                    "name": user_name,
                    "picture": user_info.get('picture', ''),
                    "subscribed": False,
                    "payment_completed": False,
                    "subscription_status": "inactive",
                    "created_at": int(datetime.utcnow().timestamp()),
                    "email_processing_enabled": True,
                    # Persist Gmail tokens for new users on sign-in
                    "gmail_tokens": tokens,
                    "authflow": True,
                    "consent": True
                }
                
                # Add to Firebase
                new_user_ref = users_ref.add(new_user_data)
                print(f"Created new user {user_email} with authflow=True")
                
                # Unified access check for brand new user
                # Resolve user id for session regardless of access
                try:
                    new_user_id = new_user_ref[1].id  # type: ignore[index]
                except Exception:
                    docs2 = users_ref.where("email", "==", user_email).limit(1).get()
                    new_user_id = docs2[0].id if docs2 else ""
                try:
                    if new_user_id:
                        session_token = create_session_jwt(new_user_id)
                        # If they can access, send to dashboard; else send to pricing but keep session
                        target = f"{FRONTEND_URL}/dashboard" if user_can_access_dashboard(new_user_data) else f"{FRONTEND_URL}/pricing"
                        resp = RedirectResponse(url=target)
                        set_session_cookie(resp, session_token)
                        return resp
                except Exception:
                    pass
                # Fallback redirect without cookie
                target = f"{FRONTEND_URL}/dashboard" if user_can_access_dashboard(new_user_data) else f"{FRONTEND_URL}/pricing"
                return RedirectResponse(url=target)
        else:
            # This is Gmail connection for existing user
            # Store tokens in Firestore under users/<uid>/gmail_tokens
            db = firestore.client()
            user_ref = db.collection("identifier").document(state)
            # If we already have a refresh token stored, do not overwrite with None from Google
            existing = user_ref.get().to_dict() or {}
            existing_tokens = existing.get("gmail_tokens") or {}
            if not tokens.get("refresh_token"):
                tokens["refresh_token"] = existing_tokens.get("refresh_token")
            user_ref.update({
                "gmail_tokens": tokens,
                "authflow": True  # User has now granted Gmail access
            })
            print("Tokens stored in Firebase successfully, authflow set to True")
            
            # Maintain session cookie if present; otherwise create one
            user_id = state
            try:
                resp = RedirectResponse(url=f"{FRONTEND_URL}/payment")
                # Ensure session cookie exists
                if user_id:
                    session_token = create_session_jwt(user_id)
                    set_session_cookie(resp, session_token)
                return resp
            except Exception:
                return RedirectResponse(url=f"{FRONTEND_URL}/payment")
    except Exception as e:
        print(f"Error in OAuth callback: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def get_gmail_service_for_user(uid):
    db = firestore.client()
    user_ref = db.collection("identifier").document(uid)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise Exception("User not found")
    user_data = user_doc.to_dict()
    if not user_data:
        raise Exception("User not found")
    tokens = user_data.get("gmail_tokens")
    if not tokens:
        raise Exception("No Gmail tokens found for user")
    creds = Credentials(
        tokens.get("token"),
        refresh_token=tokens.get("refresh_token"),
        token_uri=tokens.get("token_uri"),
        client_id=tokens.get("client_id"),
        client_secret=tokens.get("client_secret"),
        scopes=tokens.get("scopes")
    )
    service = build("gmail", "v1", credentials=creds)
    return service

def fetch_recent_emails_for_user(uid, max_results=5):
    service = get_gmail_service_for_user(uid)
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
        subject = ''
        snippet = msg_detail.get('snippet', '')
        headers = msg_detail.get('payload', {}).get('headers', [])
        for header in headers:
            if header.get('name', '').lower() == 'subject':
                subject = header.get('value', '')
                break
        emails.append({'id': msg['id'], 'subject': subject, 'snippet': snippet})
    return emails

@app.get("/gmail/fetch-emails/{uid}")
def gmail_fetch_emails(uid: str):
    try:
        emails = fetch_recent_emails_for_user(uid)
        return {"emails": emails}
    except Exception as e:
        return {"error": str(e)}

firebase_manager = FirebaseManager()
email_classifier = EmailClassifier()
stripe_handler = StripeHandler()

def process_user(user_doc, verbose: bool = False):
    user_data = user_doc.to_dict()
    user_id = user_data.get('uid') or user_doc.id
    user_email = user_data.get('email', 'unknown@email.com')
    tokens = user_data.get('gmail_tokens')
    print(f"Processing user: {user_email}")
    debug = verbose or (user_email == 'vabhi9930@gmail.com')
    
    
    # Check if user has active access using unified rule (subscribed or in trial by trial_end)
    has_access = _compute_can_access(user_data)
    if not has_access:
        print(f"User {user_email} has no active access (subscribed or trial), skipping")
        return
    
    # Check if email processing is enabled for this user
    email_processing_enabled = user_data.get('email_processing_enabled', True)  # Default to True
    processing_disabled_until = user_data.get('processing_disabled_until')
    current_time = int(datetime.utcnow().timestamp())
    
    # Auto-re-enable if disabled time has passed
    if not email_processing_enabled and processing_disabled_until and current_time > processing_disabled_until:
        print(f"Auto-re-enabling email processing for user {user_email}")
        db = firestore.client()
        user_ref = db.collection('identifier').document(user_id)
        user_ref.update({
            'email_processing_enabled': True,
            'processing_disabled_until': None
        })
        email_processing_enabled = True
    
    if not email_processing_enabled:
        print(f"Email processing disabled for user: {user_email}")
        return
    
    if debug:
        try:
            scopes = (tokens or {}).get('scopes') or []
            print(f"Gmail token scopes present: {scopes}")
            print(f"Has gmail.modify: {'https://www.googleapis.com/auth/gmail.modify' in scopes}")
            print(f"Has refresh_token: {bool((tokens or {}).get('refresh_token'))}")
        except Exception:
            pass

    if not tokens:
        print(f"No Gmail tokens found for user: {user_email}")
        return
    try:
        # Initialize Gmail service
        service = get_gmail_service_for_user(user_id)
        print(f"Gmail service initialized for user: {user_email}")
        
        # Define classification labels
        classification_labels = ['Work', 'Finance', 'Security', 'OTPs', 'Family', 'Urgent', 'Spam']
        
        # Get existing Gmail labels
        all_labels = service.users().labels().list(userId='me').execute().get('labels', [])
        
        # Get ALL classification label IDs to exclude (including duplicates)
        classification_label_ids = []
        found_labels = []
        
        # Detailed debug
        if debug:
            # First, show all labels to see what we're working with
            print(f"All Gmail labels for {user_email}:")
            for label in all_labels:
                print(f"  {label['name']} (ID: {label['id']}, Type: {label.get('type', 'unknown')})")
        
        # Now find ALL labels that match our classification categories
        for label in all_labels:
            # Check if this label matches any of our classification categories
            if label['name'] in classification_labels or label['name'] == 'OTP':  # Handle OTPs -> OTP mapping
                classification_label_ids.append(label['id'])
                found_labels.append({
                    'name': label['name'],
                    'id': label['id'],
                    'type': label.get('type', 'unknown')
                })
                if debug:
                    print(f"Found classification label: {label['name']} (ID: {label['id']}, Type: {label.get('type', 'unknown')})")
        
        # Build query to exclude emails with classification labels
        query = 'in:inbox'
        if classification_label_ids:
            for label_id in classification_label_ids:
                query += f' NOT label:{label_id}'
            if debug:
                print(f"Found {len(classification_label_ids)} classification labels to exclude")
                print(f"Classification labels found: {[label['name'] for label in found_labels]}")
                print(f"Label IDs to exclude: {classification_label_ids}")
                print(f"FINAL QUERY: {query}")
        else:
            if debug:
                print("No classification labels found yet")
        
        # Commercial approach: Only exclude our specific classification labels
        if debug:
            print("Using commercial approach: exclude only our classification labels")
        
        # Build query to exclude only our specific classification labels
        # not user created labels works but not good for other users (if they already have labels)
        query = 'in:inbox'
        if found_labels:
            for label in found_labels:
                query += f' NOT label:{label["name"]}'
            if debug:
                print(f"Commercial query: {query}")
                print(f"Only excluding our labels: {[label['name'] for label in found_labels]}")
        else:
            if debug:
                print("No classification labels found to exclude; using bare 'in:inbox' query")
        
        # Enforce monthly cap: stop processing if user exceeded 10,000 emails this month
        monthly_cap = _get_env_int("MONTHLY_EMAIL_CAP", 10000)
        processed_this_month = _get_monthly_processed_count(user_id)
        remaining_quota = max(monthly_cap - processed_this_month, 0)
        if remaining_quota <= 0:
            print(f"Monthly cap reached for {user_email} (cap={monthly_cap}), skipping.")
            return

        # Fetch emails excluding only our classification labels
        # Cap fetch per run to avoid spikes; do not exceed remaining monthly quota
        per_run_limit = min(50, remaining_quota)
        request_params = {
            'userId': 'me',
            'maxResults': per_run_limit,
            'q': query
        }
        
        if debug:
            print(f"Request params: {request_params}")
        results = service.users().messages().list(**request_params).execute()
        messages = results.get('messages', [])
        
        if debug:
            print(f"Fetched {len(messages)} total emails from inbox for user: {user_email}")
        
        if not messages:
            if debug:
                print(f"No new emails to process for user: {user_email}")
            return
        
        # Check which emails already exist in our database
        emails_to_process = []
        emails_already_processed = []
        emails_without_labels = []
        
        for msg in messages:
            email_id = msg['id']
            
            # Check if email exists in Firebase
            existing_classification = firebase_manager.get_email_classification(user_id, email_id)
            
            if existing_classification:
                # Get the email's current labels from Gmail
                try:
                    email_detail = service.users().messages().get(userId='me', id=email_id).execute()
                    email_labels = email_detail.get('labelIds', [])
                    
                    # Check if email has any classification labels by name
                    email_classification_labels = []
                    for label_id in email_labels:
                        for label in all_labels:
                            if label['id'] == label_id and label['name'] in classification_labels:
                                email_classification_labels.append(f"{label['name']}({label_id})")
                                break
                    
                    has_classification_label = len(email_classification_labels) > 0
                    
                    if has_classification_label:
                        emails_already_processed.append({
                            'id': email_id,
                            'classification': existing_classification.get('classification', 'Unknown'),
                            'confidence': existing_classification.get('confidence', 0.0),
                            'gmail_labels': email_labels
                        })
                        
                        # Only show detailed info for vabhi9930@gmail.com
                        if debug:
                            print(f"  Email {email_id[:20]}... has classification label(s): {email_classification_labels}")
                    else:
                        # Email in database but no Gmail label - needs relabeling
                        emails_without_labels.append({
                            'id': email_id,
                            'classification': existing_classification.get('classification', 'Unknown'),
                            'confidence': existing_classification.get('confidence', 0.0),
                            'gmail_labels': email_labels
                        })
                        
                        # Translate label IDs to names
                        label_names = []
                        for label_id in email_labels:
                            for label in all_labels:
                                if label['id'] == label_id:
                                    label_names.append(label['name'])
                                    break
                        
                        if debug:
                            print(f"  Email {email_id[:20]}... in database as '{existing_classification.get('classification', 'Unknown')}' but no Gmail label attached")
                            print(f"    Gmail label IDs: {email_labels}")
                            print(f"    Gmail label names: {label_names}")
                        
                except Exception as e:
                    print(f"  Error getting email {email_id[:20]}... details: {e}")
                    emails_already_processed.append({
                        'id': email_id,
                        'classification': existing_classification.get('classification', 'Unknown'),
                        'confidence': existing_classification.get('confidence', 0.0)
                    })
            else:
                emails_to_process.append(msg)
        
        # Show summary for all users
        print(f"Summary for {user_email}:")
        print(f"  Total emails fetched: {len(messages)}")
        print(f"  Already in database with Gmail labels: {len(emails_already_processed)}")
        print(f"  In database but missing Gmail labels: {len(emails_without_labels)}")
        print(f"  New emails to process: {len(emails_to_process)}")
        
        if emails_without_labels and debug:
            print(f"  Emails needing relabeling: {[email['id'][:20] + '...' for email in emails_without_labels]}")
        
        if not emails_to_process and not emails_without_labels:
            if user_email == 'vabhi9930@gmail.com':
                print(f"All {len(messages)} emails already exist in database for user: {user_email}")
            return
        
        # Process new emails and relabel emails missing Gmail labels
        if debug:
            print(f"\nStarting email processing...")
        
        # Process new emails (classify and label)
        if emails_to_process:
            if debug:
                print(f"Processing {len(emails_to_process)} new emails...")
            
            for email in emails_to_process:
                try:
                    # Get email details
                    email_detail = service.users().messages().get(userId='me', id=email['id']).execute()
                    subject = ''
                    headers = email_detail.get('payload', {}).get('headers', [])
                    for header in headers:
                        if header.get('name', '').lower() == 'subject':
                            subject = header.get('value', '')
                            break
                    
                    snippet = email_detail.get('snippet', '')
                    
                    # Classify the email
                    result = email_classifier.classify_single_email(subject, snippet, email['id'])
                    classification = result.get('classification', 'Spam')
                    confidence = result.get('confidence', 0.5)
                    if debug:
                        print(f"Classified {email['id'][:20]}... as '{classification}' (conf={confidence})")
                    
                    # Store in Firebase
                    success = firebase_manager.store_email_classification(
                        user_id=user_id,
                        email_id=email['id'],
                        classification=classification,
                        confidence=confidence
                    )
                    
                    if success:
                        # Apply Gmail label
                        label_success = apply_gmail_label(service, email['id'], classification, found_labels)
                        if debug:
                            print(f"Applied label result for {email['id'][:20]}...: {label_success}")
                        
                        # Update timestamp
                        db = firestore.client()
                        doc_ref = db.collection('identifier').document(user_id).collection('email_classifications').document(email['id'])
                        doc_ref.update({
                            'timestamp': int(datetime.utcnow().timestamp())
                        })
                        try:
                            _update_user_stats_on_classification(
                                user_id=user_id,
                                classification=classification,
                                ts_seconds=int(datetime.utcnow().timestamp()),
                            )
                        except Exception:
                            pass
                    
                except Exception as e:
                    if debug:
                        print(f"  Error processing email {email['id'][:20]}...: {e}")
        
        # Relabel emails missing Gmail labels
        if emails_without_labels:
            if debug:
                print(f"Relabeling {len(emails_without_labels)} emails missing Gmail labels...")
            
            for email in emails_without_labels:
                try:
                    classification = email['classification']
                    
                    # Apply Gmail label
                    label_success = apply_gmail_label(service, email['id'], classification, found_labels)
                    
                except Exception as e:
                    if debug:
                        print(f"  Error relabeling email {email['id'][:20]}...: {e}")
        
        if debug:
            print(f"Email processing completed for {user_email}")
        
    except Exception as e:
        print(f"Error processing user {user_email}: {e}")
        import traceback
        traceback.print_exc()

def apply_gmail_label(service, email_id, classification, found_labels):
    """Apply Gmail label to email based on classification.
    Uses get_or_create_label() to handle name mappings (e.g., OTPs -> OTP) and create if missing.
    """
    try:
        # Handle spam emails - move to spam folder
        if classification.lower() == 'spam':
            modify_body = {
                'addLabelIds': ['SPAM'],
                'removeLabelIds': ['INBOX']
            }
            try:
                service.users().messages().modify(userId='me', id=email_id, body=modify_body).execute()
                print(f"Moved {email_id[:20]}... to SPAM and removed INBOX")
            except Exception as e:
                print(f"  Error moving to SPAM for {email_id[:20]}...: {e}")
                return False
            return True

        # Resolve/create proper Gmail label ID for this classification
        try:
            label_id = get_or_create_label(service, classification)
        except Exception as _e:
            # Fallback: try found_labels with simple mapping comparison
            mapped_name = {'OTPs': 'OTP'}.get(classification, classification)
            label_id = None
            for label in found_labels:
                if str(label.get('name', '')).lower() == str(mapped_name).lower():
                    label_id = label.get('id')
                    break
            if not label_id:
                print(f"  No label found for classification: {classification} (mapped: {mapped_name})")
                return False

        # Apply the label
        modify_body = { 'addLabelIds': [label_id] }
        try:
            service.users().messages().modify(userId='me', id=email_id, body=modify_body).execute()
            print(f"  Applied label id {label_id} for {email_id[:20]}...")
        except Exception as e:
            print(f"  Error applying label id {label_id} to {email_id[:20]}...: {e}")
            return False
        return True

    except Exception as e:
        print(f"  Error applying label to email {email_id}: {e}")
        return False

def background_email_job():
    print("=== BACKGROUND JOB STARTED ===")
    db = firestore.client()
    users = list(db.collection('identifier').stream())
    
    # Process emails for users with access
    worker_count = _get_env_int("SCHEDULER_WORKERS", 5)
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        executor.map(process_user, users)
    
    # Update billing dates and check trial expiration
    current_time = int(datetime.utcnow().timestamp())
    for user_doc in users:
        user_data = user_doc.to_dict()
        user_ref = db.collection('identifier').document(user_doc.id)
        
        # Check if user has no active access
        free_trial = user_data.get('free_trial', False)
        subscribed = user_data.get('subscribed', False)
        
        # Check if trial has expired
        if user_data.get('trial_end') and current_time > user_data.get('trial_end'):
            # End trial if passed
            print(f"Trial expired for user {user_doc.id}, setting free_trial to False")
            user_ref.update({
                'free_trial': False,  # legacy field
                'last_sync': current_time
            })
            free_trial = False
            # Fallback disable access if no subscription
            if not user_data.get('subscribed'):
                user_ref.update({'can_access': False, 'email_processing_enabled': False})
        
        if not free_trial and not subscribed:
            # Update next_billing_date to tomorrow for immediate billing when they pay
            tomorrow = current_time + (24 * 60 * 60)  # 24 hours from now
            user_ref.update({
                'last_sync': current_time,
                'next_billing_date': tomorrow
            })
            print(f"Updated billing date for user {user_doc.id} to tomorrow (no active access)")
        else:
            # Update last_sync and maintain can_access fallbacks
            docd = user_doc.to_dict() or {}
            can_access = _compute_can_access(docd)
            user_ref.update({'last_sync': current_time, 'can_access': can_access})
    
    print("=== BACKGROUND JOB COMPLETED ===")

# APScheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(background_email_job, 'interval', minutes=20)
scheduler.start()

def run_scheduler_in_thread():
    while True:
        time.sleep(1)

threading.Thread(target=run_scheduler_in_thread, daemon=True).start() 

@app.get("/user/{user_id}/classified-emails")
def get_classified_emails(user_id: str):
    """Get classified emails for a specific user"""
    try:
        firebase_manager = FirebaseManager()
        classifications = firebase_manager.get_user_classifications(user_id)
        return {"success": True, "classifications": classifications}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Stripe webhook endpoint (Payment Links / Checkout)
@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        result = stripe_handler.handle_webhook(payload, sig)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)

@app.post("/stripe/create-checkout")
def stripe_create_checkout(request: Request):
    """Create a Stripe Checkout Session tied to the current signed-in user."""
    user_id = get_session_user_id_or_401(request)
    db = firestore.client()
    doc = db.collection("identifier").document(user_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user = doc.to_dict() or {}
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    price_id = os.getenv("STRIPE_PRICE_ID")
    if not price_id:
        raise HTTPException(status_code=400, detail="STRIPE_PRICE_ID not configured")
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{FRONTEND_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/pricing",
            client_reference_id=user_id,
            customer_email=user.get("email"),
            allow_promotion_codes=True,
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/stripe/confirm-session")
def stripe_confirm_session(request: Request, session_id: str = Body(..., embed=True)):
    """Confirm a Stripe Checkout Session after redirect (Payment Link success URL).
    Works with or without an existing server session: resolves user by cookie or email and sets a session cookie."""
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    try:
        session = stripe.checkout.Session.retrieve(session_id, expand=["subscription"])  # type: ignore
        subscription = session.get("subscription") or {}
        customer_id = session.get("customer")
        sub_id = subscription.get("id")
        trial_end = subscription.get("trial_end")
        current_period_end = subscription.get("current_period_end")
        if not sub_id:
            raise HTTPException(status_code=400, detail="No subscription found on session")

        # Resolve user: prefer server session cookie; fallback to Stripe customer email
        db = firestore.client()
        resolved_user_id = None
        try:
            resolved_user_id = get_session_user_id_or_401(request)
        except Exception:
            resolved_user_id = None

        doc_ref = None
        if resolved_user_id:
            tmp_ref = db.collection("identifier").document(resolved_user_id)
            if tmp_ref.get().exists:
                doc_ref = tmp_ref

        if doc_ref is None:
            email = None
            cd = session.get("customer_details") or {}
            if isinstance(cd, dict):
                email = cd.get("email")
            if not email:
                email = session.get("customer_email")
            if email:
                docs = db.collection("identifier").where("email", "==", email).limit(1).get()
                if docs:
                    doc_ref = db.collection("identifier").document(docs[0].id)
                    resolved_user_id = docs[0].id

        if doc_ref is None:
            return {"success": False, "error": "User not found for session"}

        # Reflect Stripe status accurately; do not grant full access until first payment
        stripe_status = subscription.get("status")
        update = {
            "subscription_status": stripe_status or "trialing",
            "subscribed": False,  # will become True on first invoice.payment_succeeded
            "subscription_id": sub_id,
            "customer_id": customer_id,
            "trial_end": trial_end,
            "payment_completed": False,
        }
        # Prefer trial_end as next billing during trial; otherwise current_period_end
        if isinstance(trial_end, int) and (stripe_status == "trialing" or stripe_status is None):
            update["next_billing_date"] = trial_end
        elif isinstance(current_period_end, int):
            update["next_billing_date"] = current_period_end
        update["can_access"] = _compute_can_access(update)
        doc_ref.set(update, merge=True)

        resp = JSONResponse({"success": True, "user_id": resolved_user_id, "subscription_id": sub_id})
        # Ensure the browser has a valid session cookie for subsequent requests
        try:
            if resolved_user_id:
                session_token = create_session_jwt(resolved_user_id)
                set_session_cookie(resp, session_token)
        except Exception:
            pass
        return resp
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/cancel-subscription/{user_id}")
def cancel_subscription(user_id: str):
    """Cancel user's subscription at period end (or trial end). No immediate charge, access until end."""
    try:
        db = firestore.client()
        doc_ref = db.collection("identifier").document(user_id)
        snap = doc_ref.get()
        if not snap.exists:
            return {"success": False, "error": "User not found"}
        user = snap.to_dict() or {}
        sub_id = user.get("subscription_id")
        customer_id = user.get("customer_id")
        user_email = user.get("email")
        if not sub_id and not customer_id:
            return {"success": False, "error": "No subscription or customer on file"}
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        # Resolve valid subscription id
        resolved_sub_id = sub_id
        try:
            if resolved_sub_id:
                _ = stripe.Subscription.retrieve(resolved_sub_id)
        except Exception:
            resolved_sub_id = None
        if not resolved_sub_id and (customer_id or user_email):
            # If no stored customer_id, try to resolve by email
            if not customer_id and user_email:
                try:
                    custs = stripe.Customer.list(email=user_email, limit=1)
                    if getattr(custs, "data", None):
                        customer_id = custs.data[0].id
                        doc_ref.update({"customer_id": customer_id})
                except Exception:
                    customer_id = None
            if not customer_id:
                return {"success": False, "error": "No Stripe customer found for email"}
            subs = stripe.Subscription.list(customer=customer_id, status="all", limit=10)
            chosen = None
            for s in subs.auto_paging_iter():
                if s.get("status") in ("active", "trialing"):
                    chosen = s
                    break
            if not chosen:
                items = list(subs)
                if items:
                    chosen = items[0]
            if not chosen:
                return {"success": False, "error": "No Stripe subscriptions found for customer"}
            resolved_sub_id = chosen.get("id")
            doc_ref.update({"subscription_id": resolved_sub_id})
        if not resolved_sub_id:
            return {"success": False, "error": "Unable to resolve subscription id"}
        # Mark to cancel at end of current period
        sub = stripe.Subscription.modify(resolved_sub_id, cancel_at_period_end=True)
        cancels_at = sub.get("current_period_end") or sub.get("trial_end")
        # Reflect pending cancellation in Firestore
        update = {
            "subscription_status": "cancelling",
            "cancel_at_period_end": True,
            "cancels_at": cancels_at,
        }
        # Recompute can_access after marking cancelling
        snap2 = doc_ref.get()
        docd = snap2.to_dict() or {}
        docd.update(update)
        update["can_access"] = _compute_can_access(docd)
        doc_ref.set(update, merge=True)
        return {"success": True, "cancels_at": cancels_at, "subscription_status": "cancelling"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/cancel-subscription")
def cancel_subscription_me(request: Request):
    """Cancel the current signed-in user's subscription at period end using session cookie."""
    uid = get_session_user_id_or_401(request)
    return cancel_subscription(uid)

@app.get("/user/{user_id}/email-stats")
def get_user_email_stats(user_id: str):
    """Get email statistics for a specific user"""
    try:
        from datetime import datetime, timedelta
        import calendar

        firebase_manager = FirebaseManager()
        db = firestore.client()
        coll = db.collection('identifier').document(user_id).collection('email_classifications')

        # Time boundaries
        now = datetime.now().replace(tzinfo=None)
        today_midnight = datetime(year=now.year, month=now.month, day=now.day)
        end_dt = today_midnight  # exclude current day
        month_start = datetime(year=now.year, month=now.month, day=1)

        # Query monthly classifications [month_start, end_dt)
        classifications = []
        try:
            q = coll.where('timestamp', '>=', int(month_start.timestamp()))
            q = q.where('timestamp', '<', int(end_dt.timestamp()))
            classifications = [d.to_dict() for d in q.stream()]
        except Exception:
            try:
                q = coll.where('timestamp', '>=', month_start).where('timestamp', '<', end_dt)
                classifications = [d.to_dict() for d in q.stream()]
            except Exception:
                classifications = firebase_manager.get_user_classifications(user_id)

        # Always compute from Firestore (last 30 days) for MVP

        # Convert and filter to current month window (already queried)
        monthly_classifications = []
        for classification in classifications:
            timestamp = classification.get('timestamp')
            if timestamp:
                # Convert timestamp to datetime
                if isinstance(timestamp, (int, float)):
                    email_date = datetime.fromtimestamp(timestamp / 1000) if timestamp > 1000000000000 else datetime.fromtimestamp(timestamp)
                else:
                    email_date = timestamp
                
                # Ensure email_date is timezone-naive for comparison
                if hasattr(email_date, 'tzinfo') and email_date.tzinfo is not None:
                    email_date = email_date.replace(tzinfo=None)
                
                # Include if within month window (month_start <= date < end_dt)
                if month_start <= email_date < end_dt:
                    monthly_classifications.append(classification)
            else:
                # If no timestamp, include it (legacy data)
                monthly_classifications.append(classification)
        
        # Use monthly data for statistics (1st .. yesterday)
        total_processed = len(monthly_classifications)
        spam_count = len([c for c in monthly_classifications if str(c.get('classification', '')).strip().lower() == 'spam'])
        
        # Category breakdown for current month
        category_counts = {}
        for classification in monthly_classifications:
            category = classification.get('classification', 'Other')
            
            # Normalize category names to fix overlapping labels
            category = category.strip().lower()
            if category == 'spam':
                category = 'Spam'
            elif category in ['work', 'professional', 'business']:
                category = 'Work'
            elif category in ['finance', 'financial', 'banking']:
                category = 'Finance'
            elif category in ['security', 'secure', 'account']:
                category = 'Security'
            elif category in ['otps', 'otp', 'verification', 'code']:
                category = 'OTPs'
            elif category in ['family', 'personal', 'friends']:
                category = 'Family'
            elif category in ['urgent', 'important', 'priority']:
                category = 'Urgent'
            else:
                category = 'Other'
            
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Find top category
        top_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else "None"
        
        # Calculate accuracy (simplified - could be enhanced with confidence scores)
        accuracy = 94.7  # Default accuracy for now
        
        # Prepare category breakdown for frontend
        category_breakdown = []
        for category, count in category_counts.items():
            percentage = (count / total_processed) * 100 if total_processed > 0 else 0
            category_breakdown.append({
                "category": category,
                "count": count,
                "percentage": round(percentage, 1)
            })
        
        # Sort by count descending
        category_breakdown.sort(key=lambda x: x['count'], reverse=True)
        
        # Weekly chart: use week start at midnight (Mon..Sun), exclude today
        week_start = today_midnight - timedelta(days=today_midnight.weekday())
        weekly_data = []
        # Build a dict for counts from monthly_classifications
        by_day = {}
        for c in monthly_classifications:
            ts = c.get('timestamp')
            if not ts:
                continue
            d = datetime.fromtimestamp(ts / 1000) if isinstance(ts, (int, float)) and ts > 1000000000000 else (datetime.fromtimestamp(ts) if isinstance(ts, (int, float)) else ts)
            if hasattr(d, 'tzinfo') and d.tzinfo is not None:
                d = d.replace(tzinfo=None)
            day_key = datetime(year=d.year, month=d.month, day=d.day)
            if not (week_start <= day_key < end_dt):
                continue
            entry = by_day.get(day_key)
            if not entry:
                entry = { 'processed': 0, 'spam': 0 }
                by_day[day_key] = entry
            entry['processed'] += 1
            if str(c.get('classification', '')).strip().lower() == 'spam':
                entry['spam'] += 1

        d = week_start
        while d < end_dt:
            entry = by_day.get(d) or { 'processed': 0, 'spam': 0 }
            weekly_data.append({
                "day": calendar.day_abbr[d.weekday()],
                "date": d.strftime('%Y-%m-%d'),
                "processed": entry['processed'],
                "spam": entry['spam']
            })
            d += timedelta(days=1)
        
        # Add date range info for month
        date_range = f"{month_start.strftime('%b %d')} - {(end_dt - timedelta(days=1)).strftime('%b %d, %Y')}"
        
        return {
            "success": True,
            "stats": {
                "total_processed": total_processed,
                "spam_count": spam_count,
                "accuracy": accuracy,
                "top_category": top_category,
                "category_breakdown": category_breakdown,
                "weekly_data": weekly_data,
                "date_range": date_range
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/user/{user_id}/billing-data")
def get_user_billing_data(user_id: str):
    """Get user billing data including trial and billing dates"""
    try:
        db = firestore.client()
        doc_ref = db.collection("identifier").document(user_id)
        snap = doc_ref.get()
        if not snap.exists:
            return {"success": False, "error": "User not found"}

        user = snap.to_dict() or {}
        trial_end = user.get("trial_end")
        next_billing_date = user.get("next_billing_date")

        # If trial_end is missing but we have a subscription/customer, fetch from Stripe
        if not trial_end:
            try:
                stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
                subscription_id = user.get("subscription_id")
                customer_id = user.get("customer_id")
                sub = None
                if subscription_id:
                    sub = stripe.Subscription.retrieve(subscription_id)
                elif customer_id:
                    subs = stripe.Subscription.list(customer=customer_id, status="all", limit=10)
                    # Prefer active/trialing, else most recent
                    chosen = None
                    for s in subs.auto_paging_iter():
                        if s.get("status") in ("active", "trialing"):
                            chosen = s
                            break
                    if not chosen:
                        items = list(subs)
                        if items:
                            chosen = items[0]
                    sub = chosen
                if sub:
                    se = sub.get("trial_end")
                    cpe = sub.get("current_period_end")
                    status = sub.get("status")
                    if isinstance(se, int):
                        trial_end = se
                    # Set next_billing_date using trial_end during trial, else current period end
                    if status == "trialing" and isinstance(se, int):
                        next_billing_date = se
                    elif isinstance(cpe, int):
                        next_billing_date = cpe
                    # Persist back to Firestore
                    update = {}
                    if trial_end is not None:
                        update["trial_end"] = trial_end
                    if next_billing_date is not None:
                        update["next_billing_date"] = next_billing_date
                    if update:
                        doc_ref.set(update, merge=True)
            except Exception:
                pass

        # Fallback compute next_billing_date if still missing
        if not next_billing_date:
            try:
                from datetime import datetime as _dt
                if user.get("trial_end"):
                    te = int(user.get("trial_end"))
                    now_s = int(_dt.utcnow().timestamp())
                    next_billing_date = te if te > now_s else te + (30 * 24 * 60 * 60)
                elif user.get("payment_date"):
                    next_billing_date = int(user.get("payment_date")) + (30 * 24 * 60 * 60)
            except Exception:
                next_billing_date = None

        return {
            "success": True,
            "billing_data": {
                "trial_start": user.get("trial_start"),
                "trial_end": trial_end or user.get("trial_end"),
                "payment_date": user.get("payment_date"),
                "next_billing_date": next_billing_date,
                "subscription_status": user.get("subscription_status"),
                "subscribed": user.get("subscribed"),
                "payment_completed": user.get("payment_completed"),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/trigger-background-job")
def trigger_background_job():
    """Manually trigger the background email classification job"""
    try:
        background_email_job()
        return {"success": True, "message": "Background job completed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/trigger-user-sync/{user_id}")
def trigger_user_sync(user_id: str, verbose: bool = True):
    """Manually trigger email classification for a specific user only"""
    try:
        print(f"=== MANUAL SYNC FOR USER {user_id} STARTED ===")
        db = firestore.client()
        
        # Get the specific user document
        user_ref = db.collection('identifier').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return {"success": False, "error": "User not found"}
        
        user_data = user_doc.to_dict()
        
        # Check if user has active access (free trial or subscribed)
        free_trial = user_data.get('free_trial', False)
        subscribed = user_data.get('subscribed', False)
        
        if not free_trial and not subscribed:
            return {"success": False, "error": "No active access - free trial or subscription required"}
        
        # Process only this specific user
        process_user(user_doc, verbose=verbose)
        
        # Update last_sync for this user only
        current_time = int(datetime.utcnow().timestamp())
        user_ref.update({'last_sync': current_time})
        
        print(f"=== MANUAL SYNC FOR USER {user_id} COMPLETED ===")
        return {"success": True, "message": f"Email classification completed for user {user_id}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_or_create_label(service, label_name):
    # Gmail label mapping (AI output -> Gmail label name)
    gmail_label_mapping = {
        'OTPs': 'OTP'  # Gmail doesn't like "OTPs", use "OTP" instead
    }
    
    # Use Gmail label name if mapping exists, otherwise use original
    gmail_label_name = gmail_label_mapping.get(label_name, label_name)
    
    # Get all labels
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    
    for label in labels:
        if label['name'].lower() == gmail_label_name.lower():
            return label['id']
    
    # If not found, create it
    label_obj = {
        "name": gmail_label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
        "type": "user"
    }
    
    new_label = service.users().labels().create(userId='me', body=label_obj).execute()
    return new_label['id']

# Stripe Payment Routes
class PaymentRequest(BaseModel):
    customer_email: str
    customer_name: str = None

class TokenRequest(BaseModel):
    token: str

class CodeExchangeRequest(BaseModel):
    code: str
    state: str

class ConsentRequest(BaseModel):
    consent: bool

@app.post("/create-payment-intent")
def create_payment_intent(payment_request: PaymentRequest):
    """Create a setup intent for the £5.99 subscription with 7-day trial"""
    try:
        result = stripe_handler.create_payment_intent(payment_request.customer_email)
        return result  # Return the result directly from stripe_handler
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for payment confirmation"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        result = stripe_handler.handle_webhook(payload, sig_header)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/create-subscription")
def create_subscription(customer_email: str, customer_name: str = None):
    """Create a Stripe customer and subscription"""
    try:
        # Create customer
        customer_id = stripe_handler.create_customer(customer_email, customer_name)
        
        # Create subscription
        subscription_id = stripe_handler.create_subscription(customer_id)
        
        return {
            "success": True,
            "customer_id": customer_id,
            "subscription_id": subscription_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/verify-token")
def verify_token(token_request: TokenRequest):
    """Verify Firebase custom token and return user data"""
    try:
        # Exchange custom token for ID token
        id_token = auth.verify_id_token(token_request.token)
        user_uid = id_token["uid"]
        
        # Get user data from Firestore
        db = firestore.client()
        user_ref = db.collection("identifier").document(user_uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_doc.to_dict()
        
        # Check if user has active subscription
        if not user_data.get("payment_completed") or user_data.get("subscription_status") != "active" or user_data.get("subscribed") != True:
            raise HTTPException(status_code=403, detail="No active subscription")
        
        return user_data
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}") 

 

 

@app.get("/list-firebase")
def list_firebase():
    """List all collections and documents in Firebase"""
    try:
        db = firestore.client()
        
        # Get all collections
        collections = db.collections()
        result = {}
        
        for collection in collections:
            collection_name = collection.id
            print(f"Collection: {collection_name}")
            
            # Get all documents in this collection
            docs = collection.stream()
            documents = []
            
            for doc in docs:
                doc_data = doc.to_dict()
                documents.append({
                    "id": doc.id,
                    "data": doc_data
                })
                print(f"  Document: {doc.id}")
                print(f"    Data: {doc_data}")
            
            result[collection_name] = documents
        
        return {
            "success": True,
            "collections": result,
            "total_collections": len(result)
        }
    except Exception as e:
        return {"success": False, "error": str(e)} 

@app.post("/user/{user_id}/consent")
def set_user_consent(user_id: str, req: ConsentRequest):
    """Set user's consent flag in Firestore and return next redirect target."""
    try:
        db = firestore.client()
        doc_ref = db.collection("identifier").document(user_id)
        doc = doc_ref.get()
        if not doc.exists:
            return {"success": False, "error": "User not found"}
        # Update consent
        doc_ref.update({"consent": bool(req.consent)})
        user_data = doc.to_dict() or {}
        user_data["consent"] = bool(req.consent)
        # Decide where to send them next
        if not user_data.get("consent"):
            target = f"{FRONTEND_URL}/consent"
        else:
            target = f"{FRONTEND_URL}/dashboard" if user_can_access_dashboard(user_data) else f"{FRONTEND_URL}/"
        return {"success": True, "redirect_url": target}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/update-users-subscribed")
def update_users_subscribed():
    """Update all existing users to include the subscribed field"""
    try:
        db = firestore.client()
        
        # Get all users in the identifier collection
        users_ref = db.collection("identifier")
        docs = users_ref.stream()
        
        updated_count = 0
        for doc in docs:
            user_data = doc.to_dict()
            
            # Check if user has active subscription
            if user_data.get("payment_completed") and user_data.get("subscription_status") == "active":
                # User is subscribed
                user_data["subscribed"] = True
            else:
                # User is not subscribed
                user_data["subscribed"] = False
            
            # Update the document
            doc.reference.update({"subscribed": user_data["subscribed"]})
            updated_count += 1
            print(f"Updated user {doc.id}: subscribed = {user_data['subscribed']}")
        
        return {
            "success": True, 
            "message": f"Updated {updated_count} users with subscribed field"
        }
    except Exception as e:
        return {"success": False, "error": str(e)} 

@app.post("/update-user-subscription/{email}")
def update_user_subscription(email: str):
    """Update a specific user's subscription status to active"""
    try:
        db = firestore.client()
        
        # Find user by email
        users_ref = db.collection("identifier")
        query = users_ref.where("email", "==", email).limit(1)
        docs = query.get()
        
        if not docs:
            return {"success": False, "error": f"User with email {email} not found"}
        
        user_doc = docs[0]
        user_data = user_doc.to_dict()
        
        # Update subscription data
        update_data = {
            "subscription_status": "active",
            "subscribed": True,
            "payment_completed": True,
            "subscription_id": f"sub_{user_data.get('uid', 'user')}",
            "customer_id": f"cus_{user_data.get('uid', 'user')}",
            "trial_end": int(datetime.utcnow().timestamp()) + (7 * 24 * 60 * 60),  # 7 days from now
            "settings": {
                "auto_categorize": True,
                "confidence_threshold": "0.8",
                "spam_sensitivity": "medium"
            }
        }
        
        # Update the document
        user_doc.reference.update(update_data)
        
        print(f"Updated user {email}: subscription activated")
        
        return {
            "success": True, 
            "message": f"User {email} subscription activated",
            "user_id": user_doc.id
        }
    except Exception as e:
        return {"success": False, "error": str(e)} 

@app.post("/fix-user-subscription/{email}")
def fix_user_subscription(email: str):
    """Fix a user's subscription data to ensure they can access dashboard"""
    try:
        db = firestore.client()
        
        # Find user by email
        users_ref = db.collection("identifier")
        query = users_ref.where("email", "==", email).limit(1)
        docs = query.get()
        
        if not docs:
            return {"success": False, "error": f"User with email {email} not found"}
        
        user_doc = docs[0]
        user_data = user_doc.to_dict()
        
        # Force update all subscription fields
        update_data = {
            "subscription_status": "active",
            "subscribed": True,
            "payment_completed": True,
            "subscription_id": f"sub_{user_data.get('uid', 'user')}",
            "customer_id": f"cus_{user_data.get('uid', 'user')}",
            "trial_end": int(datetime.utcnow().timestamp()) + (7 * 24 * 60 * 60),  # 7 days from now
            "settings": {
                "auto_categorize": True,
                "confidence_threshold": "0.8",
                "spam_sensitivity": "medium"
            }
        }
        
        # Update the document
        user_doc.reference.update(update_data)
        
        print(f"Fixed user {email}: {update_data}")
        
        return {
            "success": True, 
            "message": f"User {email} subscription fixed",
            "user_id": user_doc.id,
            "updated_data": update_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)} 

@app.post("/exchange-code")
def exchange_code(request: CodeExchangeRequest):
    """Exchange OAuth code for tokens and determine redirect"""
    try:
        print("=== CODE EXCHANGE STARTED ===")
        print(f"Code: {request.code[:20]}...")
        print(f"State: {request.state}")
        
        # Create OAuth flow
        flow = Flow.from_client_config(GOOGLE_CLIENT_CONFIG, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
        
        # Exchange code for tokens
        flow.fetch_token(code=request.code)
        credentials = flow.credentials
        
        # Get user info from Google
        from googleapiclient.discovery import build
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        user_email = user_info.get('email')
        
        print(f"User email: {user_email}")
        
        # If this callback is from Gmail connect (state carries user_id), store Gmail tokens and finish
        try:
            if request.state and request.state != "signin":
                db = firestore.client()
                user_ref = db.collection("identifier").document(request.state)
                user_snap = user_ref.get()
                if user_snap.exists:
                    existing = user_snap.to_dict() or {}
                    tokens = {
                        "token": credentials.token,
                        "refresh_token": credentials.refresh_token,
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "client_id": credentials.client_id,
                        "client_secret": credentials.client_secret,
                        "scopes": credentials.scopes,
                        "expiry": credentials.expiry.isoformat() if credentials.expiry else None
                    }
                    # Preserve previous refresh_token if Google didn't return a new one
                    existing_tokens = existing.get("gmail_tokens") or {}
                    if not tokens.get("refresh_token"):
                        tokens["refresh_token"] = existing_tokens.get("refresh_token")
                    user_ref.update({
                        "gmail_tokens": tokens,
                        "authflow": True
                    })
                    # Redirect to dashboard after successful Gmail connect
                    safe_user = _sanitize_user_for_client(_json_safe(existing))
                    resp = JSONResponse({
                        "redirect_url": f"{FRONTEND_URL}/dashboard",
                        "user_id": request.state,
                        "user_data": safe_user
                    })
                    return resp
        except Exception as e:
            print(f"Gmail connect handling error: {e}")
        
        # Check Firebase for subscription with basic retry to handle quota blips
        db = firestore.client()
        users_ref = db.collection("identifier")
        attempts = 0
        docs = []
        while attempts < 3:
            attempts += 1
            try:
                docs = users_ref.where("email", "==", user_email).limit(1).get()
                break
            except Exception as fe:
                # Simple backoff: 0.3s, 0.6s, 1.2s
                import time as _t
                _t.sleep(0.3 * (2 ** (attempts - 1)))
                if attempts >= 3:
                    raise fe
        
        if docs:
            user_doc = docs[0]
            user_data = user_doc.to_dict()
            
            # Do not change authflow here; it's reserved for Gmail access only
            print(f"Existing user {user_email}; authflow remains: {user_data.get('authflow')}")
            
            print(
                "User found: payment_completed=", user_data.get("payment_completed"),
                ", subscription_status=", user_data.get("subscription_status"),
                ", subscribed=", user_data.get("subscribed")
            )
            
            # Google consent is the only consent screen. Existing users go directly based on access.
            target = f"{FRONTEND_URL}/dashboard" if user_can_access_dashboard(user_data) else f"{FRONTEND_URL}/pricing"
            print(f"Returning redirect_url: {target}")
            safe_user = _sanitize_user_for_client(_json_safe(user_data))
            # Set httpOnly session cookie
            session_token = create_session_jwt(user_doc.id)
            resp = JSONResponse({
                "redirect_url": target,
                "user_data": safe_user,
                "user_id": user_doc.id
            })
            set_session_cookie(resp, session_token)
            return resp
        else:
            print("New user, creating record and redirecting to pricing")
            # Create new user record (idempotent: if email exists by race, fetch again)
            new_user_data = {
                "email": user_email,
                "name": user_info.get('name', ''),
                "picture": user_info.get('picture', ''),
                "subscribed": False,
                "payment_completed": False,
                "subscription_status": "inactive",
                "created_at": int(datetime.utcnow().timestamp()),
                "email_processing_enabled": True,
                "authflow": False  # Gmail access not yet granted
            }
            
            # Attempt add; if quota/race, re-query
            try:
                new_user_ref = users_ref.add(new_user_data)
                new_user_id = new_user_ref[1].id
            except Exception:
                # Re-query to find the created user
                docs2 = users_ref.where("email", "==", user_email).limit(1).get()
                if docs2:
                    new_user_id = docs2[0].id
                else:
                    raise
            
            # New users: direct to dashboard if they have access, else to pricing
            target = f"{FRONTEND_URL}/dashboard" if user_can_access_dashboard(new_user_data) else f"{FRONTEND_URL}/pricing"
            print(f"Returning redirect_url: {target}")
            safe_new = _sanitize_user_for_client(_json_safe(new_user_data))
            session_token = create_session_jwt(new_user_id)
            resp = JSONResponse({
                "redirect_url": target,
                "user_data": safe_new,
                "user_id": new_user_id
            })
            set_session_cookie(resp, session_token)
            return resp
            
    except Exception as e:
        print(f"Error in code exchange: {e}")
        import traceback
        traceback.print_exc()
        return {"redirect_url": f"{FRONTEND_URL}/pricing"}

@app.get("/debug-user/{user_id}")
def debug_user(user_id: str):
    """Debug endpoint to check raw user data in Firebase"""
    try:
        db = firestore.client()
        doc_ref = db.collection("identifier").document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            raw = doc.to_dict() or {}
            has_tokens = bool(raw.get("gmail_tokens"))
            user_data = _sanitize_user_for_client(_json_safe(raw))
            # Expose a non-sensitive flag so frontend can show connection status
            user_data["has_gmail_tokens"] = has_tokens
            return {
                "success": True,
                "user_data": user_data,
                "has_next_billing_date": "next_billing_date" in user_data,
                "next_billing_date_value": user_data.get("next_billing_date"),
                "trial_end_value": user_data.get("trial_end"),
                "subscribed_value": user_data.get("subscribed"),
                "subscription_status": user_data.get("subscription_status")
            }
        else:
            return {"success": False, "error": "User not found"}
    except Exception as e:
        return {"success": False, "error": str(e)} 

@app.get("/check-authflow/{user_id}")
def check_authflow(user_id: str):
    """Check if user has granted Gmail access (authflow field)"""
    try:
        db = firestore.client()
        user_ref = db.collection("identifier").document(user_id)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_data = user_doc.to_dict()
            authflow = user_data.get("authflow", False)
            return {
                "success": True,
                "authflow": authflow,
                "needs_gmail_oauth": not authflow
            }
        else:
            return {"success": False, "error": "User not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/gmail/connect-simple/{user_id}")
def gmail_connect_simple(user_id: str):
    """Start Gmail OAuth flow for a specific user without requiring Firebase token"""
    try:
        print(f"Starting Gmail OAuth for user: {user_id}")
        # Start OAuth flow for Gmail
        flow = Flow.from_client_config(GOOGLE_CLIENT_CONFIG, scopes=GOOGLE_SCOPES, redirect_uri=GOOGLE_REDIRECT_URI)
        # Use user's UID as state to identify them in callback
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=user_id,
            prompt="consent"
        )
        print(f"Gmail OAuth URL generated for user {user_id}")
        # Redirect directly to Google OAuth
        return RedirectResponse(url=auth_url)
    except Exception as e:
        print(f"Error starting Gmail OAuth for user {user_id}: {e}")
        return {"error": str(e)}

@app.post("/update-existing-users-authflow")
def update_existing_users_authflow():
    """Update existing users to have authflow field based on whether they have Gmail tokens"""
    try:
        db = firestore.client()
        users_ref = db.collection("identifier")
        docs = users_ref.get()
        
        updated_count = 0
        for doc in docs:
            user_data = doc.to_dict()
            gmail_tokens = user_data.get("gmail_tokens")
            authflow = user_data.get("authflow")
            
            # If user has Gmail tokens but no authflow field, set authflow to True
            if gmail_tokens and authflow is None:
                doc.reference.update({"authflow": True})
                updated_count += 1
                print(f"Updated user {doc.id} with authflow=True")
            # If user has no Gmail tokens and no authflow field, set authflow to False
            elif not gmail_tokens and authflow is None:
                doc.reference.update({"authflow": False})
                updated_count += 1
                print(f"Updated user {doc.id} with authflow=False")
        
        return {"success": True, "updated_count": updated_count}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/toggle-email-processing/{user_id}")
def toggle_email_processing(user_id: str, enabled: bool = True):
    """Toggle email processing on/off for a specific user"""
    try:
        print(f"=== TOGGLE EMAIL PROCESSING CALLED ===")
        print(f"User ID: {user_id}")
        print(f"Enabled parameter: {enabled}")
        
        db = firestore.client()
        current_time = int(datetime.utcnow().timestamp())
        
        if enabled:
            # Enable processing
            update_data = {
                'email_processing_enabled': True,
                'processing_disabled_until': None
            }
            status = "enabled"
        else:
            # Disable processing for 1 hour
            disabled_until = current_time + (60 * 60)  # 1 hour from now
            update_data = {
                'email_processing_enabled': False,
                'processing_disabled_until': disabled_until
            }
            status = "disabled for 1 hour"
        
        print(f"Update data: {update_data}")
        
        # Update the user's processing setting
        user_ref = db.collection('identifier').document(user_id)
        user_ref.update(update_data)
        
        print(f"Firebase update completed")
        print(f"Email processing {status} for user {user_id}")
        
        return {
            "success": True, 
            "message": f"Email processing {status}",
            "processing_enabled": enabled,
            "disabled_until": update_data.get('processing_disabled_until')
        }
    except Exception as e:
        print(f"Error in toggle_email_processing: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)} 


@app.post("/auth/logout")
def auth_logout():
    resp = JSONResponse({"success": True})
    clear_session_cookie(resp)
    return resp

@app.get("/session/me")
def session_me(request: Request):
    user_id = get_session_user_id_or_401(request)
    db = firestore.client()
    doc = db.collection("identifier").document(user_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    safe_user = _sanitize_user_for_client(_json_safe(doc.to_dict() or {}))
    return {"user_id": user_id, "user_data": safe_user}