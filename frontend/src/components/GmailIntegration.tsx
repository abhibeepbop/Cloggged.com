import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Progress } from "./ui/progress"
import { CheckCircle, RefreshCw, Mail, AlertCircle, Clock } from "lucide-react"

export function GmailIntegration() {
  const integrationData = {
    isConnected: true,
    lastSync: "2 minutes ago",
    emailsProcessed: 2847,
    pendingEmails: 12,
    syncInProgress: false,
    accountEmail: "user@gmail.com"
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
                Auto-sync every 15 minutes
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
              disabled={integrationData.syncInProgress}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${integrationData.syncInProgress ? 'animate-spin' : ''}`} />
              {integrationData.syncInProgress ? 'Syncing...' : 'Sync Now'}
            </Button>
          </div>

          {integrationData.pendingEmails > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Pending Emails</span>
                <span>{integrationData.pendingEmails} emails</span>
              </div>
              <Progress value={(integrationData.pendingEmails / 100) * 100} className="h-2" />
              <p className="text-xs text-muted-foreground">
                These emails are queued for processing
              </p>
            </div>
          )}
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
            <Button className="w-full">
              <Mail className="h-4 w-4 mr-2" />
              Reconnect Gmail
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Sync Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Sync Settings</CardTitle>
          <CardDescription>
            Configure how your emails are synchronized
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Sync Frequency</label>
              <select className="w-full p-2 border rounded-md text-sm">
                <option value="15">Every 15 minutes</option>
                <option value="30">Every 30 minutes</option>
                <option value="60">Every hour</option>
                <option value="manual">Manual only</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Folders to Sync</label>
              <select className="w-full p-2 border rounded-md text-sm">
                <option value="inbox">Inbox only</option>
                <option value="all">All folders</option>
                <option value="custom">Custom selection</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}