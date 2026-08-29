"use client"

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api-client';

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

  const handleAction = async (decision: 'APPROVE' | 'CORRECT') => {
    setSubmitting(true);
    try {
      const payload = {
        decision,
        corrected_answer: decision === 'CORRECT' ? correctedAnswer : null,
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

  if (loading) return <div className="p-8 text-center">Loading task...</div>;
  if (error && !task) return <div className="p-8 text-center text-destructive">{error}</div>;

  return (
    <div className="container max-w-5xl py-8 space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Review Task</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            ID: {task.id}
          </p>
        </div>
        <Badge variant={task.status === 'PENDING' ? 'default' : 'secondary'} className="text-sm px-3 py-1">
          {task.status}
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Escalation Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-muted-foreground">Reason for Escalation</Label>
                <div className="font-medium mt-1 p-3 bg-destructive/10 text-destructive rounded-md">
                  {task.reason}
                </div>
              </div>
              
              <div className="pt-4">
                <Label className="text-muted-foreground">User Query</Label>
                <div className="font-medium mt-1 p-3 bg-muted rounded-md text-sm">
                  {task.payload?.query || "No query available"}
                </div>
              </div>

              <div className="pt-4">
                <Label className="text-muted-foreground">System Generated Answer</Label>
                <div className="font-medium mt-1 p-3 border rounded-md text-sm bg-card whitespace-pre-wrap">
                  {task.payload?.generated_answer || "No answer available"}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Evidence & Sources</CardTitle>
            </CardHeader>
            <CardContent>
              {task.payload?.citations?.length > 0 ? (
                <div className="space-y-4">
                  {task.payload.citations.map((cite: any, i: number) => (
                    <div key={i} className="text-sm border-l-2 border-primary pl-4">
                      <p className="font-medium text-foreground">{cite.document_id} (Page {cite.page_number})</p>
                      <p className="text-muted-foreground mt-1">{cite.text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">No evidence provided.</div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="border-primary/50 shadow-sm">
            <CardHeader>
              <CardTitle>Expert Action</CardTitle>
              <CardDescription>Determine the correct response</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {error && <div className="text-sm text-destructive font-medium">{error}</div>}
              
              <div className="space-y-2">
                <Label>Expert Comment (Optional)</Label>
                <Textarea 
                  placeholder="Notes on your decision..." 
                  value={comment}
                  onChange={e => setComment(e.target.value)}
                  disabled={task.status !== 'PENDING' && task.status !== 'IN_REVIEW'}
                />
              </div>

              <div className="space-y-2">
                <Label>Corrected Answer</Label>
                <Textarea 
                  className="min-h-[150px]"
                  placeholder="If correcting, provide the new answer here..."
                  value={correctedAnswer}
                  onChange={e => setCorrectedAnswer(e.target.value)}
                  disabled={task.status !== 'PENDING' && task.status !== 'IN_REVIEW'}
                />
              </div>

              {(task.status === 'PENDING' || task.status === 'IN_REVIEW') && (
                <div className="flex flex-col gap-3 pt-4 border-t">
                  <Button 
                    className="w-full" 
                    variant="default"
                    disabled={submitting}
                    onClick={() => handleAction('APPROVE')}
                  >
                    Approve Original Answer
                  </Button>
                  <Button 
                    className="w-full" 
                    variant="destructive"
                    disabled={submitting}
                    onClick={() => handleAction('CORRECT')}
                  >
                    Submit Correction
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
