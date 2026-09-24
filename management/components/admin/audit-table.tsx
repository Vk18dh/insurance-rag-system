"use client"

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Filter, RefreshCcw, ChevronLeft, ChevronRight } from 'lucide-react';

export function AuditTable() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [skip, setSkip] = useState(0);
  const [total, setTotal] = useState(0);
  
  const [actionFilter, setActionFilter] = useState('');
  const [actorFilter, setActorFilter] = useState('');

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError('');
      const params = new URLSearchParams({
        skip: skip.toString(),
        limit: "20"
      });
      if (actionFilter) params.append("action", actionFilter);
      if (actorFilter) params.append("actor_id", actorFilter);

      const data = await apiClient.fetchWithAuth(`/admin/audit?${params.toString()}`);
      setLogs(data.items);
      setTotal(data.total);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [skip]);

  const handleSearch = () => {
    if (skip === 0) {
      fetchLogs();
    } else {
      setSkip(0);
    }
  };

  return (
    <Card className="border shadow-sm">
      <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-b gap-4 bg-card/50">
        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-48">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Actor ID" 
              className="pl-9 h-9"
              value={actorFilter} 
              onChange={e => setActorFilter(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <div className="relative w-full sm:w-48">
            <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Action type" 
              className="pl-9 h-9"
              value={actionFilter} 
              onChange={e => setActionFilter(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <Button onClick={handleSearch} variant="secondary" size="sm" className="h-9">Search</Button>
        </div>
        <Button onClick={fetchLogs} variant="outline" size="sm" disabled={loading} className="h-9 w-full sm:w-auto">
          <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b">
            <tr>
              <th className="px-6 py-3 font-medium">Time (UTC)</th>
              <th className="px-6 py-3 font-medium">Actor</th>
              <th className="px-6 py-3 font-medium">Action</th>
              <th className="px-6 py-3 font-medium">Resource</th>
              <th className="px-6 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading && logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                  <div className="flex justify-center items-center gap-2">
                    <RefreshCcw className="h-4 w-4 animate-spin" />
                    Loading audit logs...
                  </div>
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-destructive">
                  {error}
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                  No audit logs found.
                </td>
              </tr>
            ) : (
              logs.map((log: any) => (
                <tr key={log.id} className="border-b hover:bg-muted/30 transition-colors">
                  <td className="px-6 py-3 whitespace-nowrap text-muted-foreground text-xs font-mono">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap font-medium">
                    {log.actor_id || 'SYSTEM'}
                  </td>
                  <td className="px-6 py-3 font-mono text-xs text-foreground">
                    {log.action}
                  </td>
                  <td className="px-6 py-3 text-muted-foreground truncate max-w-[200px]">
                    {log.target_id || '—'}
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <div className={`h-2 w-2 rounded-full ${
                        log.outcome === 'SUCCESS' ? 'bg-green-500' : 'bg-destructive'
                      }`} />
                      <span className="text-xs font-medium">{log.outcome}</span>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-t gap-4 bg-card/50">
        <div className="text-sm text-muted-foreground">
          Showing <span className="font-medium text-foreground">{total === 0 ? 0 : skip + 1}</span> to <span className="font-medium text-foreground">{Math.min(skip + 20, total)}</span> of <span className="font-medium text-foreground">{total}</span> records
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            disabled={skip === 0 || loading} 
            onClick={() => setSkip(Math.max(0, skip - 20))}
            className="h-8 w-8 p-0"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            disabled={skip + 20 >= total || loading} 
            onClick={() => setSkip(skip + 20)}
            className="h-8 w-8 p-0"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
