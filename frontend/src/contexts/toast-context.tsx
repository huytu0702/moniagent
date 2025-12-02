"use client"

import { createContext, useContext, useState, useCallback, ReactNode } from "react"
import { ToastProps } from "@/components/ui/toast"

interface ToastContextType {
    toasts: ToastProps[]
    addToast: (toast: Omit<ToastProps, "id"> & { id?: string }) => string
    removeToast: (id: string) => void
    updateToast: (id: string, updates: Partial<ToastProps>) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastProps[]>([])

    const addToast = useCallback(
        ({ id, title, description, variant = "default", duration = 3000 }: Omit<ToastProps, "id"> & { id?: string }) => {
            const toastId = id || Math.random().toString(36).substring(2, 9)
            const newToast: ToastProps = { id: toastId, title, description, variant, duration }

            setToasts((prev) => {
                // Remove existing toast with same id if exists
                const filtered = prev.filter(t => t.id !== toastId)
                return [...filtered, newToast]
            })

            if (duration > 0) {
                setTimeout(() => {
                    removeToast(toastId)
                }, duration)
            }

            return toastId
        },
        []
    )

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id))
    }, [])

    const updateToast = useCallback((id: string, updates: Partial<ToastProps>) => {
        setToasts((prev) =>
            prev.map((toast) =>
                toast.id === id ? { ...toast, ...updates } : toast
            )
        )

        // If duration is updated, set new timeout
        if (updates.duration && updates.duration > 0) {
            setTimeout(() => {
                removeToast(id)
            }, updates.duration)
        }
    }, [removeToast])

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast, updateToast }}>
            {children}
        </ToastContext.Provider>
    )
}

export function useGlobalToast() {
    const context = useContext(ToastContext)
    if (context === undefined) {
        throw new Error("useGlobalToast must be used within a ToastProvider")
    }
    return context
}
