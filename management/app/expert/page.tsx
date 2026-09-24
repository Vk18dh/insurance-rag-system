"use client"

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button, buttonVariants } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import { Search, Filter, RefreshCcw, ArrowRight } from 'lucide-react';

export default function ExpertDashboard() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const data = await apiClient.fetchWithAuth('/expert/reviews');
      if (!data) throw new Error("Failed to fetch review tasks");
      setTasks(data);
    } catch (e: any) {
      console.error("Failed to fetch review tasks", e);
    } finally {
      setLoading(false);
    }
  };

  const filteredTasks = tasks.filter(task => {
    if (!search) return true;
    const q = search.toLowerCase();
    const queryStr = task.payload?.query?.toLowerCase() || '';
    const reasonStr = task.reason?.toLowerCase() || '';
    return queryStr.includes(q) || reasonStr.includes(q) || task.status.toLowerCase().includes(q);
  });

  return (
    <div className="container max-w-[1400px] py-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Review Queue</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Escalated tasks requiring human review
          </p>
        </div>
      </div>

      <Card className="border shadow-sm">
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-b gap-4 bg-card/50">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search queries or reasons..."
                className="pl-9 h-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Button variant="outline" size="sm" className="h-9 hidden sm:flex">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
          </div>
          <Button onClick={fetchTasks} variant="outline" size="sm" disabled={loading} className="h-9 w-full sm:w-auto">
            <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b">
              <tr>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Query</th>
                <th className="px-6 py-3 font-medium">Reason</th>
                <th className="px-6 py-3 font-medium">Confidence</th>
                <th className="px-6 py-3 font-medium">Created</th>
                <th className="px-6 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading && tasks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground">
                    <div className="flex justify-center items-center gap-2">
                      <RefreshCcw className="h-4 w-4 animate-spin" />
                      Loading queue...
                    </div>
                  </td>
                </tr>
              ) : filteredTasks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-muted-foreground">
                    No review tasks found.
                  </td>
                </tr>
              ) : (
                filteredTasks.map((task) => (
                  <tr key={task.id} className="border-b hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className={`h-2 w-2 rounded-full ${
                          task.status === 'PENDING' ? 'bg-amber-500' :
                          task.status === 'IN_REVIEW' ? 'bg-blue-500' : 'bg-green-500'
                        }`} />
                        <span className="font-medium">{task.status}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="max-w-[300px] lg:max-w-[400px] truncate font-medium" title={task.payload?.query}>
                        {task.payload?.query || '—'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-muted-foreground whitespace-nowrap">
                      {task.reason}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {task.payload?.confidence !== undefined ? (
                        <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
                          {Number(task.payload.confidence).toFixed(2)}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-6 py-4 text-muted-foreground whitespace-nowrap text-xs">
                      {new Date(task.created_at).toLocaleDateString()} {new Date(task.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <Link href={`/expert/${task.id}`} className={buttonVariants({ variant: task.status === 'PENDING' ? 'default' : 'secondary', size: "sm" })}>
                        {task.status === 'PENDING' ? 'Review' : 'View'}
                        <ArrowRight className="h-3 w-3 ml-2" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
