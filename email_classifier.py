from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from config import OPENAI_API_KEY, AI_MODEL, MAX_PARALLEL_REQUESTS
import asyncio
import time
from openai import RateLimitError
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
                    "- If the email is a reply to a previous email, classify as NOT SPAM\n"
                    "- If the email contains any finances, like purchases, refunds or bank transfers, classify as NOT SPAM\n"
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
    
    async def _classify_email_async(self, email_data):
        for attempt in range(3):  # Retry up to 3 times
            try:
                return self.classification_chain.invoke(email_data)
            except RateLimitError:
                wait_time = 2 ** attempt
                print(f"Rate limit hit, retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                print(f"Error classifying email {email_data.get('email_id')}: {e}")
                return {
                    'email_id': email_data.get('email_id'),
                    'subject': email_data.get('subject', ''),
                    'snippet': email_data.get('snippet', ''),
                    'classification': 'spam',
                    'confidence': 0.5
                }
        return {
            'email_id': email_data.get('email_id'),
            'subject': email_data.get('subject', ''),
            'snippet': email_data.get('snippet', ''),
            'classification': 'spam',
            'confidence': 0.5
        }

    def classify_emails_parallel(self, emails):
        async def classify_all():
            sem = asyncio.Semaphore(MAX_PARALLEL_REQUESTS)
            async def sem_task(email):
                async with sem:
                    return await self._classify_email_async(email)
            tasks = [sem_task(email) for email in emails]
            return await asyncio.gather(*tasks)
        return asyncio.run(classify_all())
    
    def classify_single_email(self, subject: str, snippet: str, email_id: str = None) -> Dict:
        """Classify a single email"""
        email_data = {
            'email_id': email_id,
            'subject': subject,
            'snippet': snippet
        }
        result = self.classification_chain.invoke(email_data)
        return result 