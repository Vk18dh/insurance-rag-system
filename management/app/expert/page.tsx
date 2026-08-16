"use client"

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';

export default function ExpertDashboard() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await apiClient.fetchWithAuth('/expert/reviews');
      const data = await response.json();
      setTasks(data);
    } catch (e) {
      console.error("Failed to fetch review tasks", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container max-w-6xl py-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Review Queue</h1>
          <p className="text-muted-foreground mt-1">
            Manage escalated tasks requiring human-in-the-loop review.
          </p>
        </div>
        <Button onClick={fetchTasks} variant="outline" disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      <div className="grid gap-4">
        {loading && tasks.length === 0 ? (
          <div className="text-center p-8 text-muted-foreground border rounded-xl">
            Loading tasks...
          </div>
        ) : tasks.length === 0 ? (
          <div className="text-center p-12 border border-dashed rounded-xl bg-card">
            <h3 className="text-lg font-medium">All caught up!</h3>
            <p className="text-muted-foreground">No tasks currently require your review.</p>
          </div>
        ) : (
          tasks.map((task) => (
            <Card key={task.id} className="overflow-hidden transition-colors hover:bg-accent/50">
              <CardHeader className="flex flex-row items-center justify-between p-6">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg">Escalation Task</CardTitle>
                    <Badge variant={task.status === 'PENDING' ? 'default' : 'secondary'}>
                      {task.status}
                    </Badge>
                  </div>
                  <CardDescription>
                    Created {new Date(task.created_at).toLocaleString()}
                  </CardDescription>
                </div>
                <Button asChild>
                  <Link href={`/expert/${task.id}`}>
                    Review Case
                  </Link>
                </Button>
              </CardHeader>
              <CardContent className="px-6 pb-6 pt-0">
                <div className="text-sm bg-muted p-4 rounded-md">
                  <span className="font-semibold text-muted-foreground">Reason:</span> {task.reason}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
