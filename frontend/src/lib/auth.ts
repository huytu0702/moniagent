// Quản lý authentication token

const TOKEN_KEY = 'moniagent_access_token';
const TOKEN_EXPIRY_KEY = 'moniagent_token_expiry';

export const authStorage = {
  /**
   * Lưu token
   */
  setToken: (token: string, expiresIn: number = 3600) => {
    if (typeof window === 'undefined') return;
    
    localStorage.setItem(TOKEN_KEY, token);
    const expiryTime = Date.now() + expiresIn * 1000;
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
  },

  /**
   * Lấy token
   */
  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    
    const token = localStorage.getItem(TOKEN_KEY);
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);

    if (!token || !expiry) return null;

    // Kiểm tra token hết hạn chưa
    if (Date.now() > parseInt(expiry)) {
      authStorage.clearToken();
      return null;
    }

    return token;
  },

  /**
   * Xóa token
   */
  clearToken: () => {
    if (typeof window === 'undefined') return;
    
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  },

  /**
   * Kiểm tra đã đăng nhập chưa
   */
  isAuthenticated: (): boolean => {
    return authStorage.getToken() !== null;
  },
};
