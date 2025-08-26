import { API_BASE } from "../utils/api"
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
        // Resolve user id from localStorage, then fallback to /session/me
        let userId = ''
        try {
          const userData = JSON.parse(localStorage.getItem('userData') || '{}')
          userId = userData.user_id || userData.uid || ''
        } catch {}
        if (!userId) {
          try {
            const me = await fetch(`${API_BASE}/session/me`, { credentials: 'include' })
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
        
        const response = await fetch(`${API_BASE}/user/${userId}/billing-data`)
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

  const nowSec = Math.floor(Date.now() / 1000)
  const isCancelling = (billingData?.subscription_status === 'cancelling') || (billingData as any)?.cancel_at_period_end === true
  const inTrial = typeof billingData?.trial_end === 'number' && (billingData!.trial_end > nowSec) && (billingData?.payment_completed !== true)
  const status = isCancelling ? 'Cancelling' : inTrial ? 'Trial' : (billingData?.subscribed ? 'Active' : 'Inactive')
  const cancelsAt = (billingData as any)?.cancels_at || billingData?.trial_end || billingData?.next_billing_date
  const subscriptionData = {
    status,
    plan: "Standard Plan • £5.99/month",
    nextBilling: getNextBillingDate(),
    trialDaysLeft: inTrial ? calculateDaysLeft(billingData?.trial_end) : null,
    isActive: (billingData?.subscribed || inTrial) && !isCancelling,
    isCancelling,
    cancelsAtFormatted: cancelsAt ? new Date(cancelsAt * 1000).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : null
  }

  const handleCancelSubscription = async () => {
    setCancelling(true)
    try {
      // Resolve user id from session first, fallback to localStorage
      let userId = ''
      try {
        const me = await fetch(`${API_BASE}/session/me`, { credentials: 'include' })
        if (me.ok) {
          const data = await me.json()
          userId = data?.user_id || ''
        }
      } catch {}
      if (!userId) {
        try {
          const ls = JSON.parse(localStorage.getItem('userData') || '{}')
          userId = ls.user_id || ls.uid || ''
        } catch {}
      }
      if (!userId) {
        alert('Unable to determine user. Please sign in again.')
        setCancelling(false)
        return
      }

      const response = await fetch(`${API_BASE}/cancel-subscription`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })

      const result = await response.json()
      if (result?.success) {
        // Refresh billing data to reflect "Cancelling" and date
        const billingResponse = await fetch(`${API_BASE}/user/${userId}/billing-data`, { credentials: 'include' })
        const billingResult = await billingResponse.json()
        if (billingResult?.success) {
          setBillingData(billingResult.billing_data)
        }
        alert('Subscription cancelled successfully. You will not be charged again.')
      } else {
        alert('Failed to cancel subscription: ' + (result?.error || 'Unknown error'))
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
                {subscriptionData.status === 'Cancelling' ? (
                  <>
                    <Badge className="bg-orange-100 text-orange-800">Cancelling</Badge>
                    {subscriptionData.cancelsAtFormatted && (
                      <p className="text-sm text-muted-foreground">Ends on {subscriptionData.cancelsAtFormatted}</p>
                    )}
                  </>
                ) : (
                  <>
                    <Badge 
                      variant={subscriptionData.status === "Trial" ? "secondary" : (subscriptionData.status === 'Active' ? 'default' : 'outline')}
                      className={
                        subscriptionData.status === "Trial" ? "bg-orange-100 text-orange-800" : (
                          subscriptionData.status === 'Active' ? "bg-green-100 text-green-800" : ""
                        )
                      }
                    >
                      {subscriptionData.status}
                    </Badge>
                    {subscriptionData.trialDaysLeft && (
                      <p className="text-sm text-muted-foreground">
                        {subscriptionData.trialDaysLeft} days left in trial
                      </p>
                    )}
                  </>
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
                  Standard AI Email Sorting
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

        {/* Current Subscription (copied from BillingManagement) */}
        <Card className="shadow-sm border-gray-200">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Current Subscription</CardTitle>
            <CardDescription>
              Your active subscription details and billing cycle
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold">Standard Plan</h3>
                <p className="text-sm text-muted-foreground">£5.99/month</p>
              </div>
              <Badge variant="secondary" className={subscriptionData.isCancelling ? "bg-orange-100 text-orange-800" : (subscriptionData.status === 'Active' ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800") }>
                {subscriptionData.isCancelling ? 'Cancelling' : subscriptionData.status}
              </Badge>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Free Trial Ends</span>
                <span className="text-sm text-muted-foreground">{billingData?.trial_end ? formatDate(billingData.trial_end) : 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Next Billing</span>
                <span className="text-sm text-muted-foreground">{getNextBillingDate()}</span>
              </div>
            </div>

            {/* Move Cancel Subscription action here */}
            {!subscriptionData.isCancelling && (subscriptionData.status === 'Active' || subscriptionData.status === 'Trial') && (
              <div className="flex space-x-2 pt-2">
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button 
                      variant="destructive" 
                      size="sm"
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
                        Are you sure you want to cancel your subscription? You'll continue to have access until {getNextBillingDate()}, but your subscription will not renew.
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
              </div>
            )}
          </CardContent>
        </Card>

        {/* Billing History (summary) */}
        <Card className="shadow-sm border-gray-200">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Billing History</CardTitle>
            <CardDescription>
              Your recent invoices and payment history
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">View full details in the Billing tab.</div>
          </CardContent>
        </Card>

        

        {/* Cancel Subscription moved into Current Subscription card above */}
        </>
      )}
    </div>
  )
}