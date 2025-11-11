// Utility per gestione autenticazione
export class AuthManager {
  private static readonly TOKEN_KEY = 'authToken';
  private static readonly USERNAME_KEY = 'username';
  
  static isAuthenticated(): boolean {
    return localStorage.getItem(this.TOKEN_KEY) !== null;
  }
  
  static getUsername(): string | null {
    return localStorage.getItem(this.USERNAME_KEY);
  }
  
  static setAuth(username: string): void {
    localStorage.setItem(this.TOKEN_KEY, 'django-session');
    localStorage.setItem(this.USERNAME_KEY, username);
  }
  
  static clearAuth(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USERNAME_KEY);
  }
  
  static getCsrfToken(): string | null {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return decodeURIComponent(value);
      }
    }
    return null;
  }
  
  static async makeAuthenticatedRequest(url: string, options: RequestInit = {}): Promise<Response> {
    const defaultOptions: RequestInit = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };
    
    const response = await fetch(url, defaultOptions);
    
    // Se 401/403, redirect al login
    if (response.status === 401 || response.status === 403) {
      this.clearAuth();
      window.location.href = '/login';
    }
    
    return response;
  }
  
  static requireAuth(): void {
    if (!this.isAuthenticated()) {
      window.location.href = '/login';
    }
  }
}