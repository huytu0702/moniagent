'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import {
  Plus,
  Pencil,
  Trash2,
  ArrowLeft,
  Save,
  X,
  AlertTriangle
} from 'lucide-react'
import Link from 'next/link'
import { budgetService, Budget, Category, CreateBudgetData, UpdateBudgetData } from '@/lib/api/budgetService'
import { toast } from 'sonner'

export default function BudgetSettingsPage() {
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Form states
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingBudget, setEditingBudget] = useState<Budget | null>(null)
  const [formData, setFormData] = useState<CreateBudgetData>({
    category_id: '',
    limit_amount: 0,
    period: 'monthly',
    alert_threshold: 0.8,
  })

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [budgetsData, categoriesData] = await Promise.all([
        budgetService.getBudgets(),
        budgetService.getCategories(),
      ])
      setBudgets(budgetsData)
      setCategories(categoriesData)
    } catch (error: any) {
      toast.error(error.message || 'Không thể tải dữ liệu')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateBudget = async () => {
    if (!formData.category_id || formData.limit_amount <= 0) {
      toast.error('Vui lòng điền đầy đủ thông tin')
      return
    }

    try {
      setSaving(true)
      const newBudget = await budgetService.createBudget(formData)
      setBudgets([...budgets, newBudget])
      toast.success('Tạo ngân sách thành công!')
      resetForm()
    } catch (error: any) {
      toast.error(error.message || 'Không thể tạo ngân sách')
    } finally {
      setSaving(false)
    }
  }

  const handleUpdateBudget = async () => {
    if (!editingBudget) return

    try {
      setSaving(true)
      const updateData: UpdateBudgetData = {
        limit_amount: formData.limit_amount,
        period: formData.period,
        alert_threshold: formData.alert_threshold,
      }
      const updatedBudget = await budgetService.updateBudget(editingBudget.id, updateData)
      setBudgets(budgets.map(b => b.id === editingBudget.id ? updatedBudget : b))
      toast.success('Cập nhật ngân sách thành công!')
      resetForm()
    } catch (error: any) {
      toast.error(error.message || 'Không thể cập nhật ngân sách')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteBudget = async (budgetId: string) => {
    if (!confirm('Bạn có chắc muốn xóa ngân sách này?')) return

    try {
      await budgetService.deleteBudget(budgetId)
      setBudgets(budgets.filter(b => b.id !== budgetId))
      toast.success('Xóa ngân sách thành công!')
    } catch (error: any) {
      toast.error(error.message || 'Không thể xóa ngân sách')
    }
  }

  const startEdit = (budget: Budget) => {
    setEditingBudget(budget)
    setFormData({
      category_id: budget.category_id,
      limit_amount: budget.limit_amount,
      period: budget.period,
      alert_threshold: budget.alert_threshold,
    })
    setShowAddForm(true)
  }

  const resetForm = () => {
    setShowAddForm(false)
    setEditingBudget(null)
    setFormData({
      category_id: '',
      limit_amount: 0,
      period: 'monthly',
      alert_threshold: 0.8,
    })
  }

  const getCategoryIcon = (categoryName: string): string => {
    const iconMap: Record<string, string> = {
      "Ăn uống": "🍜",
      "Đi lại": "🚗",
      "Nhà ở": "🏠",
      "Mua sắm cá nhân": "👕",
      "Giải trí & du lịch": "🎬",
      "Giáo dục & học tập": "📚",
      "Sức khỏe & thể thao": "💪",
      "Gia đình & quà tặng": "🎁",
      "Đầu tư & tiết kiệm": "💰",
      "Khác": "⚙️",
    }
    return iconMap[categoryName] || "📝"
  }

  const getProgressColor = (spent: number, limit: number, threshold: number) => {
    const percentage = (spent / limit) * 100
    if (percentage >= threshold * 100) return 'bg-red-500'
    if (percentage >= threshold * 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  // Lấy categories chưa có budget
  const availableCategories = categories.filter(
    cat => !budgets.some(b => b.category_id === cat.id) || editingBudget?.category_id === cat.id
  )

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
        <div className="mx-auto max-w-4xl px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/dashboard">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Quay lại
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-foreground">Cài đặt ngân sách</h1>
                <p className="text-sm text-muted-foreground">Quản lý ngân sách theo danh mục</p>
              </div>
            </div>
            <Button onClick={() => setShowAddForm(true)} disabled={showAddForm}>
              <Plus className="h-4 w-4 mr-2" />
              Thêm ngân sách
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-8">
        {/* Add/Edit Form */}
        {showAddForm && (
          <Card className="p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">
              {editingBudget ? 'Sửa ngân sách' : 'Thêm ngân sách mới'}
            </h2>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="category">Danh mục</Label>
                <select
                  id="category"
                  className="w-full mt-1 p-2 border border-border rounded-md bg-background"
                  value={formData.category_id}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  disabled={!!editingBudget}
                >
                  <option value="">Chọn danh mục</option>
                  {availableCategories.map(cat => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <Label htmlFor="limit_amount">Hạn mức (VNĐ)</Label>
                <Input
                  id="limit_amount"
                  type="number"
                  min="0"
                  step="10000"
                  value={formData.limit_amount}
                  onChange={(e) => setFormData({ ...formData, limit_amount: Number(e.target.value) })}
                  placeholder="Nhập hạn mức"
                />
              </div>

              <div>
                <Label htmlFor="period">Chu kỳ</Label>
                <select
                  id="period"
                  className="w-full mt-1 p-2 border border-border rounded-md bg-background"
                  value={formData.period}
                  onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                >
                  <option value="daily">Hàng ngày</option>
                  <option value="weekly">Hàng tuần</option>
                  <option value="monthly">Hàng tháng</option>
                  <option value="yearly">Hàng năm</option>
                </select>
              </div>

              <div>
                <Label htmlFor="alert_threshold">Ngưỡng cảnh báo (%)</Label>
                <Input
                  id="alert_threshold"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.alert_threshold * 100}
                  onChange={(e) => setFormData({ ...formData, alert_threshold: Number(e.target.value) / 100 })}
                  placeholder="80"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <Button
                onClick={editingBudget ? handleUpdateBudget : handleCreateBudget}
                disabled={saving}
              >
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Đang lưu...' : editingBudget ? 'Cập nhật' : 'Tạo mới'}
              </Button>
              <Button variant="outline" onClick={resetForm}>
                <X className="h-4 w-4 mr-2" />
                Hủy
              </Button>
            </div>
          </Card>
        )}

        {/* Budget List */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Danh sách ngân sách ({budgets.length})</h2>

          {budgets.length === 0 ? (
            <Card className="p-8 text-center">
              <div className="flex flex-col items-center justify-center">
                <div className="rounded-full bg-muted p-4 mb-4">
                  <AlertTriangle className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-lg font-medium text-foreground mb-2">Chưa có ngân sách nào</p>
                <p className="text-sm text-muted-foreground mb-4">
                  Tạo ngân sách để bắt đầu theo dõi chi tiêu
                </p>
                <Button onClick={() => setShowAddForm(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Thêm ngân sách đầu tiên
                </Button>
              </div>
            </Card>
          ) : (
            budgets.map((budget) => {
              const percentage = budget.limit_amount > 0
                ? (budget.spent_amount / budget.limit_amount) * 100
                : 0
              const isWarning = percentage >= budget.alert_threshold * 100

              return (
                <Card key={budget.id} className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted text-2xl">
                        {getCategoryIcon(budget.category_name)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-foreground">{budget.category_name}</h3>
                        <p className="text-sm text-muted-foreground">
                          Chu kỳ: {budget.period === 'monthly' ? 'Hàng tháng' :
                            budget.period === 'weekly' ? 'Hàng tuần' :
                              budget.period === 'daily' ? 'Hàng ngày' : 'Hàng năm'}
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => startEdit(budget)}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteBudget(budget.id)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">
                        Đã chi: {budget.spent_amount.toLocaleString('vi-VN')}đ
                      </span>
                      <span className="font-medium">
                        Hạn mức: {budget.limit_amount.toLocaleString('vi-VN')}đ
                      </span>
                    </div>

                    <Progress
                      value={Math.min(percentage, 100)}
                      className={`h-2 ${isWarning ? '[&>div]:bg-red-500' : '[&>div]:bg-green-500'}`}
                    />

                    <div className="flex justify-between text-sm">
                      <span className={isWarning ? 'text-red-500 font-medium' : 'text-muted-foreground'}>
                        {percentage.toFixed(1)}% đã sử dụng
                      </span>
                      <span className="text-muted-foreground">
                        Còn lại: {budget.remaining_amount.toLocaleString('vi-VN')}đ
                      </span>
                    </div>

                    {isWarning && (
                      <div className="flex items-center gap-2 mt-2 p-2 bg-red-50 dark:bg-red-950 rounded-lg">
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                        <span className="text-sm text-red-600 dark:text-red-400">
                          Đã vượt {budget.alert_threshold * 100}% ngưỡng cảnh báo!
                        </span>
                      </div>
                    )}
                  </div>
                </Card>
              )
            })
          )}
        </div>
      </main>
    </div>
  )
}