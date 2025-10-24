import type React from "react"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

interface CategoryCardProps {
  category: {
    id: string
    name: string
    icon: string
    color: string
    spent: number
    budget: number
  }
}

export function CategoryCard({ category }: CategoryCardProps) {
  const percentage = (category.spent / category.budget) * 100
  const isOverBudget = percentage > 100
  const isNearLimit = percentage > 80 && percentage <= 100

  return (
    <Card className="p-4 transition-all hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className="flex h-12 w-12 items-center justify-center rounded-lg text-2xl"
            style={{ backgroundColor: `${category.color}20` }}
          >
            {category.icon}
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{category.name}</h3>
            <p className="text-sm text-muted-foreground">{category.spent.toLocaleString("vi-VN")}đ</p>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <div className="mb-2 flex items-center justify-between text-xs">
          <span className="text-muted-foreground">{category.budget.toLocaleString("vi-VN")}đ</span>
          <span
            className={
              isOverBudget
                ? "font-semibold text-destructive"
                : isNearLimit
                  ? "font-semibold text-yellow-600"
                  : "text-muted-foreground"
            }
          >
            {percentage.toFixed(0)}%
          </span>
        </div>
        <Progress
          value={Math.min(percentage, 100)}
          className="h-2"
          style={
            {
              "--progress-background": category.color,
            } as React.CSSProperties
          }
        />
      </div>
    </Card>
  )
}
