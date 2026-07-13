import axios from 'axios';

// Ensure this matches the env variables configured in Vite and Docker
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Reusable Axios Interceptor for injecting JWT Tokens seamlessly
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Generic interceptor for gracefully handling 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and force redirect
      localStorage.removeItem('access_token');
      // A full app reload resets auth state elegantly for this architecture
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'; 
      }
    }
    return Promise.reject(error);
  }
);
