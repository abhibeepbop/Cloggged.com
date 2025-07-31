import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Switch } from "./ui/switch"
import { Label } from "./ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./ui/alert-dialog"
import { Separator } from "./ui/separator"
import { Bell, Mail, Shield, Trash2, AlertTriangle } from "lucide-react"
import { useState } from "react"

export function SettingsPanel() {
  const [notifications, setNotifications] = useState({
    emailProcessing: true,
    spamDetection: true,
    weeklyReports: false,
    accountChanges: true
  })

  const [emailSettings, setEmailSettings] = useState({
    autoCategorie: true,
    confidenceThreshold: "medium",
    spamSensitivity: "high"
  })

  return (
    <div className="space-y-6">
      <div>
        <h2>Settings</h2>
        <p className="text-muted-foreground">
          Manage your email preferences, notifications, and account settings
        </p>
      </div>

      {/* Email Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Preferences
          </CardTitle>
          <CardDescription>
            Configure how your emails are processed and categorized
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto-categorize emails</Label>
              <div className="text-sm text-muted-foreground">
                Automatically sort incoming emails into categories
              </div>
            </div>
            <Switch 
              checked={emailSettings.autoCategorie}
              onCheckedChange={(checked) => 
                setEmailSettings(prev => ({ ...prev, autoCategorie: checked }))
              }
            />
          </div>

          <Separator />

          <div className="space-y-2">
            <Label>AI Confidence Threshold</Label>
            <Select 
              value={emailSettings.confidenceThreshold}
              onValueChange={(value) => 
                setEmailSettings(prev => ({ ...prev, confidenceThreshold: value }))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low (70%) - More categorizations</SelectItem>
                <SelectItem value="medium">Medium (85%) - Balanced</SelectItem>
                <SelectItem value="high">High (95%) - Only high confidence</SelectItem>
              </SelectContent>
            </Select>
            <div className="text-sm text-muted-foreground">
              Lower thresholds categorize more emails but may be less accurate
            </div>
          </div>

          <div className="space-y-2">
            <Label>Spam Detection Sensitivity</Label>
            <Select 
              value={emailSettings.spamSensitivity}
              onValueChange={(value) => 
                setEmailSettings(prev => ({ ...prev, spamSensitivity: value }))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low - Fewer false positives</SelectItem>
                <SelectItem value="medium">Medium - Balanced detection</SelectItem>
                <SelectItem value="high">High - Maximum protection</SelectItem>
              </SelectContent>
            </Select>
            <div className="text-sm text-muted-foreground">
              Higher sensitivity may occasionally mark legitimate emails as spam
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notification Settings
          </CardTitle>
          <CardDescription>
            Choose what notifications you want to receive
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Email processing updates</Label>
              <div className="text-sm text-muted-foreground">
                Get notified when your emails are processed
              </div>
            </div>
            <Switch 
              checked={notifications.emailProcessing}
              onCheckedChange={(checked) => 
                setNotifications(prev => ({ ...prev, emailProcessing: checked }))
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Spam detection alerts</Label>
              <div className="text-sm text-muted-foreground">
                Get alerted when spam is detected and filtered
              </div>
            </div>
            <Switch 
              checked={notifications.spamDetection}
              onCheckedChange={(checked) => 
                setNotifications(prev => ({ ...prev, spamDetection: checked }))
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Weekly reports</Label>
              <div className="text-sm text-muted-foreground">
                Receive weekly summaries of your email activity
              </div>
            </div>
            <Switch 
              checked={notifications.weeklyReports}
              onCheckedChange={(checked) => 
                setNotifications(prev => ({ ...prev, weeklyReports: checked }))
              }
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Account changes</Label>
              <div className="text-sm text-muted-foreground">
                Get notified about important account changes
              </div>
            </div>
            <Switch 
              checked={notifications.accountChanges}
              onCheckedChange={(checked) => 
                setNotifications(prev => ({ ...prev, accountChanges: checked }))
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Privacy Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Privacy Settings
          </CardTitle>
          <CardDescription>
            Control your data privacy and security preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium">Data Processing</h4>
              <p className="text-sm text-muted-foreground mt-1">
                We process your email metadata (sender, subject, date) to categorize emails. 
                Email content is analyzed locally and not stored on our servers.
              </p>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium">Data Retention</h4>
              <p className="text-sm text-muted-foreground mt-1">
                Email processing statistics are retained for 12 months. 
                You can request data deletion at any time.
              </p>
            </div>

            <Button variant="outline" className="w-full">
              Download My Data
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <Trash2 className="h-5 w-5" />
            Danger Zone
          </CardTitle>
          <CardDescription>
            Irreversible and destructive actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" className="w-full">
                Delete Account
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                  Permanently Delete Account
                </AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete your account, 
                  cancel any active subscriptions, and remove all your data from our servers.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                  Yes, Delete My Account
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>
    </div>
  )
}