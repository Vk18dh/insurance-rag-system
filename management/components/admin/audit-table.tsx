"use client"

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

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
  }, [skip]); // Re-fetch on pagination change

  const handleSearch = () => {
    if (skip === 0) {
      fetchLogs();
    } else {
      setSkip(0); // This will trigger useEffect
    }
  };

  if (error) {
    return <div className="text-destructive">Failed to load audit logs: {error}</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Audit Logs</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex space-x-2 mb-4">
          <Input 
            placeholder="Filter by Action" 
            value={actionFilter} 
            onChange={e => setActionFilter(e.target.value)} 
          />
          <Input 
            placeholder="Filter by Actor ID" 
            value={actorFilter} 
            onChange={e => setActorFilter(e.target.value)} 
          />
          <Button onClick={handleSearch}>Search</Button>
        </div>

        <div className="border rounded-md">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted text-muted-foreground border-b">
              <tr>
                <th className="p-3 font-medium">Timestamp (UTC)</th>
                <th className="p-3 font-medium">Action</th>
                <th className="p-3 font-medium">Actor</th>
                <th className="p-3 font-medium">Target</th>
                <th className="p-3 font-medium">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="p-4 text-center">Loading...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={5} className="p-4 text-center">No audit logs found.</td></tr>
              ) : (
                logs.map((log: any) => (
                  <tr key={log.id} className="border-b">
                    <td className="p-3">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="p-3 font-medium">{log.action}</td>
                    <td className="p-3">{log.actor_id || '-'}</td>
                    <td className="p-3">{log.target_id || '-'}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs ${log.outcome === 'SUCCESS' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {log.outcome}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between mt-4 text-sm text-muted-foreground">
          <div>Showing {skip + 1} to {Math.min(skip + 20, total)} of {total} records</div>
          <div className="space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              disabled={skip === 0} 
              onClick={() => setSkip(Math.max(0, skip - 20))}
            >
              Previous
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              disabled={skip + 20 >= total} 
              onClick={() => setSkip(skip + 20)}
            >
              Next
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
