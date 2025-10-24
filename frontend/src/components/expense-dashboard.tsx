"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MessageSquare, Plus, TrendingDown, TrendingUp, Settings } from "lucide-react"
import Link from "next/link"
import { CategoryCard } from "./category-card"
import { ExpenseChart } from "./expense-chart"
import { RecentTransactions } from "./recent-transactions"

const VIETNAMESE_CATEGORIES = [
  { id: "cat-001", name: "Ăn uống", icon: "🍜", color: "#FF6B6B", spent: 2450000, budget: 3000000 },
  { id: "cat-002", name: "Đi lại", icon: "🚗", color: "#4ECDC4", spent: 1200000, budget: 1500000 },
  { id: "cat-003", name: "Nhà ở", icon: "🏠", color: "#95E1D3", spent: 5000000, budget: 5000000 },
  { id: "cat-004", name: "Mua sắm", icon: "👕", color: "#F38181", spent: 800000, budget: 2000000 },
  { id: "cat-005", name: "Giải trí", icon: "🎬", color: "#AA96DA", spent: 650000, budget: 1000000 },
  { id: "cat-006", name: "Giáo dục", icon: "📚", color: "#FCBAD3", spent: 1500000, budget: 2000000 },
  { id: "cat-007", name: "Sức khỏe", icon: "💪", color: "#A8E6CF", spent: 450000, budget: 1000000 },
  { id: "cat-008", name: "Quà tặng", icon: "🎁", color: "#FFD3B6", spent: 300000, budget: 500000 },
]

export function ExpenseDashboard() {
  const [selectedMonth] = useState("Tháng 10, 2025")

  const totalSpent = VIETNAMESE_CATEGORIES.reduce((sum, cat) => sum + cat.spent, 0)
  const totalBudget = VIETNAMESE_CATEGORIES.reduce((sum, cat) => sum + cat.budget, 0)
  const percentageUsed = (totalSpent / totalBudget) * 100

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
                <p className="mt-2 text-3xl font-bold text-foreground">{totalSpent.toLocaleString("vi-VN")}đ</p>
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
                <p className="mt-2 text-3xl font-bold text-foreground">{totalBudget.toLocaleString("vi-VN")}đ</p>
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
          <h2 className="mb-4 text-xl font-semibold text-foreground">Danh mục chi tiêu</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {VIETNAMESE_CATEGORIES.map((category) => (
              <CategoryCard key={category.id} category={category} />
            ))}
          </div>
        </div>

        {/* Chart */}
        <div className="mb-8">
          <ExpenseChart categories={VIETNAMESE_CATEGORIES} />
        </div>

        {/* Recent Transactions */}
        <RecentTransactions />
      </main>
    </div>
  )
}
