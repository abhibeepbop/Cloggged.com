import { API_BASE } from "../utils/api";
import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';

// Load Stripe (replace with your publishable key)
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || 'pk_test_your_key_here');

interface PaymentFormProps {
  onSuccess: () => void;
  onCancel: () => void;
  customerEmail: string;
}

function CheckoutForm({ onSuccess, onCancel, customerEmail }: PaymentFormProps) {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clientSecret, setClientSecret] = useState<string | null>(null);

  React.useEffect(() => {
    // Create payment intent when component mounts
    const createPaymentIntent = async () => {
      try {
        const response = await fetch(`${API_BASE}/create-payment-intent`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            customer_email: customerEmail,
          }),
        });

        const data = await response.json();

        if (data.success) {
          setClientSecret(data.client_secret);
        } else {
          setError(data.error || 'Failed to create payment intent');
        }
      } catch (err) {
        setError('Failed to initialize payment');
      }
    };

    createPaymentIntent();
  }, [customerEmail]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements || !clientSecret) {
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Handle card payment
      const result = await stripe.confirmCardSetup(clientSecret, {
        payment_method: {
          card: elements.getElement(CardElement)!,
          billing_details: {
            email: customerEmail,
          },
        },
      });

      if (result.error) {
        setError(result.error.message || 'Payment failed');
      } else {
        // Payment successful
        onSuccess();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Payment failed');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white p-8 rounded-3xl border-4 border-navy-800 shadow-[10px_10px_0px_0px_rgba(30,58,138,0.2)]">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Complete Your Subscription
        </h3>
        
        <div className="mb-4">
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Card Details
          </label>
          <div className="border border-gray-300 rounded-md p-3">
            <CardElement
              options={{
                style: {
                  base: {
                    fontSize: '16px',
                    color: '#424770',
                    '::placeholder': {
                      color: '#aab7c4',
                    },
                  },
                  invalid: {
                    color: '#9e2146',
                  },
                },
              }}
            />
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={!stripe || isProcessing || !clientSecret}
            className="flex-1 bg-[#EFA6A7] hover:bg-[#e89899] text-black font-medium py-2 px-4 rounded-full transition-colors disabled:opacity-50"
          >
            {isProcessing ? 'Processing...' : 'Start 7-Day Free Trial'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </form>
  );
}

export function PaymentForm({ onSuccess, onCancel, customerEmail }: PaymentFormProps) {
  return (
    <Elements stripe={stripePromise}>
      <CheckoutForm
        onSuccess={onSuccess}
        onCancel={onCancel}
        customerEmail={customerEmail}
      />
    </Elements>
  );
} 