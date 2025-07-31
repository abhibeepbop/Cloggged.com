import React from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Search, Menu, Settings, HelpCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function InboxHeader() {
  const navigate = useNavigate();
  
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
            <span className="text-xl text-gray-700">
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

        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="sm" className="p-2">
            <HelpCircle className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="sm" className="p-2">
            <Settings className="h-5 w-5" />
          </Button>
          <Button variant="outline" size="sm">
            Watch demo
          </Button>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => window.location.href = 'http://localhost:8000/auth/google'}
          >
            Sign in
          </Button>
          <Button 
            size="sm" 
            className="bg-primary hover:bg-primary/90"
            onClick={() => window.location.href = 'http://localhost:8000/auth/google'}
          >
            Get started
          </Button>
        </div>
      </div>
    </header>
  );
} 