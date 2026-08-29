import React from 'react';
import { AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { ReviewTaskResponse } from '@/lib/api-client';

interface ReviewStatusBannerProps {
  status: string;
}

export function ReviewStatusBanner({ status }: ReviewStatusBannerProps) {
  if (status === 'PENDING' || status === 'IN_REVIEW') {
    return (
      <div className="mt-2 flex items-center gap-2 rounded-md bg-amber-500/10 px-3 py-2 text-sm text-amber-500 border border-amber-500/20">
        <Clock className="size-4" />
        <span className="font-medium">Pending Expert Review</span>
      </div>
    );
  }
  
  if (status === 'APPROVED') {
    return (
      <div className="mt-2 flex items-center gap-2 rounded-md bg-emerald-500/10 px-3 py-2 text-sm text-emerald-500 border border-emerald-500/20">
        <CheckCircle className="size-4" />
        <span className="font-medium">Expert Approved</span>
      </div>
    );
  }
  
  if (status === 'CORRECTED') {
    return (
      <div className="mt-2 flex items-center gap-2 rounded-md bg-blue-500/10 px-3 py-2 text-sm text-blue-500 border border-blue-500/20">
        <AlertCircle className="size-4" />
        <span className="font-medium">Expert Corrected</span>
      </div>
    );
  }

  return null;
}
