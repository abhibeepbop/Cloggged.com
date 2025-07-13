import os
from gmail_auth import gmail_authenticate

# Set this to your public webhook URL (e.g., from ngrok)
webhook_url = "https://7030e9d62cfa.ngrok-free.app/gmail/notify"

# Gmail label to watch ("INBOX" watches all incoming mail)
label_ids = ["INBOX"]

if __name__ == "__main__":
    service = gmail_authenticate()
    request_body = {
        "labelIds": label_ids,
        "topicName": webhook_url  # For Gmail API, this is usually a Google Pub/Sub topic, but for testing, webhook_url is used for demonstration
    }
    try:
        # The real Gmail API expects a Google Pub/Sub topic for push notifications.
        # For direct webhooks, you may need to use polling or a third-party service.
        # This code is for demonstration and will not work unless you have a Pub/Sub topic set up.
        response = service.users().watch(userId="me", body=request_body).execute()
        print("Watch response:", response)
        print("Successfully registered for Gmail push notifications.")
    except Exception as e:
        print("Error registering for Gmail watch:", e)
        print("Note: For production, you must use a Google Pub/Sub topic as the webhook destination.") 