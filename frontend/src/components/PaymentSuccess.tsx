import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { setAuth } from "../utils/auth";

export function PaymentSuccess() {
  const navigate = useNavigate();
  const { search } = useLocation();

  useEffect(() => {
    const sessionId = new URLSearchParams(search).get("session_id");
    if (!sessionId) {
      navigate("/pricing");
      return;
    }
    (async () => {
      try {
        const r = await fetch("http://localhost:8000/stripe/confirm-session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ session_id: sessionId }),
        });
        if (r.ok) {
          // Refresh auth state from server so dashboard guard passes
          try {
            const me = await fetch("http://localhost:8000/session/me", { credentials: "include" });
            if (me.ok) {
              const data = await me.json();
              setAuth({ ...(data?.user_data || {}), user_id: data?.user_id });
            }
          } catch {}
          navigate("/dashboard");
        } else {
          navigate("/pricing");
        }
      } catch {
        navigate("/pricing");
      }
    })();
  }, [search, navigate]);

  return null;
}


