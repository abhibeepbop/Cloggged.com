import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Badge } from "./ui/badge"
import { Progress } from "./ui/progress"
import { CheckCircle, Clock, CreditCard } from "lucide-react"

export function AccountOverview() {
  const subscriptionData = {
    status: "Active", // Trial, Active, Cancelled
    plan: "£5.99/month",
    nextBilling: "February 28, 2025",
    trialDaysLeft: null,
    isActive: true
  }

  return (
    <div className="space-y-6">
      <div>
        <h2>Account Overview</h2>
        <p className="text-muted-foreground">
          Manage your subscription and account details
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Subscription Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Subscription Status</CardTitle>
            {subscriptionData.isActive ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <Clock className="h-4 w-4 text-orange-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Badge 
                variant={subscriptionData.isActive ? "default" : "secondary"}
                className={subscriptionData.isActive ? "bg-green-100 text-green-800" : ""}
              >
                {subscriptionData.status}
              </Badge>
              {subscriptionData.trialDaysLeft && (
                <p className="text-sm text-muted-foreground">
                  {subscriptionData.trialDaysLeft} days left in trial
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Current Plan */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Current Plan</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">{subscriptionData.plan}</div>
              <p className="text-sm text-muted-foreground">
                Premium AI Email Sorting
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Next Billing */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Next Billing</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-sm font-medium">{subscriptionData.nextBilling}</div>
              <p className="text-sm text-muted-foreground">
                Auto-renewal enabled
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Account Usage Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Usage</CardTitle>
          <CardDescription>
            Your email processing usage for this billing period
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Emails Processed</span>
              <span>2,847 / 10,000</span>
            </div>
            <Progress value={28.47} className="h-2" />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>AI Categorizations</span>
              <span>2,654 / 10,000</span>
            </div>
            <Progress value={26.54} className="h-2" />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Spam Filtered</span>
              <span>193 emails blocked</span>
            </div>
            <div className="text-sm text-muted-foreground">
              6.8% of total emails were spam
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}