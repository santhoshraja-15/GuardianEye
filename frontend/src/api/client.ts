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

    // A 401 from the login/refresh endpoints themselves means "wrong
    // credentials" / "invalid refresh token", not "an existing session went
    // stale" — it must surface as a normal rejected request (so the login
    // form can show the real message) rather than trigger the
    // clear-session-and-redirect flow built for authenticated requests.
    const requestUrl = error.config?.url ?? '';
    const isAuthEndpoint = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/refresh');

    if (status !== 401 || isAuthEndpoint) {
      return Promise.reject(new ApiError(message, status, error.code, payload));
    }

    const session = useSessionStore.getState();
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (!session.refreshToken || !originalRequest) {
      session.clearSession();
      if (typeof window !== 'undefined') {
        window.location.assign('/login');
      }
      return Promise.reject(new ApiError('Session expired. Please sign in again.', status, error.code, payload));
    }

    if (originalRequest._retry) {
      session.clearSession();
      if (typeof window !== 'undefined') {
        window.location.assign('/login');
      }
      return Promise.reject(new ApiError('Session expired. Please sign in again.', status, error.code, payload));
    }

    try {
      const { data } = await axios.post<{ access_token: string; refresh_token: string; expires_in: number }>(
        `${appConfig.apiBaseUrl}/auth/refresh`,
        { refresh_token: session.refreshToken },
      );

      session.updateAccessToken(data.access_token, data.expires_in);

      if (!originalRequest.headers) {
        originalRequest.headers = new AxiosHeaders();
      }

      originalRequest.headers.set('Authorization', `Bearer ${data.access_token}`);
      originalRequest._retry = true;

      return apiClient(originalRequest);
    } catch {
      session.clearSession();
      if (typeof window !== 'undefined') {
        window.location.assign('/login');
      }
      return Promise.reject(new ApiError('Session expired. Please sign in again.', status, error.code, payload));
    }
  },
);
