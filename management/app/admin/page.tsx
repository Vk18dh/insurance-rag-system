"use client"

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { Activity, Users, AlertTriangle, CheckCircle, XCircle, Search, RefreshCcw, ServerCrash, ArrowRight, BarChart3, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import { Button, buttonVariants } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [providerHealth, setProviderHealth] = useState<any>(null);
  const [reviews, setReviews] = useState<any[]>([]);
  const [evals, setEvals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [metricsData, healthData, reviewsData, evalsData] = await Promise.all([
        apiClient.fetchWithAuth('/admin/metrics').catch(() => null),
        apiClient.fetchWithAuth('/admin/provider-health').catch(() => null),
        apiClient.fetchWithAuth('/expert/reviews').catch(() => []),
        apiClient.fetchWithAuth('/admin/evaluations').catch(() => [])
      ]);
      
      if (metricsData) setMetrics(metricsData);
      if (healthData) setProviderHealth(healthData);
      if (Array.isArray(reviewsData)) setReviews(reviewsData.slice(0, 5));
      if (Array.isArray(evalsData)) setEvals(evalsData.slice(0, 3));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="container max-w-[1400px] py-8 space-y-6">
      {/* ROW 1: Page Title */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">System Overview</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time observability and operational metrics
          </p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm" disabled={loading} className="h-9">
          <RefreshCcw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-destructive/10 text-destructive rounded-md border border-destructive/20 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5" />
          <p className="font-medium text-sm">{error}</p>
        </div>
      )}

      {/* ROW 2: Compact KPI Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 flex flex-col justify-between border shadow-sm h-28">
          <div className="flex justify-between items-start text-muted-foreground">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Users</span>
            <Users className="h-4 w-4" />
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight">{loading ? '—' : (metrics?.active_users || 0)}</div>
            <div className="text-xs text-muted-foreground mt-1">Currently registered users</div>
          </div>
        </Card>
        <Card className="p-4 flex flex-col justify-between border shadow-sm h-28">
          <div className="flex justify-between items-start text-muted-foreground">
            <span className="text-xs font-semibold uppercase tracking-wider">Queries (24h)</span>
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight">{loading ? '—' : (metrics?.queries_today || 0)}</div>
            <div className="text-xs text-muted-foreground mt-1">Total inbound requests</div>
          </div>
        </Card>
        <Card className="p-4 flex flex-col justify-between border shadow-sm h-28">
          <div className="flex justify-between items-start text-muted-foreground">
            <span className="text-xs font-semibold uppercase tracking-wider">Escalation Rate</span>
            <AlertTriangle className="h-4 w-4 text-amber-500/70" />
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight text-amber-500">
              {loading ? '—' : `${(metrics?.escalation_rate * 100).toFixed(1)}%`}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Queries requiring human review</div>
          </div>
        </Card>
        <Card className="p-4 flex flex-col justify-between border shadow-sm h-28">
          <div className="flex justify-between items-start text-muted-foreground">
            <span className="text-xs font-semibold uppercase tracking-wider">Avg Latency</span>
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight font-mono">{loading ? '—' : (metrics?.avg_latency_ms || 0)}<span className="text-xl text-muted-foreground font-sans ml-1">ms</span></div>
            <div className="text-xs text-green-500 mt-1 font-medium">Within SLA constraints</div>
          </div>
        </Card>
      </div>

      {/* ROW 3: Two-column operational area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border shadow-sm flex flex-col">
          <div className="p-4 border-b bg-muted/20">
            <h2 className="text-sm font-semibold uppercase tracking-wider">System Status</h2>
          </div>
          <div className="p-6 flex-1 flex flex-col justify-center items-center">
            {loading ? (
              <RefreshCcw className="h-8 w-8 text-muted-foreground animate-spin" />
            ) : metrics?.system_status === 'healthy' ? (
              <div className="text-center space-y-3">
                <div className="mx-auto w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center border border-green-500/20">
                  <CheckCircle className="h-8 w-8" />
                </div>
                <div>
                  <div className="text-xl font-bold tracking-tight text-green-500 uppercase">Operational</div>
                  <div className="text-sm text-muted-foreground mt-1">Core services are running normally</div>
                </div>
              </div>
            ) : (
              <div className="text-center space-y-3">
                <div className="mx-auto w-16 h-16 bg-destructive/10 text-destructive rounded-full flex items-center justify-center border border-destructive/20">
                  <ServerCrash className="h-8 w-8" />
                </div>
                <div>
                  <div className="text-xl font-bold tracking-tight text-destructive uppercase">Degraded</div>
                  <div className="text-sm text-muted-foreground mt-1">Some services are experiencing issues</div>
                </div>
              </div>
            )}
          </div>
        </Card>

        <Card className="border shadow-sm flex flex-col">
          <div className="p-4 border-b bg-muted/20">
            <h2 className="text-sm font-semibold uppercase tracking-wider">LLM Provider Health</h2>
          </div>
          <div className="p-0 flex-1 flex flex-col">
            <div className="grid grid-cols-2 border-b h-full">
              <div className="p-6 border-r flex flex-col justify-center">
                <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Primary</div>
                <div className="text-lg font-bold capitalize">{loading ? '—' : providerHealth?.primary_provider}</div>
                <div className="mt-2 flex items-center gap-2">
                  <div className={`h-2 w-2 rounded-full ${providerHealth?.primary_status === 'AVAILABLE' ? 'bg-green-500' : 'bg-destructive'}`} />
                  <span className="text-sm font-medium">{loading ? '—' : providerHealth?.primary_status}</span>
                </div>
              </div>
              <div className="p-6 flex flex-col justify-center">
                <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Secondary (Failover)</div>
                <div className="text-lg font-bold capitalize">{loading ? '—' : providerHealth?.secondary_provider}</div>
                <div className="mt-2 flex items-center gap-2">
                  <div className={`h-2 w-2 rounded-full ${providerHealth?.secondary_status === 'AVAILABLE' ? 'bg-green-500' : 'bg-destructive'}`} />
                  <span className="text-sm font-medium">{loading ? '—' : providerHealth?.secondary_status}</span>
                </div>
              </div>
            </div>
            <div className="p-4 bg-muted/10 flex justify-between items-center text-sm">
              <span className="text-muted-foreground font-medium">Failover Events (24h)</span>
              <span className="font-bold text-foreground bg-background border px-2 py-0.5 rounded font-mono">
                {loading ? '-' : (providerHealth?.failover_events_24h || 0)}
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* ROW 4 & 5 container for equal height feeling */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* ROW 4: Recent Review Activity */}
        <Card className="border shadow-sm flex flex-col">
          <div className="p-4 border-b bg-muted/20 flex justify-between items-center">
            <h2 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-muted-foreground" />
              Actionable Review Queue
            </h2>
            <Link href="/expert" className="text-xs text-primary font-medium hover:underline flex items-center">
              View All <ArrowRight className="h-3 w-3 ml-1" />
            </Link>
          </div>
          <div className="p-0 overflow-x-auto flex-1">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase border-b bg-muted/10">
                <tr>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Query</th>
                  <th className="px-4 py-2 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">Loading queue...</td>
                  </tr>
                ) : reviews.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">No pending review tasks.</td>
                  </tr>
                ) : (
                  reviews.map(task => (
                    <tr key={task.id} className="border-b hover:bg-muted/30 last:border-0">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className={`h-2 w-2 rounded-full ${
                          task.status === 'PENDING' ? 'bg-amber-500' :
                          task.status === 'IN_REVIEW' ? 'bg-blue-500' : 'bg-green-500'
                        }`} title={task.status} />
                      </td>
                      <td className="px-4 py-3 truncate max-w-[200px]" title={task.payload?.query}>
                        {task.payload?.query || '—'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link href={`/expert/${task.id}`} className="text-xs font-medium text-primary hover:underline">
                          Review
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* ROW 5: RAG Evaluation summary */}
        <Card className="border shadow-sm flex flex-col">
          <div className="p-4 border-b bg-muted/20 flex justify-between items-center">
            <h2 className="text-sm font-semibold uppercase tracking-wider flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              Recent Evaluations
            </h2>
            <Link href="/admin/evaluation" className="text-xs text-primary font-medium hover:underline flex items-center">
              View All <ArrowRight className="h-3 w-3 ml-1" />
            </Link>
          </div>
          <div className="p-0 overflow-x-auto flex-1">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-muted-foreground uppercase border-b bg-muted/10">
                <tr>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Model</th>
                  <th className="px-4 py-2 font-medium text-center">Score</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">Loading evaluations...</td>
                  </tr>
                ) : evals.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">No recent evaluation runs.</td>
                  </tr>
                ) : (
                  evals.map(run => (
                    <tr key={run.id} className="border-b hover:bg-muted/30 last:border-0">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Badge variant="outline" className={`text-[10px] uppercase font-mono ${
                          run.status === 'COMPLETED' ? 'border-green-500/50 text-green-500' : 
                          run.status === 'FAILED' ? 'border-destructive/50 text-destructive' : 'border-blue-500/50 text-blue-500'
                        }`}>
                          {run.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {run.evaluator_model}
                        <div className="text-muted-foreground text-[10px]">v{run.dataset_version}</div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`font-mono font-medium ${
                          run.overall_score >= 0.8 ? 'text-green-600' :
                          run.overall_score >= 0.5 ? 'text-amber-600' : 'text-destructive'
                        }`}>
                          {(run.overall_score * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
