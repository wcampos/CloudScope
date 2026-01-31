import axios from 'axios';

// Use empty string for same-origin (Docker nginx proxy or Vite dev proxy).
// Use full origin e.g. http://localhost:5001 only when API is on another port and no proxy.
const envUrl = import.meta.env.VITE_API_URL;
const baseURL =
  typeof envUrl === 'string' && envUrl.trim() !== '' && !envUrl.startsWith('/')
    ? envUrl.replace(/\/$/, '') // full URL, strip trailing slash
    : ''; // same-origin so /api/* is proxied

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
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error(
        'API unreachable. Check that the API is running and the URL is correct. ' +
          'Docker: ensure api container is up. Dev: run API on port 5001 or set VITE_API_URL.'
      );
    } else {
      const data = error.response?.data as { message?: string; error?: string; detail?: string | string[] } | undefined;
      let message: string;
      if (data?.detail != null) {
        message = Array.isArray(data.detail) ? data.detail.join(', ') : String(data.detail);
      } else {
        message = data?.message ?? data?.error ?? error.message ?? 'Unknown error';
      }
      console.error('API error:', message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
