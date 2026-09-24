"use client"

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { Loader2, PlayCircle, BarChart3, RefreshCcw, ArrowRight } from 'lucide-react';
import { Button, buttonVariants } from '@/components/ui/button';
import Link from 'next/link';

export default function EvaluationDashboard() {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  const fetchRuns = async () => {
    try {
      const data = await apiClient.fetchWithAuth('/admin/evaluations');
      setRuns(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  const triggerEvaluation = async () => {
    try {
      setTriggering(true);
      await apiClient.fetchWithAuth('/admin/evaluations', {
        method: 'POST'
      });
      await fetchRuns();
    } catch (e) {
      alert("Failed to trigger evaluation");
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="container max-w-[1400px] py-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">RAG Evaluation</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Offline evaluation using local Ollama model
          </p>
        </div>
      </div>

      <Card className="border shadow-sm">
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-b gap-4 bg-card/50">
          <div className="text-sm text-muted-foreground font-medium flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Evaluation Runs
          </div>
          <div className="flex gap-2 w-full sm:w-auto">
            <Button 
              onClick={fetchRuns}
              variant="outline"
              size="sm"
              disabled={loading}
              className="h-9"
            >
              <RefreshCcw className={`h-4 w-4 mr-2 ${loading && !triggering ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button 
              onClick={triggerEvaluation}
              disabled={triggering}
              size="sm"
              className="h-9"
            >
              {triggering ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : <PlayCircle className="mr-2 h-4 w-4" />}
              Run Evaluation
            </Button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b">
              <tr>
                <th className="px-6 py-3 font-medium">Run ID</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Model & Dataset</th>
                <th className="px-6 py-3 font-medium">Started At</th>
                <th className="px-6 py-3 font-medium text-center">Score</th>
                <th className="px-6 py-3 font-medium text-center">Passed / Total</th>
                <th className="px-6 py-3 font-medium text-right">Report</th>
              </tr>
            </thead>
            <tbody>
              {loading && runs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-muted-foreground">
                    <div className="flex justify-center items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading evaluation history...
                    </div>
                  </td>
                </tr>
              ) : runs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-muted-foreground">
                    No evaluation runs yet.
                  </td>
                </tr>
              ) : (
                runs.map(run => (
                  <tr key={run.id} className="border-b hover:bg-muted/30 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-xs font-medium">
                      {run.id.split('-')[0]}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <div className={`h-2 w-2 rounded-full ${
                          run.status === 'COMPLETED' ? 'bg-green-500' : 
                          run.status === 'FAILED' ? 'bg-destructive' : 
                          'bg-blue-500 animate-pulse'
                        }`} />
                        <span className="text-xs font-medium capitalize">{run.status.toLowerCase()}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      <div className="font-medium">{run.evaluator_model}</div>
                      <div className="text-muted-foreground">v{run.dataset_version}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-muted-foreground">
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className={`font-mono font-medium ${
                        run.overall_score >= 0.8 ? 'text-green-600' :
                        run.overall_score >= 0.5 ? 'text-amber-600' : 'text-destructive'
                      }`}>
                        {(run.overall_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-xs">
                      {run.status === 'COMPLETED' ? (
                        <span className="font-mono">
                          <span className="text-green-600 font-medium">{run.passed_cases}</span>
                          <span className="text-muted-foreground mx-1">/</span>
                          <span>{run.total_cases}</span>
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      {run.status === 'COMPLETED' ? (
                        <Link href={`/admin/evaluation/${run.id}`} className={buttonVariants({ variant: 'secondary', size: 'sm' })}>
                          View
                          <ArrowRight className="h-3 w-3 ml-1" />
                        </Link>
                      ) : (
                        <Button variant="ghost" size="sm" disabled>Wait</Button>
                      )}
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
