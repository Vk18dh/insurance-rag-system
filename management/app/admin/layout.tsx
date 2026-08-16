"use client"

import React, { useEffect } from 'react';
import { useAuth } from '@/components/auth-provider';
import { useRouter } from 'next/navigation';
import { SiteHeader } from '@/components/site-header';
import { Settings } from 'lucide-react';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, role } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/login');
      } else if (role !== 'admin') {
        router.push('/unauthorized');
      }
    }
  }, [isLoading, isAuthenticated, role, router]);

  if (isLoading || (!isAuthenticated) || (role !== 'admin')) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Checking authorization...</div>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-col">
      <SiteHeader title="Admin Workspace" icon={<Settings className="h-5 w-5" />} />
      <div className="flex-1">
        {children}
      </div>
    </div>
  );
}
