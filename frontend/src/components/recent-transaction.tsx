"use client"

import { Card } from "@/components/ui/card"
import { Expense } from "@/lib/api/dashboardService"
import { ReceiptText } from "lucide-react"

interface RecentTransactionsProps {
  expenses?: Expense[]
}

export function RecentTransactions({ expenses = [] }: RecentTransactionsProps) {
  const formatCurrency = (amount: number) => {
    return amount.toLocaleString("vi-VN")
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    })
  }

  const getCategoryIcon = (categoryName?: string): string => {
    if (!categoryName) return "📝"

    const iconMap: Record<string, string> = {
      "Ăn uống": "🍜",
      "Đi lại": "🚗",
      "Nhà ở": "🏠",
      "Mua sắm cá nhân": "👕",
      "Mua sắm": "👕",
      "Giải trí & du lịch": "🎬",
      "Giải trí": "🎬",
      "Giáo dục & học tập": "📚",
      "Giáo dục": "📚",
      "Sức khỏe & thể thao": "💪",
      "Sức khỏe": "💪",
      "Gia đình & quà tặng": "🎁",
      "Quà tặng": "🎁",
      "Đầu tư & tiết kiệm": "💰",
      "Khác": "⚙️",
    }
    return iconMap[categoryName] || "📝"
  }

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-xl font-semibold text-foreground">Giao dịch gần đây</h2>

      {expenses.length === 0 ? (
        <div className="py-12 text-center">
          <div className="flex flex-col items-center justify-center">
            <div className="rounded-full bg-muted p-4 mb-4">
              <ReceiptText className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-lg font-medium text-foreground mb-2">Chưa có giao dịch nào</p>
            <p className="text-sm text-muted-foreground">
              Bắt đầu thêm chi tiêu của bạn để theo dõi ngân sách
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {expenses.map((expense) => (
            <div
              key={expense.id}
              className="flex items-center justify-between border-b border-border pb-4 last:border-0 last:pb-0"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-xl">
                  {getCategoryIcon(expense.category_name)}
                </div>
                <div>
                  <p className="font-medium text-foreground">{expense.merchant_name}</p>
                  <p className="text-sm text-muted-foreground">
                    {expense.category_name || "Khác"}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-semibold text-foreground">
                  -{formatCurrency(expense.amount)}đ
                </p>
                <p className="text-sm text-muted-foreground">
                  {formatDate(expense.date)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}