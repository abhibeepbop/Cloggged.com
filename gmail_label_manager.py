from gmail_auth import gmail_authenticate
from config import SPAM_LABEL_NAME, NOT_SPAM_LABEL_NAME
import time

class GmailLabelManager:
    def __init__(self):
        self.service = gmail_authenticate()
        self.spam_label_id = None
        self.not_spam_label_id = None
        self._ensure_labels_exist()
    
    def _ensure_labels_exist(self):
        """Ensure that the required labels exist, create them if they don't"""
        try:
            # Get existing labels
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Find or create spam label
            self.spam_label_id = self._find_or_create_label(labels, SPAM_LABEL_NAME)
            
            # Find or create not spam label
            self.not_spam_label_id = self._find_or_create_label(labels, NOT_SPAM_LABEL_NAME)
            
            print(f"Labels ready - Spam: {self.spam_label_id}, Not Spam: {self.not_spam_label_id}")
            
        except Exception as e:
            print(f"Error setting up labels: {e}")
    
    def _find_or_create_label(self, existing_labels, label_name):
        """Find an existing label or create a new one"""
        # Check if label already exists
        for label in existing_labels:
            if label.get('name') == label_name:
                return label['id']
        
        # Create new label
        try:
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            created_label = self.service.users().labels().create(userId='me', body=label_object).execute()
            print(f"Created label: {label_name}")
            return created_label['id']
        except Exception as e:
            print(f"Error creating label {label_name}: {e}")
            return None
    
    def move_email_to_label(self, email_id, classification):
        """Move an email to the appropriate label based on classification"""
        try:
            if classification == 'spam':
                label_id = self.spam_label_id
            elif classification == 'not_spam':
                label_id = self.not_spam_label_id
            else:
                print(f"Unknown classification: {classification}")
                return False
            
            if not label_id:
                print("Label ID not found")
                return False
            
            # Add the label to the email
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            
            print(f"Moved email {email_id} to {classification} label")
            return True
            
        except Exception as e:
            print(f"Error moving email {email_id}: {e}")
            return False
    
    def process_classified_emails(self, classifications):
        """Process a list of classified emails and move them to appropriate labels"""
        success_count = 0
        for classification in classifications:
            email_id = classification.get('email_id')
            classification_result = classification.get('classification')
            
            if email_id and classification_result:
                if self.move_email_to_label(email_id, classification_result):
                    success_count += 1
        
        print(f"Successfully processed {success_count}/{len(classifications)} emails")
        return success_count 