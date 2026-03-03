import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
});

// Add auth token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (email: string, password: string) =>
  api.post('/auth/login', new URLSearchParams({ username: email, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

export const getMe = () => api.get('/auth/me');

// Employees
export const getEmployees = (activeOnly = true) =>
  api.get('/employees', { params: { active_only: activeOnly } });

export const getEmployee = (id: number) => api.get(`/employees/${id}`);

export const createEmployee = (data: any) => api.post('/employees', data);

export const updateEmployee = (id: number, data: any) =>
  api.patch(`/employees/${id}`, data);

export const deactivateEmployee = (id: number) =>
  api.delete(`/employees/${id}`);

// Config
export const getConfig = (year: number, month: number) =>
  api.get(`/config/${year}/${month}`);

export const createConfig = (data: any) => api.post('/config', data);

export const updateConfig = (year: number, month: number, data: any) =>
  api.patch(`/config/${year}/${month}`, data);

// Exceptions
export const getExceptions = (year: number, month: number) =>
  api.get(`/config/${year}/${month}/exceptions`);

export const addException = (year: number, month: number, data: any) =>
  api.post(`/config/${year}/${month}/exceptions`, data);

export const removeException = (year: number, month: number, id: number) =>
  api.delete(`/config/${year}/${month}/exceptions/${id}`);

// Payroll
export const runPayroll = (year: number, month: number) =>
  api.post(`/payroll/calculate/${year}/${month}`);

export const getPayrollResults = (year: number, month: number) =>
  api.get(`/payroll/results/${year}/${month}`);

export const finalizePayroll = (year: number, month: number) =>
  api.post(`/payroll/finalize/${year}/${month}`);

// Compensation
export const addCompensation = (data: any) =>
  api.post('/payroll/compensation', data);

export const getCompensationHistory = (employeeId: number) =>
  api.get(`/payroll/compensation/${employeeId}`);

// Audit
export const getAuditLog = (params?: any) =>
  api.get('/audit', { params });

// Health
export const healthCheck = () => api.get('/health');

export default api;
