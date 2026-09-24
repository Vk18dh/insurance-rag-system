"use client"

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { AnimatePresence, motion } from 'motion/react';
import { ArrowUp, Search, User, ShieldCheck, Sparkles, Copy, RotateCcw, ChevronRight, X, Paperclip, FileText, CheckCircle2, ShieldAlert, AlertTriangle } from 'lucide-react';
import { apiClient, QueryResponse, MessageResponse, ReviewTaskResponse, RetrievedSource } from '@/lib/api-client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Chat3DBackground } from './chat-3d-background';

const EXAMPLES = [
  "What is the waiting period for pre-existing conditions?",
  "What are the key benefits of LIC Bima Jyoti?",
  "What is the surrender value under this policy?",
  "What documents are required for an accidental injury claim?",
];

const PROCESSING_STAGES = [
  "Analyzing your question...",
  "Retrieving relevant policy documents...",
  "Checking evidence...",
  "Preparing grounded response..."
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
  
  const [messages, setMessages] = useState<MessageResponse[]>(initialMessages);
  const [lastResult, setLastResult] = useState<QueryResponse | null>(null);
  const [reviewTasks, setReviewTasks] = useState<ReviewTaskResponse[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [loadingStage, setLoadingStage] = useState(0);
  const [activeSource, setActiveSource] = useState<RetrievedSource | null>(null);

  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);

  useEffect(() => {
    try {
      const tempResult = sessionStorage.getItem('temp_last_result');
      if (tempResult) {
        setLastResult(JSON.parse(tempResult));
        sessionStorage.removeItem('temp_last_result');
      }
    } catch (e) { }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, loading, lastResult, error]);

  useEffect(() => {
    if (!loading) {
      setLoadingStage(0);
      return;
    }
    const interval = setInterval(() => {
      setLoadingStage(prev => Math.min(prev + 1, PROCESSING_STAGES.length - 1));
    }, 1500);
    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    if (!conversationId) {
      setReviewTasks([]);
      return;
    }

    let isMounted = true;
    const fetchReviews = async () => {
      try {
        const data = await apiClient.getConversationReviews(conversationId);
        if (isMounted) setReviewTasks(data);
      } catch (e: any) {
        if (e.message === 'Failed to fetch' || e.name === 'TypeError') return;
      }
    };

    fetchReviews();
    const intervalId = setInterval(fetchReviews, 3000);
    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [conversationId]);

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  async function submit(value: string) {
    const q = value.trim();
    if (!q || loading) return;
    
    setLoading(true);
    setError(null);
    setLastResult(null);
    
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    const tempUserMsgId = Date.now().toString();
    setMessages(prev => [...prev, { id: tempUserMsgId, role: 'user', content: q }]);
    setQuery('');

    try {
      const data = await apiClient.postQuery({
        query: q,
        conversation_id: conversationId || null,
      });

      if (!conversationId && data.conversation_id) {
        try { sessionStorage.setItem('temp_last_result', JSON.stringify(data)); } catch(e) {}
        router.push(`/c/${data.conversation_id}`);
      } else {
        setLastResult(data);
      }

      setMessages(prev => [...prev, { id: data.message_id || data.query_id, role: 'assistant', content: data.final_answer }]);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      if (e.nativeEvent.isComposing || e.keyCode === 229) return;
      e.preventDefault();
      submit(query);
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const isEmpty = messages.length === 0 && !loading && !error;

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0 relative bg-[#0a0f1c]">
      <Chat3DBackground isActive={!isEmpty} />

      {/* Main Chat Header */}
      {!isEmpty && (
        <div className="flex-none h-14 border-b border-border/30 bg-background/80 backdrop-blur-xl z-20 flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-foreground tracking-tight">Current Conversation</span>
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground/80 bg-primary/10 px-3 py-1.5 rounded-full border border-primary/20">
            <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            Grounded responses
          </div>
        </div>
      )}

      {/* Message Scroll Area */}
      <div className="flex-1 overflow-y-auto overscroll-y-none z-10 px-4 sm:px-8 py-6 scrollbar-thin scrollbar-thumb-border/50" style={{ overflowAnchor: 'none' }}>
        <div className="mx-auto max-w-4xl space-y-12 pb-48">
          
          {/* EMPTY STATE */}
          {isEmpty && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col items-center pt-24 text-center sm:pt-32"
            >
              <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-5 py-2 shadow-[0_0_20px_rgba(var(--primary),0.15)] backdrop-blur-md">
                <ShieldCheck className="size-4 text-primary" />
                <span className="text-xs font-bold tracking-widest text-primary uppercase">InsuraLens Intelligence</span>
              </div>
              <h1 className="text-balance text-4xl font-bold tracking-tight sm:text-6xl text-foreground drop-shadow-md leading-[1.15]">
                How can I help you?
              </h1>
              <p className="mt-6 max-w-xl text-pretty text-lg md:text-xl leading-relaxed text-muted-foreground">
                Ask about insurance policies and get answers grounded in trusted documents with verifiable citations.
              </p>
              
              <div className="mt-16 w-full max-w-3xl grid grid-cols-1 md:grid-cols-2 gap-4">
                {EXAMPLES.map((ex, i) => (
                  <motion.button
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + i * 0.1, duration: 0.5 }}
                    key={ex}
                    type="button"
                    onClick={() => {
                      setQuery(ex);
                      submit(ex);
                    }}
                    disabled={loading}
                    className="text-left rounded-2xl border border-white/5 bg-white/[0.02] p-5 transition-all duration-300 hover:border-primary/40 hover:bg-primary/5 hover:-translate-y-1 hover:shadow-[0_4px_20px_rgba(var(--primary),0.1)] group disabled:opacity-50 disabled:hover:translate-y-0"
                  >
                    <p className="text-sm font-medium text-muted-foreground group-hover:text-foreground leading-relaxed">{ex}</p>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {/* ACTIVE MESSAGES */}
          {messages.map((msg, idx) => {
            const isLastMessage = idx === messages.length - 1;
            const isAssistant = msg.role === 'assistant';
            const reviewTask = reviewTasks.find(r => r.message_id === msg.id) || 
                               (isLastMessage && lastResult?.review_task_id && (lastResult.message_id === msg.id || lastResult.query_id === msg.id) 
                                ? { status: lastResult.review_status || 'PENDING' } as ReviewTaskResponse : null);
            
            const displayContent = (reviewTask?.status === 'CORRECTED' && reviewTask.corrected_answer) 
              ? reviewTask.corrected_answer 
              : msg.content;
            
            if (!isAssistant) {
              return (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} key={msg.id} className="flex justify-end mb-6 w-full">
                  <div className="max-w-[75%] rounded-3xl rounded-tr-sm bg-card/60 backdrop-blur-md px-6 py-4 text-[15px] leading-relaxed text-foreground border border-white/5 shadow-sm">
                    {displayContent}
                  </div>
                </motion.div>
              );
            }

            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} key={msg.id} className="flex gap-5 mb-8 w-full max-w-4xl mx-auto">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 shadow-sm mt-1">
                  <img src="/logo.png" alt="InsuraLens" className="h-4 w-auto object-contain opacity-80" />
                </div>
                <div className="flex flex-col gap-4 min-w-0 flex-1">
                  
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-foreground">InsuraLens</span>
                    <span className="text-xs text-muted-foreground">•</span>
                    <span className="text-xs font-medium text-primary inline-flex items-center gap-1.5 bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                      <CheckCircle2 className="size-3" />
                      Grounded in retrieved sources
                    </span>
                  </div>
                  
                  <div className="prose prose-sm dark:prose-invert max-w-none text-[15px] leading-relaxed text-foreground/90">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {displayContent}
                    </ReactMarkdown>
                  </div>
                  
                  {/* Sources List if available */}
                  {isLastMessage && lastResult && lastResult.sources && lastResult.sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-border/40">
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Sources</p>
                      <div className="flex flex-wrap gap-2">
                        {lastResult.sources.map((src, i) => (
                          <button
                            key={i}
                            onClick={() => setActiveSource(src)}
                            className="inline-flex items-center gap-2 bg-card/50 hover:bg-primary/10 border border-white/5 hover:border-primary/30 rounded-lg px-3 py-1.5 transition-all text-sm group"
                          >
                            <span className="text-xs font-bold text-primary/70 group-hover:text-primary">[{i + 1}]</span>
                            <span className="text-foreground/80 font-medium truncate max-w-[200px]">{src.document.replace(/\.[^/.]+$/, "").replace(/_/g, " - ")}</span>
                            {src.page > 0 && <span className="text-xs text-muted-foreground">p. {src.page}</span>}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Message Actions */}
                  <div className="flex items-center gap-2 mt-2">
                    <button onClick={() => copyToClipboard(displayContent)} className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors px-2 py-1.5 rounded-md hover:bg-card">
                      <Copy className="size-3.5" /> Copy
                    </button>
                    {isLastMessage && (
                      <button onClick={() => {
                        const lastUserMsg = messages.filter(m => m.role === 'user').pop();
                        if (lastUserMsg) submit(lastUserMsg.content);
                      }} className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors px-2 py-1.5 rounded-md hover:bg-card">
                        <RotateCcw className="size-3.5" /> Regenerate
                      </button>
                    )}
                    {isLastMessage && lastResult?.confidence_score && (
                      <div className="ml-auto text-xs font-medium text-muted-foreground bg-card px-2 py-1 rounded-md border border-white/5">
                        Confidence: {Math.round(lastResult.confidence_score * 100)}%
                      </div>
                    )}
                  </div>

                  {reviewTask && reviewTask.status !== 'CORRECTED' && (
                    <div className="mt-2 text-xs font-medium text-amber-500 bg-amber-500/10 border border-amber-500/20 px-3 py-2 rounded-lg inline-flex items-center gap-2 w-fit">
                      <ShieldAlert className="size-4" />
                      Pending expert review
                    </div>
                  )}

                </div>
              </motion.div>
            );
          })}

          {/* LOADING STATE */}
          {loading && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-5 mb-8 w-full max-w-4xl mx-auto">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 border border-primary/20 shadow-sm mt-1">
                <div className="size-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              </div>
              <div className="flex flex-col justify-center min-h-[40px]">
                <div className="text-[15px] font-medium text-foreground/80 flex items-center gap-3">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary"></span>
                  </span>
                  {PROCESSING_STAGES[loadingStage]}
                </div>
              </div>
            </motion.div>
          )}

          {/* ERROR STATES */}
          {error && !loading && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-5 mb-8 w-full max-w-4xl mx-auto">
               <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-destructive/10 border border-destructive/20 mt-1">
                <AlertTriangle className="size-5 text-destructive" />
              </div>
              <div className="flex flex-col gap-2">
                <div className="text-[15px] font-semibold text-destructive">
                  {error.includes('503') || error.toLowerCase().includes('unavailable') 
                    ? "InsuraLens is temporarily unavailable." 
                    : (error.includes('safe') || error.toLowerCase().includes('refusal'))
                      ? "I couldn't provide a reliable answer from the available insurance documents."
                      : "A network or system error occurred."}
                </div>
                <div className="text-sm text-muted-foreground leading-relaxed max-w-2xl">
                   {error.includes('503') || error.toLowerCase().includes('unavailable') 
                    ? "The AI service could not process this request right now. Please try again in a few moments." 
                    : (error.includes('safe') || error.toLowerCase().includes('refusal'))
                      ? "The available sources do not contain enough relevant information to answer this question securely."
                      : error}
                </div>
                <div className="mt-2">
                  <button onClick={() => {
                        const lastUserMsg = messages.filter(m => m.role === 'user').pop();
                        if (lastUserMsg) submit(lastUserMsg.content);
                      }} className="inline-flex items-center gap-1.5 text-xs font-semibold text-foreground bg-card hover:bg-card/80 border border-white/10 px-3 py-1.5 rounded-lg transition-colors">
                    <RotateCcw className="size-3.5" /> Try again
                  </button>
                </div>
              </div>
            </motion.div>
          )}
          
          <div ref={messagesEndRef} className="h-1" />
        </div>
      </div>

      {/* COMPOSER */}
      <div className={`absolute left-0 right-0 z-20 pointer-events-none transition-all duration-500 ease-[0.16,1,0.3,1] ${isEmpty ? 'bottom-1/4 translate-y-1/2' : 'bottom-0'}`}>
        <div className="mx-auto w-full max-w-4xl px-4 sm:px-6 pb-6">
          <form onSubmit={(e) => { e.preventDefault(); submit(query); }} className="pointer-events-auto relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 via-accent/10 to-primary/20 rounded-[32px] blur-lg opacity-30 transition-opacity duration-500 group-focus-within:opacity-100" />
            <div className="relative flex flex-col rounded-[28px] border border-white/10 shadow-2xl transition-all duration-300 focus-within:border-primary/50 focus-within:shadow-[0_10px_40px_rgba(var(--primary),0.15)] bg-[#111524]/90 backdrop-blur-2xl">
              
              <div className="flex px-5 pt-4">
                <textarea
                  ref={textareaRef}
                  value={query}
                  onChange={handleInput}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  placeholder="Ask about policies, clauses, waiting periods, exclusions, benefits..."
                  className="w-full resize-none bg-transparent text-[15px] font-medium leading-relaxed outline-none placeholder:text-muted-foreground/60 text-foreground py-1"
                  aria-label="Composer input"
                />
              </div>

              <div className="flex items-center justify-between px-3 pb-3 pt-2">
                <div className="flex items-center gap-1">
                  <button type="button" className="p-2 text-muted-foreground hover:text-foreground transition-colors rounded-full hover:bg-white/5 relative group/attach">
                    <Paperclip className="size-4" />
                    <span className="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 bg-card border border-white/10 rounded-md text-[10px] font-semibold tracking-wide opacity-0 group-hover/attach:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                      Document upload coming soon
                    </span>
                  </button>
                </div>
                <div className="flex items-center gap-3">
                  <span className="hidden items-center gap-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground/50 sm:flex">
                    Enter to send
                  </span>
                  <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="flex size-10 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-[0_0_15px_rgba(var(--primary),0.3)] transition-all hover:scale-105 hover:shadow-[0_0_25px_rgba(var(--primary),0.5)] disabled:scale-100 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
                  >
                    <ArrowUp className="size-5" />
                  </button>
                </div>
              </div>

            </div>
          </form>
          {!isEmpty && (
            <div className="text-center mt-3 text-[10px] text-muted-foreground/50 font-medium tracking-wide">
              AI-generated information grounded in official policy documents.
            </div>
          )}
        </div>
      </div>

      {/* SOURCE DRAWER */}
      <AnimatePresence>
        {activeSource && (
          <>
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-background/60 backdrop-blur-sm z-40"
              onClick={() => setActiveSource(null)}
            />
            <motion.div 
              initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="absolute right-0 top-0 bottom-0 w-full sm:w-[400px] bg-card border-l border-border/50 z-50 shadow-2xl flex flex-col"
            >
              <div className="flex items-center justify-between p-5 border-b border-border/40 bg-background/50">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <FileText className="size-4 text-primary" />
                  Source Document
                </h3>
                <button onClick={() => setActiveSource(null)} className="p-1.5 text-muted-foreground hover:text-foreground rounded-md hover:bg-white/5 transition-colors">
                  <X className="size-4" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-1">Document Name</p>
                  <p className="text-[15px] font-medium text-foreground">{activeSource.document.replace(/\.[^/.]+$/, "").replace(/_/g, " ")}</p>
                </div>
                {activeSource.page > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-1">Page</p>
                    <p className="text-[15px] font-medium text-foreground">{activeSource.page}</p>
                  </div>
                )}
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-2">Retrieval Confidence</p>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 bg-background rounded-full overflow-hidden border border-white/5">
                      <div className="h-full bg-primary transition-all" style={{ width: `${activeSource.confidence * 100}%` }} />
                    </div>
                    <span className="text-sm font-bold tabular-nums text-foreground">{Math.round(activeSource.confidence * 100)}%</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-2">Relevant Passage</p>
                  <div className="rounded-xl border border-border/40 bg-background/40 p-4 relative">
                    <div className="absolute top-0 left-0 w-1 h-full bg-primary/50 rounded-l-xl" />
                    {activeSource.content_snippet ? (
                      <p className="text-[14px] leading-relaxed text-foreground/90 italic">
                        "{activeSource.content_snippet.trim()}"
                      </p>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">Snippet unavailable.</p>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
