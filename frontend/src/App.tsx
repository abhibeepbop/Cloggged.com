import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { InboxHeader } from "./components/InboxHeader";
import { InboxHeaderUser } from "./components/InboxHeaderUser";
import { InboxSidebar } from "./components/InboxSidebar";
import { InboxContent } from "./components/InboxContent";
import { Pricing } from "./components/Pricing";
import { OAuthCallback } from "./components/OAuthCallback";
import { PaymentPage } from "./components/PaymentPage";
import { Dashboard } from "./components/Dashboard";
import { Consent } from "./components/Consent";
import { getStoredUser, canAccessDashboard } from "./utils/auth";

// Inbox Component
import { isAuthenticated } from "./utils/auth";

function Inbox() {
  const authed = isAuthenticated();
  return (
    <div className="min-h-screen bg-gray-50">
      {authed ? <InboxHeaderUser /> : <InboxHeader />}
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
    window.location.href = 'http://localhost:8000/auth/google';
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
        <Route path="/oauth-callback" element={<OAuthCallback />} />
        <Route
          path="/dashboard"
          element={canAccessDashboard(getStoredUser()) ? <Dashboard /> : <Navigate to="/" replace />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
} 