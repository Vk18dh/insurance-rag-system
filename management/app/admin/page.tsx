"use client"

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { Activity, Users, FileText, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [providerHealth, setProviderHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [metricsRes, healthRes] = await Promise.all([
        apiClient.fetchWithAuth('/admin/metrics'),
        apiClient.fetchWithAuth('/admin/provider-health')
      ]);

      if (!metricsRes.ok || !healthRes.ok) throw new Error("Failed to fetch admin data");
      
      setMetrics(await metricsRes.json());
      setProviderHealth(await healthRes.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-muted-foreground">Loading admin dashboard...</div>;
  if (error) return <div className="p-8 text-center text-destructive">{error}</div>;

  return (
    <div className="container max-w-6xl py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          System observability and metrics.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.active_users || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Queries Today</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.queries_today || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Escalation Rate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(metrics?.escalation_rate * 100).toFixed(1) || 0}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.avg_latency_ms || 0}ms</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>Overall application health</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              {metrics?.system_status === 'healthy' ? (
                <CheckCircle className="h-8 w-8 text-green-500" />
              ) : (
                <XCircle className="h-8 w-8 text-destructive" />
              )}
              <div>
                <p className="text-lg font-medium capitalize">{metrics?.system_status || 'Unknown'}</p>
                <p className="text-sm text-muted-foreground">Core services are operational</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>LLM Provider Health</CardTitle>
            <CardDescription>Primary and failover status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <span className="font-medium capitalize">{providerHealth?.primary_provider} (Primary)</span>
              <span className={`text-sm ${providerHealth?.primary_status === 'AVAILABLE' ? 'text-green-500' : 'text-destructive'}`}>
                {providerHealth?.primary_status}
              </span>
            </div>
            <div className="flex justify-between items-center border-b pb-2">
              <span className="font-medium capitalize">{providerHealth?.secondary_provider} (Secondary)</span>
              <span className={`text-sm ${providerHealth?.secondary_status === 'AVAILABLE' ? 'text-green-500' : 'text-destructive'}`}>
                {providerHealth?.secondary_status}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-medium">Failover Events (24h)</span>
              <span className="text-sm text-muted-foreground font-bold">
                {providerHealth?.failover_events_24h || 0}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
