import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format currency in Vietnamese Dong
 */
export function formatCurrency(amount: number, locale: string = "vi-VN"): string {
  return `${amount.toLocaleString(locale)}đ`;
}

/**
 * Format date string or Date object
 */
export function formatDate(date: string | Date | null | undefined, locale: string = "vi-VN"): string {
  if (!date) return "N/A";
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return "N/A";
  return dateObj.toLocaleDateString(locale);
}

/**
 * Format time from date
 */
export function formatTime(date: string | Date | null | undefined, locale: string = "vi-VN"): string {
  if (!date) return "N/A";
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return "N/A";
  return dateObj.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
}

/**
 * Format datetime with full details
 */
export function formatDateTime(date: string | Date | null | undefined, locale: string = "vi-VN"): string {
  if (!date) return "N/A";
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return "N/A";
  return dateObj.toLocaleString(locale);
}

/**
 * Calculate percentage safely
 */
export function calculatePercentage(numerator: number, denominator: number): number {
  if (denominator === 0) return 0;
  return (numerator / denominator) * 100;
}
