import type { Metadata, Viewport } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { AppProvider } from "@/contexts/app-context"
import { ToastProvider } from "@/contexts/toast-context"
import { GlobalToastContainer } from "@/components/ui/global-toast-container"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: {
    default: "MoniAgent - AI Financial Assistant",
    template: "%s | MoniAgent",
  },
  description: "Your personal AI-powered financial management assistant",
  keywords: ["financial", "expense tracking", "budget", "AI assistant", "money management"],
  authors: [{ name: "MoniAgent Team" }],
  creator: "MoniAgent",
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000"),
  openGraph: {
    type: "website",
    locale: "vi_VN",
    url: "/",
    siteName: "MoniAgent",
    title: "MoniAgent - AI Financial Assistant",
    description: "Your personal AI-powered financial management assistant",
  },
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className={`${inter.variable} ${inter.className} antialiased`}>
        <ToastProvider>
          <AppProvider>
            {children}
          </AppProvider>
          <GlobalToastContainer />
        </ToastProvider>
      </body>
    </html>
  )
}