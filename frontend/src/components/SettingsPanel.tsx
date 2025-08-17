import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Switch } from "./ui/switch"
import { Label } from "./ui/label"
import { Shield } from "lucide-react"

export function SettingsPanel() {




  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="text-3xl font-bold text-gray-900">Privacy</h2>
        <p className="text-gray-600">
          Download your privacy and data settings
        </p>
      </div>





      {/* Privacy Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Data
          </CardTitle>
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


    </div>
  )
}