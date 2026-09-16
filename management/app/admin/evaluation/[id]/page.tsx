"use client"

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import { Loader2, ArrowLeft, CheckCircle2, XCircle } from 'lucide-react';

export default function EvaluationDetail() {
  const params = useParams();
  const runId = params?.id as string;
  const [run, setRun] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!runId) return;
    
    const fetchRun = async () => {
      try {
        const data = await apiClient.fetchWithAuth(`/admin/evaluations/${runId}`);
        setRun(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchRun();
  }, [runId]);

  if (loading) return <div className="p-8 text-center text-muted-foreground"><Loader2 className="animate-spin inline mr-2"/>Loading details...</div>;
  if (!run) return <div className="p-8 text-center text-destructive">Evaluation run not found</div>;

  return (
    <div className="container max-w-6xl py-8 space-y-6">
      <div className="flex items-center space-x-4">
        <a href="/admin/evaluation" className="p-2 hover:bg-secondary rounded-full">
          <ArrowLeft className="h-5 w-5" />
        </a>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Run Details: {run.id.split('-')[0]}</h1>
          <p className="text-muted-foreground mt-1">
            Overall Score: {(run.overall_score * 100).toFixed(0)}% | Dataset: v{run.dataset_version} | Status: {run.status}
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {run.results?.map((res: any, idx: number) => (
          <Card key={res.id} className="overflow-hidden border-l-4" style={{borderLeftColor: res.passed ? '#22c55e' : '#ef4444'}}>
            <CardHeader className="bg-secondary/30 pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center space-x-2">
                  <span className="text-sm px-2 py-1 bg-background rounded border text-muted-foreground font-mono">Case {idx+1}: {res.case_id}</span>
                  <span className="text-sm font-normal text-muted-foreground capitalize">({res.category.replace('_', ' ')})</span>
                </CardTitle>
                {res.passed ? <CheckCircle2 className="text-green-500 h-6 w-6"/> : <XCircle className="text-red-500 h-6 w-6"/>}
              </div>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-muted-foreground uppercase mb-2">Query</h4>
                <p className="text-lg font-medium">{res.query}</p>
              </div>
              
              <div className="grid md:grid-cols-2 gap-6 bg-muted/20 p-4 rounded-lg">
                <div>
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase mb-2">Generated Answer</h4>
                  <p className="text-sm whitespace-pre-wrap">{res.generated_answer}</p>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-muted-foreground uppercase mb-2">Evaluator Reason</h4>
                  <p className="text-sm">{res.evaluator_reason}</p>
                  
                  <div className="mt-4 pt-4 border-t border-border/50">
                    <h4 className="text-sm font-semibold text-muted-foreground uppercase mb-2">Metrics</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex justify-between"><span>Retrieval:</span> <span className="font-mono">{res.retrieval_score}</span></div>
                      <div className="flex justify-between"><span>Relevance:</span> <span className="font-mono">{res.relevance_score}</span></div>
                      <div className="flex justify-between"><span>Faithful:</span> <span className="font-mono">{res.faithfulness_score}</span></div>
                      <div className="flex justify-between"><span>Hallucination:</span> <span className="font-mono">{res.hallucination_score}</span></div>
                    </div>
                  </div>
                  
                  <div className="mt-4 pt-4 border-t border-border/50">
                    <h4 className="text-sm font-semibold text-muted-foreground uppercase mb-2">HITL Isolation</h4>
                    <div className="text-sm">
                      <span className="font-medium text-amber-600">Expected:</span> {res.hitl_expected ? 'Yes' : 'No'} | 
                      <span className="font-medium text-amber-600 ml-2">Actual Captured:</span> {res.hitl_actual ? 'Yes' : 'No'}
                      <div className="text-xs text-muted-foreground mt-1">(Production DB unmodified)</div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
