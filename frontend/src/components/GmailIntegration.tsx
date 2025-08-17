import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Progress } from "./ui/progress"
import { Switch } from "./ui/switch"
import { CheckCircle, RefreshCw, Mail, AlertCircle, Clock, Settings } from "lucide-react"
import { useState, useEffect } from "react"

interface UserData {
  email?: string
  gmail_tokens?: any
  last_sync?: number
}

export function GmailIntegration() {
  const [userData, setUserData] = useState<UserData | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncInProgress, setSyncInProgress] = useState(false)
  const [emailStats, setEmailStats] = useState<{total_processed: number} | null>(null)
  const [processingPaused, setProcessingPaused] = useState(false)
  const [pauseLoading, setPauseLoading] = useState(false)

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        // Resolve user ID from localStorage, then fallback to /session/me
        let userId = ''
        try {
          const uds = JSON.parse(localStorage.getItem('userData') || '{}')
          userId = uds.user_id || uds.uid || ''
        } catch {}
        if (!userId) {
          try {
            const me = await fetch('http://localhost:8000/session/me', { credentials: 'include' })
            if (me.ok) {
              const data = await me.json()
              userId = data?.user_id || ''
            }
          } catch {}
        }
        if (!userId) {
          setLoading(false)
          return
        }
        
        console.log('GmailIntegration - Using User ID:', userId)
        
        const response = await fetch(`http://localhost:8000/user/${userId}/billing-data`)
        const result = await response.json()
        console.log('GmailIntegration - Billing data response:', result)

        // Always fetch user doc to determine connection status
        const userResponse = await fetch(`http://localhost:8000/debug-user/${userId}`)
        const userResult = await userResponse.json()
        if (userResult.success) {
          setUserData(userResult.user_data)
          console.log('GmailIntegration - User data set:', userResult.user_data)
          const paused = userResult.user_data.email_processing_enabled === false
          setProcessingPaused(paused)
        }

        // Fetch email stats regardless of billing success
        const statsResponse = await fetch(`http://localhost:8000/user/${userId}/email-stats`)
        const statsResult = await statsResponse.json()
        if (statsResult.success) {
          setEmailStats(statsResult.stats)
          console.log('GmailIntegration - Email stats set:', statsResult.stats)
        }
      } catch (error) {
        console.error('GmailIntegration - Error fetching user data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [])



  const handleManualSync = async () => {
    if (syncInProgress) return
    
    setSyncInProgress(true)
    try {
      // Get user ID from localStorage or context
      const userDataFromStorage = JSON.parse(localStorage.getItem('userData') || '{}')
      const userId = userDataFromStorage.uid || 'Ekpd3Bvr5Ght5Cc00T7EezlH3Hf2'
      
      console.log('Triggering manual sync for user:', userId)
      const response = await fetch(`http://localhost:8000/trigger-user-sync/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      const result = await response.json()
      console.log('Manual sync result:', result)
      
      if (result.success) {
        // Refresh user data to get updated last_sync
      const userResponse = await fetch(`http://localhost:8000/debug-user/${userId}`)
        const userResult = await userResponse.json()
        
        if (userResult.success) {
          setUserData(userResult.user_data)
        }
      }
    } catch (error) {
      console.error('Error during manual sync:', error)
    } finally {
      setSyncInProgress(false)
    }
  }

  const handlePauseProcessing = async () => {
    if (pauseLoading) return
    
    setPauseLoading(true)
    try {
      const userDataFromStorage = JSON.parse(localStorage.getItem('userData') || '{}')
      const userId = userDataFromStorage.uid || 'Ekpd3Bvr5Ght5Cc00T7EezlH3Hf2'
      
      // Determine if we're pausing or resuming
      const shouldEnable = processingPaused
      const action = shouldEnable ? 'RESUME' : 'PAUSE'
      
      console.log(`=== ${action} PROCESSING CALLED ===`)
      console.log(`User ID: ${userId}`)
      console.log(`Current paused state: ${processingPaused}`)
      console.log(`Should enable: ${shouldEnable}`)
      
      const response = await fetch(`http://localhost:8000/toggle-email-processing/${userId}?enabled=${shouldEnable}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      console.log(`Response status: ${response.status}`)
      const result = await response.json()
      console.log(`${action} processing result:`, result)
      
      if (result.success) {
        console.log(`${action} successful, updating state`)
        setProcessingPaused(!shouldEnable) // Toggle the paused state
        
        // Refresh user data
        const userResponse = await fetch(`http://localhost:8000/debug-user/${userId}`)
        const userResult = await userResponse.json()
        
          if (userResult.success) {
            setUserData(userResult.user_data)
          console.log('User data refreshed:', userResult.user_data)
        }
      } else {
        console.error(`${action} failed:`, result.error)
      }
    } catch (error) {
      console.error(`Error ${processingPaused ? 'resuming' : 'pausing'} processing:`, error)
    } finally {
      setPauseLoading(false)
    }
  }

  const formatLastSync = (timestamp: number | undefined) => {
    if (!timestamp) return "Never"
    
    const now = Math.floor(Date.now() / 1000)
    const diff = now - timestamp
    
    if (diff < 60) {
      return `${diff} seconds ago`
    } else if (diff < 3600) {
      const minutes = Math.floor(diff / 60)
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
    } else if (diff < 86400) {
      const hours = Math.floor(diff / 3600)
      return `${hours} hour${hours > 1 ? 's' : ''} ago`
    } else {
      const days = Math.floor(diff / 86400)
      return `${days} day${days > 1 ? 's' : ''} ago`
    }
  }



  const integrationData = {
    isConnected: !!(userData as any)?.has_gmail_tokens || !!(userData as any)?.gmail_tokens,
    lastSync: formatLastSync(userData?.last_sync),
    emailsProcessed: emailStats?.total_processed || 0,
    pendingEmails: 12,
    syncInProgress: syncInProgress,
    accountEmail: userData?.email || "Loading..."
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold text-gray-900">Gmail Integration</h2>
          <p className="text-gray-600">
            Manage your Gmail connection and email synchronization
          </p>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-600">Loading user data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="text-3xl font-bold text-gray-900">Gmail Integration</h2>
        <p className="text-gray-600">
          Manage your Gmail connection and email synchronization
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Connection Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Connection Status</CardTitle>
            {integrationData.isConnected ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Badge 
                variant={integrationData.isConnected ? "default" : "destructive"}
                className={integrationData.isConnected ? "bg-green-100 text-green-800" : ""}
              >
                {integrationData.isConnected ? "Connected" : "Disconnected"}
              </Badge>
              {integrationData.isConnected && (
                <p className="text-sm text-muted-foreground">
                  {integrationData.accountEmail}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Last Sync */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Last Sync</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-sm font-medium">{integrationData.lastSync}</div>
              <p className="text-sm text-muted-foreground">
                Auto-sync every 5 minutes
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Processing Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Email Processing</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">{integrationData.emailsProcessed.toLocaleString()}</div>
              <p className="text-sm text-muted-foreground">
                Emails processed this month
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sync Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Synchronization Controls</CardTitle>
          <CardDescription>
            Manage your email synchronization settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="space-y-1">
              <div className="text-sm font-medium">Manual Sync</div>
              <div className="text-sm text-muted-foreground">
                Force sync your latest emails now
              </div>
            </div>
            <Button 
              variant="outline" 
              disabled={syncInProgress}
              onClick={handleManualSync}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${syncInProgress ? 'animate-spin' : ''}`} />
              {syncInProgress ? 'Syncing...' : 'Sync Now'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Email Processing Control */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Email Processing Control
          </CardTitle>
          <CardDescription>
            Temporarily pause email categorization
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="space-y-1">
              <div className="text-sm font-medium">Email Categorization</div>
              <div className="text-sm text-muted-foreground">
                {processingPaused 
                  ? "Email processing is paused" 
                  : "AI is actively categorizing your emails"
                }
              </div>
            </div>
            <Button
              variant={processingPaused ? "outline" : "destructive"}
              onClick={handlePauseProcessing}
              disabled={pauseLoading}
              className="flex items-center gap-2"
            >
              {pauseLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
              ) : (
                <Settings className="h-4 w-4" />
              )}
              {processingPaused ? 'Resume Processing' : 'Pause Processing'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Reconnection */}
      {!integrationData.isConnected && (
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-red-600">Gmail Disconnected</CardTitle>
            <CardDescription>
              Your Gmail account is not connected. Reconnect to continue email processing.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full" onClick={async () => {
              try {
                let userId = ''
                try {
                  const uds = JSON.parse(localStorage.getItem('userData') || '{}')
                  userId = uds.user_id || uds.uid || ''
                } catch {}
                if (!userId) {
                  const me = await fetch('http://localhost:8000/session/me', { credentials: 'include' })
                  if (me.ok) {
                    const data = await me.json()
                    userId = data?.user_id || ''
                  }
                }
                if (userId) {
                  window.location.href = `http://localhost:8000/gmail/connect-simple/${userId}`
                }
              } catch {}
            }}>
              <Mail className="h-4 w-4 mr-2" />
              Reconnect Gmail
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}