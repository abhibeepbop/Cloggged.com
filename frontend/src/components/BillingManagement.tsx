import { API_BASE } from "../utils/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./ui/alert-dialog"
import { CreditCard, Download, AlertTriangle } from "lucide-react"
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

export function BillingManagement() {
  const [billingData, setBillingData] = useState<BillingData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchBillingData = async () => {
      try {
        // Get user ID from localStorage or context
        const userData = JSON.parse(localStorage.getItem('userData') || '{}')
        const userId = userData.uid || 'user_vabhi9920' // fallback for testing
        
        const response = await fetch(`${API_BASE}/user/${userId}/billing-data`)
        const result = await response.json()
        
        console.log('BillingManagement - Billing data response:', result) // Debug log
        
        if (result.success) {
          setBillingData(result.billing_data)
          console.log('BillingManagement - Billing data set:', result.billing_data) // Debug log
        } else {
          console.error('BillingManagement - Failed to fetch billing data:', result.error)
        }
      } catch (error) {
        console.error('BillingManagement - Error fetching billing data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchBillingData()
  }, [])

  const formatDate = (timestamp: number | undefined) => {
    console.log('Formatting date for timestamp:', timestamp)
    if (!timestamp) {
      console.log('No timestamp provided')
      return 'N/A'
    }
    
    try {
      // Handle both seconds and milliseconds timestamps
      const date = timestamp > 1000000000000 ? new Date(timestamp) : new Date(timestamp * 1000)
      console.log('Formatted date:', date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      }))
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      })
    } catch (error) {
      console.error('Error formatting date:', error)
      return 'Invalid Date'
    }
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

  const generateBillingHistory = () => {
    console.log('Generating billing history with data:', billingData)
    
    if (!billingData) {
      console.log('No billing data available')
      return []
    }
    
    const billingHistory = []
    
    // Add upcoming billing if we have next_billing_date from Firebase
    if (billingData.next_billing_date) {
      console.log('Adding upcoming billing from Firebase:', billingData.next_billing_date)
      billingHistory.push({
        id: "INV-2025-001",
        date: formatDate(billingData.next_billing_date),
        amount: "£5.99",
        status: "Upcoming",
        description: "Monthly Subscription"
      })
    }
    
    // Add trial start if available
    if (billingData.trial_start) {
      console.log('Adding trial start:', billingData.trial_start)
      billingHistory.push({
        id: "TRIAL-001",
        date: formatDate(billingData.trial_start),
        amount: "£0.00",
        status: "Paid",
        description: "7-Day Free Trial Started"
      })
    }
    
    // Add payment date if available and different from next billing
    if (billingData.payment_date && billingData.payment_date !== billingData.next_billing_date) {
      console.log('Adding payment date:', billingData.payment_date)
      billingHistory.push({
        id: "INV-2024-001",
        date: formatDate(billingData.payment_date),
        amount: "£5.99",
        status: "Paid",
        description: "Initial Payment"
      })
    }
    
    console.log('Final billing history:', billingHistory)
    
    // Sort by date (newest first)
    return billingHistory.sort((a, b) => {
      const dateA = new Date(a.date).getTime()
      const dateB = new Date(b.date).getTime()
      return dateB - dateA
    })
  }

  const billingHistory = generateBillingHistory()

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="text-3xl font-bold text-gray-900">Billing Management</h2>
        <p className="text-gray-600">
          Manage your subscription, billing history, and payment methods
        </p>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <p className="text-gray-600">Loading billing information...</p>
        </div>
      ) : (
        <>
          {/* Current Subscription */}
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
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  Active
                </Badge>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Free Trial Ends</span>
                  <span className="text-sm text-muted-foreground">{formatDate(billingData?.trial_end)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Next Billing</span>
                  <span className="text-sm text-muted-foreground">{getNextBillingDate()}</span>
                </div>
              </div>
              
              <div className="flex space-x-2">
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" size="sm">
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      Cancel Subscription
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Cancel Subscription</AlertDialogTitle>
                      <AlertDialogDescription>
                        Are you sure you want to cancel your subscription? You'll lose access to standard features at the end of your current billing period ({getNextBillingDate()}).
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Keep Subscription</AlertDialogCancel>
                      <AlertDialogAction className="bg-red-600 hover:bg-red-700">
                        Cancel Subscription
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </CardContent>
          </Card>

          {/* Billing History */}
          <Card className="shadow-sm border-gray-200">
            <CardHeader>
              <CardTitle className="text-xl font-semibold">Billing History</CardTitle>
              <CardDescription>
                Your recent invoices and payment history
              </CardDescription>
            </CardHeader>
            <CardContent>
              {billingHistory.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Description</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {billingHistory.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell className="font-medium">{invoice.id}</TableCell>
                        <TableCell>{invoice.date}</TableCell>
                        <TableCell>{invoice.amount}</TableCell>
                        <TableCell>
                          <Badge 
                            variant={invoice.status === "Paid" ? "default" : "secondary"}
                            className={invoice.status === "Paid" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}
                          >
                            {invoice.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{invoice.description}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600 mb-2">No billing history available</p>
                  <p className="text-sm text-gray-500">
                    Your billing history will appear here once your subscription is active
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}