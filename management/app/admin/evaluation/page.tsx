"use client"

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { Loader2, PlayCircle, BarChart3 } from 'lucide-react';

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

  if (loading) return <div className="p-8 text-center text-muted-foreground"><Loader2 className="animate-spin inline mr-2"/>Loading evaluations...</div>;

  return (
    <div className="container max-w-6xl py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">RAG Evaluation</h1>
          <p className="text-muted-foreground mt-1">
            Offline evaluation using local Ollama model.
          </p>
        </div>
        <button 
          onClick={triggerEvaluation}
          disabled={triggering}
          className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center justify-center rounded-md text-sm font-medium h-10 px-4 py-2 disabled:opacity-50"
        >
          {triggering ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : <PlayCircle className="mr-2 h-4 w-4" />}
          Run Evaluation
        </button>
      </div>

      <div className="space-y-4">
        {runs.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground bg-muted/20 rounded-lg">
            <BarChart3 className="mx-auto h-12 w-12 opacity-20 mb-4" />
            <p>No evaluation runs yet.</p>
          </div>
        ) : (
          runs.map(run => (
            <Card key={run.id} className="overflow-hidden">
              <div className={`h-1 w-full ${run.status === 'COMPLETED' ? 'bg-green-500' : run.status === 'FAILED' ? 'bg-red-500' : 'bg-blue-500 animate-pulse'}`} />
              <CardContent className="p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-lg flex items-center">
                      Run {run.id.split('-')[0]}
                      <span className="ml-3 text-xs px-2 py-1 bg-secondary rounded-full font-mono">{run.status}</span>
                    </h3>
                    <div className="text-sm text-muted-foreground mt-1 space-x-4">
                      <span>Started: {new Date(run.started_at).toLocaleString()}</span>
                      <span>Model: {run.evaluator_model}</span>
                      <span>Dataset: v{run.dataset_version}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold">{(run.overall_score * 100).toFixed(0)}%</div>
                    <div className="text-sm text-muted-foreground">Overall Score</div>
                  </div>
                </div>
                
                {run.status === 'COMPLETED' && (
                  <div className="mt-6 pt-6 border-t flex items-center justify-between">
                    <div className="flex space-x-8 text-sm">
                      <div>
                        <div className="text-muted-foreground">Cases</div>
                        <div className="font-medium text-lg">{run.total_cases}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Passed</div>
                        <div className="font-medium text-lg text-green-600">{run.passed_cases}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Failed</div>
                        <div className="font-medium text-lg text-red-600">{run.failed_cases}</div>
                      </div>
                    </div>
                    <a href={`/admin/evaluation/${run.id}`} className="text-primary hover:underline text-sm font-medium">
                      View Detail Report &rarr;
                    </a>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
