import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

// Các route công khai không cần authentication
const publicRoutes = ["/login", "/register", "/"]
const authRoutes = ["/login", "/register"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Kiểm tra token từ localStorage sẽ được thực hiện ở client-side
  // Middleware chỉ kiểm tra route protection
  
  // Nếu đang ở trang auth và đã đăng nhập, chuyển về dashboard
  // (sẽ được xử lý ở client component)
  
  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
}
