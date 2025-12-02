"use client"

import { useState, useCallback } from "react"
import { ToastProps } from "@/components/ui/toast"

export function useToast() {
    const [toasts, setToasts] = useState<ToastProps[]>([])

    const addToast = useCallback(
        ({ title, description, variant = "default", duration = 3000 }: Omit<ToastProps, "id">) => {
            const id = Math.random().toString(36).substring(2, 9)
            const newToast: ToastProps = { id, title, description, variant, duration }

            setToasts((prev) => [...prev, newToast])

            if (duration > 0) {
                setTimeout(() => {
                    removeToast(id)
                }, duration)
            }

            return id
        },
        []
    )

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id))
    }, [])

    return { toasts, addToast, removeToast }
}
