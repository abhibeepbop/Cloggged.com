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
    if (authedNow && canAccessDashboard(getStoredUser())) {
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