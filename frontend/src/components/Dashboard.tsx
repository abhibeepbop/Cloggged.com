import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider, SidebarTrigger } from "./ui/sidebar"
import React, { useState, useEffect, lazy, Suspense } from "react"
import { useNavigate } from "react-router-dom"
const AccountOverview = lazy(() => import("./AccountOverview").then(m => ({ default: m.AccountOverview })))
const GmailIntegration = lazy(() => import("./GmailIntegration").then(m => ({ default: m.GmailIntegration })))
const EmailStats = lazy(() => import("./EmailStats").then(m => ({ default: m.EmailStats })))
// Note: BillingManagement and SettingsPanel are not actively used; keep eager import if needed elsewhere
import { QuickActions } from "./QuickActions"
import { 
  BarChart3, 
  CreditCard, 
  Mail, 
  Settings, 
  User
} from "lucide-react"

export function Dashboard() {
  const [activeSection, setActiveSection] = useState("overview")
  const [user, setUser] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    // Check for token in URL (from OAuth callback)
    const urlParams = new URLSearchParams(window.location.search)
    const token = urlParams.get('token')
    
    if (token) {
      // User came from OAuth with token, verify with Firebase
      verifyFirebaseToken(token)
    } else {
      // Check for existing authentication
      const isAuthenticated = localStorage.getItem('isAuthenticated')
      const userData = localStorage.getItem('userData')
      
      if (!isAuthenticated || !userData) {
        navigate('/pricing')
        return
      }
      
      try {
        const user = JSON.parse(userData)
        setUser(user)
        // Clean up URL if no token
        window.history.replaceState({}, document.title, '/dashboard')
      } catch (error) {
        console.error('Error parsing user data:', error)
        navigate('/pricing')
      }
    }
  }, [navigate])

  const verifyFirebaseToken = async (token: string) => {
    try {
      // Verify token with Firebase
      const response = await fetch('http://localhost:8000/verify-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token })
      })
      
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
        localStorage.setItem('isAuthenticated', 'true')
        localStorage.setItem('userData', JSON.stringify(userData))
        // Clean up URL
        window.history.replaceState({}, document.title, '/dashboard')
      } else {
        console.error('Token verification failed')
        navigate('/pricing')
      }
    } catch (error) {
      console.error('Error verifying token:', error)
      navigate('/pricing')
    }
  }

  // Show loading while checking authentication
  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-900">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const menuItems = [
    { id: "overview", label: "Account Overview", icon: User },
    { id: "gmail", label: "Gmail Integration", icon: Mail },
    { id: "stats", label: "Email Stats", icon: BarChart3 },
  ]

  const renderContent = () => {
    switch (activeSection) {
      case "overview":
        return <AccountOverview />
      case "gmail":
        return <GmailIntegration />
      case "stats":
        return <EmailStats />
      default:
        return <AccountOverview />
    }
  }

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <Sidebar className="mt-16">
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>MailSort AI Dashboard</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {menuItems.map((item) => (
                    <SidebarMenuItem key={item.id}>
                      <SidebarMenuButton 
                        onClick={() => setActiveSection(item.id)}
                        isActive={activeSection === item.id}
                      >
                        <item.icon className="w-4 h-4" />
                        <span>{item.label}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>
        
        <main className="flex-1 flex flex-col bg-gray-50">
          <header className="border-b bg-white px-6 py-4 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-4">
              <SidebarTrigger />
              <h1 className="text-xl font-semibold text-gray-900">MailSort AI Dashboard</h1>
            </div>
            <QuickActions />
          </header>
          
          <div className="flex-1 p-6 overflow-auto">
            <div className="max-w-7xl mx-auto">
              <Suspense fallback={<div className="p-4 text-gray-600">Loading…</div>}>
                {renderContent()}
              </Suspense>
            </div>
          </div>
        </main>
      </div>
    </SidebarProvider>
  )
} 