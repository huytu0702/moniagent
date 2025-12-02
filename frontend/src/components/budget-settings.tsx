"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ArrowLeft, Save, Home, MessageSquare } from "lucide-react"
import Link from "next/link"
import { authStorage } from "@/lib/auth"
import { budgetAPI } from "@/lib/api"
import { Budget } from "@/lib/api/types"
import { getErrorMessage } from "@/lib/error-handler"
import { formatCurrency, calculatePercentage } from "@/lib/utils"
import { useGlobalToast } from "@/contexts/toast-context"
import { useAppData } from "@/contexts/app-context"

export function BudgetSettings() {
  const router = useRouter()
  const { addToast, updateToast, removeToast } = useGlobalToast()
  const { categories, budgets: budgetsList, isLoading, refreshBudgets } = useAppData()
  const [token, setToken] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [budgetAmounts, setBudgetAmounts] = useState<Record<string, number>>({})

  // Check authentication
  useEffect(() => {
    const accessToken = authStorage.getToken()
    if (!accessToken) {
      router.push("/login")
      return
    }
    setToken(accessToken)
  }, [router])

  // Create budget maps using useMemo
  const existingBudgets = useMemo(() => {
    const existingBudgetMap: Record<string, Budget> = {}
    budgetsList.forEach(budget => {
      existingBudgetMap[budget.category_id] = budget
    })
    return existingBudgetMap
  }, [budgetsList])

  // Initialize budget amounts when data loads
  useEffect(() => {
    const budgetMap: Record<string, number> = {}

    budgetsList.forEach(budget => {
      budgetMap[budget.category_id] = budget.limit_amount
    })

    categories.forEach(cat => {
      if (!(cat.id in budgetMap)) {
        budgetMap[cat.id] = 0
      }
    })

    setBudgetAmounts(budgetMap)
  }, [categories, budgetsList])

  const fetchBudgetData = async () => {
    await refreshBudgets()
  }

  const handleBudgetChange = (categoryId: string, value: string) => {
    const numValue = Number.parseInt(value.replace(/\D/g, "")) || 0
    setBudgetAmounts(prev => ({ ...prev, [categoryId]: numValue }))
  }

  const handleSave = async () => {
    if (!token) return

    // Prepare all API requests
    const requests = categories
      .map((category) => {
        const budgetAmount = budgetAmounts[category.id]
        const existingBudget = existingBudgets[category.id]

        if (existingBudget) {
          if (existingBudget.limit_amount !== budgetAmount) {
            return {
              type: 'update' as const,
              category,
              budgetAmount,
              existingBudget,
              fn: () => budgetAPI.update(existingBudget.id, { limit_amount: budgetAmount }, token)
            }
          }
        } else if (budgetAmount > 0) {
          return {
            type: 'create' as const,
            category,
            budgetAmount,
            fn: () => budgetAPI.create({
              category_id: category.id,
              limit_amount: budgetAmount,
              period: 'monthly',
              alert_threshold: 0.8,
            }, token)
          }
        }
        return null
      })
      .filter(Boolean)

    if (requests.length === 0) {
      addToast({
        title: "Không có thay đổi",
        description: "Không có ngân sách nào được cập nhật",
        variant: "default",
      })
      return
    }

    setIsSaving(true)

    // Show persistent loading toast
    const loadingToastId = `budget-save-${Date.now()}`
    addToast({
      id: loadingToastId,
      title: "Đang lưu...",
      description: `Đang cập nhật ${requests.length} ngân sách`,
      variant: "default",
      duration: 0, // Don't auto-dismiss - persist across pages
    })

    // Execute API calls in parallel
    Promise.all(requests.map(req => req!.fn()))
      .then(async () => {
        console.log('✅ Save completed')

        // Refresh data
        await refreshBudgets()

        // Update toast to success
        updateToast(loadingToastId, {
          title: "Đã lưu!",
          description: `Đã cập nhật ${requests.length} ngân sách thành công`,
          variant: "success",
          duration: 3000, // Auto-dismiss after 3s
        })
      })
      .catch((err) => {
        console.error('❌ Save failed:', err)

        // Update toast to error
        updateToast(loadingToastId, {
          title: "Lỗi",
          description: getErrorMessage(err),
          variant: "error",
          duration: 5000, // Auto-dismiss after 5s
        })
      })
      .finally(() => {
        setIsSaving(false)
      })
  }

  const totalBudget = Object.values(budgetAmounts).reduce((sum, budget) => sum + budget, 0)

  // Loading state
  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Đang tải dữ liệu...</p>
    </div>
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-4 flex-1 min-w-0">
              <div>
                <h1 className="text-2xl font-bold text-foreground">Cài đặt ngân sách</h1>
                <p className="text-sm text-muted-foreground">Thiết lập ngân sách hàng tháng cho từng danh mục</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link href="/dashboard">
                <Button variant="outline" size="sm">
                  <Home className="mr-2 h-4 w-4" />
                  Dashboard
                </Button>
              </Link>
              <Link href="/chat">
                <Button variant="outline" size="sm">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Chat AI
                </Button>
              </Link>
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
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
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
                        value={formatCurrency(budgetAmounts[category.id] || 0).replace("đ", "")}
                        onChange={(e) => handleBudgetChange(category.id, e.target.value)}
                        className="pr-8"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">đ</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {calculatePercentage(budgetAmounts[category.id] || 0, totalBudget).toFixed(1)}% tổng ngân sách
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
