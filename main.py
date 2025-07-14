# main.py - Gmail AI Spam Classifier with Firebase Integration

from gmail_auth import gmail_authenticate
from email_classifier import EmailClassifier
from firebase_manager import FirebaseManager
from gmail_label_manager import GmailLabelManager
from config import MAX_PARALLEL_REQUESTS
import time

class GmailSpamClassifier:
    def __init__(self):
        self.service = gmail_authenticate()
        self.classifier = EmailClassifier()
        self.firebase = FirebaseManager()
        self.label_manager = GmailLabelManager()
    
    def fetch_recent_emails(self, max_results=10):
        """Fetch recent emails from Gmail"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                q='-label:AI_Processed',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                msg_detail = self.service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()
                
                subject = ''
                snippet = msg_detail.get('snippet', '')
                
                # Extract subject from headers
                headers = msg_detail.get('payload', {}).get('headers', [])
                for header in headers:
                    if header.get('name', '').lower() == 'subject':
                        subject = header.get('value', '')
                        break
                
                emails.append({
                    'email_id': msg['id'],
                    'subject': subject,
                    'snippet': snippet
                })
            
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def classify_and_store_emails(self, emails):
        """Classify emails using AI and store results in Firebase"""
        if not emails:
            print("No emails to classify")
            return []
        
        print(f"Classifying {len(emails)} emails...")
        
        # Classify emails in parallel
        classifications = self.classifier.classify_emails_parallel(emails)
        
        # Store classifications in Firebase
        for classification in classifications:
            self.firebase.store_email_classification(
                email_id=classification['email_id'],
                subject=classification['subject'],
                snippet=classification['snippet'],
                classification=classification['classification'],
                confidence=classification.get('confidence')
            )
        
        print(f"Stored {len(classifications)} classifications in Firebase")
        return classifications
    
    def process_and_organize_emails(self, classifications):
        """Process classified emails and organize them into Gmail labels"""
        if not classifications:
            print("No classifications to process")
            return 0
        
        print(f"Organizing {len(classifications)} emails into labels...")
        
        # Move emails to appropriate labels
        success_count = self.label_manager.process_classified_emails(classifications)
        
        # Mark as processed in Firebase
        for classification in classifications:
            self.firebase.mark_as_processed(classification['email_id'])
        
        return success_count
    
    def run_classification_pipeline(self, max_emails=10):
        """Run the complete email classification pipeline"""
        print("Starting Gmail AI Spam Classifier...")
        print("=" * 50)
        
        # Step 1: Fetch recent emails
        print("Fetching recent emails...")
        emails = self.fetch_recent_emails(max_emails)
        print(f"Found {len(emails)} emails to process")
        
        if not emails:
            print("No emails found to process")
            return
        
        # Step 2: Classify emails with AI
        print("\nClassifying emails with AI...")
        classifications = self.classify_and_store_emails(emails)
        
        # Step 3: Organize emails into labels
        print("\nOrganizing emails into labels...")
        processed_count = self.process_and_organize_emails(classifications)
        
        # Step 4: Show results
        print("\nResults:")
        stats = self.firebase.get_classification_stats()
        print(f"Total classified: {stats['total_count']}")
        print(f"Spam: {stats['spam_count']}")
        print(f"Not Spam: {stats['not_spam_count']}")
        print(f"Successfully organized: {processed_count} emails")
        
        print("\nPipeline completed!")

def main():
    classifier = GmailSpamClassifier()
    classifier.run_classification_pipeline(max_emails=5)  # Start with 5 emails for testing

if __name__ == "__main__":
    main() 