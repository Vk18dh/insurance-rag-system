"use client"

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { Loader2, ArrowLeft, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

export default function EvaluationDetail() {
  const params = useParams();
  const runId = params?.id as string;
  const [run, setRun] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!runId) return;
    
    const fetchRun = async () => {
      try {
        const data = await apiClient.fetchWithAuth(`/admin/evaluations/${runId}`);
        setRun(data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchRun();
  }, [runId]);

  if (loading) return (
    <div className="container max-w-[1400px] py-8 space-y-6">
      <div className="animate-pulse space-y-4">
        <div className="h-4 w-32 bg-muted rounded"></div>
        <div className="h-8 w-64 bg-muted rounded"></div>
        <div className="h-[400px] bg-muted/50 rounded-lg"></div>
      </div>
    </div>
  );

  if (error || !run) return (
    <div className="container max-w-[1400px] py-8">
      <div className="p-4 bg-destructive/10 text-destructive rounded-md border border-destructive/20 flex items-center gap-3">
        <AlertTriangle className="h-5 w-5" />
        <p className="font-medium">{error || "Evaluation run not found"}</p>
      </div>
      <Link href="/admin/evaluation" className="mt-4 inline-flex items-center text-sm font-medium hover:underline">
        <ArrowLeft className="h-4 w-4 mr-1" /> Return to Evaluations
      </Link>
    </div>
  );

  return (
    <div className="container max-w-[1400px] py-8 space-y-6">
      <div className="flex flex-col gap-1">
        <Link href="/admin/evaluation" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors w-fit">
          <ArrowLeft className="h-4 w-4" />
          Back to Evaluations
        </Link>
        <div className="flex justify-between items-end mt-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
              Run Details: {run.id.split('-')[0]}
              <Badge variant={run.status === 'COMPLETED' ? 'default' : run.status === 'FAILED' ? 'destructive' : 'secondary'} className="text-xs px-2 py-0.5 rounded-sm font-medium">
                {run.status}
              </Badge>
            </h1>
            <p className="text-sm text-muted-foreground mt-1 flex gap-4 font-mono">
              <span>Overall Score: {(run.overall_score * 100).toFixed(0)}%</span>
              <span>•</span>
              <span>Dataset: v{run.dataset_version}</span>
              <span>•</span>
              <span>Date: {new Date(run.started_at).toLocaleString()}</span>
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {run.results?.map((res: any, idx: number) => (
          <Card key={res.id} className="border shadow-sm overflow-hidden flex flex-col md:flex-row">
            <div className={`w-1.5 shrink-0 ${res.passed ? 'bg-green-500' : 'bg-destructive'}`} />
            
            <div className="flex-1 p-0">
              <div className="flex items-center justify-between p-4 border-b bg-muted/20">
                <div className="flex items-center gap-3">
                  {res.passed ? <CheckCircle2 className="text-green-500 h-5 w-5"/> : <XCircle className="text-destructive h-5 w-5"/>}
                  <span className="font-semibold text-sm">Case {idx+1}: <span className="font-mono font-normal text-muted-foreground">{res.case_id}</span></span>
                  <Badge variant="outline" className="capitalize text-xs rounded-sm font-normal text-muted-foreground bg-background">
                    {res.category.replace('_', ' ')}
                  </Badge>
                </div>
              </div>
              
              <div className="p-5 grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Query</h4>
                    <p className="text-sm font-medium bg-muted/40 p-3 rounded-md border">{res.query}</p>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Generated Answer</h4>
                    <p className="text-sm whitespace-pre-wrap leading-relaxed text-muted-foreground bg-card p-3 rounded-md border">{res.generated_answer}</p>
                  </div>
                </div>
                
                <div className="space-y-6 border-t lg:border-t-0 pt-6 lg:pt-0">
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Evaluator Reason</h4>
                    <p className="text-sm leading-relaxed">{res.evaluator_reason}</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-muted/20 rounded-md border">
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Metrics</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between items-center"><span className="text-muted-foreground">Retrieval</span> <span className="font-mono font-medium">{res.retrieval_score}</span></div>
                        <div className="flex justify-between items-center"><span className="text-muted-foreground">Relevance</span> <span className="font-mono font-medium">{res.relevance_score}</span></div>
                        <div className="flex justify-between items-center"><span className="text-muted-foreground">Faithful</span> <span className="font-mono font-medium">{res.faithfulness_score}</span></div>
                        <div className="flex justify-between items-center"><span className="text-muted-foreground">Hallucination</span> <span className="font-mono font-medium">{res.hallucination_score}</span></div>
                      </div>
                    </div>
                    
                    <div className="p-3 bg-muted/20 rounded-md border">
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">HITL Isolation</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Expected</span> 
                          <Badge variant={res.hitl_expected ? "default" : "secondary"} className="text-[10px] uppercase">{res.hitl_expected ? 'Yes' : 'No'}</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Actual</span> 
                          <Badge variant={res.hitl_actual ? "default" : "secondary"} className="text-[10px] uppercase">{res.hitl_actual ? 'Yes' : 'No'}</Badge>
                        </div>
                        <div className="text-xs text-muted-foreground mt-3 pt-3 border-t">Production DB isolated.</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
