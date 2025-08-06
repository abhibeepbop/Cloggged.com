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
        
    
    def store_email_classification(self, user_id, email_id, classification, confidence=None):
        """Store email classification in Firebase under the user's document"""
        if self.db is None:
            self._initialize_firebase()
        try:
            doc_ref = self.db.collection('identifier').document(user_id).collection('email_classifications').document(email_id)
            doc_ref.set({
                'email_id': email_id,
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
        """Get all email classifications for a specific user"""
        if self.db is None:
            self._initialize_firebase()
        try:
            docs = self.db.collection('identifier').document(user_id).collection('email_classifications').stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error getting user classifications: {e}")
            return []
    
    def get_email_classification(self, user_id, email_id):
        """Check if an email has already been classified for a specific user"""
        if self.db is None:
            self._initialize_firebase()
        try:
            doc_ref = self.db.collection('identifier').document(user_id).collection('email_classifications').document(email_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error checking email classification: {e}")
            return None 

    def get_user_billing_data(self, user_id):
        """Get user billing data including trial and billing dates"""
        if self.db is None:
            self._initialize_firebase()
        try:
            doc_ref = self.db.collection("identifier").document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                user_data = doc.to_dict()
                
                # Calculate next billing date from Firebase data
                next_billing_date = user_data.get('next_billing_date')
                
                # If no next_billing_date, calculate it from trial_end or payment_date
                if not next_billing_date:
                    if user_data.get('trial_end'):
                        trial_end = user_data.get('trial_end')
                        current_time = int(datetime.utcnow().timestamp())
                        
                        if trial_end > current_time:
                            # Trial hasn't ended yet
                            next_billing_date = trial_end
                        else:
                            # Trial has ended, calculate next monthly billing
                            next_billing_date = trial_end + (30 * 24 * 60 * 60)  # 30 days
                    elif user_data.get('payment_date'):
                        # Calculate from payment date
                        payment_date = user_data.get('payment_date')
                        next_billing_date = payment_date + (30 * 24 * 60 * 60)  # 30 days
                
                return {
                    'trial_start': user_data.get('trial_start'),
                    'trial_end': user_data.get('trial_end'),
                    'payment_date': user_data.get('payment_date'),
                    'next_billing_date': next_billing_date,
                    'subscription_status': user_data.get('subscription_status'),
                    'subscribed': user_data.get('subscribed'),
                    'payment_completed': user_data.get('payment_completed')
                }
            return None
        except Exception as e:
            print(f"Error getting user billing data: {e}")
            return None 