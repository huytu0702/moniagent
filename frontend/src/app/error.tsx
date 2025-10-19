"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle } from "lucide-react"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error)
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-destructive/10">
              <AlertCircle className="w-6 h-6 text-destructive" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">Có lỗi xảy ra</CardTitle>
          <CardDescription>
            Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg bg-muted p-4">
            <p className="text-sm text-muted-foreground font-mono">
              {error.message || "Unknown error"}
            </p>
            {error.digest && (
              <p className="text-xs text-muted-foreground mt-2">
                Error ID: {error.digest}
              </p>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button onClick={reset} className="flex-1">
            Thử lại
          </Button>
          <Button variant="outline" onClick={() => window.location.href = "/"} className="flex-1">
            Về trang chủ
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
