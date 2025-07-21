import firebase_admin
from firebase_admin import credentials, firestore
from config import (
    FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY_ID, FIREBASE_PRIVATE_KEY,
    FIREBASE_CLIENT_EMAIL, FIREBASE_CLIENT_ID
)
import json
from datetime import datetime

class FirebaseManager:
    def __init__(self):
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        self.db = firestore.client()
        """Initialize Firebase with service account credentials"""
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
        except ValueError:
            # Create service account credentials
            service_account_info = {
                "type": "service_account",
                "project_id": FIREBASE_PROJECT_ID,
                "private_key_id": FIREBASE_PRIVATE_KEY_ID,
                "private_key": FIREBASE_PRIVATE_KEY.replace('\\n', '\n') if FIREBASE_PRIVATE_KEY else None,
                "client_email": FIREBASE_CLIENT_EMAIL,
                "client_id": FIREBASE_CLIENT_ID,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{FIREBASE_CLIENT_EMAIL}"
            }
            
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
        
    
    def store_email_classification(self, user_id, email_id, subject, snippet, classification, confidence=None):
        """Store email classification in Firebase under the user's document"""
        if self.db is None:
            self._initialize_firebase()
        try:
            doc_ref = self.db.collection('identifier').document(user_id).collection('email_classifications').document(email_id)
            doc_ref.set({
                'email_id': email_id,
                'subject': subject,
                'snippet': snippet,
                'classification': classification,
                'confidence': confidence,
                'timestamp': datetime.now(),
                'processed': False
            })
            return True
        except Exception as e:
            print(f"Error storing email classification: {e}")
            return False
    
    def get_unprocessed_classifications(self):
        """Get all unprocessed email classifications"""
        if self.db is None:
            self._initialize_firebase()
        try:
            docs = self.db.collection('email_classifications').where('processed', '==', False).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error getting unprocessed classifications: {e}")
            return []
    
    def mark_as_processed(self, email_id):
        """Mark an email classification as processed"""
        if self.db is None:
            self._initialize_firebase()
        try:
            doc_ref = self.db.collection('email_classifications').document(email_id)
            doc_ref.update({'processed': True})
            return True
        except Exception as e:
            print(f"Error marking email as processed: {e}")
            return False
    
    def get_classification_stats(self):
        """Get classification statistics"""
        if self.db is None:
            self._initialize_firebase()
        try:
            spam_count = len(list(self.db.collection('email_classifications')
                                .where('classification', '==', 'spam')
                                .stream()))
            not_spam_count = len(list(self.db.collection('email_classifications')
                                    .where('classification', '==', 'not_spam')
                                    .stream()))
            return {
                'spam_count': spam_count,
                'not_spam_count': not_spam_count,
                'total_count': spam_count + not_spam_count
            }
        except Exception as e:
            print(f"Error getting classification stats: {e}")
            return {'spam_count': 0, 'not_spam_count': 0, 'total_count': 0} 

    def get_user_classifications(self, user_id):
        if self.db is None:
            self._initialize_firebase()
        try:
            docs = self.db.collection('identifier').document(user_id).collection('email_classifications').stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error getting user classifications: {e}")
            return [] 