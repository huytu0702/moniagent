"use client"

import * as React from "react"
import { CheckCircle, AlertCircle, Info, X } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ToastProps {
    id: string
    title?: string
    description?: string
    variant?: "default" | "success" | "error" | "info"
    duration?: number
}

const toastVariants = {
    default: "bg-card border-border text-foreground",
    success: "bg-green-50 border-green-200 text-green-700",
    error: "bg-destructive/10 border-destructive/20 text-destructive",
    info: "bg-blue-50 border-blue-200 text-blue-700",
}

const toastIcons = {
    default: Info,
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
}

export function Toast({ id, title, description, variant = "default", onClose }: ToastProps & { onClose: (id: string) => void }) {
    const Icon = toastIcons[variant]

    return (
        <div
            className={cn(
                "pointer-events-auto w-full max-w-md overflow-hidden rounded-lg border shadow-lg transition-all animate-in slide-in-from-top-5",
                toastVariants[variant]
            )}
        >
            <div className="flex items-start gap-3 p-4">
                <Icon className="h-5 w-5 mt-0.5 shrink-0" />
                <div className="flex-1 space-y-1">
                    {title && <p className="text-sm font-semibold">{title}</p>}
                    {description && <p className="text-sm opacity-90">{description}</p>}
                </div>
                <button
                    onClick={() => onClose(id)}
                    className="shrink-0 rounded-md p-1 hover:bg-black/5 transition-colors"
                >
                    <X className="h-4 w-4" />
                </button>
            </div>
        </div>
    )
}

export function ToastContainer({ toasts, onClose }: { toasts: ToastProps[]; onClose: (id: string) => void }) {
    return (
        <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
            {toasts.map((toast) => (
                <Toast key={toast.id} {...toast} onClose={onClose} />
            ))}
        </div>
    )
}
