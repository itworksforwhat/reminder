import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User, Company } from '../types';
import { authApi } from '../services/api';
import { wsService } from '../services/websocket';

interface AuthState {
  user: User | null;
  company: Company | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  createCompany: (name: string, businessNumber?: string) => Promise<Company>;
  setCompany: (company: Company) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    company: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Connect/disconnect WebSocket when auth state or company changes
  useEffect(() => {
    if (state.isAuthenticated && state.company) {
      const token = localStorage.getItem('access_token');
      if (token) {
        wsService.connect(state.company.id, token);
      }
    } else {
      wsService.disconnect();
    }
    return () => {
      wsService.disconnect();
    };
  }, [state.isAuthenticated, state.company]);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      authApi.getMe()
        .then((res) => {
          setState((prev) => ({
            ...prev,
            user: res.data,
            isAuthenticated: true,
            isLoading: false,
          }));
        })
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setState((prev) => ({ ...prev, isLoading: false }));
        });
    } else {
      setState((prev) => ({ ...prev, isLoading: false }));
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await authApi.login(email, password);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setState((prev) => ({
      ...prev,
      user: data.user,
      isAuthenticated: true,
    }));
  }, []);

  const register = useCallback(async (email: string, password: string, name: string) => {
    const { data } = await authApi.register(email, password, name);
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    setState((prev) => ({
      ...prev,
      user: data.user,
      isAuthenticated: true,
    }));
  }, []);

  const logout = useCallback(() => {
    wsService.disconnect();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('current_company');
    setState({ user: null, company: null, isAuthenticated: false, isLoading: false });
  }, []);

  const createCompany = useCallback(async (name: string, businessNumber?: string) => {
    const { data } = await authApi.createCompany(name, businessNumber);
    setState((prev) => ({ ...prev, company: data }));
    localStorage.setItem('current_company', JSON.stringify(data));
    return data;
  }, []);

  const setCompany = useCallback((company: Company) => {
    setState((prev) => ({ ...prev, company }));
    localStorage.setItem('current_company', JSON.stringify(company));
  }, []);

  // Load saved company
  useEffect(() => {
    const saved = localStorage.getItem('current_company');
    if (saved) {
      try {
        setState((prev) => ({ ...prev, company: JSON.parse(saved) }));
      } catch { /* ignore */ }
    }
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, createCompany, setCompany }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
