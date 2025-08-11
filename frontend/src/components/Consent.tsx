import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getStoredUser, setAuth } from "../utils/auth";
import { InboxHeaderUser } from "./InboxHeaderUser";

export function Consent() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const [accepted, setAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    if (!user) {
      navigate("/");
      return;
    }
    const userId = (user as any).user_id || (user as any).uid;
    if (!userId) {
      navigate("/");
      return;
    }
    try {
      setLoading(true);
      const resp = await fetch(`http://localhost:8000/user/${userId}/consent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ consent: accepted }),
      });
      const data = await resp.json();
      if (!resp.ok || !data.success) {
        throw new Error(data.error || "Failed to set consent");
      }
      // Persist updated consent locally as well
      const updated = { ...user, consent: accepted } as any;
      setAuth(updated);
      window.location.href = data.redirect_url || "/";
    } catch (e: any) {
      setError(e.message || "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <InboxHeaderUser />
      <main className="max-w-2xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-semibold text-gray-900 mb-4">Consent</h1>
        <p className="text-gray-600 mb-6">
          Please confirm that you consent to the processing necessary for MailSort AI to organize your inbox.
          You can withdraw consent at any time in Settings.
        </p>
        <label className="flex items-start gap-3 bg-white border rounded-lg p-4">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
          />
          <span className="text-gray-800">
            I agree to the Terms of Service and acknowledge the Privacy Policy.
          </span>
        </label>
        {error && <p className="text-red-600 mt-3">{error}</p>}
        <div className="mt-6 flex gap-3">
          <button
            disabled={!accepted || loading}
            onClick={handleSubmit}
            className="bg-black text-white rounded-md px-4 py-2 disabled:opacity-50"
          >
            {loading ? "Saving..." : "Continue"}
          </button>
          <button
            onClick={() => navigate("/")}
            className="border border-gray-300 rounded-md px-4 py-2"
          >
            Cancel
          </button>
        </div>
      </main>
    </div>
  );
}


