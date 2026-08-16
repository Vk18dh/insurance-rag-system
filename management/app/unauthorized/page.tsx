"use client"

import React from 'react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/components/auth-provider';
import { ShieldAlert } from 'lucide-react';

export default function UnauthorizedPage() {
  const { logout } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center space-y-4 p-8 max-w-md w-full">
        <div className="flex justify-center mb-4">
          <ShieldAlert className="h-16 w-16 text-destructive" />
        </div>
        <h1 className="text-2xl font-bold text-foreground">Access Denied</h1>
        <p className="text-muted-foreground">
          You do not have the required permissions to access the Management Website. 
          Only accounts with EXPERT or ADMIN roles are permitted here.
        </p>
        <Button onClick={logout} className="mt-6 w-full">
          Sign Out
        </Button>
      </div>
    </div>
  );
}
