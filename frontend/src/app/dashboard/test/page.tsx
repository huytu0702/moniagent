'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { dashboardService } from '@/lib/api/dashboardService'
import { toast } from 'sonner'

export default function DashboardTestPage() {
    const [results, setResults] = useState<any>({})
    const [loading, setLoading] = useState<string | null>(null)

    const testGetExpenses = async () => {
        setLoading('expenses')
        try {
            const data = await dashboardService.getExpenses()
            setResults((prev: any) => ({ ...prev, expenses: data }))
            toast.success(`✅ GET /expenses - Thành công! (${data.length} items)`)
            console.log('Expenses:', data)
        } catch (error: any) {
            toast.error(`❌ GET /expenses - Thất bại: ${error.message}`)
            console.error('Error:', error)
        } finally {
            setLoading(null)
        }
    }

    const testGetBudgets = async () => {
        setLoading('budgets')
        try {
            const data = await dashboardService.getBudgets()
            setResults((prev: any) => ({ ...prev, budgets: data }))
            toast.success(`✅ GET /budgets - Thành công! (${data.length} items)`)
            console.log('Budgets:', data)
        } catch (error: any) {
            toast.error(`❌ GET /budgets - Thất bại: ${error.message}`)
            console.error('Error:', error)
        } finally {
            setLoading(null)
        }
    }

    const testGetCategories = async () => {
        setLoading('categories')
        try {
            const data = await dashboardService.getCategories()
            setResults((prev: any) => ({ ...prev, categories: data }))
            toast.success(`✅ GET /categories - Thành công! (${data.length} items)`)
            console.log('Categories:', data)
        } catch (error: any) {
            toast.error(`❌ GET /categories - Thất bại: ${error.message}`)
            console.error('Error:', error)
        } finally {
            setLoading(null)
        }
    }

    const testGetCategoriesWithSpending = async () => {
        setLoading('categoriesWithSpending')
        try {
            const now = new Date()
            const data = await dashboardService.getCategoriesWithSpending(
                now.getMonth(),
                now.getFullYear()
            )
            setResults((prev: any) => ({ ...prev, categoriesWithSpending: data }))
            toast.success(`✅ getCategoriesWithSpending - Thành công! (${data.length} items)`)
            console.log('Categories with Spending:', data)
        } catch (error: any) {
            toast.error(`❌ getCategoriesWithSpending - Thất bại: ${error.message}`)
            console.error('Error:', error)
        } finally {
            setLoading(null)
        }
    }

    const testAll = async () => {
        await testGetExpenses()
        await testGetBudgets()
        await testGetCategories()
        await testGetCategoriesWithSpending()
    }

    const checkToken = () => {
        const token = localStorage.getItem('access_token')
        if (token) {
            toast.success(`✅ Token tồn tại: ${token.substring(0, 20)}...`)
            console.log('Full token:', token)
        } else {
            toast.error('❌ Không tìm thấy token trong localStorage')
        }
    }

    return (
        <div className="min-h-screen bg-background p-8">
            <div className="max-w-4xl mx-auto space-y-6">
                <Card className="p-6">
                    <h1 className="text-2xl font-bold mb-4">Dashboard API Test</h1>
                    <p className="text-muted-foreground mb-4">
                        Test các API endpoints của Dashboard. Kết quả sẽ hiển thị trong Console (F12).
                    </p>

                    {/* Token Check */}
                    <div className="mb-6">
                        <h2 className="text-lg font-semibold mb-2">1. Kiểm tra Token</h2>
                        <Button onClick={checkToken} variant="outline">
                            Check Token
                        </Button>
                    </div>

                    {/* Individual Tests */}
                    <div className="space-y-4 mb-6">
                        <h2 className="text-lg font-semibold">2. Test từng API</h2>

                        <div className="grid grid-cols-2 gap-4">
                            <Button
                                onClick={testGetExpenses}
                                disabled={loading === 'expenses'}
                                variant="outline"
                            >
                                {loading === 'expenses' ? 'Testing...' : 'Test GET /expenses'}
                            </Button>

                            <Button
                                onClick={testGetBudgets}
                                disabled={loading === 'budgets'}
                                variant="outline"
                            >
                                {loading === 'budgets' ? 'Testing...' : 'Test GET /budgets'}
                            </Button>

                            <Button
                                onClick={testGetCategories}
                                disabled={loading === 'categories'}
                                variant="outline"
                            >
                                {loading === 'categories' ? 'Testing...' : 'Test GET /categories'}
                            </Button>

                            <Button
                                onClick={testGetCategoriesWithSpending}
                                disabled={loading === 'categoriesWithSpending'}
                                variant="outline"
                            >
                                {loading === 'categoriesWithSpending' ? 'Testing...' : 'Test Categories + Spending'}
                            </Button>
                        </div>
                    </div>

                    {/* Test All */}
                    <div>
                        <h2 className="text-lg font-semibold mb-2">3. Test tất cả</h2>
                        <Button onClick={testAll} disabled={loading !== null}>
                            {loading ? 'Testing...' : 'Test All APIs'}
                        </Button>
                    </div>
                </Card>

                {/* Results Display */}
                <Card className="p-6">
                    <h2 className="text-xl font-bold mb-4">Kết quả</h2>

                    {Object.keys(results).length === 0 ? (
                        <p className="text-muted-foreground">Chưa có kết quả. Hãy chạy test.</p>
                    ) : (
                        <div className="space-y-4">
                            {results.expenses && (
                                <div>
                                    <h3 className="font-semibold mb-2">Expenses ({results.expenses.length})</h3>
                                    <pre className="bg-muted p-4 rounded-lg overflow-auto text-xs max-h-60">
                                        {JSON.stringify(results.expenses, null, 2)}
                                    </pre>
                                </div>
                            )}

                            {results.budgets && (
                                <div>
                                    <h3 className="font-semibold mb-2">Budgets ({results.budgets.length})</h3>
                                    <pre className="bg-muted p-4 rounded-lg overflow-auto text-xs max-h-60">
                                        {JSON.stringify(results.budgets, null, 2)}
                                    </pre>
                                </div>
                            )}

                            {results.categories && (
                                <div>
                                    <h3 className="font-semibold mb-2">Categories ({results.categories.length})</h3>
                                    <pre className="bg-muted p-4 rounded-lg overflow-auto text-xs max-h-60">
                                        {JSON.stringify(results.categories, null, 2)}
                                    </pre>
                                </div>
                            )}

                            {results.categoriesWithSpending && (
                                <div>
                                    <h3 className="font-semibold mb-2">
                                        Categories with Spending ({results.categoriesWithSpending.length})
                                    </h3>
                                    <pre className="bg-muted p-4 rounded-lg overflow-auto text-xs max-h-60">
                                        {JSON.stringify(results.categoriesWithSpending, null, 2)}
                                    </pre>
                                </div>
                            )}
                        </div>
                    )}
                </Card>
            </div>
        </div>
    )
}