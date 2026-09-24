"use client"

import React, { useEffect } from 'react';
import { useAuth } from '@/components/auth-provider';
import { useRouter } from 'next/navigation';
import { ManagementLayout } from '@/components/management-layout';

export default function ExpertLayout({
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
      } else if (role !== 'expert' && role !== 'admin') {
        router.push('/unauthorized');
      }
    }
  }, [isLoading, isAuthenticated, role, router]);

  if (isLoading || (!isAuthenticated) || (role !== 'expert' && role !== 'admin')) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Checking authorization...</div>
      </div>
    );
  }

  return (
    <ManagementLayout role={role}>
      {children}
    </ManagementLayout>
  );
}
