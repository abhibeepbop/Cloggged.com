import stripe
import os
from fastapi import HTTPException
from dotenv import load_dotenv
from firebase_admin import firestore
from datetime import datetime

load_dotenv()

# Initialize Stripe with your secret key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripeHandler:
    def __init__(self):
        self.currency = 'gbp'
        self.amount = 599  # £5.99 in pence
        
    def create_payment_intent(self, customer_email: str):
        """Create a setup intent for the £5.99 subscription with 7-day trial"""
        try:
            # Create customer first
            customer = stripe.Customer.create(
                email=customer_email,
                metadata={'source': 'clogged_ai'}
            )
            
            # Create subscription with trial
            subscription = self.create_subscription_with_trial(customer.id)
            
            # Create a setup intent for saving payment method (no immediate charge)
            setup_intent = stripe.SetupIntent.create(
                customer=customer.id,
                payment_method_types=['card'],
                metadata={
                    'customer_email': customer_email,
                    'subscription_type': 'standard',
                    'subscription_id': subscription.id,
                    'trial_end': subscription.trial_end
                },
                description='Clogged.ai Standard Plan - 7-day free trial'
            )
            return {
                'success': True,
                'client_secret': setup_intent.client_secret,
                'setup_intent_id': setup_intent.id,
                'customer_id': customer.id,
                'subscription_id': subscription.id,
                'trial_end': subscription.trial_end
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    def create_customer(self, email: str, name: str = None):
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'source': 'clogged_ai'
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    def create_subscription_with_trial(self, customer_id: str):
        """Create a subscription with 7-day trial"""
        try:
            # Use the price ID from your Stripe Dashboard
            price_id = os.getenv('STRIPE_PRICE_ID')
            
            # Create the subscription with trial
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                trial_period_days=7,  # 7-day free trial
                metadata={
                    'service': 'clogged_ai'
                }
            )
            return subscription
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    def create_subscription(self, customer_id: str):
        """Create a subscription with 7-day free trial"""
        try:
            # Use the price ID from your Stripe Dashboard
            price_id = os.getenv('STRIPE_PRICE_ID')  # Add this to your .env file
            
            # Create the subscription with trial
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                trial_period_days=7,  # 7-day free trial
                metadata={
                    'service': 'clogged_ai'
                }
            )
            return subscription.id
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    def handle_webhook(self, payload: bytes, sig_header: str):
        """Handle Stripe webhooks for payment confirmation"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
            )
            
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                # Handle successful payment
                return self.handle_payment_success(payment_intent)
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                # Handle failed payment
                return self.handle_payment_failure(payment_intent)
            elif event['type'] == 'customer.subscription.created':
                subscription = event['data']['object']
                # Handle subscription creation (trial started)
                return self.handle_subscription_created(subscription)
            elif event['type'] == 'customer.subscription.trial_will_end':
                subscription = event['data']['object']
                # Handle trial ending soon
                return self.handle_trial_ending(subscription)
            elif event['type'] == 'invoice.payment_succeeded':
                invoice = event['data']['object']
                # Handle first payment after trial
                return self.handle_first_payment(invoice)
                
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    def handle_payment_success(self, payment_intent):
        """Handle successful payment"""
        customer_email = payment_intent.get('metadata', {}).get('customer_email')
        # Here you would:
        # 1. Update user status in Firebase
        # 2. Start Gmail integration process
        # 3. Send welcome email
        return {
            'status': 'success',
            'customer_email': customer_email,
            'payment_intent_id': payment_intent['id']
        }
    
    def handle_payment_failure(self, payment_intent):
        """Handle failed payment"""
        return {
            'status': 'failed',
            'payment_intent_id': payment_intent['id']
        }
    
    def handle_subscription_created(self, subscription):
        """Handle subscription creation (trial started)"""
        try:
            # Get customer details
            customer = stripe.Customer.retrieve(subscription['customer'])
            customer_email = customer.email
            
            # Save user to Firebase
            db = firestore.client()
            
            # Create user document
            user_data = {
                "uid": f"user_{subscription['customer']}",  # Use customer ID as UID
                "email": customer_email,
                "name": customer.name or "User",
                "created_at": datetime.utcnow(),
                "subscription_status": "active",
                "subscribed": True,
                "subscription_id": subscription['id'],
                "customer_id": subscription['customer'],
                "trial_end": subscription['trial_end'],
                "trial_start": subscription['created'],  # When trial started
                "payment_date": datetime.utcnow().timestamp(),  # When payment was completed
                "next_billing_date": subscription['trial_end'],  # First billing after trial
                "payment_completed": True,  # Trial is considered payment completed
                "settings": {
                    "auto_categorize": True,
                    "confidence_threshold": "0.8",
                    "spam_sensitivity": "medium"
                },
                "gmail_tokens": None,
                "last_sync": None
            }
            
            # Add to identifiers collection
            user_ref = db.collection("identifier").document(f"user_{subscription['customer']}")
            user_ref.set(user_data)
            
            print(f"User {customer_email} saved to Firebase with subscription {subscription['id']}")
            
            return {
                'status': 'trial_started',
                'subscription_id': subscription['id'],
                'trial_end': subscription['trial_end'],
                'customer_email': customer_email,
                'firebase_uid': f"user_{subscription['customer']}"
            }
        except Exception as e:
            print(f"Error saving user to Firebase: {e}")
            return {
                'status': 'trial_started',
                'subscription_id': subscription['id'],
                'trial_end': subscription['trial_end'],
                'customer_email': customer_email,
                'error': str(e)
            }
    
    def handle_trial_ending(self, subscription):
        """Handle trial ending soon (3 days before)"""
        customer_email = subscription.get('metadata', {}).get('customer_email')
        # Here you could send an email reminder
        return {
            'status': 'trial_ending',
            'subscription_id': subscription['id'],
            'trial_end': subscription['trial_end'],
            'customer_email': customer_email
        }
    
    def handle_first_payment(self, invoice):
        """Handle first payment after trial"""
        customer_email = invoice.get('customer_email')
        return {
            'status': 'first_payment',
            'invoice_id': invoice['id'],
            'amount': invoice['amount_paid'],
            'customer_email': customer_email
        } 