// Utility per gestire il token di autenticazione
export function getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('authToken');
}

export function setAuthToken(token: string): void {
    if (typeof window !== 'undefined') {
        localStorage.setItem('authToken', token);
    }
}

export function removeAuthToken(): void {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
    }
}

export function setUserInfo(userInfo: any): void {
    if (typeof window !== 'undefined') {
        localStorage.setItem('userInfo', JSON.stringify(userInfo));
    }
}

export function getUserInfo(): any {
    if (typeof window === 'undefined') return null;
    const userInfo = localStorage.getItem('userInfo');
    return userInfo ? JSON.parse(userInfo) : null;
}

// Client API base
const API_BASE_URL = 'http://localhost:8000';

export async function apiRequest(endpoint: string, options: any = {}) {
    const token = getAuthToken();
    
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Token ${token}` }),
            ...options.headers,
        },
        ...options,
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        if (!response.ok) {
            if (response.status === 401) {
                // Token scaduto o invalido
                removeAuthToken();
                if (typeof window !== 'undefined') {
                    window.location.href = '/login';
                }
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return response;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Auth API
export async function login(username: string, password: string) {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
        throw new Error('Login failed');
    }

    const data = await response.json();
    setAuthToken(data.token);
    setUserInfo({
        id: data.user_id,
        username: data.username,
        email: data.email,
    });
    
    return data;
}

export async function logout() {
    try {
        await apiRequest('/auth/logout/', { method: 'POST' });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        removeAuthToken();
        if (typeof window !== 'undefined') {
            window.location.href = '/login';
        }
    }
}

export interface MetaField {
  id: number;
  name: string;
  field_type: string;
  verbose_name: string;
  help_text: string;
  required: boolean;
  unique: boolean;
  default_value: string | null;
  related_model: string | null;
  relation_type: string | null;
  order: number;
}

export interface MetaModel {
  id: number;
  name: string;
  table_name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  meta_fields: MetaField[];
}

export interface DynamicRecord {
  id?: number;
  [key: string]: any;
}

// API per MetaModels
export const metaModelApi = {
  async list(): Promise<MetaModel[]> {
    const response = await apiRequest('/api/meta-models/');
    return response.results || response;
  },

  async get(id: number): Promise<MetaModel> {
    return await apiRequest(`/api/meta-models/${id}/`);
  },

  async create(data: Partial<MetaModel>): Promise<MetaModel> {
    return await apiRequest('/api/meta-models/', {
        method: 'POST',
        body: JSON.stringify(data),
    });
  },

  async update(id: number, data: Partial<MetaModel>): Promise<MetaModel> {
    return await apiRequest(`/api/meta-models/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(data),
    });
  },

  async delete(id: number): Promise<void> {
    await apiRequest(`/api/meta-models/${id}/`, {
        method: 'DELETE',
    });
  },

  async createTable(id: number): Promise<void> {
    await apiRequest(`/api/meta-models/${id}/create_table/`, {
        method: 'POST',
    });
  },

  async updateTable(id: number): Promise<void> {
    await apiRequest(`/api/meta-models/${id}/update_table/`, {
        method: 'POST',
    });
  }
};

// API per dati dinamici
export const dynamicDataApi = {
  async list(modelName: string): Promise<DynamicRecord[]> {
    const response = await apiRequest(`/api/data/${modelName}/`);
    return response.results || response;
  },

  async get(modelName: string, id: number): Promise<DynamicRecord> {
    return await apiRequest(`/api/data/${modelName}/${id}/`);
  },

  async create(modelName: string, data: DynamicRecord): Promise<DynamicRecord> {
    return await apiRequest(`/api/data/${modelName}/`, {
        method: 'POST',
        body: JSON.stringify(data),
    });
  },

  async update(modelName: string, id: number, data: DynamicRecord): Promise<DynamicRecord> {
    return await apiRequest(`/api/data/${modelName}/${id}/`, {
        method: 'PUT',
        body: JSON.stringify(data),
    });
  },

  async delete(modelName: string, id: number): Promise<void> {
    await apiRequest(`/api/data/${modelName}/${id}/`, {
        method: 'DELETE',
    });
  }
};