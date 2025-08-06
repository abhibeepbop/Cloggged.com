import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Badge } from "./ui/badge"
import { Progress } from "./ui/progress"
import { Button } from "./ui/button"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./ui/alert-dialog"
import { CheckCircle, Clock, CreditCard, AlertTriangle } from "lucide-react"
import { useState, useEffect } from "react"

interface BillingData {
  trial_start?: number
  trial_end?: number
  payment_date?: number
  next_billing_date?: number
  subscription_status?: string
  subscribed?: boolean
  payment_completed?: boolean
}

export function AccountOverview() {
  const [billingData, setBillingData] = useState<BillingData | null>(null)
  const [loading, setLoading] = useState(true)
  const [cancelling, setCancelling] = useState(false)

  useEffect(() => {
    const fetchBillingData = async () => {
      try {
        // Get user ID from localStorage or context
        const userData = JSON.parse(localStorage.getItem('userData') || '{}')
        const userId = userData.uid || 'user_vabhi9920' // fallback for testing
        
        const response = await fetch(`http://localhost:8000/user/${userId}/billing-data`)
        const result = await response.json()
        
        console.log('Billing data response:', result) // Debug log
        
        if (result.success) {
          setBillingData(result.billing_data)
          console.log('Billing data set:', result.billing_data) // Debug log
        } else {
          console.error('Failed to fetch billing data:', result.error)
        }
      } catch (error) {
        console.error('Error fetching billing data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchBillingData()
  }, [])

  const formatDate = (timestamp: number | undefined) => {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp * 1000) // Convert from Unix timestamp
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  }

  const calculateDaysLeft = (endTimestamp: number | undefined) => {
    if (!endTimestamp) return null
    const now = new Date().getTime() / 1000 // Current time in seconds
    const daysLeft = Math.ceil((endTimestamp - now) / (24 * 60 * 60))
    return daysLeft > 0 ? daysLeft : 0
  }

  // Calculate next billing date if not available
  const getNextBillingDate = () => {
    if (billingData?.next_billing_date) {
      return formatDate(billingData.next_billing_date)
    }
    
    // Fallback: calculate from trial end or current date
    if (billingData?.trial_end) {
      // If trial ends, next billing is trial end date
      return formatDate(billingData.trial_end)
    }
    
    // Default: 7 days from now
    const defaultNextBilling = Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60)
    return formatDate(defaultNextBilling)
  }

  const subscriptionData = {
    status: billingData?.subscription_status === 'active' ? 'Trial' : 'Active',
    plan: "£5.99/month",
    nextBilling: getNextBillingDate(),
    trialDaysLeft: calculateDaysLeft(billingData?.trial_end),
    isActive: billingData?.subscribed || false
  }

  const handleCancelSubscription = async () => {
    setCancelling(true)
    try {
      const userData = JSON.parse(localStorage.getItem('userData') || '{}')
      const userId = userData.uid || 'Ekpd3Bvr5Ght5Cc00T7EezlH3Hf2'
      
      console.log('Cancelling subscription for user:', userId)
      
      const response = await fetch(`http://localhost:8000/cancel-subscription/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      const result = await response.json()
      console.log('Cancel subscription result:', result)
      
      if (result.success) {
        // Refresh billing data
        const billingResponse = await fetch(`http://localhost:8000/user/${userId}/billing-data`)
        const billingResult = await billingResponse.json()
        
        if (billingResult.success) {
          setBillingData(billingResult.billing_data)
        }
        
        alert('Subscription cancelled successfully. You will not be charged again.')
      } else {
        alert('Failed to cancel subscription: ' + result.error)
      }
    } catch (error) {
      console.error('Error cancelling subscription:', error)
      alert('Error cancelling subscription. Please try again.')
    } finally {
      setCancelling(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="text-3xl font-bold text-gray-900">Account Overview</h2>
        <p className="text-gray-600">
          Manage your subscription and account details
        </p>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <p className="text-gray-600">Loading billing information...</p>
        </div>
      ) : (
        <>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
          {/* Subscription Status */}
          <Card className="shadow-sm border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg font-semibold">Subscription Status</CardTitle>
              {subscriptionData.isActive ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <Clock className="h-4 w-4 text-orange-600" />
              )}
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Badge 
                  variant={subscriptionData.status === "Trial" ? "secondary" : "default"}
                  className={subscriptionData.status === "Trial" ? "bg-orange-100 text-orange-800" : "bg-green-100 text-green-800"}
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
          <Card className="shadow-sm border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg font-semibold">Current Plan</CardTitle>
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
          <Card className="shadow-sm border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-lg font-semibold">Next Billing</CardTitle>
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
        <Card className="shadow-sm border-gray-200">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Monthly Usage</CardTitle>
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

        {/* Cancel Subscription */}
        <Card className="shadow-sm border-red-200">
          <CardHeader>
            <CardTitle className="text-xl font-semibold text-red-600">Cancel Subscription</CardTitle>
            <CardDescription>
              Cancel your subscription and stop future billing
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="space-y-2">
                  <h4 className="font-medium text-red-800">Important Information</h4>
                  <ul className="text-sm text-red-700 space-y-1">
                    <li>• You'll continue to have access until the end of your current billing period</li>
                    <li>• No refunds will be issued for the current period</li>
                    <li>• You can reactivate your subscription at any time</li>
                    <li>• Your email processing will stop after the current period ends</li>
                  </ul>
                </div>
              </div>
            </div>
            
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button 
                  variant="destructive" 
                  className="w-full"
                  disabled={cancelling}
                >
                  {cancelling ? 'Cancelling...' : 'Cancel Subscription'}
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-destructive" />
                    Cancel Subscription
                  </AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to cancel your subscription? You'll continue to have access until {subscriptionData.nextBilling}, but your subscription will not renew.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Keep Subscription</AlertDialogCancel>
                  <AlertDialogAction 
                    onClick={handleCancelSubscription}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    Yes, Cancel Subscription
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </CardContent>
        </Card>
        </>
      )}
    </div>
  )
}