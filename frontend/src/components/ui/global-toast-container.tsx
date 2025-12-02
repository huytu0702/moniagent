"use client"

import { ToastContainer } from "./toast"
import { useGlobalToast } from "@/contexts/toast-context"

export function GlobalToastContainer() {
    const { toasts, removeToast } = useGlobalToast()

    return <ToastContainer toasts={toasts} onClose={removeToast} />
}

export default GlobalToastContainer
