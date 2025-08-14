import stripe
import os
from fastapi import HTTPException
from dotenv import load_dotenv
from firebase_admin import firestore
from datetime import datetime
import time
from typing import Any, Dict

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
            try:
                print(f"[Stripe] Event received: id={event.get('id')} type={event.get('type')} livemode={event.get('livemode')}")
            except Exception:
                pass
            # Idempotency guard: skip already processed events
            try:
                db = firestore.client()
                evt_ref = db.collection("stripe_events").document(event['id'])
                if evt_ref.get().exists:
                    print(f"[Stripe] Duplicate event ignored: {event['id']}")
                    return {"status": "duplicate", "event_id": event['id']}
                # Pre-create marker; merge later with outcome info if needed
                evt_ref.set({"received_at": int(time.time()), "type": event.get('type'), "livemode": event.get('livemode')})
            except Exception:
                # If idempotency store fails, continue; Stripe will retry on non-2xx
                pass
            
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                # For subscriptions created via Payment Links / Checkout
                try:
                    if session.get('mode') == 'subscription' and session.get('subscription'):
                        print(f"[Stripe] checkout.session.completed for subscription={session.get('subscription')} customer={session.get('customer')}")
                        subscription = stripe.Subscription.retrieve(session['subscription'])
                        # Prefer email from session (customer_details.email)
                        email = None
                        cd = session.get('customer_details') or {}
                        if isinstance(cd, dict):
                            email = cd.get('email')
                        if not email:
                            email = session.get('customer_email')
                        client_ref = session.get('client_reference_id')
                        print(f"[Stripe] Extracted email from session: {email} client_reference_id={client_ref}")
                        return self._upsert_user_from_subscription(subscription, email, user_id_override=client_ref)
                    else:
                        # One-time payments can be handled via payment_intent.succeeded
                        return {'status': 'checkout_completed', 'mode': session.get('mode')}
                except Exception as e:
                    print(f"[Stripe] Error handling checkout.session.completed: {e}")
                    return {'status': 'checkout_completed', 'error': str(e)}

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
        return self._upsert_user_from_subscription(subscription)

    def _upsert_user_from_subscription(self, subscription: dict, email_override: str | None = None, user_id_override: str | None = None) -> Dict[str, Any]:
        try:
            # Get customer details
            customer = stripe.Customer.retrieve(subscription['customer'])
            customer_email = email_override or getattr(customer, 'email', None) or None
            print(f"[Stripe] Upsert from subscription: sub_id={subscription.get('id')} customer_id={subscription.get('customer')} email_override={email_override} resolved_email={customer_email} user_id_override={user_id_override}")

            # Save user to Firebase
            db = firestore.client()

            # Create user document
            now = int(time.time())
            trial_end = subscription.get('trial_end')
            in_trial = isinstance(trial_end, int) and trial_end > now
            print(f"[Stripe] Trial info: trial_end={trial_end} in_trial={in_trial}")

            user_data = {
                "uid": f"user_{subscription['customer']}",  # Use customer ID as UID
                "email": customer_email,
                "name": getattr(customer, 'name', None) or "User",
                "created_at": datetime.utcnow(),
                "subscription_status": "active",
                "subscribed": True,
                "subscription_id": subscription['id'],
                "customer_id": subscription['customer'],
                "trial_end": trial_end,
                "trial_start": subscription['created'],  # When trial started
                "payment_date": datetime.utcnow().timestamp(),
                "next_billing_date": trial_end,  # First billing after trial
                "payment_completed": True if not in_trial else False,
                "settings": {
                    "auto_categorize": True,
                    "confidence_threshold": "0.8",
                    "spam_sensitivity": "medium"
                },
                "gmail_tokens": None,
                "last_sync": None
            }
            # Compute can_access
            try:
                now_ts = int(time.time())
            except Exception:
                now_ts = 0
            user_data["can_access"] = bool(user_data.get("subscribed") or (isinstance(trial_end, int) and trial_end > now_ts))

            users_ref = db.collection("identifier")
            user_ref = None
            # Highest priority: explicit user id from client_reference_id
            if user_id_override:
                print(f"[Stripe] Using user_id_override to link: {user_id_override}")
                user_ref = users_ref.document(user_id_override)
            # Prefer linking to an existing user by email
            if user_ref is None and customer_email:
                print(f"[Stripe] Searching user by email: {customer_email}")
                docs = users_ref.where("email", "==", customer_email).limit(1).get()
                if docs:
                    print(f"[Stripe] Found existing user by email: {docs[0].id}")
                    user_ref = users_ref.document(docs[0].id)
            # Otherwise try by stored Stripe customer id
            if user_ref is None:
                print(f"[Stripe] Searching user by customer_id: {subscription['customer']}")
                docs = users_ref.where("customer_id", "==", subscription['customer']).limit(1).get()
                if docs:
                    print(f"[Stripe] Found existing user by customer_id: {docs[0].id}")
                    user_ref = users_ref.document(docs[0].id)
            if user_ref is None:
                # Do not create a new user doc implicitly; wait for confirm-session to link or a later webhook match
                print(f"[Stripe] No existing user matched by user_id/email/customer_id; skipping upsert for subscription {subscription.get('id')}")
                return {"status": "no_user_match", "subscription_id": subscription.get('id')}
            print(f"[Stripe] Writing user doc: {user_ref.id} with fields: subscription_status={user_data['subscription_status']} subscribed={user_data['subscribed']} payment_completed={user_data['payment_completed']} trial_end={user_data['trial_end']}")
            user_ref.set(user_data, merge=True)

            print(f"User {customer_email or 'unknown'} saved/updated with subscription {subscription['id']}")

            return {
                'status': 'trial_started',
                'subscription_id': subscription['id'],
                'trial_end': subscription.get('trial_end'),
                'customer_email': customer_email,
                'firebase_uid': user_ref.id
            }
        except Exception as e:
            print(f"Error saving user to Firebase: {e}")
            return {
                'status': 'trial_started',
                'subscription_id': subscription.get('id'),
                'trial_end': subscription.get('trial_end'),
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
        try:
            customer_email = invoice.get('customer_email')
            customer_id = invoice.get('customer')
            print(f"[Stripe] invoice.payment_succeeded for invoice={invoice.get('id')} customer_id={customer_id} email={customer_email}")
            db = firestore.client()
            users_ref = db.collection("identifier")
            user_ref = None
            if customer_email:
                print(f"[Stripe] Searching user by email for invoice: {customer_email}")
                docs = users_ref.where("email", "==", customer_email).limit(1).get()
                if docs:
                    user_ref = users_ref.document(docs[0].id)
            if user_ref is None and customer_id:
                print(f"[Stripe] Searching user by customer_id for invoice: {customer_id}")
                docs = users_ref.where("customer_id", "==", customer_id).limit(1).get()
                if docs:
                    user_ref = users_ref.document(docs[0].id)
            if user_ref is not None:
                print(f"[Stripe] Updating user {user_ref.id} to payment_completed=true, active subscription")
                update = {
                    "subscription_status": "active",
                    "payment_completed": True,
                    "subscribed": True,
                    "payment_date": datetime.utcnow().timestamp()
                }
                # Maintain can_access
                try:
                    now_ts = int(time.time())
                except Exception:
                    now_ts = 0
                # Read trial_end to recompute
                doc = user_ref.get()
                trial_end_val = None
                try:
                    docd = doc.to_dict() or {}
                    trial_end_val = docd.get("trial_end")
                except Exception:
                    pass
                update["can_access"] = bool(True or (isinstance(trial_end_val, int) and trial_end_val > now_ts))
                user_ref.update(update)
            else:
                print(f"[Stripe] No user matched by email/customer_id for invoice {invoice.get('id')}; skipping update")
            return {
                'status': 'first_payment',
                'invoice_id': invoice['id'],
                'amount': invoice['amount_paid'],
                'customer_email': customer_email
            }
        except Exception as e:
            print(f"[Stripe] Error in handle_first_payment: {e}")
            return {'status': 'first_payment', 'error': str(e)}