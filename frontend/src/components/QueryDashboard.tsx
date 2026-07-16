import React, { useState, useEffect, useRef } from 'react';
import {
  Button, TextField, Typography, Container, Box, Paper, CircularProgress, Chip,
  LinearProgress, Divider
} from '@mui/material';
import ReactMarkdown from 'react-markdown';
import { apiClient } from '../services/apiClient';

interface Source {
  document: string;
  page: number;
  content_snippet?: string;
}
interface AgentStep {
  agent_name: string;
  duration_ms: number;
  status: string;
}
interface QueryResponse {
  final_answer: string;
  is_safe: boolean;
  sources: Source[];
  execution_time_ms: number;
  agent_steps?: AgentStep[];
}

// ── The full ordered pipeline ──────────────────────────────────────────────
const PIPELINE_AGENTS = [
  { name: 'QueryUnderstandingAgent', label: 'Query Analysis',     emoji: '🔍' },
  { name: 'RetrievalAgent',          label: 'Document Retrieval', emoji: '📚' },
  { name: 'VerificationAgent',       label: 'Evidence Check',     emoji: '✅' },
  { name: 'ReasoningAgent',          label: 'AI Reasoning',       emoji: '🧠' },
  { name: 'RiskAssessmentAgent',     label: 'Risk Assessment',    emoji: '⚠️' },
  { name: 'ContradictionAgent',      label: 'Contradiction Scan', emoji: '🔄' },
  { name: 'ResponseBuilder',         label: 'Response Building',  emoji: '✍️' },
];

type AgentStatus = 'idle' | 'running' | 'success' | 'failure';

interface LiveAgent {
  name: string;
  label: string;
  emoji: string;
  status: AgentStatus;
  duration_ms?: number;
}

export const QueryDashboard: React.FC = () => {
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [liveAgents, setLiveAgents] = useState<LiveAgent[]>([]);
  const [activeAgentIdx, setActiveAgentIdx] = useState<number>(-1);
  const tickerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Animate agents stepping through the pipeline while loading
  useEffect(() => {
    if (loading) {
      const initial: LiveAgent[] = PIPELINE_AGENTS.map(a => ({ ...a, status: 'idle' }));
      setLiveAgents(initial);
      setActiveAgentIdx(0);
    } else {
      if (tickerRef.current) clearInterval(tickerRef.current);
    }
  }, [loading]);

  useEffect(() => {
    if (!loading || activeAgentIdx < 0) return;
    if (activeAgentIdx >= PIPELINE_AGENTS.length) return;

    setLiveAgents(prev => prev.map((a, i) => ({
      ...a,
      status: i < activeAgentIdx ? 'success' : i === activeAgentIdx ? 'running' : 'idle',
    })));

    tickerRef.current = setInterval(() => {
      setActiveAgentIdx(prev => {
        const next = prev + 1;
        return next <= PIPELINE_AGENTS.length ? next : prev;
      });
    }, 1800);

    return () => { if (tickerRef.current) clearInterval(tickerRef.current); };
  }, [activeAgentIdx, loading]);

  // When result comes back, reconcile with actual execution history
  const reconcileAgents = (steps: AgentStep[]) => {
    const stepMap: Record<string, AgentStep> = {};
    steps.forEach(s => { stepMap[s.agent_name] = s; });

    setLiveAgents(PIPELINE_AGENTS.map(a => {
      const step = stepMap[a.name];
      if (!step) return { ...a, status: 'idle' };
      return {
        ...a,
        status: step.status === 'SUCCESS' || step.status === 'success' ? 'success'
              : step.status === 'FAILURE' || step.status === 'failure' ? 'failure'
              : 'success',
        duration_ms: step.duration_ms,
      };
    }));
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedQuery(query);
    setLoading(true);
    setResult(null);
    setActiveAgentIdx(0);
    try {
      const response = await apiClient.post<QueryResponse>('/query', { query });
      setResult(response.data);
      if (response.data.agent_steps?.length) {
        reconcileAgents(response.data.agent_steps);
      } else {
        // Mark all as succeeded if no agent data returned
        setLiveAgents(PIPELINE_AGENTS.map(a => ({ ...a, status: 'success' })));
      }
    } catch (err) {
      setLiveAgents(PIPELINE_AGENTS.map(a => ({ ...a, status: 'failure' })));
      alert('Error executing query. Check console.');
    } finally {
      setLoading(false);
    }
  };

  const agentColor = (status: AgentStatus) => {
    if (status === 'running') return '#2196f3';
    if (status === 'success') return '#4caf50';
    if (status === 'failure') return '#f44336';
    return '#555';
  };

  const agentBg = (status: AgentStatus) => {
    if (status === 'running') return 'rgba(33,150,243,0.12)';
    if (status === 'success') return 'rgba(76,175,80,0.10)';
    if (status === 'failure') return 'rgba(244,67,54,0.10)';
    return 'rgba(255,255,255,0.03)';
  };

  const isFallback = result?.final_answer?.includes("could not find this information") || result?.final_answer?.includes("fallback");

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, mb: 1 }}>
        <Typography variant="h5" fontWeight={700}>AI-Driven Insurance Knowledge Assessment System</Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          Powered by OpenRouter · Phase 1 RAG + Phase 2 Multi-Agent Pipeline
        </Typography>
      </Box>

      {/* ── Query Input ── */}
      <Paper sx={{ p: 3, mt: 2 }}>
        <form onSubmit={handleQuery}>
          <Box display="flex" gap={2}>
            <TextField
              fullWidth
              label="Ask questions about your LIC Policies and IRDAI Guidelines..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              variant="outlined"
            />
            <Button
              variant="contained"
              type="submit"
              disabled={loading || !query}
              sx={{ minWidth: 120, borderRadius: 2 }}
            >
              {loading ? <CircularProgress size={22} color="inherit" /> : 'Ask AI'}
            </Button>
          </Box>
        </form>
      </Paper>

      {/* ── Conditional Rendering ── */}
      {isFallback ? (
        <Box sx={{ mt: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* User Query Bubble */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, bgcolor: '#1e2126', p: 2, borderRadius: 2 }}>
            <Box sx={{ width: 40, height: 40, bgcolor: '#f44336', display: 'flex', justifyContent: 'center', alignItems: 'center', borderRadius: 2, flexShrink: 0 }}>
              <span style={{ fontSize: '1.2rem' }}>👦</span>
            </Box>
            <Typography variant="body1">{submittedQuery}</Typography>
          </Box>

          {/* Bot Fallback Bubble */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, bgcolor: '#1e2126', p: 2, borderRadius: 2 }}>
            <Box sx={{ width: 40, height: 40, bgcolor: '#ff9800', display: 'flex', justifyContent: 'center', alignItems: 'center', borderRadius: 2, flexShrink: 0 }}>
              <span style={{ fontSize: '1.2rem' }}>🤖</span>
            </Box>
            <Typography variant="body1">{result?.final_answer}</Typography>
          </Box>
        </Box>
      ) : (
        <>
          {/* ── Live Agent Activity Panel ── */}
          {(loading || (liveAgents.length > 0 && result)) && (
            <Paper sx={{ p: 3, mt: 3, border: '1px solid rgba(255,255,255,0.08)' }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                🤖 Agent Pipeline Activity
              </Typography>
              {loading && <LinearProgress sx={{ mb: 2, borderRadius: 1 }} />}

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {liveAgents.map((agent, idx) => (
                  <Box
                    key={idx}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      p: 1.5,
                      borderRadius: 2,
                      border: `1px solid ${agent.status === 'running' ? '#2196f3' : 'transparent'}`,
                      background: agentBg(agent.status),
                      transition: 'all 0.4s ease',
                      animation: agent.status === 'running' ? 'pulse 1.4s ease-in-out infinite' : 'none',
                      '@keyframes pulse': {
                        '0%, 100%': { opacity: 1 },
                        '50%':       { opacity: 0.6 },
                      },
                    }}
                  >
                    <Typography sx={{ fontSize: '1.2rem', width: 28, textAlign: 'center' }}>
                      {agent.emoji}
                    </Typography>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" fontWeight={600} sx={{ color: agentColor(agent.status) }}>
                        {agent.label}
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                        {agent.name}
                      </Typography>
                    </Box>
                    <Box sx={{ minWidth: 100, textAlign: 'right' }}>
                      {agent.status === 'running' && (
                        <Typography variant="caption" sx={{ color: '#2196f3', fontStyle: 'italic' }}>
                          ● Running…
                        </Typography>
                      )}
                      {agent.status === 'success' && (
                        <Typography variant="caption" sx={{ color: '#4caf50' }}>
                          ✓ {agent.duration_ms ? `${agent.duration_ms.toFixed(0)}ms` : 'Done'}
                        </Typography>
                      )}
                      {agent.status === 'failure' && (
                        <Typography variant="caption" sx={{ color: '#f44336' }}>
                          ✗ Failed
                        </Typography>
                      )}
                      {agent.status === 'idle' && (
                        <Typography variant="caption" sx={{ color: 'text.disabled' }}>
                          — Waiting
                        </Typography>
                      )}
                    </Box>
                  </Box>
                ))}
              </Box>
            </Paper>
          )}

          {/* ── Results ── */}
          {result && (
            <Paper sx={{ p: 4, mt: 3 }}>
              <Typography variant="h6" gutterBottom>Final Answer</Typography>
              <Box sx={{
                typography: 'body1', mb: 2,
                '& p': { mb: 2 }, '& ul': { pl: 3, mb: 2 }, '& li': { mb: 1 },
                '& strong': { color: 'primary.light' },
              }}>
                <ReactMarkdown>{result.final_answer}</ReactMarkdown>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  ⏱ Total: {result.execution_time_ms.toFixed(0)}ms
                </Typography>
                <Typography variant="caption" sx={{ color: result.is_safe ? '#4caf50' : '#f44336' }}>
                  {result.is_safe ? '✓ Safe to display' : '⚠ Human review recommended'}
                </Typography>
              </Box>

              {result.sources && result.sources.length > 0 && (
                <Box mt={2}>
                  <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
                    📄 Referenced Sources:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {result.sources.map((s, idx) => (
                      <Chip
                        key={idx}
                        label={`${s.document} (pg ${s.page})`}
                        color="secondary"
                        variant="outlined"
                        size="small"
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Paper>
          )}
        </>
      )}
    </Container>
  );
};
