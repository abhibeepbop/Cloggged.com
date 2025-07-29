import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { InboxHeader } from "./components/InboxHeader";
import { InboxSidebar } from "./components/InboxSidebar";
import { InboxContent } from "./components/InboxContent";
import { Pricing } from "./components/Pricing";

// Inbox Component
function Inbox() {
  return (
    <div className="min-h-screen bg-gray-50">
      <InboxHeader />
      <div className="flex">
        <InboxSidebar />
        <InboxContent />
      </div>
    </div>
  );
}



export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Inbox />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

// Pricing Page Component
function PricingPage() {
  const handleStartFreeTrial = () => {
    console.log("Starting free trial...");
    // After payment, redirect to Gmail OAuth flow
    window.location.href = "http://localhost:8000/gmail/connect";
  };

  return <Pricing onStartFreeTrial={handleStartFreeTrial} />;
} 