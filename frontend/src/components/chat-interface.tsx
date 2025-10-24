"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ArrowLeft, Send, Sparkles } from "lucide-react"
import Link from "next/link"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  extractedExpense?: {
    merchant: string
    amount: number
    category: string
  }
  askingConfirmation?: boolean
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Xin chào! Tôi là trợ lý AI của bạn. Tôi có thể giúp bạn ghi lại chi tiêu, phân tích ngân sách và đưa ra lời khuyên tài chính. Hãy cho tôi biết bạn đã chi tiêu gì hôm nay nhé!",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")

  const handleSend = () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "Tôi đã lưu các thông tin chi tiêu sau vào hệ thống:\n\n📌 **Thông tin chi tiêu:**\n   • Cửa hàng: Starbucks\n   • Số tiền: 85,000đ\n   • Ngày: 2025-10-23\n   • Danh mục: Ăn uống\n\nBạn có muốn thay đổi thông tin nào không?",
        timestamp: new Date(),
        extractedExpense: {
          merchant: "Starbucks",
          amount: 85000,
          category: "Ăn uống",
        },
        askingConfirmation: true,
      }
      setMessages((prev) => [...prev, aiMessage])
    }, 1000)

    setInput("")
  }

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                <Sparkles className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h1 className="font-semibold text-foreground">Trợ lý AI</h1>
                <p className="text-xs text-muted-foreground">Luôn sẵn sàng hỗ trợ bạn</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-4 py-6">
          <div className="space-y-6">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === "user" ? "bg-primary text-primary-foreground" : "bg-card border border-border"
                  }`}
                >
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>

                  {message.extractedExpense && (
                    <Card className="mt-3 bg-muted/50 p-3">
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Cửa hàng:</span>
                          <span className="font-medium">{message.extractedExpense.merchant}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Số tiền:</span>
                          <span className="font-medium">
                            {message.extractedExpense.amount.toLocaleString("vi-VN")}đ
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Danh mục:</span>
                          <span className="font-medium">{message.extractedExpense.category}</span>
                        </div>
                      </div>
                    </Card>
                  )}

                  {message.askingConfirmation && (
                    <div className="mt-3 flex gap-2">
                      <Button size="sm" variant="outline" className="text-xs bg-transparent">
                        Không, đúng rồi
                      </Button>
                      <Button size="sm" variant="outline" className="text-xs bg-transparent">
                        Thay đổi
                      </Button>
                    </div>
                  )}

                  <p className="mt-2 text-xs opacity-60">
                    {message.timestamp.toLocaleTimeString("vi-VN", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-border bg-card">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Nhập chi tiêu của bạn... (VD: Tôi vừa mua cafe 50k)"
              className="flex-1"
            />
            <Button onClick={handleSend} size="icon">
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Bạn có thể nhập chi tiêu bằng văn bản hoặc gửi ảnh hóa đơn
          </p>
        </div>
      </div>
    </div>
  )
}
