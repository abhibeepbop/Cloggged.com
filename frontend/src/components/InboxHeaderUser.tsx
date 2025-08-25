import { API_BASE } from "../utils/api";
import React from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Search, Menu } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { getStoredUser, clearAuth, canAccessDashboard, isAuthenticated } from "../utils/auth";
import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar";

export function InboxHeaderUser() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const authed = isAuthenticated();
  const canDash = canAccessDashboard(user);

  const handleStartFreeTrial = () => {
    navigate('/pricing');
  };

  const handleSignOut = async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' });
    } catch (_) {
      // ignore network errors on logout
    }
    clearAuth();
    // Use hard redirect to avoid race with in-page redirects
    window.location.href = '/';
  };

  return (
    <header className="border-b bg-white px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" className="p-2">
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded bg-primary flex items-center justify-center">
              <span className="text-primary-foreground text-sm font-medium">C</span>
            </div>
            <span 
              className="text-xl font-semibold text-gray-700 cursor-pointer hover:text-gray-900 transition-colors"
              onClick={() => navigate('/')}
            >
              cloggged.com
            </span>
          </div>
        </div>

        <div className="flex-1 max-w-xl mx-6 md:mx-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input 
              placeholder="Search your perfectly organized inbox..."
              className="pl-10 h-9 md:h-10 bg-gray-50 border-gray-200 focus:bg-white rounded-md"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 md:gap-4">
          <Button variant="outline" size="sm">
            Watch demo
          </Button>

          {authed && canDash ? (
            <>
              <div className="flex items-center gap-2 pr-1">
                <Avatar>
                  <AvatarImage src={user?.picture || ""} alt={user?.name || "User"} />
                  <AvatarFallback>{(user?.name?.[0] || "U").toUpperCase()}</AvatarFallback>
                </Avatar>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/dashboard')}
              >
                Go to dashboard
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSignOut}
              >
                Sign out
              </Button>
            </>
          ) : authed ? (
            <>
              <div className="flex items-center gap-2 pr-1">
                <Avatar>
                  <AvatarImage src={user?.picture || ""} alt={user?.name || "User"} />
                  <AvatarFallback>{(user?.name?.[0] || "U").toUpperCase()}</AvatarFallback>
                </Avatar>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSignOut}
              >
                Sign out
              </Button>
              <span className="h-5 w-px bg-gray-200" />
              <Button
                size="sm"
                className="bg-primary hover:bg-primary/90"
                onClick={handleStartFreeTrial}
              >
                Start free trial
              </Button>
            </>
          ) : (
            <>
              <Button
                size="sm"
                className="bg-primary hover:bg-primary/90"
                onClick={() => (window.location.href = `${API_BASE}/auth/google`)}
              >
                Sign in
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleStartFreeTrial}
              >
                Start free trial
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

