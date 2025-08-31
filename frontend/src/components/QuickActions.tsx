import { API_BASE } from "../utils/api";
import { Button } from "./ui/button"
import { RefreshCw, Download, MessageSquare, Bell, LogOut } from "lucide-react"
import { Badge } from "./ui/badge"
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover"
import { useNavigate } from "react-router-dom"

export function QuickActions() {
  const navigate = useNavigate()
  
  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' })
    } catch (_) {
      // ignore network errors on logout
    }
    // Clear user data
    localStorage.removeItem('userData')
    localStorage.removeItem('isAuthenticated')
    // Redirect to home page
    window.location.href = '/'
  }

  const notifications = [
    { id: 1, message: "47 new emails processed", time: "2 min ago", unread: true },
    { id: 2, message: "Spam filter blocked 3 emails", time: "15 min ago", unread: true },
    { id: 3, message: "Weekly report is ready", time: "1 hour ago", unread: false }
  ]

  const unreadCount = notifications.filter(n => n.unread).length

  return (
    <div className="flex items-center gap-2">
      {/* How it works */}
      <Button variant="outline" size="sm" onClick={() => navigate('/how-it-works')}>
        How it works
      </Button>

      {/* Contact Support */}
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="sm">
            <MessageSquare className="h-4 w-4 mr-1" />
            Support
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-64">
          <div className="space-y-2 text-sm">
            <div className="font-medium text-gray-900">Need help?</div>
            <p className="text-gray-600">Email us any time.</p>
            <a href="mailto:vabhi9930@gmail.com" className="text-primary underline">vabhi9930@gmail.com</a>
          </div>
        </PopoverContent>
      </Popover>

      {/* Logout */}
      <Button variant="ghost" size="sm" onClick={handleLogout}>
        <LogOut className="h-4 w-4 mr-1" />
        Logout
      </Button>
    </div>
  )
}