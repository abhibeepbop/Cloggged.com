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

app = FastAPI()

# Initialize Firebase Admin (do this once at startup)
cred = credentials.Certificate("../KEYS/maila-248fc-firebase-adminsdk-fbsvc-0cc3ab381b.json")
firebase_admin.initialize_app(cred)

GOOGLE_OAUTH_CLIENT_SECRET_PATH = "C:\\Users\\vabhi\\OneDrive\\Desktop\\Personal\\coding\\KEYS\\client_secret_536404685178-e9efhvprp9gl1t72pgvmn4u2o2n6clsu.apps.googleusercontent.com.json"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email"
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
def read_root():
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
    return {"auth_url": auth_url}

@app.get("/gmail/oauth2callback")
def gmail_oauth2callback(code: str, state: str):
    print("GOOGLE_REDIRECT_URI:", GOOGLE_REDIRECT_URI)
    # state is the user's UID
    flow = Flow.from_client_secrets_file(
        GOOGLE_OAUTH_CLIENT_SECRET_PATH,
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    flow.fetch_token(code=code)
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
    # Store tokens in Firestore under users/<uid>/gmail_tokens
    db = firestore.client()
    user_ref = db.collection("identifier").document(state)
    user_ref.update({"gmail_tokens": tokens})
    return {"success": True, "message": "Gmail tokens stored for user.", "user": state}

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

def background_email_job():
    print("=== BACKGROUND JOB STARTED ===")
    db = firestore.client()
    users = db.collection('identifier').stream()
    user_count = 0
    for user_doc in users:
        user_data = user_doc.to_dict()
        user_id = user_data.get('uid') or user_doc.id
        tokens = user_data.get('gmail_tokens')
        print(f"Processing user: {user_id}")
        if not tokens:
            print(f"No Gmail tokens found for user: {user_id}")
            continue
        try:
            # Fetch recent emails for this user
            service = get_gmail_service_for_user(user_id)
            processed_label_id = get_processed_label_id(service)
            # Gmail search uses label names, not IDs, for the q param
            results = service.users().messages().list(
                userId='me',
                maxResults=5,
                q='-label:Processed'
            ).execute()
            messages = results.get('messages', [])
            print(f"Found {len(messages)} emails for user: {user_id}")
            for msg in messages:
                # Check if email is already processed
                if is_email_already_processed(service, msg['id']):
                    print(f"Email {msg['id']} already processed, skipping...")
                    continue
                
                msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
                subject = ''
                snippet = msg_detail.get('snippet', '')
                headers = msg_detail.get('payload', {}).get('headers', [])
                for header in headers:
                    if header.get('name', '').lower() == 'subject':
                        subject = header.get('value', '')
                        break
                # Classify email
                print(f"Classifying email: {subject[:50]}...")
                result = email_classifier.classify_single_email(subject, snippet, msg['id'])
                classification = result.get('classification', 'spam')
                confidence = result.get('confidence', 0.5)
                print(f"Classification result: {classification} (confidence: {confidence})")

                # Store result under user (per-user subcollection)
                print(f"Storing classification in Firebase for user: {user_id}")
                success = firebase_manager.store_email_classification(
                    user_id=user_id,
                    email_id=msg['id'],
                    subject=subject,
                    snippet=snippet,
                    classification=classification,
                    confidence=confidence
                )
                print(f"Firebase storage success: {success}")

                # --- Gmail labeling and moving ---
                label_name = "Spam" if classification == "spam" else "Not Spam"
                print(f"Applying Gmail label: {label_name}")
                
                # Get label IDs
                label_id = get_or_create_label(service, label_name)
                processed_label_id = get_processed_label_id(service)
                
                # Prepare modification body
                modify_body = {
                    'addLabelIds': [label_id, processed_label_id]
                }
                
                # If it's spam, move it to the Spam folder (remove from INBOX)
                if classification == "spam":
                    # Get the SPAM label ID (Gmail's built-in spam label)
                    spam_label_id = "SPAM"
                    modify_body['removeLabelIds'] = ['INBOX']
                    modify_body['addLabelIds'].append(spam_label_id)
                    print(f"Moving spam email to Spam folder")
                
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
        "messageListVisibility": "show"
    }
    new_label = service.users().labels().create(userId='me', body=label_obj).execute()
    return new_label['id']

def get_processed_label_id(service):
    """Get or create the 'Processed' label to mark emails as already processed"""
    return get_or_create_label(service, "Processed")

def is_email_already_processed(service, email_id):
    """Check if email already has the 'Processed' label"""
    try:
        msg = service.users().messages().get(userId='me', id=email_id).execute()
        label_ids = msg.get('labelIds', [])
        
        # Get the processed label ID
        processed_label_id = get_processed_label_id(service)
        
        return processed_label_id in label_ids
    except Exception as e:
        print(f"Error checking if email is processed: {e}")
        return False 