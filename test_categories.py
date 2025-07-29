from email_classifier import EmailClassifier
import asyncio

def test_email_categories():
    classifier = EmailClassifier()
    
    # Test emails with different categories
    test_emails = [
        {
            "subject": "Q4 Strategy Meeting - Tomorrow 2PM",
            "snippet": "Hi team, just a reminder about our strategic planning session tomorrow at 2 PM. Please prepare your quarterly reports.",
            "expected": "Work"
        },
        {
            "subject": "Your Chase Bank statement is ready",
            "snippet": "Your monthly credit card statement is now available for review. Please log in to your account to view the details.",
            "expected": "Finance"
        },
        {
            "subject": "New sign-in to your Google account",
            "snippet": "We detected a new sign-in to your Google account from a new device. If this was you, no action is needed.",
            "expected": "Security"
        },
        {
            "subject": "Your verification code is: 123456",
            "snippet": "Use this code to complete your purchase: 123456. This code will expire in 10 minutes.",
            "expected": "OTPs"
        },
        {
            "subject": "Family dinner this Sunday?",
            "snippet": "Hey honey, would you like to come over for dinner this Sunday? I'm making your favorite lasagna.",
            "expected": "Family"
        },
        {
            "subject": "URGENT: Client meeting in 30 minutes",
            "snippet": "The client meeting has been moved up to 3 PM today. Please prepare the presentation immediately.",
            "expected": "Urgent"
        },
        {
            "subject": "50% OFF - Limited Time Offer!",
            "snippet": "Don't miss out on our amazing sale! Get 50% off everything in our store. Limited time only!",
            "expected": "Spam"
        }
    ]
    
    print("Testing Email Classification Categories\n")
    print("=" * 50)
    
    for i, email in enumerate(test_emails, 1):
        print(f"\nTest {i}: {email['subject']}")
        print(f"Expected: {email['expected']}")
        
        try:
            result = classifier.classify_single_email(
                subject=email['subject'],
                snippet=email['snippet'],
                email_id=f"test_{i}"
            )
            
            classification = result['classification']
            print(f"Result: {classification}")
            
            if classification == email['expected']:
                print("✅ PASS")
            else:
                print("❌ FAIL - Expected vs Actual mismatch")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_email_categories() 