import stripe
import os
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

# Initialize Stripe with your secret key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripeHandler:
    def __init__(self):
        self.currency = 'gbp'
        self.amount = 599  # £5.99 in pence
        
    def create_payment_intent(self, customer_email: str):
        """Create a payment intent for the £5.99 subscription"""
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=self.amount,
                currency=self.currency,
                metadata={
                    'customer_email': customer_email,
                    'subscription_type': 'standard'
                },
                description='Clogged.ai Standard Plan - £5.99/month'
            )
            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id
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
    
    def create_subscription(self, customer_id: str):
        """Create a subscription for the customer"""
        try:
            # First, create a product and price if they don't exist
            product = stripe.Product.create(
                name="Clogged.ai Standard Plan",
                description="AI-powered email management and organization"
            )
            
            price = stripe.Price.create(
                product=product.id,
                unit_amount=self.amount,
                currency=self.currency,
                recurring={'interval': 'month'}
            )
            
            # Create the subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price.id}],
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