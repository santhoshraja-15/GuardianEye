import axios, { AxiosError, AxiosHeaders, InternalAxiosRequestConfig } from 'axios';
import { appConfig } from '../config/app';
import { useSessionStore } from '../stores/session-store';

export class ApiError extends Error {
  status?: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status?: number, code?: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export const apiClient = axios.create({
  baseURL: appConfig.apiBaseUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useSessionStore.getState().accessToken;

  if (token) {
    if (!config.headers) {
      config.headers = new AxiosHeaders();
    }

    config.headers.set('Authorization', `Bearer ${token}`);
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ detail?: string; message?: string }>) => {
    const status = error.response?.status;
    const payload = error.response?.data;
    const message = payload?.detail ?? payload?.message ?? error.message ?? 'Request failed';

    return Promise.reject(new ApiError(message, status, error.code, payload));
  },
);

