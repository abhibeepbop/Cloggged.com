# Gmail AI Spam Classifier Setup

This application uses AI to classify emails as spam or not spam, then organizes them into Gmail labels.

## Prerequisites

1. **Google Cloud Project** with Gmail API enabled
2. **OpenAI API Key** for AI classification
3. **Firebase Project** for data storage

## Setup Steps

### 1. Google Cloud Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download `client_id.json` and place in project root

### 2. OpenAI Setup
1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add to environment variables or `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### 3. Firebase Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Go to Project Settings > Service Accounts
4. Generate new private key
5. Add Firebase credentials to environment variables:
   ```
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_PRIVATE_KEY_ID=your_private_key_id
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
   FIREBASE_CLIENT_ID=your_client_id
   ```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
python main.py
```

## How It Works

1. **Email Fetching**: Fetches recent emails from Gmail
2. **AI Classification**: Uses OpenAI GPT-3.5-turbo to classify emails as spam/not spam
3. **Firebase Storage**: Stores classification results in Firebase Firestore
4. **Gmail Organization**: Creates labels and moves emails to appropriate folders

## Configuration

Edit `config.py` to customize:
- AI model used for classification
- Label names for spam/not spam
- Number of emails processed in parallel
- Gmail scopes

## Files Structure

- `main.py` - Main application orchestrator
- `email_classifier.py` - AI classification logic
- `firebase_manager.py` - Firebase database operations
- `gmail_label_manager.py` - Gmail label and email management
- `gmail_auth.py` - Gmail authentication
- `config.py` - Configuration settings 