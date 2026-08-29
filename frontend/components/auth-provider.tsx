"use client"

import React, { createContext, useContext, useEffect, useState } from 'react';
import { getToken, apiClient } from '@/lib/api-client';
import { useRouter, usePathname } from 'next/navigation';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  login: () => {},
  logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = getToken();
    setIsAuthenticated(!!token);
    setIsLoading(false);
  }, []);

  const login = (token: string) => {
    setIsAuthenticated(true);
    router.push('/');
  };

  const logout = () => {
    setIsAuthenticated(false);
  };

  const hasAttemptedGuestLogin = React.useRef(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated && !hasAttemptedGuestLogin.current) {
      hasAttemptedGuestLogin.current = true;
      apiClient.guestLogin().then(() => {
        setIsAuthenticated(true);
        if (pathname === '/login' || pathname === '/register') {
          router.push('/');
        }
      }).catch((e) => {
        console.error("Failed to auto-login guest", e);
      });
    }
  }, [isLoading, isAuthenticated, pathname, router]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
