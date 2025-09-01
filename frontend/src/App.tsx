import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { DashboardRoute } from "./components/DashboardRoute";
import { InboxHeader } from "./components/InboxHeader";
import { InboxHeaderUser } from "./components/InboxHeaderUser";
import { InboxSidebar } from "./components/InboxSidebar";
import { InboxContent } from "./components/InboxContent";
import { Pricing } from "./components/Pricing";
import { OAuthCallback } from "./components/OAuthCallback";
import { PaymentPage } from "./components/PaymentPage";
import { Dashboard } from "./components/Dashboard";
import { Consent } from "./components/Consent";
import { PaymentSuccess } from "./components/PaymentSuccess";
import { getStoredUser, canAccessDashboard, syncAuthFromSession } from "./utils/auth";
import { useEffect, useState } from "react";

// Inbox Component
import { isAuthenticated } from "./utils/auth";

function Inbox() {
  const [authReady, setAuthReady] = useState(false);

  // Sync from server session once on mount; trigger rerender when done
  useEffect(() => {
    let mounted = true;
    (async () => {
      await syncAuthFromSession();
      if (mounted) setAuthReady(true);
    })();
    return () => { mounted = false; };
  }, []);

  // After sync, decide redirect
  useEffect(() => {
    if (!authReady) return;
    const authedNow = isAuthenticated();
    const path = window.location.pathname;
    // Only auto-redirect from the dedicated /inbox route; allow '/' (home) for signed-in users
    if (path === '/inbox' && authedNow && canAccessDashboard(getStoredUser())) {
      window.history.replaceState({}, document.title, '/dashboard');
      window.location.href = '/dashboard';
    }
  }, [authReady]);
  return (
    <div className="min-h-screen bg-gray-50">
      {isAuthenticated() ? <InboxHeaderUser /> : <InboxHeader />}
      <div className="flex">
        <InboxSidebar />
        <InboxContent />
      </div>
    </div>
  );
}

function HowItWorks() {
  return (
    <div className="min-h-screen bg-gray-50">
      {isAuthenticated() ? <InboxHeaderUser /> : <InboxHeader />}
      <div className="max-w-5xl mx-auto px-4 py-12">
        <div className="space-y-8">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-gray-900">How it works</h1>
            <p className="text-gray-600">
              The agent connects to Gmail, classifies incoming mail into clear folders (Urgent, Finance & Admin, Security & Systems, etc.),
              moves obvious spam out of your inbox, and keeps your inbox tidy automatically.
            </p>
            <p className="text-red-700 font-medium">
              The agent does not store any of your emails or data. All emails are processed locally and removed. The agent does not delete any emails; spam is only moved to your Spam folder.
            </p>
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Get started</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="text-sm text-gray-500">Step 1</div>
                <div className="font-medium text-gray-900 text-lg">Sign in with Google</div>
                <p className="text-base text-gray-600 mt-1">Use the Sign in / Get started button to authenticate.</p>
              </div>
              <div className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="text-sm text-gray-500">Step 2</div>
                <div className="font-medium text-gray-900 text-lg">Grant Gmail access</div>
                <p className="text-base text-gray-600 mt-1">On first use, approve Gmail permissions. If prompted later, go to Dashboard → Gmail Integration → Reconnect Gmail.</p>
              </div>
              <div className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="text-sm text-gray-500">Step 3</div>
                <div className="font-medium text-gray-900 text-lg">Start your trial</div>
                <p className="text-base text-gray-600 mt-1">Complete checkout to enable continuous processing.</p>
              </div>
              <div className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="text-sm text-gray-500">Step 4</div>
                <div className="font-medium text-gray-900 text-lg">Setting up the agent</div>
                <p className="text-base text-gray-600 mt-1">Dashboard → Gmail Integration → check if the email is connected. If not simply press "Reconnect Gmail". Manual sync option is there if required.</p>
              </div>
              <div className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="text-sm text-gray-500">Step 5</div>
                <div className="font-medium text-gray-900 text-lg">Automatic processing</div>
                <p className="text-base text-gray-600 mt-1">The agent runs automatically throughout the day, you wont have to lift a finger.</p>
              </div>
              <div className="bg-white border rounded-lg p-4 shadow-sm">
                <div className="text-sm text-gray-500">Step 6</div>
                  <div className="font-medium text-gray-900 text-lg">Manage access</div>
                <p className="text-base text-gray-600 mt-1">Dashboard → Account Overview to manage billing, cancel subscription, or reconnect Gmail.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Pricing Page Component
function PricingPage() {
  const handleStartFreeTrial = () => {
    // Redirect to Google OAuth for sign-in (same as inbox page)
    const API = process.env.REACT_APP_API_BASE || 'http://localhost:8000';
    window.location.href = `${API}/auth/google`;
  };

  return <Pricing onStartFreeTrial={handleStartFreeTrial} />;
}


export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Inbox />} />
        <Route path="/inbox" element={<Inbox />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/payment" element={<PaymentPage />} />
        <Route path="/consent" element={<Consent />} />
        <Route path="/payment-success" element={<PaymentSuccess />} />
        <Route path="/oauth-callback" element={<OAuthCallback />} />
        <Route path="/dashboard" element={<DashboardRoute><Dashboard /></DashboardRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
} 