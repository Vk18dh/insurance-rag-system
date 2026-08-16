"use client"

import React, { createContext, useContext, useEffect, useState } from 'react';
import { getToken, apiClient } from '@/lib/api-client';
import { useRouter, usePathname } from 'next/navigation';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  role: string | null;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  role: null,
  login: () => {},
  logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

function decodeJWT(token: string) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [role, setRole] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = getToken();
    setIsAuthenticated(!!token);
    if (token) {
        const payload = decodeJWT(token);
        if (payload && payload.role) {
            setRole(payload.role);
        }
    }
    setIsLoading(false);
  }, []);

  const login = (token: string) => {
    setIsAuthenticated(true);
    const payload = decodeJWT(token);
    let newRole = null;
    if (payload && payload.role) {
        setRole(payload.role);
        newRole = payload.role;
    }
    
    if (newRole === 'admin') {
        router.push('/admin');
    } else if (newRole === 'expert') {
        router.push('/expert');
    } else {
        router.push('/unauthorized');
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    setRole(null);
    router.push('/login');
  };

  useEffect(() => {
    if (!isLoading && !isAuthenticated && pathname !== '/login') {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, pathname, router]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, role, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
