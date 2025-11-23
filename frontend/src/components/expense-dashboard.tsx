"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MessageSquare, TrendingDown, TrendingUp, Settings, RefreshCw } from "lucide-react"
import Link from "next/link"
import { CategoryCard } from "./category-card"
import { ExpenseChart } from "./expense-chart"
import { RecentTransactions } from "./recent-transaction"
import { dashboardService, CategoryWithSpending, Expense } from "@/lib/api/dashboardService"
import { toast } from "sonner"

export function ExpenseDashboard() {
  const [categories, setCategories] = useState<CategoryWithSpending[]>([])
  const [recentExpenses, setRecentExpenses] = useState<Expense[]>([])
  const [loading, setLoading] = useState(true)

  const [selectedMonth] = useState(() => {
    const now = new Date()
    return `Tháng ${now.getMonth() + 1}, ${now.getFullYear()}`
  })

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)

      const now = new Date()
      const month = now.getMonth()
      const year = now.getFullYear()

      const categoriesData = await dashboardService.getCategoriesWithSpending(month, year)
      setCategories(categoriesData)

      const expenses = await dashboardService.getExpenses()
      const recent = dashboardService.getRecentExpenses(expenses, 10)
      setRecentExpenses(recent)

    } catch (error: any) {
      console.error('Error fetching dashboard data:', error)
      const errorMessage = error.message || 'Không thể tải dữ liệu dashboard'

      toast.error(errorMessage, {
        description: 'Vui lòng thử lại sau',
        duration: 5000,
      })
    } finally {
      setLoading(false)
    }
  }

  const totalSpent = categories.reduce((sum, cat) => sum + cat.spent, 0)
  const totalBudget = categories.reduce((sum, cat) => sum + cat.budget, 0)
  const percentageUsed = totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Đang tải dữ liệu...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">Chi tiêu của tôi</h1>
              <p className="text-sm text-muted-foreground">{selectedMonth}</p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchDashboardData}
                disabled={loading}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Làm mới
              </Button>
              <Link href="/settings">
                <Button variant="outline" size="sm">
                  <Settings className="mr-2 h-4 w-4" />
                  Cài đặt ngân sách
                </Button>
              </Link>
              <Link href="/chat">
                <Button variant="outline" size="sm">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Chat AI
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Summary Cards */}
        <div className="mb-8 grid gap-4 md:grid-cols-3">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Tổng chi tiêu</p>
                <p className="mt-2 text-3xl font-bold text-foreground">
                  {totalSpent.toLocaleString("vi-VN")}đ
                </p>
              </div>
              <div className="rounded-full bg-destructive/10 p-3">
                <TrendingDown className="h-6 w-6 text-destructive" />
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Ngân sách</p>
                <p className="mt-2 text-3xl font-bold text-foreground">
                  {totalBudget.toLocaleString("vi-VN")}đ
                </p>
              </div>
              <div className="rounded-full bg-primary/10 p-3">
                <TrendingUp className="h-6 w-6 text-primary" />
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Còn lại</p>
                <p className="mt-2 text-3xl font-bold text-foreground">
                  {(totalBudget - totalSpent).toLocaleString("vi-VN")}đ
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {percentageUsed.toFixed(1)}% đã sử dụng
                </p>
              </div>
              <div className="h-16 w-16">
                <svg className="h-full w-full -rotate-90 transform">
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    className="text-muted"
                  />
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    strokeDasharray={`${percentageUsed * 1.76} 176`}
                    className="text-primary"
                  />
                </svg>
              </div>
            </div>
          </Card>
        </div>

        {/* Categories Grid */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-foreground">Danh mục chi tiêu</h2>
            {categories.length > 0 && (
              <Link href="/settings/budget">
                <Button variant="outline" size="sm">
                  Quản lý ngân sách
                </Button>
              </Link>
            )}
          </div>

          {categories.length === 0 ? (
            <Card className="p-8 text-center">
              <div className="flex flex-col items-center justify-center">
                <div className="rounded-full bg-muted p-4 mb-4">
                  <Settings className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-lg font-medium text-foreground mb-2">Chưa có danh mục nào</p>
                <p className="text-sm text-muted-foreground mb-4">
                  Vui lòng tạo ngân sách để bắt đầu theo dõi chi tiêu
                </p>
                <Link href="/settings/budget">
                  <Button>
                    <Settings className="mr-2 h-4 w-4" />
                    Tạo ngân sách ngay
                  </Button>
                </Link>
              </div>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {categories.map((category) => (
                <CategoryCard
                  key={category.id}
                  category={{
                    id: category.id,
                    name: category.name,
                    icon: category.icon,
                    color: category.color,
                    spent: category.spent,
                    budget: category.budget,
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Chart */}
        {categories.length > 0 && (
          <div className="mb-8">
            <ExpenseChart
              categories={categories.map(cat => ({
                id: cat.id,
                name: cat.name,
                icon: cat.icon,
                color: cat.color,
                spent: cat.spent,
                budget: cat.budget,
              }))}
            />
          </div>
        )}

        {/* Recent Transactions */}
        <RecentTransactions expenses={recentExpenses} />
      </main>
    </div>
  )
}