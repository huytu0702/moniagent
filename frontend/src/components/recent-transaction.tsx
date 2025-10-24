import { Card } from "@/components/ui/card"

const RECENT_TRANSACTIONS = [
  { id: "1", merchant: "Starbucks", amount: 85000, date: "2025-10-22", category: "Ăn uống", icon: "🍜" },
  { id: "2", merchant: "Grab", amount: 45000, date: "2025-10-22", category: "Đi lại", icon: "🚗" },
  { id: "3", merchant: "Circle K", amount: 120000, date: "2025-10-21", category: "Ăn uống", icon: "🍜" },
  { id: "4", merchant: "Shopee", amount: 350000, date: "2025-10-21", category: "Mua sắm", icon: "👕" },
  { id: "5", merchant: "CGV Cinema", amount: 200000, date: "2025-10-20", category: "Giải trí", icon: "🎬" },
]

export function RecentTransactions() {
  return (
    <Card className="p-6">
      <h2 className="mb-4 text-xl font-semibold text-foreground">Giao dịch gần đây</h2>
      <div className="space-y-4">
        {RECENT_TRANSACTIONS.map((transaction) => (
          <div
            key={transaction.id}
            className="flex items-center justify-between border-b border-border pb-4 last:border-0 last:pb-0"
          >
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-xl">
                {transaction.icon}
              </div>
              <div>
                <p className="font-medium text-foreground">{transaction.merchant}</p>
                <p className="text-sm text-muted-foreground">{transaction.category}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-semibold text-foreground">-{transaction.amount.toLocaleString("vi-VN")}đ</p>
              <p className="text-sm text-muted-foreground">{transaction.date}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
