"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ArrowLeft, Send, Sparkles, AlertCircle } from "lucide-react"
import Link from "next/link"
import { chatAPI } from "@/lib/api"
import { authStorage } from "@/lib/auth"
import { useRouter } from "next/navigation"
import { getErrorMessage, logError } from "@/lib/error-handler"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  extractedExpense?: {
    merchant: string
    amount: number
    category: string
    date: string
  }
  askingConfirmation?: boolean
  savedExpense?: {
    id: string
    merchant_name: string
    amount: number
    date: string
    category_id: string
    category_name?: string
  }
  budgetWarning?: string
  advice?: string
  interrupted?: boolean  // NEW: Whether graph execution was interrupted
}

export function ChatInterface() {
  const router = useRouter()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [token, setToken] = useState<string | null>(null)
  
  // Track pending confirmation state for multi-turn flow
  const [pendingConfirmation, setPendingConfirmation] = useState<{
    savedExpense: {
      id: string
      merchant_name: string
      amount: number
      date: string
      category_id: string
    } | null
    isWaiting: boolean
  }>({ savedExpense: null, isWaiting: false })

  useEffect(() => {
    let isMounted = true

    const init = async () => {
      const accessToken = authStorage.getToken()
      if (!accessToken) {
        router.push("/login")
        return
      }
      
      if (!isMounted) return
      setToken(accessToken)

      try {
        const response = await chatAPI.startSession(
          { session_title: "Chat Session - " + new Date().toLocaleString("vi-VN") },
          accessToken
        )
        
        if (!isMounted) return
        
        setSessionId(response.session_id)
        setMessages([
          {
            id: "initial",
            role: "assistant",
            content: response.initial_message || "Xin chào! Tôi là trợ lý AI của bạn. Tôi có thể giúp bạn ghi lại chi tiêu, phân tích ngân sách và đưa ra lời khuyên tài chính. Hãy cho tôi biết bạn đã chi tiêu gì hôm nay nhé!",
            timestamp: new Date(),
          },
        ])
      } catch (err: unknown) {
        if (isMounted) {
          logError(err, 'ChatInterface.initChatSession')
          setError("Không thể khởi tạo phiên chat. " + getErrorMessage(err))
        }
      }
    }

    init()

    return () => {
      isMounted = false
    }
  }, [])

  const handleSend = async () => {
    if (!input.trim() || !sessionId || !token || isLoading) return

    const userMessageId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const userMessage: Message = {
      id: userMessageId,
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const messageContent = input
    setInput("")
    setIsLoading(true)
    setError("")

    try {
      // Determine if this is a confirmation response
      const isConfirmationResponse = pendingConfirmation.isWaiting && pendingConfirmation.savedExpense !== null
      
      const response = await chatAPI.sendMessage(
        sessionId,
        { 
          content: messageContent, 
          message_type: "text",
          is_confirmation_response: isConfirmationResponse,
          saved_expense: isConfirmationResponse ? pendingConfirmation.savedExpense : undefined,
        },
        token
      )
      
      // Clear pending confirmation after sending
      if (isConfirmationResponse) {
        setPendingConfirmation({ savedExpense: null, isWaiting: false })
      }

      // Tạo tin nhắn AI response với unique ID
      const aiMessageId = response.message_id || `ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      const aiMessage: Message = {
        id: aiMessageId,
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
        budgetWarning: response.budget_warning,
        advice: response.advice,
        askingConfirmation: response.asking_confirmation,
        savedExpense: response.saved_expense,
        interrupted: response.interrupted,
      }

      // Nếu có extracted expense và có đủ thông tin cần thiết
      if (response.extracted_expense && response.extracted_expense.amount !== null) {
        aiMessage.extractedExpense = {
          merchant: response.extracted_expense.merchant_name || "N/A",
          amount: response.extracted_expense.amount,
          category: "",
          date: response.extracted_expense.date || "",
        }
      }

      setMessages((prev) => [...prev, aiMessage])
      
      // Track confirmation state for multi-turn flow
      // When interrupted=true or asking_confirmation=true, save the expense for next turn
      if ((response.interrupted || response.asking_confirmation) && response.saved_expense) {
        setPendingConfirmation({
          savedExpense: response.saved_expense,
          isWaiting: true,
        })
      }
    } catch (err: unknown) {
      logError(err, 'ChatInterface.handleSend')
      const errorMessage = getErrorMessage(err, "Có lỗi xảy ra khi gửi tin nhắn")
      setError(errorMessage)
      // Thêm error message với unique ID
      const errorMessageId = `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      setMessages((prev) => [
        ...prev,
        {
          id: errorMessageId,
          role: "assistant",
          content: "Xin lỗi, tôi gặp lỗi khi xử lý tin nhắn của bạn. Vui lòng thử lại.",
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
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
                <p className="text-xs text-muted-foreground">
                  {sessionId ? "Đang hoạt động" : "Đang kết nối..."}
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-destructive/10 border-b border-destructive/20">
          <div className="mx-auto max-w-4xl px-4 py-2">
            <div className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </div>
        </div>
      )}

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

                  {/* Budget Warning */}
                  {message.budgetWarning && (
                    <div className="mt-3 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                      <p className="text-xs text-amber-600 dark:text-amber-400">⚠️ {message.budgetWarning}</p>
                    </div>
                  )}

                  {/* Financial Advice */}
                  {message.advice && (
                    <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                      <p className="text-xs text-blue-600 dark:text-blue-400">💡 {message.advice}</p>
                    </div>
                  )}

                  {/* Saved Expense (only show when asking for confirmation, not after update) */}
                  {message.savedExpense && (message.askingConfirmation || message.interrupted) && (
                    <Card className="mt-3 bg-muted/50 p-3">
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Cửa hàng:</span>
                          <span className="font-medium">{message.savedExpense.merchant_name || "Không xác định"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Số tiền:</span>
                          <span className="font-medium">
                            {message.savedExpense.amount.toLocaleString("vi-VN")}đ
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Ngày:</span>
                          <span className="font-medium">{message.savedExpense.date || "Hôm nay"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Danh mục:</span>
                          <span className="font-medium">{message.savedExpense.category_name || "Chưa phân loại"}</span>
                        </div>
                      </div>
                    </Card>
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
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-card border border-border rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                  </div>
                </div>
              </div>
            )}
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
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder="Nhập chi tiêu của bạn... (VD: Tôi vừa mua cafe 50k)"
              className="flex-1"
              disabled={isLoading || !sessionId}
            />
            <Button onClick={handleSend} size="icon" disabled={isLoading || !sessionId || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {pendingConfirmation.isWaiting 
              ? "💬 Đang chờ bạn xác nhận chi tiêu... (nhắn 'ok' để lưu hoặc cho biết cần sửa gì)"
              : "Bạn có thể nhập chi tiêu bằng văn bản hoặc gửi ảnh hóa đơn"
            }
          </p>
        </div>
      </div>
    </div>
  )
}
