"use client"

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { AnimatePresence, motion } from 'motion/react';
import { ArrowUp, CornerDownLeft, Search, TriangleAlert, User, ShieldCheck } from 'lucide-react';
import { apiClient, QueryResponse, MessageResponse } from '@/lib/api-client';
import { AnswerDisplay } from '@/components/answer-display';
import { AnswerSkeleton } from '@/components/answer-skeleton';
import { MetricsPanel } from '@/components/metrics-panel';
import { CitationsPanel } from '@/components/citations-panel';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const EXAMPLES = [
  "What is the waiting period for the basic health insurance?",
  "Are pre-existing conditions covered under the standard tier?",
  "What documentation is required to file an accidental injury claim?",
];

interface ChatInterfaceProps {
  conversationId?: string;
  initialMessages?: MessageResponse[];
}

export function ChatInterface({ conversationId, initialMessages = [] }: ChatInterfaceProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // To handle rendering multiple pairs, we can store history locally or just display a single response if the backend only gives FinalResponse.
  // Wait, if we use the backend, we get a list of messages. However, `FinalResponse` (citations, metrics) is only returned from the POST `/query` endpoint, it's not saved in the `messages` history natively, or is it?
  // Let's check `MessageResponse` from backend: `id`, `role`, `content`. It doesn't have citations.
  // The PRD says: "Agentic RAG Response... Render the actual backend FinalResponse". 
  // If the user visits an old chat, we only have `content`. 
  // For the active query, we have `QueryResponse` with citations.
  
  const [messages, setMessages] = useState<MessageResponse[]>(initialMessages);
  const [lastResult, setLastResult] = useState<QueryResponse | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, lastResult]);

  async function submit(value: string) {
    const q = value.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    setLastResult(null);
    
    // Add optimistic user message
    const tempUserMsgId = Date.now().toString();
    setMessages(prev => [...prev, { id: tempUserMsgId, role: 'user', content: q }]);
    setQuery('');

    try {
      const data = await apiClient.postQuery({
        query: q,
        conversation_id: conversationId || null,
      });

      // If it's a new conversation, redirect to its URL
      if (!conversationId && data.conversation_id) {
        // We push to the new URL, but we also want to display the result immediately so it doesn't flicker.
        router.push(`/c/${data.conversation_id}`);
      }

      setLastResult(data);
      // Backend automatically appends the assistant message, we will fetch it when the page reloads, but for now we append optimistically
      setMessages(prev => [...prev, { id: data.query_id, role: 'assistant', content: data.final_answer }]);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    submit(query);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      if (e.nativeEvent.isComposing || e.keyCode === 229) return;
      e.preventDefault();
      submit(query);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 pb-32">
        <div className="mx-auto max-w-4xl space-y-8">
          {messages.length === 0 && !loading && !lastResult && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="flex flex-col items-center pt-16 text-center sm:pt-24"
            >
              <span className="glass mb-5 inline-flex items-center gap-2 rounded-full border border-border/60 px-3 py-1 font-mono text-xs text-muted-foreground">
                <span className="size-1.5 rounded-full bg-accent" />
                Agentic RAG · Grounded Citations
              </span>
              <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-6xl">AI Insurance Auditor</h1>
              <p className="mt-4 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
                Query regulatory policies and insurance rules with guaranteed citations.
              </p>
              
              <div className="mt-8 flex flex-wrap justify-center gap-2 max-w-2xl">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    type="button"
                    onClick={() => {
                      setQuery(ex);
                      submit(ex);
                    }}
                    disabled={loading}
                    className="glass rounded-full border border-border/60 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground disabled:opacity-50"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {messages.map((msg, idx) => {
            const isLastMessage = idx === messages.length - 1;
            const isAssistant = msg.role === 'assistant';
            
            return (
              <div key={msg.id} className={`flex gap-4 ${isAssistant ? '' : 'flex-row-reverse'}`}>
                <div className={`flex size-8 shrink-0 items-center justify-center rounded-full ${isAssistant ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'}`}>
                  {isAssistant ? <ShieldCheck className="size-4" /> : <User className="size-4" />}
                </div>
                <div className={`flex flex-col gap-2 max-w-[85%] ${isAssistant ? '' : 'items-end'}`}>
                  <div className={`rounded-2xl px-4 py-3 ${isAssistant ? 'glass border border-border/50' : 'bg-primary text-primary-foreground'}`}>
                    <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
                      {msg.content}
                    </div>
                  </div>
                  
                  {isAssistant && isLastMessage && lastResult && (
                    <div className="grid gap-5 lg:grid-cols-[1fr_340px] mt-4 w-full">
                      <div className="flex flex-col gap-5">
                         <MetricsPanel result={lastResult} />
                         <CitationsPanel sources={lastResult.sources} />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex gap-4">
              <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <ShieldCheck className="size-4" />
              </div>
              <div className="max-w-[85%]">
                <AnswerSkeleton />
              </div>
            </div>
          )}

          {error && !loading && (
            <div className="flex justify-center">
              <Alert variant="destructive" className="glass max-w-2xl border-destructive/40">
                <TriangleAlert className="size-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background via-background to-transparent pt-6 pb-6 px-4 sm:px-6 z-20">
        <div className="mx-auto w-full max-w-3xl">
          <form onSubmit={handleSubmit}>
            <div className="glass group rounded-2xl border border-border/70 p-2 shadow-xl shadow-primary/5 transition-colors focus-within:border-primary/60 bg-background/80 backdrop-blur-xl">
              <div className="flex items-start gap-3 px-3 pt-2.5">
                <Search className="mt-1 size-5 shrink-0 text-muted-foreground" />
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={2}
                  placeholder="Ask about policy clauses, waiting periods, exclusions, or compliance rules…"
                  className="max-h-40 min-h-11 w-full resize-none bg-transparent text-[15px] leading-relaxed outline-none placeholder:text-muted-foreground"
                  aria-label="Insurance policy query"
                />
              </div>
              <div className="flex items-center justify-between px-3 pb-1.5 pt-1">
                <span className="hidden items-center gap-1.5 font-mono text-[11px] text-muted-foreground sm:flex">
                  <CornerDownLeft className="size-3" />
                  Enter to send · Shift + Enter for newline
                </span>
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="ml-auto inline-flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {loading ? "Sending..." : "Send"}
                  <ArrowUp className="size-4" />
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
