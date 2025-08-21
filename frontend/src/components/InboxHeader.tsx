import { API_BASE } from "../utils/api";
import React from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Search, Menu } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { isAuthenticated, getStoredUser, clearAuth, canAccessDashboard } from "../utils/auth";
import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar";

export function InboxHeader() {
  const navigate = useNavigate();
  const authed = isAuthenticated();
  const user = getStoredUser();
  const canDash = canAccessDashboard(user);

  const handleStartFreeTrial = () => {
    // Use Pricing page logic to decide OAuth vs Payment based on authflow
    navigate('/pricing');
  };
  
  return (
    <header className="border-b bg-white px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" className="p-2">
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded bg-primary flex items-center justify-center">
              <span className="text-primary-foreground text-sm font-medium">C</span>
            </div>
            <span 
              className="text-xl text-gray-700 cursor-pointer hover:text-gray-900 transition-colors"
              onClick={() => navigate('/')}
            >
              Clogged.ai
            </span>
          </div>
        </div>

        <div className="flex-1 max-w-2xl mx-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input 
              placeholder="Search your perfectly organized inbox..."
              className="pl-10 bg-gray-50 border-gray-200 focus:bg-white"
            />
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            Watch demo
          </Button>
          {!authed && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => (window.location.href = `${API_BASE}/auth/google`)}
              >
                Sign in
              </Button>
              <Button
                size="sm"
                className="bg-primary hover:bg-primary/90"
                onClick={() => (window.location.href = `${API_BASE}/auth/google`)}
              >
                Get started
              </Button>
            </>
          )}

          {authed && canDash && (
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
                onClick={() => {
                  clearAuth();
                  navigate('/');
                }}
              >
                Sign out
              </Button>
            </>
          )}

          {authed && !canDash && (
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
                onClick={() => {
                  clearAuth();
                  navigate('/');
                }}
              >
                Sign out
              </Button>
              <span className="text-gray-300">|</span>
              <Button
                size="sm"
                className="bg-primary hover:bg-primary/90"
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