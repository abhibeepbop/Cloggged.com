from fastapi import FastAPI, HTTPException, status, Depends, Request, Security
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status, Request
from firebase_admin import firestore
from datetime import datetime

app = FastAPI()

# Initialize Firebase Admin (do this once at startup)
cred = credentials.Certificate("../KEYS/maila-248fc-firebase-adminsdk-fbsvc-0cc3ab381b.json")
firebase_admin.initialize_app(cred)

def verify_firebase_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    id_token = auth_header.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        # Ensure user profile exists in Firestore
        db = firestore.client()
        user_ref = db.collection("users").document(decoded_token["uid"])
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

bearer_scheme = HTTPBearer()

@app.get("/protected")
def protected_route(
    user=Depends(verify_firebase_token),
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    return {"message": f"Hello, {user['uid']}!"} 