import { API_BASE } from "./../utils/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Badge } from "./ui/badge"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts"
import { TrendingUp, Mail, Filter, Shield, Target } from "lucide-react"
import { useState, useEffect } from "react"

interface EmailStatsData {
  total_processed: number
  spam_count: number
  accuracy: number
  top_category: string
  category_breakdown: Array<{
    category: string
    count: number
    percentage: number
  }>
  weekly_data: Array<{
    day: string
    date: string
    processed: number
    spam: number
  }>
  date_range: string
}

export function EmailStats() {
  const [statsData, setStatsData] = useState<EmailStatsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchEmailStats = async () => {
      try {
        // Get user ID from localStorage first, then fallback to /session/me
        let userId = ''
        try {
          const ls = JSON.parse(localStorage.getItem('userData') || '{}')
          userId = ls.user_id || ls.uid || ''
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
        // console.log('EmailStats - User ID:', userId)
        
        const response = await fetch(`${API_BASE}/user/${userId}/email-stats`, { credentials: 'include' })
        const result = await response.json()
        
        console.log('EmailStats - Response:', result)
        
        if (result.success) {
          setStatsData(result.stats)
          console.log('EmailStats - Stats set:', result.stats)
        } else {
          console.error('EmailStats - Failed to fetch stats:', result.error)
        }
      } catch (error) {
        console.error('EmailStats - Error fetching stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchEmailStats()
  }, [])

  const pieColors = [
    "#8B5CF6", "#06B6D4", "#10B981", "#F59E0B", 
    "#EF4444", "#6366F1", "#84CC16"
  ]

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold text-gray-900">Email Organization Statistics</h2>
          <p className="text-gray-600">
            Detailed analytics of your email processing and categorization
          </p>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-600">Loading email statistics...</p>
        </div>
      </div>
    )
  }

  if (!statsData) {
    return (
      <div className="space-y-8">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold text-gray-900">Email Organization Statistics</h2>
          <p className="text-gray-600">
            Detailed analytics of your email processing and categorization
          </p>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-600">No email statistics available</p>
        </div>
      </div>
    )
  }

  const { total_processed, spam_count, accuracy, top_category, category_breakdown, weekly_data, date_range } = statsData

  // Prepare chart data with explicit non-spam series
  const chartData = weekly_data.map(d => ({
    ...d,
    nonSpam: Math.max((d.processed || 0) - (d.spam || 0), 0),
  }))

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h2 className="text-3xl font-bold text-gray-900">Email Organization Statistics</h2>
        <p className="text-gray-600">
          Detailed analytics of your email processing and categorization
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Total Processed</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{total_processed.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {total_processed > 0 ? "Emails processed this month" : "No emails processed this month"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Spam Filtered</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{spam_count}</div>
            <p className="text-xs text-muted-foreground">
              {total_processed > 0 ? `${((spam_count / total_processed) * 100).toFixed(1)}% of monthly emails` : "No emails processed"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>AI Accuracy</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{accuracy}%</div>
            <p className="text-xs text-muted-foreground">
              Categorization accuracy
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Top Category</CardTitle>
            <Filter className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{top_category}</div>
            <p className="text-xs text-muted-foreground">
              {category_breakdown.length > 0 ? `${category_breakdown[0]?.percentage}% of all emails` : "No categories yet"}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Email Categories Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Email Categories</CardTitle>
            <CardDescription>
              Distribution of emails by category this month ({date_range})
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              {category_breakdown.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={category_breakdown}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ category, percentage }) => `${category} (${percentage}%)`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {category_breakdown.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className="text-gray-500">No email categories available this month</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Weekly Processing */}
        <Card>
          <CardHeader>
            <CardTitle>Weekly Email Processing</CardTitle>
            <CardDescription>
              Daily email processing and spam detection for the last 7 days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value: any, name: string, props: any) => [value, props?.dataKey === 'nonSpam' ? 'Non-Spam' : 'Spam']}
                    labelFormatter={(label) => {
                      const dayData = chartData.find(d => d.day === label)
                      return dayData ? `${label} (${dayData.date})` : label
                    }}
                  />
                  <Bar dataKey="nonSpam" fill="#8B5CF6" name="Non-Spam" />
                  <Bar dataKey="spam" fill="#EF4444" name="Spam" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Category Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle>Category Breakdown</CardTitle>
          <CardDescription>
            Detailed breakdown of email categories and counts
          </CardDescription>
        </CardHeader>
        <CardContent>
          {category_breakdown.length > 0 ? (
            <div className="space-y-4">
              {category_breakdown.map((category, index) => (
                <div key={category.category} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: pieColors[index] }}
                    />
                    <div>
                      <div className="font-medium">{category.category}</div>
                      <div className="text-sm text-muted-foreground">
                        {category.percentage}% of total
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{category.count.toLocaleString()}</div>
                    <div className="text-sm text-muted-foreground">emails</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No email categories available</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}