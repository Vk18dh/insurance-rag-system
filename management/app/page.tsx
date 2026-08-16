"use client"

import React, { useEffect } from 'react';
import { useAuth } from '@/components/auth-provider';
import { useRouter } from 'next/navigation';

export default function RootPage() {
  const { isAuthenticated, isLoading, role } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/login');
      } else if (role === 'admin') {
        router.push('/admin');
      } else if (role === 'expert') {
        router.push('/expert');
      } else {
        router.push('/unauthorized');
      }
    }
  }, [isLoading, isAuthenticated, role, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="animate-pulse text-muted-foreground">Loading Management Workspace...</div>
    </div>
  );
}
