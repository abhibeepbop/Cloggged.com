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
                    "You are an email classifier. Respond with ONLY one of these categories (exact text):\n"
                    "- 'Urgent / Action Required' – Time-sensitive and needs attention now (client escalations, manager requests, last-minute approvals).\n"
                    "- 'Waiting on Others' – You can’t progress until someone else replies (follow-ups, blockers).\n"
                    "- 'Projects / Workstreams / Meetings' – Project/task updates, deliverables, standups, and meeting info.\n"
                    "- 'Clients / External' – Communication with customers, partners, or vendors (any external party).\n"
                    "- 'Finance & Admin' – Invoices, expenses, HR updates, payroll, policies, ops.\n"
                    "- 'Security & Systems' – OTPs/login codes, system alerts, IT notifications.\n"
                    "- 'Spam' – Unwanted marketing/promotions/newsletters or irrelevant bulk email.\n\n"
                    "Rules:\n"
                    "- If login/security/OTP/system alert → 'Security & Systems'\n"
                    "- If finance/HR/expenses/policies → 'Finance & Admin'\n"
                    "- If meetings/tasks/project updates → 'Projects / Workstreams / Meetings'\n"
                    "- If external parties/clients/vendors → 'Clients / External'\n"
                    "- If waiting for a reply to proceed → 'Waiting on Others'\n"
                    "- If urgent and time-sensitive → 'Urgent / Action Required'\n"
                    "- If obviously unwanted promotions/newsletters/ads or anything that the user might have subscribed to accidentally → 'Spam'\n\n"
                    "Signals (keywords that strongly indicate a category):\n"
                    "- Security & Systems: otp, one-time password, verification code, 2fa, mfa, login, password, security alert, suspicious activity, system alert, it, ops.\n"
                    "- Finance & Admin: invoice, receipt, billing, payment, payroll, expense, hr, policy, bank, statement, refund, tax.\n"
                    "- Urgent / Action Required: urgent, asap, immediately, action required, need your approval, deadline.\n"
                    "- Waiting on Others: waiting on, awaiting, blocked, following up, follow-up, gentle reminder, pending your.\n"
                    "- Clients / External: client, customer, vendor, partner, external.\n"
                    "- Projects / Workstreams / Meetings: meeting, calendar, invite, schedule, reschedule, reminder, standup, project, task, ticket, spec.\n"
                    "- Spam: unsubscribe, newsletter, marketing, promotion, sale, deal, offer, advertisement.\n\n"
                    "Choose the single best category based on these signals and the content. If signals conflict, prefer the strongest signal matching the core intent. Respond with exactly one category string, nothing else."
                )),
                HumanMessage(content=f"Subject: {subject}\n\nSnippet: {snippet}")
            ]
            
            try:
                response = self.llm.invoke(prompt)
                classification = response.content.strip().lower()

                # Heuristic override for obvious buckets based on keywords (ordered)
                text = f"{subject} {snippet}".lower()
                spam_kw = [
                    'unsubscribe', 'newsletter', 'marketing', 'promotion', 'promotions', 'sale', 'deal', 'offer', 'special offer', 'limited time', 'ad '
                ]
                security_kw = [
                    'otp', 'one-time password', 'one time password', 'verification code', '2fa', 'mfa',
                    'login', 'log in', 'signin', 'sign-in', 'password', 'security alert', 'suspicious', 'unusual activity',
                    'google verification code', 'auth code', 'verification required'
                ]
                finance_kw = [
                    'invoice', 'invoices', 'receipt', 'billing', 'payment', 'payroll', 'expense', 'expenses',
                    'hr', 'policy', 'policies', 'bank', 'statement', 'refund', 'tax'
                ]
                urgent_kw = ['urgent', 'asap', 'immediately', 'action required', 'need your approval', 'deadline']
                waiting_kw = ['waiting on', 'awaiting', 'blocked', 'pending your', 'following up', 'follow-up', 'gentle reminder']
                clients_kw = ['client', 'customer', 'vendor', 'partner', 'external']
                meetings_kw = ['meeting', 'calendar', 'invite', 'schedule', 'reschedule', 'reminder', 'standup', 'stand-up']

                if any(k in text for k in spam_kw):
                    classification = 'spam'
                elif any(k in text for k in security_kw):
                    classification = 'security & systems'
                elif any(k in text for k in finance_kw):
                    classification = 'finance & admin'
                elif any(k in text for k in urgent_kw):
                    classification = 'urgent / action required'
                elif any(k in text for k in waiting_kw):
                    classification = 'waiting on others'
                elif any(k in text for k in clients_kw):
                    classification = 'clients / external'
                elif any(k in text for k in meetings_kw):
                    classification = 'projects / workstreams / meetings'
                
                # Map variations/synonyms to the new standard categories
                category_mapping = {
                    # Exact phrase self-maps (model may return the exact category)
                    'urgent / action required': 'Urgent / Action Required',
                    'waiting on others': 'Waiting on Others',
                    'projects / workstreams / meetings': 'Projects / Workstreams / Meetings',
                    'clients / external': 'Clients / External',
                    'finance & admin': 'Finance & Admin',
                    'security & systems': 'Security & Systems',

                    'urgent': 'Urgent / Action Required',
                    'urgent / action required': 'Urgent / Action Required',
                    'important': 'Urgent / Action Required',
                    'asap': 'Urgent / Action Required',
                    'priority': 'Urgent / Action Required',

                    'waiting': 'Waiting on Others',
                    'waiting on others': 'Waiting on Others',
                    'awaiting': 'Waiting on Others',
                    'blocked': 'Waiting on Others',
                    'follow-up': 'Waiting on Others',
                    'follow up': 'Waiting on Others',

                    'meeting': 'Projects / Workstreams / Meetings',
                    'meetings': 'Projects / Workstreams / Meetings',
                    'calendar': 'Projects / Workstreams / Meetings',
                    'invite': 'Projects / Workstreams / Meetings',
                    'schedule': 'Projects / Workstreams / Meetings',
                    'reschedule': 'Projects / Workstreams / Meetings',
                    'reminder': 'Projects / Workstreams / Meetings',
                    'project': 'Projects / Workstreams / Meetings',
                    'projects': 'Projects / Workstreams / Meetings',
                    'task': 'Projects / Workstreams / Meetings',
                    'tasks': 'Projects / Workstreams / Meetings',
                    'ticket': 'Projects / Workstreams / Meetings',
                    'issue': 'Projects / Workstreams / Meetings',
                    'details': 'Projects / Workstreams / Meetings',
                    'spec': 'Projects / Workstreams / Meetings',

                    'client': 'Clients / External',
                    'clients': 'Clients / External',
                    'customer': 'Clients / External',
                    'customers': 'Clients / External',
                    'vendor': 'Clients / External',
                    'vendors': 'Clients / External',
                    'partner': 'Clients / External',
                    'partners': 'Clients / External',
                    'external': 'Clients / External',

                    'finance': 'Finance & Admin',
                    'finances': 'Finance & Admin',
                    'financial': 'Finance & Admin',
                    'banking': 'Finance & Admin',
                    'invoice': 'Finance & Admin',
                    'invoices': 'Finance & Admin',
                    'payment': 'Finance & Admin',
                    'payments': 'Finance & Admin',
                    'receipt': 'Finance & Admin',
                    'billing': 'Finance & Admin',
                    'hr': 'Finance & Admin',
                    'payroll': 'Finance & Admin',
                    'policy': 'Finance & Admin',
                    'policies': 'Finance & Admin',

                    'security': 'Security & Systems',
                    'login': 'Security & Systems',
                    'logins': 'Security & Systems',
                    'password': 'Security & Systems',
                    '2fa': 'Security & Systems',
                    'mfa': 'Security & Systems',
                    'otp': 'Security & Systems',
                    'otps': 'Security & Systems',
                    'verification': 'Security & Systems',
                    'code': 'Security & Systems',
                    'alert': 'Security & Systems',
                    'system': 'Security & Systems',
                    'systems': 'Security & Systems',
                    'it': 'Security & Systems',
                    'ops': 'Security & Systems',

                    'spam': 'Spam',
                    'promotion': 'Spam',
                    'promotions': 'Spam',
                    'newsletter': 'Spam',
                    'newsletters': 'Spam',
                    'marketing': 'Spam',
                    'ads': 'Spam',
                    'advertisement': 'Spam',
                    'deal': 'Spam',
                    'sale': 'Spam',
                }
                
                # Get the mapped category; do not fallback to a bucket
                classification = category_mapping.get(classification, classification)
                
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
                    'classification': 'Spam',
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
                    'classification': 'Spam',
                    'confidence': 0.5
                }
        return {
            'email_id': email_data.get('email_id'),
            'subject': email_data.get('subject', ''),
            'snippet': email_data.get('snippet', ''),
            'classification': 'Spam',
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