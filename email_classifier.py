from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from config import OPENAI_API_KEY, AI_MODEL, MAX_PARALLEL_REQUESTS
import asyncio
from typing import List, Dict, Tuple

class EmailClassifier:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=AI_MODEL,
            temperature=0.1  # Low temperature for consistent classification
        )
        
        # Create the classification chain
        self.classification_chain = self._create_classification_chain()
    
    def _create_classification_chain(self):
        """Create a LangChain chain for email classification"""
        
        def classify_single_email(email_data: Dict) -> Dict:
            """Classify a single email"""
            subject = email_data.get('subject', '')
            snippet = email_data.get('snippet', '')
            
            prompt = [
                SystemMessage(content=(
                    "You are an email spam classifier. Analyze the email and respond with ONLY 'spam' or 'not_spam'.\n\n"
                    "Classification rules:\n"
                    "- Marketing emails, promotional content, newsletters = SPAM\n"
                    "- Job alerts, recruitment emails = SPAM\n"
                    "- Personal emails from friends/family = NOT SPAM\n"
                    "- Important notifications (OTPs, passwords, security) = NOT SPAM\n"
                    "- Work-related emails = NOT SPAM\n"
                    "- If unsure, classify as SPAM\n\n"
                    "Respond with exactly one word: 'spam' or 'not_spam'"
                )),
                HumanMessage(content=f"Subject: {subject}\n\nSnippet: {snippet}")
            ]
            
            try:
                response = self.llm.invoke(prompt)
                classification = response.content.strip().lower()
                
                # Ensure valid classification
                if classification not in ['spam', 'not_spam']:
                    classification = 'spam'  # Default to spam if unclear
                
                return {
                    'email_id': email_data.get('email_id'),
                    'subject': subject,
                    'snippet': snippet,
                    'classification': classification,
                    'confidence': 0.8  # Placeholder confidence
                }
            except Exception as e:
                print(f"Error classifying email {email_data.get('email_id')}: {e}")
                return {
                    'email_id': email_data.get('email_id'),
                    'subject': subject,
                    'snippet': snippet,
                    'classification': 'spam',  # Default to spam on error
                    'confidence': 0.5
                }
        
        return RunnableLambda(classify_single_email)
    
    def classify_emails_parallel(self, emails: List[Dict]) -> List[Dict]:
        """Classify multiple emails in parallel"""
        try:
            # Process emails in batches to avoid rate limits
            results = []
            for i in range(0, len(emails), MAX_PARALLEL_REQUESTS):
                batch = emails[i:i + MAX_PARALLEL_REQUESTS]
                batch_results = self.classification_chain.batch(batch)
                results.extend(batch_results)
            
            return results
        except Exception as e:
            print(f"Error in parallel classification: {e}")
            # Fallback to sequential processing
            return [self.classification_chain.invoke(email) for email in emails]
    
    def classify_single_email(self, subject: str, snippet: str, email_id: str = None) -> Dict:
        """Classify a single email"""
        email_data = {
            'email_id': email_id,
            'subject': subject,
            'snippet': snippet
        }
        result = self.classification_chain.invoke(email_data)
        return result 