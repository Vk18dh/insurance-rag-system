"use client"

import React from 'react';
import { AuditTable } from '@/components/admin/audit-table';

export default function AuditPage() {
  return (
    <div className="container max-w-6xl py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Security Audit Log</h1>
          <p className="text-muted-foreground mt-1">
            Immutable log of systemic security and action events.
          </p>
        </div>
        <a href="/admin" className="bg-secondary text-secondary-foreground hover:bg-secondary/80 inline-flex items-center justify-center rounded-md text-sm font-medium h-10 px-4 py-2">
          Back to Dashboard
        </a>
      </div>
      
      <AuditTable />
    </div>
  );
}
