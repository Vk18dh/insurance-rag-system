import React, { useState } from 'react';
import { Button, TextField, Typography, Container, Box, Paper, CircularProgress, Chip } from '@mui/material';
import { apiClient } from '../services/apiClient';

interface Source {
  document: string;
  page: number;
}
interface QueryResponse {
  final_answer: string;
  is_safe: boolean;
  confidence_score: number;
  sources: Source[];
  execution_time_ms: number;
}

export const QueryDashboard: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  
  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await apiClient.post<QueryResponse>('/query', { query });
      setResult(response.data);
    } catch (err) {
      alert("Error executing query. Check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5">Insurance Knowledge Dashboard</Typography>
      </Box>
      
      <Paper sx={{ p: 4, mt: 4 }}>
        <form onSubmit={handleQuery}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField 
              fullWidth
              label="Ask an insurance question..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <Button
                variant="contained" 
                type="submit" 
                disabled={loading || !query}
                sx={{minWidth: 120}}
            >
              {loading ? <CircularProgress size={24} /> : 'Ask AI'}
            </Button>
          </Box>
        </form>
      </Paper>

      {result && (
        <Paper sx={{ p: 4, mt: 4, bgcolor: result.is_safe ? 'grey.50' : '#ffebee' }}>
          {result.confidence_score < 0.7 && (
            <Box sx={{ mb: 3, p: 2, bgcolor: "#ef5350", color: "white", borderRadius: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                ⚠️ LOW CONFIDENCE / OUT-OF-DOMAIN DETECTED
              </Typography>
              <Typography variant="body2">
                This query triggered the Uncertainty-Aware bounds (Confidence: {(result.confidence_score * 100).toFixed(0)}%). In the future Human-in-the-Loop phase, this is automatically routed to an expert for review.
              </Typography>
            </Box>
          )}
          {!result.is_safe && (
            <Box sx={{ mb: 3, p: 2, bgcolor: "#ff9800", color: "white", borderRadius: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                ⚠️ REGULATORY RISK / CONTRADICTION DETECTED
              </Typography>
              <Typography variant="body2">
                Agents identified potential policy contradictions or compliance risks in the source documents requiring Human-in-the-Loop validation securely.
              </Typography>
            </Box>
          )}
          <Typography variant="h6" gutterBottom>Final Answer</Typography>
          <Typography variant="body1" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>{result.final_answer}</Typography>
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2">Execution Time: {result.execution_time_ms.toFixed(2)}ms</Typography>
            <Typography variant="subtitle2" sx={{mt: 1, mb: 1}}>Sources:</Typography>
            {result.sources.map((s, idx) => (
              <Chip key={idx} label={`${s.document} (pg ${s.page})`} sx={{mr: 1, mb: 1}} />
            ))}
          </Box>
        </Paper>
      )}
    </Container>
  );
};
