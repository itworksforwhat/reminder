import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  TokenResponse, ReminderListResponse, Reminder,
  ReminderCreate, ReminderUpdate, Template,
  TemplateApplyRequest, TemplateApplyResponse, Company,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: attach token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 with refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          }
          return api(originalRequest);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  register: (email: string, password: string, name: string) =>
    api.post<TokenResponse>('/auth/register', { email, password, name }),

  login: (email: string, password: string) =>
    api.post<TokenResponse>('/auth/login', { email, password }),

  getMe: () => api.get('/auth/me'),

  createCompany: (name: string, businessNumber?: string) =>
    api.post<Company>('/auth/companies', { name, business_number: businessNumber }),
};

// Reminders API
export const remindersApi = {
  list: (companyId: string, params?: {
    page?: number; page_size?: number; category?: string;
    completed?: boolean; year?: number; month?: number;
  }) => api.get<ReminderListResponse>('/reminders', {
    params: { company_id: companyId, ...params },
  }),

  get: (id: string) => api.get<Reminder>(`/reminders/${id}`),

  create: (companyId: string, data: ReminderCreate) =>
    api.post<Reminder>('/reminders', data, { params: { company_id: companyId } }),

  update: (id: string, data: ReminderUpdate) =>
    api.put<Reminder>(`/reminders/${id}`, data),

  delete: (id: string) => api.delete(`/reminders/${id}`),

  exportExcel: (companyId: string, year?: number, category?: string) =>
    api.get('/reminders/export/excel', {
      params: { company_id: companyId, year, category },
      responseType: 'blob',
    }),

  importExcel: (companyId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/reminders/import/excel', formData, {
      params: { company_id: companyId },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Templates API
export const templatesApi = {
  list: () => api.get<Template[]>('/templates'),

  get: (id: string) => api.get<Template>(`/templates/${id}`),

  preview: (request: TemplateApplyRequest) =>
    api.post<TemplateApplyResponse>('/templates/preview', request),

  apply: (request: TemplateApplyRequest) =>
    api.post<Reminder[]>('/templates/apply', request),
};

export default api;
