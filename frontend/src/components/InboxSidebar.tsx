import React from "react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Inbox, Star, Send, FileText, Trash2, Briefcase, Wallet, Shield, KeyRound, Users, AlertTriangle } from "lucide-react";
import { Separator } from "./ui/separator";
import { useNavigate } from "react-router-dom";

export function InboxSidebar() {
  const navigate = useNavigate();
  const sidebarItems = [
    { icon: Inbox, label: "Inbox", count: 847, active: true },
    { icon: Star, label: "Starred", count: 23 },
    { icon: Send, label: "Sent" },
    { icon: FileText, label: "Drafts", count: 12 },
    { icon: Trash2, label: "Spam", count: 0, highlight: true },
    { icon: Briefcase, label: "Work", count: 156 },
    { icon: Wallet, label: "Finance", count: 42 },
    { icon: Shield, label: "Security", count: 8 },
    { icon: KeyRound, label: "OTPs", count: 15 },
    { icon: Users, label: "Family", count: 23 },
    { icon: AlertTriangle, label: "Urgent", count: 5 },
  ];

  return (
    <aside className="w-64 bg-white border-r min-h-screen p-4">


      <nav className="space-y-1">
        {sidebarItems.map((item, index) => (
          <React.Fragment key={index}>
            <div
              className={`flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                item.active 
                  ? 'bg-primary/10 text-primary border border-primary/20' 
                  : 'hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center space-x-3">
                <item.icon className={`h-5 w-5 ${item.active ? 'text-primary' : 'text-gray-600'}`} />
                <span className={`text-sm ${item.active ? 'font-medium text-primary' : 'text-gray-700'}`}>
                  {item.label}
                </span>
              </div>
              {item.count !== undefined && (
                <Badge 
                  variant={item.highlight ? "destructive" : "secondary"} 
                  className={`text-xs ${
                    item.highlight 
                      ? 'bg-green-100 text-green-700 hover:bg-green-100' 
                      : item.active 
                        ? 'bg-primary/20 text-primary' 
                        : ''
                  }`}
                >
                  {item.count}
                </Badge>
              )}
            </div>
            {item.label === 'Spam' && (
              <Separator className="my-2" />
            )}
          </React.Fragment>
        ))}
      </nav>

      <div className="mt-8 p-4 bg-gradient-to-br from-primary/5 to-accent/5 rounded-lg border border-primary/10">
        <div className="text-sm font-medium text-gray-800 mb-2">
          Zero spam emails!
        </div>
        <div className="text-xs text-gray-600 mb-3">
          Mail Agent automatically filtered out 2,847 unwanted emails this week.
        </div>
        <Button variant="outline" size="sm" className="w-full text-primary border-primary/20">
          See how it works
        </Button>
      </div>
    </aside>
  );
} 