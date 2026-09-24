"use client"

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import { ArrowLeft, AlertTriangle, FileText, CheckCircle, Info } from 'lucide-react';

export default function ReviewTaskDetail({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const taskId = resolvedParams.id;
  const router = useRouter();
  const [task, setTask] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [correctedAnswer, setCorrectedAnswer] = useState('');
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'APPROVE' | 'CORRECT'>('APPROVE');

  useEffect(() => {
    fetchTask();
  }, [taskId]);

  const fetchTask = async () => {
    try {
      const data = await apiClient.fetchWithAuth(`/expert/reviews/${taskId}`);
      if (!data) {
        throw new Error("Failed to fetch task");
      }
      setTask(data);
      if (data.payload?.generated_answer) {
        setCorrectedAnswer(data.payload.generated_answer);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async () => {
    setSubmitting(true);
    try {
      const payload = {
        decision: activeTab,
        corrected_answer: activeTab === 'CORRECT' ? correctedAnswer : null,
        comment: comment || null
      };
      
      const data = await apiClient.fetchWithAuth(`/expert/reviews/${taskId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!data) throw new Error("Action failed");
      router.push('/expert');
    } catch (e: any) {
      setError(e.message);
      setSubmitting(false);
    }
  };

  if (loading) return (
    <div className="container max-w-[1400px] py-8 space-y-6">
      <div className="animate-pulse space-y-4">
        <div className="h-4 w-32 bg-muted rounded"></div>
        <div className="h-8 w-64 bg-muted rounded"></div>
        <div className="h-[400px] bg-muted/50 rounded-lg"></div>
      </div>
    </div>
  );

  if (error && !task) return (
    <div className="container max-w-[1400px] py-8">
      <div className="p-4 bg-destructive/10 text-destructive rounded-md border border-destructive/20 flex items-center gap-3">
        <AlertTriangle className="h-5 w-5" />
        <p className="font-medium">{error}</p>
      </div>
      <Button variant="outline" className="mt-4" onClick={() => router.push('/expert')}>
        Return to Queue
      </Button>
    </div>
  );

  const isResolved = task.status !== 'PENDING' && task.status !== 'IN_REVIEW';

  return (
    <div className="container max-w-[1400px] py-8 space-y-6">
      <div className="flex flex-col gap-1">
        <Link href="/expert" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors w-fit">
          <ArrowLeft className="h-4 w-4" />
          Back to Review Queue
        </Link>
        <div className="flex justify-between items-end mt-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
              Review Task
              <Badge variant={task.status === 'PENDING' ? 'default' : 'secondary'} className="text-xs px-2 py-0.5 rounded-sm font-medium">
                {task.status}
              </Badge>
            </h1>
            <p className="text-xs text-muted-foreground mt-1 font-mono">
              ID: {task.id} • Created: {new Date(task.created_at).toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <div className="lg:col-span-2 space-y-8">
          
          {/* Case Information */}
          <section className="space-y-4">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider border-b pb-2">Case Information</h2>
            
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-destructive uppercase tracking-wide">Escalation Reason</p>
                <p className="text-sm text-destructive mt-1">{task.reason}</p>
                {task.payload?.confidence !== undefined && (
                  <p className="text-xs text-destructive/80 mt-1 font-mono">Confidence: {Number(task.payload.confidence).toFixed(2)}</p>
                )}
              </div>
            </div>

            <div className="space-y-2 pt-2">
              <Label className="text-xs text-muted-foreground uppercase tracking-wider">User Query</Label>
              <div className="p-4 bg-muted/50 border rounded-md text-sm font-medium">
                {task.payload?.query || "—"}
              </div>
            </div>

            <div className="space-y-2 pt-2">
              <Label className="text-xs text-muted-foreground uppercase tracking-wider">System Response</Label>
              <div className="p-4 bg-card border rounded-md text-sm whitespace-pre-wrap leading-relaxed">
                {task.payload?.generated_answer || "—"}
              </div>
            </div>
          </section>

          {/* Evidence */}
          <section className="space-y-4">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider border-b pb-2">Retrieved Evidence</h2>
            
            {task.payload?.citations?.length > 0 ? (
              <div className="space-y-3">
                {task.payload.citations.map((cite: any, i: number) => (
                  <div key={i} className="p-4 border rounded-md bg-card/50 text-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="h-4 w-4 text-primary" />
                      <span className="font-semibold">{cite.document_id}</span>
                      <span className="text-muted-foreground text-xs bg-muted px-2 py-0.5 rounded">Page {cite.page_number}</span>
                    </div>
                    <p className="text-muted-foreground leading-relaxed pl-6 border-l-2 border-primary/20">{cite.text}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 border border-dashed rounded-md text-center text-sm text-muted-foreground bg-muted/20 flex flex-col items-center gap-2">
                <Info className="h-5 w-5" />
                No retrieval evidence available for this case.
              </div>
            )}
          </section>
        </div>

        {/* Expert Action Panel */}
        <div className="lg:sticky lg:top-8">
          <section className="border bg-card rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b bg-muted/30">
              <h2 className="text-sm font-semibold uppercase tracking-wider">Expert Decision</h2>
            </div>
            
            <div className="p-5 space-y-6">
              {error && (
                <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-md border border-destructive/20">
                  {error}
                </div>
              )}

              {!isResolved && (
                <div className="flex gap-2 p-1 bg-muted rounded-md">
                  <button 
                    className={`flex-1 text-sm font-medium py-1.5 rounded transition-colors ${activeTab === 'APPROVE' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                    onClick={() => setActiveTab('APPROVE')}
                  >
                    Approve Original
                  </button>
                  <button 
                    className={`flex-1 text-sm font-medium py-1.5 rounded transition-colors ${activeTab === 'CORRECT' ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                    onClick={() => setActiveTab('CORRECT')}
                  >
                    Provide Correction
                  </button>
                </div>
              )}

              {isResolved && (
                <div className="p-3 bg-secondary/50 text-secondary-foreground text-sm rounded-md border flex items-start gap-2">
                  <CheckCircle className="h-4 w-4 mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium">Task Resolved</p>
                    <p className="text-muted-foreground mt-1 text-xs">Decision: {task.expert_decision || 'Unknown'}</p>
                  </div>
                </div>
              )}
              
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground uppercase tracking-wider">Internal Comment</Label>
                  <Textarea 
                    className="min-h-[80px] text-sm resize-none"
                    placeholder={isResolved ? "No comment provided." : "Notes on your decision (optional)..."} 
                    value={isResolved ? (task.expert_comment || '') : comment}
                    onChange={e => setComment(e.target.value)}
                    disabled={isResolved}
                  />
                </div>

                {(activeTab === 'CORRECT' || (isResolved && task.corrected_answer)) && (
                  <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
                    <Label className="text-xs text-muted-foreground uppercase tracking-wider">Corrected Answer</Label>
                    <Textarea 
                      className="min-h-[150px] text-sm leading-relaxed"
                      placeholder="Write the correct response for the user here..."
                      value={isResolved ? task.corrected_answer : correctedAnswer}
                      onChange={e => setCorrectedAnswer(e.target.value)}
                      disabled={isResolved}
                    />
                  </div>
                )}
              </div>

              {!isResolved && (
                <div className="pt-2">
                  <Button 
                    className="w-full" 
                    variant={activeTab === 'APPROVE' ? 'default' : 'destructive'}
                    disabled={submitting || (activeTab === 'CORRECT' && !correctedAnswer.trim())}
                    onClick={handleAction}
                  >
                    {submitting ? 'Submitting...' : activeTab === 'APPROVE' ? 'Approve Original Answer' : 'Submit Correction'}
                  </Button>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
