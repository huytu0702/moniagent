"use client"

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { categoryAPI, budgetAPI, expenseAPI } from '@/lib/api'
import { authStorage } from '@/lib/auth'
import { Category, Budget, Expense } from '@/lib/api/types'

interface AppContextType {
    categories: Category[]
    budgets: Budget[]
    expenses: Expense[]
    isLoading: boolean
    error: string | null
    refreshData: () => Promise<void>
    refreshCategories: () => Promise<void>
    refreshBudgets: () => Promise<void>
    refreshExpenses: () => Promise<void>
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export function AppProvider({ children }: { children: ReactNode }) {
    const [categories, setCategories] = useState<Category[]>([])
    const [budgets, setBudgets] = useState<Budget[]>([])
    const [expenses, setExpenses] = useState<Expense[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const loadCategories = useCallback(async (token: string) => {
        try {
            const response = await categoryAPI.list(token)
            const categoriesData = response?.categories || []
            setCategories(categoriesData)
            return categoriesData
        } catch (err) {
            console.error('Failed to load categories:', err)
            throw err
        }
    }, [])

    const loadBudgets = useCallback(async (token: string) => {
        try {
            const budgetsData = await budgetAPI.list(token)
            setBudgets(budgetsData)
            return budgetsData
        } catch (err) {
            console.error('Failed to load budgets:', err)
            throw err
        }
    }, [])

    const loadExpenses = useCallback(async (token: string) => {
        try {
            const expensesData = await expenseAPI.list(token)
            setExpenses(expensesData)
            return expensesData
        } catch (err) {
            console.error('Failed to load expenses:', err)
            throw err
        }
    }, [])

    const loadData = useCallback(async () => {
        const token = authStorage.getToken()
        if (!token) {
            setIsLoading(false)
            return
        }

        setIsLoading(true)
        setError(null)

        try {
            await Promise.all([
                loadCategories(token),
                loadBudgets(token),
                loadExpenses(token)
            ])
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load data')
        } finally {
            setIsLoading(false)
        }
    }, [loadCategories, loadBudgets, loadExpenses])

    // Load data once on mount
    useEffect(() => {
        loadData()
    }, [loadData])

    const refreshCategories = useCallback(async () => {
        const token = authStorage.getToken()
        if (!token) return
        await loadCategories(token)
    }, [loadCategories])

    const refreshBudgets = useCallback(async () => {
        const token = authStorage.getToken()
        if (!token) return
        await loadBudgets(token)
    }, [loadBudgets])

    const refreshExpenses = useCallback(async () => {
        const token = authStorage.getToken()
        if (!token) return
        await loadExpenses(token)
    }, [loadExpenses])

    const refreshData = useCallback(async () => {
        await loadData()
    }, [loadData])

    return (
        <AppContext.Provider
            value={{
                categories,
                budgets,
                expenses,
                isLoading,
                error,
                refreshData,
                refreshCategories,
                refreshBudgets,
                refreshExpenses,
            }}
        >
            {children}
        </AppContext.Provider>
    )
}

export function useAppData() {
    const context = useContext(AppContext)
    if (context === undefined) {
        throw new Error('useAppData must be used within an AppProvider')
    }
    return context
}
