"use client"

import React, { useState } from 'react';
import { useAuth } from '@/components/auth-provider';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await apiClient.login(username, password);
      login(data.access_token);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#07111F] text-slate-200">
      <div className="w-full max-w-md space-y-8 rounded-xl border border-slate-800/60 bg-[#050A12] p-10 shadow-2xl">
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400 font-bold border border-cyan-500/20 mb-6">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">InsuraLens Console</h2>
          <p className="mt-2 text-sm text-slate-400">
            Secure access to operations & review dashboard
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md border border-destructive/20 bg-destructive/10 p-4 text-sm text-destructive flex items-center gap-3">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-slate-400 text-xs uppercase tracking-wider font-semibold">Username</Label>
              <Input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="bg-[#07111F] border-slate-800 text-slate-200 placeholder:text-slate-600 focus-visible:ring-cyan-500/50 h-11"
                placeholder="Enter your username"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-400 text-xs uppercase tracking-wider font-semibold">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-[#07111F] border-slate-800 text-slate-200 placeholder:text-slate-600 focus-visible:ring-cyan-500/50 h-11"
                placeholder="••••••••"
              />
            </div>
          </div>
          <Button type="submit" className="w-full bg-cyan-600 hover:bg-cyan-500 text-white h-11 text-base font-medium transition-colors" disabled={loading}>
            {loading ? 'Authenticating...' : 'Sign in'}
          </Button>
          <div className="text-center text-xs text-slate-500 pt-4">
            Access is restricted to authorized personnel only.
          </div>
        </form>
      </div>
    </div>
  );
}
