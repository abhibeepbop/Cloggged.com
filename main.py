# main.py - Basic Gmail email fetching

from gmail_auth import gmail_authenticate

def main():
    print("Starting Gmail email fetcher...")
    
    try:
        service = gmail_authenticate()
        print("Successfully authenticated with Gmail!")
        
        # Get recent messages
        results = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])
        
        print(f"\nFound {len(messages)} recent messages:")
        print("-" * 50)
        
        for i, msg in enumerate(messages, 1):
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
            snippet = txt.get('snippet', 'No snippet available')
            print(f"{i}. {snippet}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 