"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MessageSquare, TrendingDown, TrendingUp, Settings } from "lucide-react"
import Link from "next/link"
import { CategoryCard } from "./category-card"
import { ExpenseChart } from "./expense-chart"
import { RecentTransactions } from "./recent-transaction"
import { authStorage } from "@/lib/auth"
import { categoryAPI, budgetAPI, expenseAPI } from "@/lib/api"
import { Category, Expense } from "@/lib/api/types"
import { getErrorMessage } from "@/lib/error-handler"
import { formatCurrency, calculatePercentage } from "@/lib/utils"

// Create a merged data structure for rendering
interface CategoryWithBudget extends Category {
  spent: number;
  budget: number;
  // Ensure these are always strings for the UI
  icon: string;
  color: string;
}

export function ExpenseDashboard() {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [categories, setCategories] = useState<CategoryWithBudget[]>([])
  const [expenses, setExpenses] = useState<Expense[]>([])
  
  // Format current month for display
  const currentDate = new Date();
  const selectedMonth = `Tháng ${currentDate.getMonth() + 1}, ${currentDate.getFullYear()}`;

  useEffect(() => {
    let isMounted = true
    const controller = new AbortController()
    
    const loadData = async () => {
      const accessToken = authStorage.getToken()
      if (!accessToken) {
        router.push("/login")
        return
      }
      
      if (!isMounted) return
      setToken(accessToken)
      
      // Fetch data with abort signal
      setIsLoading(true)
      setError("")
      try {
        const [categoriesRes, budgets, expensesData] = await Promise.all([
          categoryAPI.list(accessToken),
          budgetAPI.list(accessToken),
          expenseAPI.list(accessToken),
        ])

        if (!isMounted) return

        // Calculate spent amount per category from expenses
        const spentByCategory = expensesData.reduce((acc, expense) => {
          acc[expense.category_id] = (acc[expense.category_id] || 0) + expense.amount
          return acc
        }, {} as Record<string, number>)

        // Create budget map for quick lookup
        const budgetByCategory = budgets.reduce((acc, budget) => {
          acc[budget.category_id] = budget.limit_amount
          return acc
        }, {} as Record<string, number>)

        // Merge categories with budget and spent data
        const mergedData: CategoryWithBudget[] = (categoriesRes?.categories || []).map(cat => ({
          ...cat,
          spent: spentByCategory[cat.id] || 0,
          budget: budgetByCategory[cat.id] || 0,
          icon: cat.icon || "📝",
          color: cat.color || "#cccccc",
        }))

        setCategories(mergedData)
        setExpenses(expensesData)
      } catch (err) {
        if (isMounted) {
          setError(getErrorMessage(err))
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadData()

    return () => {
      isMounted = false
      controller.abort()
    }
  }, [])

  // Refetch function for retry button
  const refetchData = async () => {
    if (!token) return
    setIsLoading(true)
    setError("")
    try {
      const [categoriesRes, budgets, expensesData] = await Promise.all([
        categoryAPI.list(token),
        budgetAPI.list(token),
        expenseAPI.list(token),
      ])

      const spentByCategory = expensesData.reduce((acc, expense) => {
        acc[expense.category_id] = (acc[expense.category_id] || 0) + expense.amount
        return acc
      }, {} as Record<string, number>)

      const budgetByCategory = budgets.reduce((acc, budget) => {
        acc[budget.category_id] = budget.limit_amount
        return acc
      }, {} as Record<string, number>)

      const mergedData: CategoryWithBudget[] = (categoriesRes?.categories || []).map(cat => ({
        ...cat,
        spent: spentByCategory[cat.id] || 0,
        budget: budgetByCategory[cat.id] || 0,
        icon: cat.icon || "📝",
        color: cat.color || "#cccccc",
      }))

      setCategories(mergedData)
      setExpenses(expensesData)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  // Calculate totals
  const totalSpent = categories.reduce((sum, cat) => sum + cat.spent, 0)
  const totalBudget = categories.reduce((sum, cat) => sum + cat.budget, 0)
  const percentageUsed = calculatePercentage(totalSpent, totalBudget)

  // Render loading state
  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Đang tải dữ liệu...</p>
    </div>
  }

  // Render error state
  if (error) {
    return <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <p className="text-destructive mb-4">{error}</p>
        <Button onClick={refetchData}>Thử lại</Button>
      </div>
    </div>
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
                <p className="mt-2 text-3xl font-bold text-foreground">{formatCurrency(totalSpent)}</p>
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
                <p className="mt-2 text-3xl font-bold text-foreground">{formatCurrency(totalBudget)}</p>
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
                  {formatCurrency(totalBudget - totalSpent)}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">{percentageUsed.toFixed(1)}% đã sử dụng</p>
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
                    strokeDasharray={`${Math.min(percentageUsed, 100) * 1.76} 176`}
                    className="text-primary"
                  />
                </svg>
              </div>
            </div>
          </Card>
        </div>

        {/* Categories Grid */}
        <div className="mb-8">
          <h2 className="mb-4 text-xl font-semibold text-foreground">Danh mục chi tiêu</h2>
          {categories.length === 0 ? (
             <p className="text-muted-foreground text-center py-8">Chưa có danh mục nào</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {categories.map((category) => (
                <CategoryCard key={category.id} category={category} />
              ))}
            </div>
          )}
        </div>

        {/* Chart */}
        <div className="mb-8">
          <ExpenseChart categories={categories} />
        </div>

        {/* Recent Transactions */}
        <RecentTransactions expenses={expenses} categories={categories} />
      </main>
    </div>
  )
}
