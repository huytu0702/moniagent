"use client"

import { Card } from "@/components/ui/card"
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

interface ExpenseChartProps {
  categories: Array<{
    name: string
    spent: number
    budget: number
    color: string
  }>
}

export function ExpenseChart({ categories }: ExpenseChartProps) {
  const data = categories.map((cat) => ({
    name: cat.name,
    "Chi tiêu": cat.spent / 1000,
    "Ngân sách": cat.budget / 1000,
  }))

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-xl font-semibold text-foreground">Biểu đồ chi tiêu</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="name" className="text-xs" />
          <YAxis className="text-xs" />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
            }}
            formatter={(value: number) => `${(value * 1000).toLocaleString("vi-VN")}đ`}
          />
          <Legend />
          <Bar dataKey="Chi tiêu" fill="#FF6B6B" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Ngân sách" fill="#4ECDC4" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )
}
