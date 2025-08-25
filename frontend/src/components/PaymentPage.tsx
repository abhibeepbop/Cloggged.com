import { API_BASE } from "./../utils/api";
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PaymentForm } from './PaymentForm';

export function PaymentPage() {
  const navigate = useNavigate();
  const [customerEmail, setCustomerEmail] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Get user email from Firebase auth or localStorage
    // For now, we'll use a placeholder - you can enhance this later
    const userEmail = localStorage.getItem('userEmail') || '';
    setCustomerEmail(userEmail);
    setIsLoading(false);
  }, []);

  const handlePaymentSuccess = () => {
    // After successful payment, redirect to dashboard
    navigate('/dashboard');
  };

  const handlePaymentCancel = () => {
    // Go back to pricing page
    navigate('/pricing');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-navy-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-navy-800 mx-auto mb-4"></div>
          <p className="text-navy-900">Loading payment form...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-navy-50 font-['Inter']">
      {/* Header */}
      <header className="border-b border-navy-800 shadow-md bg-navy-900">
        <div className="max-w-7xl mx-auto px-6 py-5 flex justify-between items-center">
          <h1 
            onClick={() => navigate('/')}
            className="text-2xl font-bold tracking-tight text-white cursor-pointer hover:text-gray-200 transition-colors"
          >
            cloggged.com
          </h1>
          <div className="flex gap-8">
            <button 
              onClick={() => navigate('/')}
              className="bg-white hover:bg-gray-100 text-black border-2 border-black px-4 py-2 rounded-full font-medium transition-colors"
            >
              Home
            </button>
            <button 
              onClick={() => window.location.href = `${API_BASE}/auth/google`}
              className="bg-[#EFA6A7] hover:bg-[#e89899] text-black px-4 py-2 rounded-full font-medium transition-colors"
            >
              Sign In
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex flex-col items-center justify-center py-16 px-6">
        <div className="max-w-2xl w-full">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-bold text-navy-900 mb-4">Start Your Free Trial</h2>
            <p className="text-lg text-navy-700 mb-4">
              You're just one step away from organizing your inbox with AI
            </p>
            <div className="text-center">
              <p className="text-navy-700 font-medium">£5.99/month • Cancel anytime</p>
            </div>
          </div>

          {/* Payment Form */}
          <PaymentForm
            onSuccess={handlePaymentSuccess}
            onCancel={handlePaymentCancel}
            customerEmail={customerEmail}
          />


        </div>
      </main>
    </div>
  );
} 