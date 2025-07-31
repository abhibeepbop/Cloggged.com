import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Badge } from "./ui/badge"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts"
import { TrendingUp, Mail, Filter, Shield, Target } from "lucide-react"

export function EmailStats() {
  const categoryData = [
    { category: "Work", count: 1247, percentage: 43.8 },
    { category: "Finance", count: 423, percentage: 14.9 },
    { category: "Security", count: 267, percentage: 9.4 },
    { category: "Shopping", count: 234, percentage: 8.2 },
    { category: "Social", count: 189, percentage: 6.6 },
    { category: "Newsletter", count: 297, percentage: 10.4 },
    { category: "Other", count: 190, percentage: 6.7 }
  ]

  const weeklyData = [
    { day: "Mon", processed: 412, spam: 28 },
    { day: "Tue", processed: 389, spam: 31 },
    { day: "Wed", processed: 445, spam: 23 },
    { day: "Thu", processed: 398, spam: 35 },
    { day: "Fri", processed: 467, spam: 29 },
    { day: "Sat", processed: 289, spam: 18 },
    { day: "Sun", processed: 447, spam: 29 }
  ]

  const pieColors = [
    "#8B5CF6", "#06B6D4", "#10B981", "#F59E0B", 
    "#EF4444", "#6366F1", "#84CC16"
  ]

  const totalProcessed = 2847
  const totalSpam = 193
  const accuracy = 94.7

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
            <div className="text-2xl font-bold">{totalProcessed.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              +12% from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle>Spam Filtered</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalSpam}</div>
            <p className="text-xs text-muted-foreground">
              {((totalSpam / totalProcessed) * 100).toFixed(1)}% of total emails
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
            <div className="text-2xl font-bold">Work</div>
            <p className="text-xs text-muted-foreground">
              43.8% of all emails
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
              Distribution of emails by category this month
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ category, percentage }) => `${category} (${percentage}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Weekly Processing */}
        <Card>
          <CardHeader>
            <CardTitle>Weekly Email Processing</CardTitle>
            <CardDescription>
              Daily email processing and spam detection over the past week
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="processed" fill="#8B5CF6" name="Processed" />
                  <Bar dataKey="spam" fill="#EF4444" name="Spam Filtered" />
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
          <div className="space-y-4">
            {categoryData.map((category, index) => (
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
        </CardContent>
      </Card>
    </div>
  )
}