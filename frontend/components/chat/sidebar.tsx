"use client"

import React, { useEffect, useState, useMemo } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { apiClient, ConversationResponse } from '@/lib/api-client';
import { useAuth } from '@/components/auth-provider';
import { Button } from '@/components/ui/button';
import { MessageSquare, LogOut, Search, User, Settings, SquarePen } from 'lucide-react';
import Link from 'next/link';

export function Sidebar() {
  const [conversations, setConversations] = useState<ConversationResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
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
      setConversations(data);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  };

  const handleNewChat = () => {
    router.push('/chat');
  };

  const filteredConversations = useMemo(() => {
    return conversations.filter(c => c.title.toLowerCase().includes(searchQuery.toLowerCase()));
  }, [conversations, searchQuery]);

  // Mock grouping based on array index since API lacks timestamps
  const grouped = useMemo(() => {
    const groups: Record<string, ConversationResponse[]> = {
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Older': []
    };
    
    filteredConversations.forEach((conv, idx) => {
      if (idx === 0) groups['Today'].push(conv);
      else if (idx === 1) groups['Yesterday'].push(conv);
      else if (idx >= 2 && idx <= 5) groups['Previous 7 Days'].push(conv);
      else groups['Older'].push(conv);
    });

    return groups;
  }, [filteredConversations]);

  return (
    <div className="flex h-full w-[280px] flex-col border-r border-border/40 bg-[#070b14]/90 backdrop-blur-3xl relative z-10 transition-all">
      
      {/* Brand Header */}
      <div className="p-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group transition-opacity hover:opacity-80">
          <img src="/logo.png" alt="InsuraLens" className="h-6 w-auto object-contain" />
        </Link>
      </div>

      <div className="px-4 pb-4 space-y-4">
        {/* New Chat Button */}
        <button 
          onClick={handleNewChat} 
          className="w-full flex items-center justify-between bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 hover:border-primary/40 transition-colors px-3 py-2.5 rounded-lg group"
        >
          <span className="text-sm font-medium">New Chat</span>
          <SquarePen className="size-4 group-hover:scale-110 transition-transform" />
        </button>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="Search conversations..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-card/40 border border-border/50 rounded-lg pl-9 pr-3 py-2 text-sm text-foreground outline-none focus:border-primary/50 transition-colors placeholder:text-muted-foreground/60"
          />
        </div>
      </div>
      
      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto overscroll-y-none px-3 pb-4 scrollbar-thin scrollbar-thumb-border/50">
        {Object.entries(grouped).map(([groupName, convs]) => {
          if (convs.length === 0) return null;
          return (
            <div key={groupName} className="mb-6">
              <div className="mb-2 px-3 text-[11px] font-semibold text-muted-foreground/60 tracking-wider">
                {groupName}
              </div>
              <div className="space-y-0.5">
                {convs.map((conv) => {
                  const isActive = activeId === conv.id;
                  return (
                    <Link key={conv.id} href={`/c/${conv.id}`} className="block">
                      <div
                        className={`group relative flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                          isActive 
                            ? 'bg-primary/10 text-primary' 
                            : 'text-muted-foreground hover:bg-card/60 hover:text-foreground'
                        }`}
                      >
                        <MessageSquare className={`size-4 shrink-0 ${isActive ? 'text-primary' : 'text-muted-foreground/60'}`} />
                        <span className="truncate font-medium flex-1">{conv.title}</span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
        
        {conversations.length === 0 && (
          <div className="px-3 py-6 text-center text-sm text-muted-foreground">
            No recent conversations.
          </div>
        )}
      </div>

      {/* User Profile Footer */}
      <div className="p-3 border-t border-border/40 bg-card/20">
        <div className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-card/60 transition-colors cursor-pointer group">
          <div className="size-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-medium shrink-0">
            GU
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">Guest User</p>
            <p className="text-xs text-muted-foreground truncate">Free Plan</p>
          </div>
          <button onClick={logout} className="p-1.5 text-muted-foreground hover:text-destructive transition-colors rounded-md hover:bg-destructive/10" aria-label="Sign out">
            <LogOut className="size-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
