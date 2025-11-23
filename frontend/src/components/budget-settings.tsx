"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ArrowLeft, Save, RefreshCw } from "lucide-react"
import Link from "next/link"
import { budgetService, Budget, Category } from "@/lib/api/budgetService"
import { toast } from "sonner"

export function BudgetSettings() {
  const [categories, setCategories] = useState<Category[]>([])
  const [budgets, setBudgets] = useState<Record<string, number>>({})
  const [existingBudgets, setExistingBudgets] = useState<Budget[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [categoriesData, budgetsData] = await Promise.all([
        budgetService.getCategories(),
        budgetService.getBudgets(),
      ])

      setCategories(categoriesData)
      setExistingBudgets(budgetsData)

      // Khởi tạo budgets từ API data
      const budgetMap: Record<string, number> = {}
      categoriesData.forEach(cat => {
        const existingBudget = budgetsData.find(b => b.category_id === cat.id)
        budgetMap[cat.id] = existingBudget?.limit_amount || 0
      })
      setBudgets(budgetMap)

    } catch (error: any) {
      toast.error(error.message || 'Không thể tải dữ liệu')
    } finally {
      setLoading(false)
    }
  }

  const handleBudgetChange = (categoryId: string, value: string) => {
    const numValue = Number.parseInt(value.replace(/\D/g, "")) || 0
    setBudgets((prev) => ({
      ...prev,
      [categoryId]: numValue,
    }))
  }

  const handleSave = async () => {
    try {
      setSaving(true)

      // Lưu từng budget
      for (const category of categories) {
        const newAmount = budgets[category.id] || 0
        const existingBudget = existingBudgets.find(b => b.category_id === category.id)

        if (existingBudget) {
          // Cập nhật nếu đã tồn tại
          if (existingBudget.limit_amount !== newAmount) {
            await budgetService.updateBudget(existingBudget.id, {
              limit_amount: newAmount,
            })
          }
        } else if (newAmount > 0) {
          // Tạo mới nếu chưa có và amount > 0
          await budgetService.createBudget({
            category_id: category.id,
            limit_amount: newAmount,
            period: 'monthly',
            alert_threshold: 0.8,
          })
        }
      }

      toast.success('Đã lưu cài đặt ngân sách!')

      // Refresh data
      await fetchData()

    } catch (error: any) {
      toast.error(error.message || 'Không thể lưu ngân sách')
    } finally {
      setSaving(false)
    }
  }

  const totalBudget = Object.values(budgets).reduce((sum, budget) => sum + budget, 0)

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
            <div className="flex gap-2">
              <Button variant="outline" onClick={fetchData} disabled={loading}>
                <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Làm mới
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Total Budget Summary */}
        <Card className="mb-8 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Tổng ngân sách hàng tháng</p>
              <p className="mt-2 text-4xl font-bold text-primary">{totalBudget.toLocaleString("vi-VN")}đ</p>
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
          <h2 className="text-lg font-semibold text-foreground">
            Ngân sách theo danh mục ({categories.length} danh mục)
          </h2>

          {categories.length === 0 ? (
            <Card className="p-8 text-center">
              <p className="text-muted-foreground">Chưa có danh mục nào</p>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {categories.map((category) => {
                const budgetAmount = budgets[category.id] || 0
                const percentage = totalBudget > 0 ? ((budgetAmount / totalBudget) * 100).toFixed(1) : '0.0'

                return (
                  <Card key={category.id} className="p-6">
                    <div className="flex items-start gap-4">
                      <div
                        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg text-2xl"
                        style={{ backgroundColor: `${category.color}20` }}
                      >
                        {category.icon}
                      </div>
                      <div className="flex-1 space-y-2">
                        <Label htmlFor={category.id} className="text-base font-medium text-foreground">
                          {category.name}
                        </Label>
                        <div className="relative">
                          <Input
                            id={category.id}
                            type="text"
                            value={budgetAmount.toLocaleString("vi-VN")}
                            onChange={(e) => handleBudgetChange(category.id, e.target.value)}
                            className="pr-8"
                          />
                          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">đ</span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {percentage}% tổng ngân sách
                        </p>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
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