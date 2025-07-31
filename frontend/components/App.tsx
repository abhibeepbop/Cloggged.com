import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider, SidebarTrigger } from "./components/ui/sidebar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card"
import { Button } from "./components/ui/button"
import { Badge } from "./components/ui/badge"
import { Progress } from "./components/ui/progress"
import { Separator } from "./components/ui/separator"
import { Switch } from "./components/ui/switch"
import { Label } from "./components/ui/label"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./components/ui/alert-dialog"
import { 
  BarChart3, 
  CreditCard, 
  Mail, 
  Settings, 
  Shield, 
  User, 
  Download, 
  RefreshCw, 
  MessageSquare, 
  CheckCircle, 
  XCircle, 
  Clock,
  TrendingUp,
  Filter,
  Archive
} from "lucide-react"
import { useState } from "react"
import { AccountOverview } from "./components/AccountOverview"
import { BillingManagement } from "./components/BillingManagement"
import { GmailIntegration } from "./components/GmailIntegration"
import { EmailStats } from "./components/EmailStats"
import { SettingsPanel } from "./components/SettingsPanel"
import { QuickActions } from "./components/QuickActions"

export default function App() {
  const [activeSection, setActiveSection] = useState("overview")

  const menuItems = [
    { id: "overview", label: "Account Overview", icon: User },
    { id: "billing", label: "Billing", icon: CreditCard },
    { id: "gmail", label: "Gmail Integration", icon: Mail },
    { id: "stats", label: "Email Stats", icon: BarChart3 },
    { id: "settings", label: "Settings", icon: Settings },
  ]

  const renderContent = () => {
    switch (activeSection) {
      case "overview":
        return <AccountOverview />
      case "billing":
        return <BillingManagement />
      case "gmail":
        return <GmailIntegration />
      case "stats":
        return <EmailStats />
      case "settings":
        return <SettingsPanel />
      default:
        return <AccountOverview />
    }
  }

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <Sidebar>
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
        
        <main className="flex-1 flex flex-col">
          <header className="border-b px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <SidebarTrigger />
              <h1>MailSort AI Dashboard</h1>
            </div>
            <QuickActions />
          </header>
          
          <div className="flex-1 p-6 overflow-auto">
            {renderContent()}
          </div>
        </main>
      </div>
    </SidebarProvider>
  )
}