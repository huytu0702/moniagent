import { Card } from "@/components/ui/card"
import { Expense, Category } from "@/lib/api/types"
import { formatCurrency, formatDate } from "@/lib/utils"

interface RecentTransactionsProps {
  expenses: Expense[]
  categories: Category[]
}

export function RecentTransactions({ expenses, categories }: RecentTransactionsProps) {
  // Create category lookup map
  const categoryMap = categories.reduce((acc, cat) => {
    acc[cat.id] = cat
    return acc
  }, {} as Record<string, Category>)

  // Get 5 most recent expenses sorted by date
  const recentExpenses = [...expenses]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5)

  if (recentExpenses.length === 0) {
    return (
      <Card className="p-6">
        <h2 className="mb-4 text-xl font-semibold text-foreground">Giao dịch gần đây</h2>
        <p className="text-muted-foreground text-center py-8">Chưa có giao dịch nào</p>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-xl font-semibold text-foreground">Giao dịch gần đây</h2>
      <div className="space-y-4">
        {recentExpenses.map((expense) => {
          const category = categoryMap[expense.category_id]
          return (
            <div
              key={expense.id}
              className="flex items-center justify-between border-b border-border pb-4 last:border-0 last:pb-0"
            >
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-xl">
                  {category?.icon || "📝"}
                </div>
                <div>
                  <p className="font-medium text-foreground">{expense.merchant_name}</p>
                  <p className="text-sm text-muted-foreground">{category?.name || "Khác"}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-semibold text-foreground">-{formatCurrency(expense.amount)}</p>
                <p className="text-sm text-muted-foreground">{formatDate(expense.date)}</p>
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}
