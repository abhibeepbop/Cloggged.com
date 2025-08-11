import { Button } from "./ui/button"
import { RefreshCw, Download, MessageSquare, Bell, LogOut } from "lucide-react"
import { Badge } from "./ui/badge"
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover"
import { useNavigate } from "react-router-dom"

export function QuickActions() {
  const navigate = useNavigate()
  
  const handleLogout = async () => {
    try {
      await fetch('http://localhost:8000/auth/logout', { method: 'POST', credentials: 'include' })
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
      {/* Notifications */}
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="sm" className="relative">
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <Badge className="absolute -top-1 -right-1 h-5 w-5 text-xs p-0 flex items-center justify-center">
                {unreadCount}
              </Badge>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-80" align="end">
          <div className="space-y-3">
            <h4 className="font-medium">Notifications</h4>
            <div className="space-y-2">
              {notifications.map((notification) => (
                <div 
                  key={notification.id}
                  className={`p-3 rounded-lg border text-sm ${
                    notification.unread ? 'bg-blue-50 border-blue-200' : 'bg-muted'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className={notification.unread ? 'font-medium' : ''}>
                        {notification.message}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {notification.time}
                      </p>
                    </div>
                    {notification.unread && (
                      <div className="w-2 h-2 bg-blue-600 rounded-full mt-1 ml-2 flex-shrink-0" />
                    )}
                  </div>
                </div>
              ))}
            </div>
            <Button variant="outline" size="sm" className="w-full">
              View All Notifications
            </Button>
          </div>
        </PopoverContent>
      </Popover>

      {/* Manual Sync */}
      <Button variant="ghost" size="sm">
        <RefreshCw className="h-4 w-4 mr-1" />
        Sync
      </Button>

      {/* Export Data */}
      <Button variant="ghost" size="sm">
        <Download className="h-4 w-4 mr-1" />
        Export
      </Button>

      {/* Contact Support */}
      <Button variant="ghost" size="sm">
        <MessageSquare className="h-4 w-4 mr-1" />
        Support
      </Button>

      {/* Logout */}
      <Button variant="ghost" size="sm" onClick={handleLogout}>
        <LogOut className="h-4 w-4 mr-1" />
        Logout
      </Button>
    </div>
  )
}