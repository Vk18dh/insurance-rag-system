import axios from 'axios';

// Ensure this matches the env variables configured in Vite and Docker
const API_BASE_URL = 'http://127.0.0.1:8005/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
