"use client"

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiClient, ConversationResponse } from '@/lib/api-client';
import { useAuth } from '@/components/auth-provider';
import { Button } from '@/components/ui/button';
import { PlusCircle, MessageSquare, LogOut } from 'lucide-react';
import Link from 'next/link';

export function Sidebar() {
  const [conversations, setConversations] = useState<ConversationResponse[]>([]);
  const { logout, isAuthenticated } = useAuth();
  const router = useRouter();
  const params = useParams();
  const activeId = params.id as string;

  useEffect(() => {
    if (isAuthenticated) {
      loadConversations();
    }
  }, [isAuthenticated, activeId]);

  const loadConversations = async () => {
    try {
      const data = await apiClient.getConversations();
      // Assume the backend returns them in chronological order or we can sort them.
      setConversations(data.reverse());
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  };

  const handleNewChat = () => {
    router.push('/');
  };

  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-card">
      <div className="p-4">
        <Button onClick={handleNewChat} className="w-full justify-start gap-2" variant="default">
          <PlusCircle className="size-4" />
          New Chat
        </Button>
      </div>
      
      <div className="flex-1 overflow-y-auto px-2">
        <div className="space-y-1">
          {conversations.map((conv) => (
            <Link key={conv.id} href={`/c/${conv.id}`}>
              <Button
                variant={activeId === conv.id ? 'secondary' : 'ghost'}
                className="w-full justify-start gap-2 overflow-hidden px-2 text-left text-sm"
              >
                <MessageSquare className="size-4 shrink-0 text-muted-foreground" />
                <span className="truncate">{conv.title}</span>
              </Button>
            </Link>
          ))}
        </div>
      </div>

      <div className="p-4 border-t border-border">
        <Button onClick={logout} variant="ghost" className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground">
          <LogOut className="size-4" />
          Sign out
        </Button>
      </div>
    </div>
  );
}
