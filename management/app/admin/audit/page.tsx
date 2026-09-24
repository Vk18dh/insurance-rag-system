"use client"

import React from 'react';
import { AuditTable } from '@/components/admin/audit-table';

export default function AuditPage() {
  return (
    <div className="container max-w-[1400px] py-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Security Audit Log</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Immutable log of systemic security and action events
          </p>
        </div>
      </div>
      
      <AuditTable />
    </div>
  );
}
