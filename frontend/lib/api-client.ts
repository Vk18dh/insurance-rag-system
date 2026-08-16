// frontend/lib/api-client.ts

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface HealthResponse {
  status: string;
  version: string;
  components: Record<string, any>;
}

export interface RetrievedSource {
  document: string;
  page: number;
  content_snippet: string;
  confidence: number;
}

export interface QueryResponse {
  query_id: string;
  conversation_id?: string | null;
  final_answer: string;
  confidence_score: number;
  is_safe: boolean;
  sources: RetrievedSource[];
  execution_time_ms: number;
}

export interface QueryRequest {
  query: string;
  language?: string;
  customer_id?: string | null;
  conversation_id?: string | null;
}

export interface Token {
  access_token: string;
  token_type: string;
  refresh_token?: string | null;
}

export interface UserResponse {
  id: string;
  username: string;
  role: string;
}

export interface ConversationResponse {
  id: string;
  title: string;
}

export interface MessageResponse {
  id: string;
  role: string;
  content: string;
}

export class ApiError extends Error {
  public status: number;
  public details: any;
  constructor(status: number, message: string, details?: any) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

export const getToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

export const setToken = (token: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', token);
  }
};

export const removeToken = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
  }
};

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeToken();
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    const errorData = await response.json().catch(() => null);
    throw new ApiError(response.status, errorData?.detail || 'An API error occurred', errorData);
  }

  return response.json();
}

export const apiClient = {
  login: async (username: string, password: string): Promise<Token> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new ApiError(response.status, errorData?.detail || 'Login failed', errorData);
    }
    const data = await response.json();
    setToken(data.access_token);
    return data;
  },

  logout: () => {
    removeToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  },

  getConversations: async (): Promise<ConversationResponse[]> => {
    return fetchWithAuth('/conversations/');
  },

  createConversation: async (title: string): Promise<ConversationResponse> => {
    return fetchWithAuth('/conversations/', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  },

  getConversation: async (id: string): Promise<ConversationResponse> => {
    return fetchWithAuth(`/conversations/${id}`);
  },

  getMessages: async (conversationId: string): Promise<MessageResponse[]> => {
    return fetchWithAuth(`/conversations/${conversationId}/messages`);
  },

  postQuery: async (request: QueryRequest): Promise<QueryResponse> => {
    return fetchWithAuth('/query', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  getHealth: async (): Promise<HealthResponse> => {
    // Health endpoint usually doesn't require auth
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  }
};
