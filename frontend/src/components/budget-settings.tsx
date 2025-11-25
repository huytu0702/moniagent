"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ArrowLeft, Save } from "lucide-react"
import Link from "next/link"
import { authStorage } from "@/lib/auth"
import { categoryAPI, budgetAPI } from "@/lib/api"
import { Category, Budget } from "@/lib/api/types"
import { getErrorMessage } from "@/lib/error-handler"
import { formatCurrency, calculatePercentage } from "@/lib/utils"

export function BudgetSettings() {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [categories, setCategories] = useState<Category[]>([])
  const [budgets, setBudgets] = useState<Record<string, number>>({})
  const [existingBudgets, setExistingBudgets] = useState<Record<string, Budget>>({})

  useEffect(() => {
    let isMounted = true

    const loadData = async () => {
      const accessToken = authStorage.getToken()
      if (!accessToken) {
        router.push("/login")
        return
      }
      
      if (!isMounted) return
      setToken(accessToken)
      
      setIsLoading(true)
      setError("")
      try {
        const [categoriesRes, budgetsList] = await Promise.all([
          categoryAPI.list(accessToken),
          budgetAPI.list(accessToken),
        ])

        if (!isMounted) return

        const categoriesData = categoriesRes?.categories || []
        const budgetsData = budgetsList || []

        setCategories(categoriesData)

        // Create budget maps
        const budgetAmounts: Record<string, number> = {}
        const existingBudgetMap: Record<string, Budget> = {}

        budgetsData.forEach(budget => {
          budgetAmounts[budget.category_id] = budget.limit_amount
          existingBudgetMap[budget.category_id] = budget
        })

        categoriesData.forEach(cat => {
          if (!(cat.id in budgetAmounts)) {
            budgetAmounts[cat.id] = 0
          }
        })

        setBudgets(budgetAmounts)
        setExistingBudgets(existingBudgetMap)
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
    }
  }, [])

  const fetchBudgetData = async (accessToken: string) => {
    setIsLoading(true)
    setError("")
    try {
      const [categoriesRes, budgetsList] = await Promise.all([
        categoryAPI.list(accessToken),
        budgetAPI.list(accessToken),
      ])

      const categoriesData = categoriesRes?.categories || []
      const budgetsData = budgetsList || []

      setCategories(categoriesData)

      const budgetAmounts: Record<string, number> = {}
      const existingBudgetMap: Record<string, Budget> = {}

      budgetsData.forEach(budget => {
        budgetAmounts[budget.category_id] = budget.limit_amount
        existingBudgetMap[budget.category_id] = budget
      })

      categoriesData.forEach(cat => {
        if (!(cat.id in budgetAmounts)) {
          budgetAmounts[cat.id] = 0
        }
      })

      setBudgets(budgetAmounts)
      setExistingBudgets(existingBudgetMap)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleBudgetChange = (categoryId: string, value: string) => {
    const numValue = Number.parseInt(value.replace(/\D/g, "")) || 0
    setBudgets(prev => ({ ...prev, [categoryId]: numValue }))
  }

  const handleSave = async () => {
    if (!token) return

    setIsSaving(true)
    setError("")

    try {
      console.log('💾 Starting save operation...')
      console.log('📝 Current budgets to save:', budgets)

      // Create or update budgets for each category
      const promises = categories.map(async (category) => {
        const budgetAmount = budgets[category.id]
        const existingBudget = existingBudgets[category.id]

        console.log(`Processing ${category.name}:`, { budgetAmount, hasExisting: !!existingBudget })

        if (existingBudget) {
          // Update existing budget if amount changed
          if (existingBudget.limit_amount !== budgetAmount) {
            console.log(`⬆️ Updating budget for ${category.name}: ${existingBudget.limit_amount} → ${budgetAmount}`)
            return budgetAPI.update(
              existingBudget.id,
              { limit_amount: budgetAmount },
              token
            )
          } else {
            console.log(`⏭️ Skipping ${category.name} - no change`)
          }
        } else if (budgetAmount > 0) {
          // Create new budget only if amount is greater than 0
          console.log(`➕ Creating new budget for ${category.name}: ${budgetAmount}`)
          return budgetAPI.create(
            {
              category_id: category.id,
              limit_amount: budgetAmount,
              period: 'monthly',
              alert_threshold: 0.8,
            },
            token
          )
        } else {
          console.log(`⏭️ Skipping ${category.name} - amount is 0`)
        }
      })

      const results = await Promise.all(promises)
      console.log('✅ Save completed. Results:', results)

      // Refresh data after save
      console.log('🔄 Refreshing budget data...')
      await fetchBudgetData(token)

      alert("Đã lưu cài đặt ngân sách!")
    } catch (err) {
      console.error('❌ Save failed:', err)
      setError(getErrorMessage(err))
      alert("Có lỗi xảy ra khi lưu ngân sách: " + getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const totalBudget = Object.values(budgets).reduce((sum, budget) => sum + budget, 0)

  // Loading state
  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Đang tải dữ liệu...</p>
    </div>
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-4xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/dashboard">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-foreground">Cài đặt ngân sách</h1>
                <p className="text-sm text-muted-foreground">Thiết lập ngân sách hàng tháng cho từng danh mục</p>
              </div>
            </div>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? (
                <span className="animate-spin mr-2">⏳</span>
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              {isSaving ? "Đang lưu..." : "Lưu thay đổi"}
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {error && (
          <Card className="mb-8 p-4 bg-destructive/10 text-destructive">
            <p>Lỗi: {error}</p>
            <Button variant="link" onClick={() => token && fetchBudgetData(token)}>Thử lại</Button>
          </Card>
        )}

        {/* Total Budget Summary */}
        <Card className="mb-8 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Tổng ngân sách hàng tháng</p>
              <p className="mt-2 text-4xl font-bold text-primary">{formatCurrency(totalBudget)}</p>
            </div>
            <div className="rounded-full bg-primary/10 p-4">
              <svg
                className="h-12 w-12 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
        </Card>

        {/* Budget Settings Grid */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Ngân sách theo danh mục</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {categories.map((category) => (
              <Card key={category.id} className="p-6">
                <div className="flex items-start gap-4">
                  <div
                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg text-2xl"
                    style={{ backgroundColor: `${category.color || "#cccccc"}20` }}
                  >
                    {category.icon || "📝"}
                  </div>
                  <div className="flex-1 space-y-2">
                    <Label htmlFor={category.id} className="text-base font-medium text-foreground">
                      {category.name}
                    </Label>
                    <div className="relative">
                      <Input
                        id={category.id}
                        type="text"
                        value={formatCurrency(budgets[category.id] || 0).replace("đ", "")}
                        onChange={(e) => handleBudgetChange(category.id, e.target.value)}
                        className="pr-8"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">đ</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {calculatePercentage(budgets[category.id] || 0, totalBudget).toFixed(1)}% tổng ngân sách
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Tips Section */}
        <Card className="mt-8 border-primary/20 bg-primary/5 p-6">
          <h3 className="mb-3 font-semibold text-foreground">💡 Mẹo quản lý ngân sách</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <span>Áp dụng quy tắc 50/30/20: 50% nhu cầu thiết yếu, 30% mong muốn, 20% tiết kiệm</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <span>Xem xét chi tiêu của tháng trước để đặt ngân sách phù hợp</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <span>Để lại khoảng 10% dự phòng cho các chi phí bất ngờ</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary">•</span>
              <span>Điều chỉnh ngân sách hàng tháng dựa trên thực tế chi tiêu</span>
            </li>
          </ul>
        </Card>
      </main>
    </div>
  )
}
