from fastapi import FastAPI, HTTPException, status, Depends, Request, Security
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase Admin (do this once at startup)
cred = credentials.Certificate("../KEYS/maila-248fc-firebase-adminsdk-fbsvc-0cc3ab381b.json")
firebase_admin.initialize_app(cred)

GOOGLE_OAUTH_CLIENT_SECRET_PATH = "C:\\Users\\vabhi\\OneDrive\\Desktop\\Personal\\coding\\KEYS\\client_secret_536404685178-e9efhvprp9gl1t72pgvmn4u2o2n6clsu.apps.googleusercontent.com.json"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]
GOOGLE_REDIRECT_URI = "http://localhost:8000/gmail/oauth2callback"

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

class UserCreate(BaseModel):
    username: str
    password: str

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

@app.get("/protected")
def protected_route(
    user=Depends(verify_firebase_token),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    return {"message": f"Hello, {user['uid']}!"}

@app.get("/gmail/connect")
def gmail_connect(user=Depends(verify_firebase_token)):
    print("GOOGLE_REDIRECT_URI:", GOOGLE_REDIRECT_URI)
    print("GOOGLE_OAUTH_CLIENT_SECRET_PATH:", GOOGLE_OAUTH_CLIENT_SECRET_PATH)
    print("GOOGLE_SCOPES:", GOOGLE_SCOPES)
    # Start OAuth flow for Gmail
    flow = Flow.from_client_secrets_file(
        GOOGLE_OAUTH_CLIENT_SECRET_PATH,
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    # Use user's UID as state to identify them in callback
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=user["uid"],
        prompt="consent"
    )
    print("AUTH_URL:", auth_url)
    print("AUTH_URL length:", len(auth_url))
    # Check if redirect_uri parameter is in the URL
    if "redirect_uri=" in auth_url:
        print("Redirect URI parameter found in URL")
    else:
        print("WARNING: Redirect URI parameter NOT found in URL")
    return {"auth_url": auth_url}

@app.get("/gmail/oauth2callback")
def gmail_oauth2callback(code: str, state: str):
    try:
        print("OAuth callback received - code:", code[:20] + "..." if code else "None")
        print("OAuth callback received - state:", state)
        print("GOOGLE_REDIRECT_URI:", GOOGLE_REDIRECT_URI)
        
        # state is the user's UID
        flow = Flow.from_client_secrets_file(
            GOOGLE_OAUTH_CLIENT_SECRET_PATH,
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
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
        
        # Store tokens in Firestore under users/<uid>/gmail_tokens
        db = firestore.client()
        user_ref = db.collection("identifier").document(state)
        user_ref.update({"gmail_tokens": tokens})
        print("Tokens stored in Firebase successfully")
        
        return {"success": True, "message": "Gmail tokens stored for user.", "user": state}
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
        tokens["token"],
        refresh_token=tokens["refresh_token"],
        token_uri=tokens["token_uri"],
        client_id=tokens["client_id"],
        client_secret=tokens["client_secret"],
        scopes=tokens["scopes"]
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

def process_user(user_doc):
    user_data = user_doc.to_dict()
    user_id = user_data.get('uid') or user_doc.id
    tokens = user_data.get('gmail_tokens')
    print(f"Processing user: {user_id}")
    if not tokens:
        print(f"No Gmail tokens found for user: {user_id}")
        return
    try:
        # Fetch recent emails for this user
        service = get_gmail_service_for_user(user_id)
        
        # Define the classification labels we use
        classification_labels = ['Work', 'Finance', 'Security', 'OTPs', 'Family', 'Urgent', 'Spam']
        
        # Build Gmail search query to exclude emails with any classification labels
        # Gmail search uses label names, not IDs
        search_query_parts = []
        for label in classification_labels:
            search_query_parts.append(f'-label:{label}')
        
        # Combine all exclusions with AND logic
        search_query = ' '.join(search_query_parts)
        print(f"Search query: {search_query}")
        
        # Fetch 5 emails that don't have any classification labels
        results = service.users().messages().list(
            userId='me',
            maxResults=5,
            q=search_query
        ).execute()
        messages = results.get('messages', [])
        print(f"Found {len(messages)} unclassified emails for user: {user_id}")
        
        for msg in messages:
            # Get email details
            msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
            subject = ''
            snippet = msg_detail.get('snippet', '')
            headers = msg_detail.get('payload', {}).get('headers', [])
            for header in headers:
                if header.get('name', '').lower() == 'subject':
                    subject = header.get('value', '')
                    break
            
            # Double-check if email already has any classification labels (race condition protection)
            email_labels = msg_detail.get('labelIds', [])
            all_labels = service.users().labels().list(userId='me').execute().get('labels', [])
            classified_label_ids = []
            for label in all_labels:
                if label.get('name') in classification_labels:
                    classified_label_ids.append(label.get('id'))
            
            has_classification_label = any(label_id in email_labels for label_id in classified_label_ids)
            if has_classification_label:
                print(f"Email already classified (double-check): {subject[:50]}... (skipping)")
                continue
            
            # Check if email already processed in Firebase
            existing_classification = firebase_manager.get_email_classification(user_id, msg['id'])
            if existing_classification:
                print(f"Email already processed in Firebase: {subject[:50]}... (skipping)")
                continue
                
            # Classify email
            print(f"Classifying email: {subject[:50]}...")
            result = email_classifier.classify_single_email(subject, snippet, msg['id'])
            classification = result.get('classification', 'Spam')
            confidence = result.get('confidence', 0.5)
            print(f"Classification result: {classification} (confidence: {confidence})")

            # Store result under user (per-user subcollection)
            print(f"Storing classification in Firebase for user: {user_id}")
            success = firebase_manager.store_email_classification(
                user_id=user_id,
                email_id=msg['id'],
                classification=classification,
                confidence=confidence
            )
            print(f"Firebase storage success: {success}")

            # --- Gmail labeling ---
            # Use the specific classification from the AI
            label_name = classification  # Use exact classification name
            print(f"Applying Gmail label: {label_name}")
            
            # Get label ID
            label_id = get_or_create_label(service, label_name)
            
            # Prepare modification body - only add the classification label
            if classification.lower() == "spam":
                modify_body = {
                    'addLabelIds': [label_id],
                    'removeLabelIds': ['INBOX']
                }
                print(f"Moving spam email to Spam folder")
            else:
                # For non-spam emails, add ONLY the specific category label
                modify_body = {
                    'addLabelIds': [label_id]
                }
                print(f"Adding {label_name} label to email")
            
            # Apply the modifications
            service.users().messages().modify(
                userId='me',
                id=msg['id'],
                body=modify_body
            ).execute()
            print(f"Gmail modifications applied successfully")

    except Exception as e:
        print(f"Error processing user {user_id}: {e}")
        import traceback
        traceback.print_exc()

def background_email_job():
    print("=== BACKGROUND JOB STARTED ===")
    db = firestore.client()
    users = list(db.collection('identifier').stream())
    with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
        executor.map(process_user, users)
    print("=== BACKGROUND JOB COMPLETED ===")

# APScheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(background_email_job, 'interval', minutes=0.5)
scheduler.start()

def run_scheduler_in_thread():
    while True:
        time.sleep(1)

threading.Thread(target=run_scheduler_in_thread, daemon=True).start() 

@app.get("/user/{user_id}/classified-emails")
def get_classified_emails(user_id: str):
    firebase_manager = FirebaseManager()
    emails = firebase_manager.get_user_classifications(user_id)
    return {"emails": emails}

@app.post("/trigger-background-job")
def trigger_background_job():
    """Manually trigger the background email classification job"""
    try:
        background_email_job()
        return {"success": True, "message": "Background job completed"}
    except Exception as e:
        return {"success": False, "error": str(e)} 

def get_or_create_label(service, label_name):
    # Get all labels
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for label in labels:
        if label['name'].lower() == label_name.lower():
            return label['id']
    
    # If not found, create it
    label_obj = {
        "name": label_name,
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

@app.post("/create-payment-intent")
def create_payment_intent(payment_request: PaymentRequest):
    """Create a payment intent for the £5.99 subscription"""
    try:
        result = stripe_handler.create_payment_intent(payment_request.customer_email)
        return {
            "success": True,
            "client_secret": result['client_secret'],
            "payment_intent_id": result['payment_intent_id']
        }
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