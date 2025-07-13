from gmail_auth import gmail_authenticate

service = gmail_authenticate()

results = service.users().messages().list(userId='me', maxResults=5).execute()
messages = results.get('messages', [])

for msg in messages:
    txt = service.users().messages().get(userId='me', id=msg['id']).execute()
    print(f"Snippet: {txt['snippet']}\n{'-'*40}")
