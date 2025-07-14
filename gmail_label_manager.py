from gmail_auth import gmail_authenticate
from config import SPAM_LABEL_NAME, PROCESSED_LABEL_NAME
import time

class GmailLabelManager:
    def __init__(self):
        self.service = gmail_authenticate()
        self.spam_label_id = None
        self.processed_label_id = None
        self._ensure_labels_exist()
    
    def _ensure_labels_exist(self):
        """Ensure that the required spam label exists, create it if it doesn't"""
        try:
            # Get existing labels
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Find or create spam label
            self.spam_label_id = self._find_or_create_label(labels, SPAM_LABEL_NAME)
            self.processed_label_id = self._find_or_create_label(labels, PROCESSED_LABEL_NAME)
            
            print(f"Label ready - Spam: {self.spam_label_id}")
            
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
        """Move an email to the spam label if classified as spam. Leave not_spam emails in the inbox."""
        try:
            label_ids = [self.processed_label_id]
            remove_label_ids = []

            if classification == 'spam':
                label_ids.append(self.spam_label_id)
                remove_label_ids.append('INBOX')

            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={
                    'addLabelIds': label_ids,
                    'removeLabelIds': remove_label_ids
                }
            ).execute()

            print(f"Processed email {email_id}: {classification}, labels applied: {label_ids}, removed: {remove_label_ids}")
            return True
        except Exception as e:
            print(f"Error moving email {email_id}: {e}")
            return False
    
    def process_classified_emails(self, classifications):
        """Process a list of classified emails and move them to the spam label if needed"""
        success_count = 0
        for classification in classifications:
            email_id = classification.get('email_id')
            classification_result = classification.get('classification')
            
            if email_id and classification_result:
                if self.move_email_to_label(email_id, classification_result):
                    success_count += 1
        
        print(f"Successfully processed {success_count}/{len(classifications)} emails")
        return success_count 