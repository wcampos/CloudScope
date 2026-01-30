import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL ?? '';

const apiClient = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message ?? error.response?.data?.error ?? error.message;
    console.error('API error:', message);
    return Promise.reject(error);
  }
);

export default apiClient;
