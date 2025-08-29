import { API_BASE } from "../utils/api";
import React from "react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Checkbox } from "./ui/checkbox";
import { Star, Archive, Trash2, Clock } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function InboxContent() {
  const navigate = useNavigate();
  const emails = [
    {
      sender: "Your CEO",
      subject: "Q4 Strategy Meeting - Tomorrow 2PM",
      preview: "Hi team, just a reminder about our strategic planning session...",
      time: "2:34 PM",
      important: true,
      unread: true,
      category: "Work"
    },
    {
      sender: "Mom",
      subject: "Family dinner this Sunday?",
      preview: "Hey honey, would you like to come over for dinner this Sunday? I'm making your favorite...",
      time: "1:45 PM",
      important: true,
      unread: true,
      category: "Family"
    },
    {
      sender: "GitHub",
      subject: "Your pull request has been merged",
      preview: "Congratulations! Your pull request #247 has been successfully merged into main...",
      time: "12:30 PM",
      unread: false,
      category: "Work"
    },
    {
      sender: "Chase Bank",
      subject: "Your statement is ready",
      preview: "Your monthly credit card statement is now available for review...",
      time: "11:15 AM",
      unread: false,
      category: "Finance"
    },
    {
      sender: "Google",
      subject: "New sign-in to your account",
      preview: "We detected a new sign-in to your Google account from a new device...",
      time: "10:45 AM",
      unread: true,
      category: "Security"
    },
    {
      sender: "Amazon",
      subject: "Your verification code is: 123456",
      preview: "Use this code to complete your purchase: 123456...",
      time: "10:30 AM",
      unread: true,
      category: "OTPs"
    },
    {
      sender: "Project Manager",
      subject: "URGENT: Client meeting in 30 minutes",
      preview: "The client meeting has been moved up to 3 PM today. Please prepare...",
      time: "9:15 AM",
      unread: true,
      category: "Urgent"
    }
  ];

  const categoryColors: Record<string, string> = {
    Work: "bg-blue-100 text-blue-700",
    Finance: "bg-green-100 text-green-700",
    Security: "bg-red-100 text-red-700",
    OTPs: "bg-purple-100 text-purple-700",
    Family: "bg-pink-100 text-pink-700",
    Urgent: "bg-orange-100 text-orange-700",
    Spam: "bg-gray-100 text-gray-700"
  };

  return (
    <div className="flex-1 bg-white">
      {/* Toolbar */}
      <div className="border-b px-4 py-3 flex items-center justify-between bg-gray-50">
        <div className="flex items-center space-x-4">
          <Checkbox />
          <Button variant="ghost" size="sm">
            <Archive className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Trash2 className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm">
            Mark as read
          </Button>
        </div>
        <div className="text-sm text-gray-600">
          1-5 of 847 emails • All important emails prioritized by AI
        </div>
      </div>

      {/* Hero email showcasing the product */}
      <div className="bg-gradient-to-r from-primary/20 to-primary/10 border-b border-primary/20 px-10 py-12">
        <div className="max-w-6xl">
          <div className="flex items-start space-x-6">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-5">
                  <span className="font-semibold text-2xl text-gray-900">cloggged.com</span>
                </div>
              </div>
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Your inbox is now perfectly organized!
              </h2>
              <p className="text-xl text-gray-700 mb-8 leading-relaxed">
                Welcome to your new, stress-free email experience. Our AI has automatically sorted your emails, 
                filtered out spam, and prioritized what matters most. Notice how clean and organized everything looks?
              </p>
              <div className="flex justify-between items-center">
                <div className="flex space-x-5">
                  <Button 
                    className="bg-primary hover:bg-primary/90 text-lg px-7 py-4"
                    onClick={() => window.location.href = `${API_BASE}/auth/google`}
                  >
                    Get started
                  </Button>
                  <Button variant="outline" className="text-lg px-7 py-4">
                    How it works
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Email list */}
      <div className="divide-y">
        {emails.map((email, index) => (
          <div
            key={index}
            className={`px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors ${
              email.unread ? 'bg-white' : 'bg-gray-50/50'
            }`}
          >
            <div className="flex items-center space-x-4">
              <Checkbox />
              <Button variant="ghost" size="sm" className="p-1">
                <Star className={`h-4 w-4 ${email.important ? 'text-yellow-500 fill-current' : 'text-gray-400'}`} />
              </Button>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3 min-w-0 flex-1">
                    <span className={`font-medium text-sm ${email.unread ? 'text-gray-900' : 'text-gray-600'}`}>
                      {email.sender}
                    </span>
                    <Badge 
                      variant="secondary" 
                      className={`text-xs ${categoryColors[email.category] || ''}`}
                    >
                      {email.category}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">{email.time}</span>
                  </div>
                </div>
                
                <div className="mt-1">
                  <span className={`text-sm ${email.unread ? 'font-medium text-gray-900' : 'text-gray-600'}`}>
                    {email.subject}
                  </span>
                  <span className="text-sm text-gray-500 ml-2">- {email.preview}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom CTA */}
      <div className="border-t bg-gradient-to-r from-gray-50 to-primary/5 px-6 py-8">
        <div className="text-center max-w-2xl mx-auto">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Ready to unclog your inbox?
          </h3>
          <p className="text-gray-600 mb-4">
            Join thousands of users who've reclaimed their time with AI-powered email management.
          </p>
          <div className="flex justify-center space-x-3">
            <Button 
              className="bg-primary hover:bg-primary/90"
              onClick={() => window.location.href = `${API_BASE}/auth/google`}
            >
              Get started
            </Button>
            <Button variant="outline">
              How it works
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
} 